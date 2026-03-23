"""Endpoints da API de Estoque — saldo, entradas, saidas."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.inventory import Inventory, InventoryEntry, InventoryExit
from app.models.product import Product
from app.models.user import User
from app.schemas.inventory import (
    EstoqueAtual, EntradaCriar, EntradaResponse,
    SaidaCriar, SaidaResponse,
)
from app.schemas.base import PaginacaoResponse, MensagemResponse
from app.services.inventory_service import add_entry, add_exit, recalculate_inventory

from datetime import date

logger = logging.getLogger("kingban.api.estoque")
router = APIRouter()


@router.get("/saldo", response_model=list[EstoqueAtual])
async def listar_saldo(
    busca: str | None = Query(None),
    apenas_criticos: bool = Query(False, description="Apenas produtos com estoque abaixo do minimo"),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista saldo atual de estoque com detalhes do produto."""
    query = (
        select(
            Product.codigo,
            Product.nome,
            Product.categoria,
            func.coalesce(Inventory.current_qty, 0).label("qty"),
            Product.preco_nf_integral,
            func.coalesce(Inventory.min_qty, 0).label("min_qty"),
            Inventory.last_entry_date,
            Inventory.last_exit_date,
        )
        .outerjoin(Inventory, (Product.id == Inventory.product_id) & (Inventory.tenant_id == tenant_id))
        .where(Product.tenant_id == tenant_id, Product.ativo == True)
    )

    if busca:
        termo = f"%{busca}%"
        query = query.where(Product.codigo.ilike(termo) | Product.nome.ilike(termo))

    if apenas_criticos:
        query = query.where(func.coalesce(Inventory.current_qty, 0) <= func.coalesce(Inventory.min_qty, 0))

    query = query.order_by(Product.codigo)
    result = await db.execute(query)
    rows = result.all()

    return [
        EstoqueAtual(
            codigo=r.codigo, nome=r.nome, categoria=r.categoria,
            quantidade_atual=r.qty,
            preco_unitario=r.preco_nf_integral or 0,
            valor_total=(r.qty or 0) * (r.preco_nf_integral or 0),
            quantidade_minima=r.min_qty,
            ultima_entrada=r.last_entry_date,
            ultima_saida=r.last_exit_date,
        )
        for r in rows
    ]


@router.get("/entradas", response_model=PaginacaoResponse[EntradaResponse])
async def listar_entradas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista entradas de estoque."""
    query = select(InventoryEntry).where(InventoryEntry.tenant_id == tenant_id)

    if data_inicio:
        query = query.where(InventoryEntry.date >= data_inicio)
    if data_fim:
        query = query.where(InventoryEntry.date <= data_fim)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(InventoryEntry.date.desc(), InventoryEntry.id.desc())
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    entradas = []
    for e in result.scalars().all():
        entradas.append(EntradaResponse(
            id=e.id, data=e.date, produto_id=e.product_id,
            codigo_produto=e.product_code, nome_produto=e.product_name,
            quantidade=e.quantity, tipo_entrada=e.entry_type,
            fornecedor_id=e.supplier_id, observacoes=e.notes,
            criado_em=e.criado_em,
        ))

    return PaginacaoResponse(
        itens=entradas, total=total, pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.post("/entradas", response_model=EntradaResponse, status_code=status.HTTP_201_CREATED)
async def criar_entrada(
    dados: EntradaCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria uma entrada de estoque."""
    # Buscar produto para codigo/nome se nao informados
    code = dados.codigo_produto or ""
    name = dados.nome_produto or ""
    if not code or not name:
        prod_r = await db.execute(select(Product).where(Product.id == dados.produto_id))
        prod = prod_r.scalar_one_or_none()
        if prod:
            code = code or prod.codigo
            name = name or prod.nome

    entry = await add_entry(
        db, tenant_id, dados.produto_id, code, name,
        dados.quantidade, dados.tipo_entrada,
        entry_date=dados.data, supplier_id=dados.fornecedor_id,
        notes=dados.observacoes,
    )
    if not entry:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")

    await db.flush()
    await log_action(db, user.id, tenant_id, "inventory_entries", entry.id, "CREATE",
                     new_values={"produto": code, "qtd": dados.quantidade, "tipo": dados.tipo_entrada})

    return EntradaResponse(
        id=entry.id, data=entry.date, produto_id=entry.product_id,
        codigo_produto=entry.product_code, nome_produto=entry.product_name,
        quantidade=entry.quantity, tipo_entrada=entry.entry_type,
        fornecedor_id=entry.supplier_id, observacoes=entry.notes,
        criado_em=entry.criado_em,
    )


@router.get("/saidas", response_model=PaginacaoResponse[SaidaResponse])
async def listar_saidas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista saidas de estoque."""
    query = select(InventoryExit).where(InventoryExit.tenant_id == tenant_id)

    if data_inicio:
        query = query.where(InventoryExit.date >= data_inicio)
    if data_fim:
        query = query.where(InventoryExit.date <= data_fim)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(InventoryExit.date.desc(), InventoryExit.id.desc())
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    saidas = []
    for s in result.scalars().all():
        saidas.append(SaidaResponse(
            id=s.id, data=s.date, produto_id=s.product_id,
            codigo_produto=s.product_code, nome_produto=s.product_name,
            quantidade=s.quantity, nome_cliente=s.client_name,
            tipo_saida=s.exit_type, venda_id=s.sale_id,
            observacoes=s.notes, criado_em=s.criado_em,
        ))

    return PaginacaoResponse(
        itens=saidas, total=total, pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.post("/saidas", response_model=SaidaResponse, status_code=status.HTTP_201_CREATED)
async def criar_saida(
    dados: SaidaCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria uma saida de estoque."""
    code = dados.codigo_produto or ""
    name = dados.nome_produto or ""
    if not code or not name:
        prod_r = await db.execute(select(Product).where(Product.id == dados.produto_id))
        prod = prod_r.scalar_one_or_none()
        if prod:
            code = code or prod.codigo
            name = name or prod.nome

    exit_rec = await add_exit(
        db, tenant_id, dados.produto_id, code, name,
        dados.quantidade, dados.tipo_saida,
        client_name=dados.nome_cliente, exit_date=dados.data,
        notes=dados.observacoes,
    )
    if not exit_rec:
        raise HTTPException(status_code=400, detail="Quantidade deve ser maior que zero")

    await db.flush()
    await log_action(db, user.id, tenant_id, "inventory_exits", exit_rec.id, "CREATE",
                     new_values={"produto": code, "qtd": dados.quantidade, "tipo": dados.tipo_saida})

    return SaidaResponse(
        id=exit_rec.id, data=exit_rec.date, produto_id=exit_rec.product_id,
        codigo_produto=exit_rec.product_code, nome_produto=exit_rec.product_name,
        quantidade=exit_rec.quantity, nome_cliente=exit_rec.client_name,
        tipo_saida=exit_rec.exit_type, venda_id=exit_rec.sale_id,
        observacoes=exit_rec.notes, criado_em=exit_rec.criado_em,
    )


@router.post("/recalcular/{produto_id}", response_model=MensagemResponse)
async def recalcular_estoque(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Recalcula o estoque de um produto a partir do historico."""
    await recalculate_inventory(db, produto_id, tenant_id)
    return MensagemResponse(mensagem="Estoque recalculado com sucesso")
