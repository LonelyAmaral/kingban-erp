"""Endpoints da API de Produtos — CRUD completo."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProdutoCriar, ProdutoAtualizar, ProdutoResponse
from app.schemas.base import PaginacaoResponse, MensagemResponse

logger = logging.getLogger("kingban.api.produtos")
router = APIRouter()


@router.get("", response_model=PaginacaoResponse[ProdutoResponse])
async def listar_produtos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busca: str | None = Query(None, description="Busca por codigo, nome ou categoria"),
    ordenar: str = Query("nome"),
    direcao: str = Query("asc"),
    ativo: bool | None = Query(None),
    categoria: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista produtos com paginacao e busca."""
    query = select(Product).where(Product.tenant_id == tenant_id)

    if ativo is not None:
        query = query.where(Product.ativo == ativo)

    if categoria:
        query = query.where(Product.categoria == categoria)

    if busca:
        termo = f"%{busca}%"
        query = query.where(
            or_(
                Product.codigo.ilike(termo),
                Product.nome.ilike(termo),
                Product.categoria.ilike(termo),
                Product.ncm.ilike(termo),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    campo = getattr(Product, ordenar, Product.nome)
    if direcao == "desc":
        query = query.order_by(campo.desc())
    else:
        query = query.order_by(campo.asc())

    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    produtos = result.scalars().all()

    return PaginacaoResponse(
        itens=produtos,
        total=total,
        pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/categorias", response_model=list[str])
async def listar_categorias(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista todas as categorias de produtos distintas."""
    result = await db.execute(
        select(Product.categoria)
        .where(Product.tenant_id == tenant_id, Product.categoria.isnot(None))
        .distinct()
        .order_by(Product.categoria)
    )
    return [row[0] for row in result.all()]


@router.get("/{produto_id}", response_model=ProdutoResponse)
async def obter_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Obtem um produto pelo ID."""
    result = await db.execute(
        select(Product).where(Product.id == produto_id, Product.tenant_id == tenant_id)
    )
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    return produto


@router.post("", response_model=ProdutoResponse, status_code=status.HTTP_201_CREATED)
async def criar_produto(
    dados: ProdutoCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria um novo produto."""
    # Verificar codigo duplicado no tenant
    existe = await db.execute(
        select(Product).where(
            Product.tenant_id == tenant_id,
            Product.codigo == dados.codigo,
        )
    )
    if existe.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Ja existe um produto com o codigo '{dados.codigo}'"
        )

    produto = Product(tenant_id=tenant_id, **dados.model_dump())
    db.add(produto)
    await db.flush()

    await log_action(db, user.id, tenant_id, "products", produto.id, "CREATE",
                     new_values=dados.model_dump())

    logger.info("Produto criado: %s - %s (ID %d)", dados.codigo, dados.nome, produto.id)
    return produto


@router.put("/{produto_id}", response_model=ProdutoResponse)
async def atualizar_produto(
    produto_id: int,
    dados: ProdutoAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Atualiza um produto existente."""
    result = await db.execute(
        select(Product).where(Product.id == produto_id, Product.tenant_id == tenant_id)
    )
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    update_data = dados.model_dump(exclude_unset=True)

    # Se esta mudando o codigo, verificar duplicidade
    if "codigo" in update_data and update_data["codigo"] != produto.codigo:
        existe = await db.execute(
            select(Product).where(
                Product.tenant_id == tenant_id,
                Product.codigo == update_data["codigo"],
                Product.id != produto_id,
            )
        )
        if existe.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail=f"Ja existe um produto com o codigo '{update_data['codigo']}'"
            )

    old_values = {}
    for campo, valor in update_data.items():
        old_values[campo] = getattr(produto, campo)
        setattr(produto, campo, valor)

    if update_data:
        await db.flush()
        await log_action(db, user.id, tenant_id, "products", produto.id, "UPDATE",
                         old_values=old_values, new_values=update_data)

    return produto


@router.delete("/{produto_id}", response_model=MensagemResponse)
async def excluir_produto(
    produto_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Exclui um produto (soft delete)."""
    result = await db.execute(
        select(Product).where(Product.id == produto_id, Product.tenant_id == tenant_id)
    )
    produto = result.scalar_one_or_none()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    produto.ativo = False
    await db.flush()

    await log_action(db, user.id, tenant_id, "products", produto.id, "DELETE",
                     old_values={"ativo": True}, new_values={"ativo": False})

    return MensagemResponse(mensagem=f"Produto '{produto.codigo} - {produto.nome}' desativado com sucesso")
