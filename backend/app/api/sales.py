"""Endpoints da API de Vendas — listagem e resumo."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.models.sale import Sale
from app.models.user import User
from app.schemas.sale import VendaResponse, ResumoVendas
from app.schemas.base import PaginacaoResponse

from datetime import date

logger = logging.getLogger("kingban.api.vendas")
router = APIRouter()


def _sale_to_response(sale: Sale) -> VendaResponse:
    """Converte model Sale para resposta PT."""
    return VendaResponse(
        id=sale.id,
        data=sale.date,
        numero_pedido=sale.order_number,
        nome_cliente=sale.client_name,
        cnpj_cpf_cliente=sale.client_cnpj_cpf,
        codigo_produto=sale.product_code,
        nome_produto=sale.product_name,
        quantidade=sale.quantity or 0,
        unidade=sale.unit or "UN",
        origem_frete=sale.shipping_origin,
        preco_unitario=sale.unit_price or 0,
        valor_total=sale.total_value or 0,
        desconto=sale.discount or 0,
        custo_unitario=sale.cost_per_unit or 0,
        custo_total=sale.cost_total or 0,
        valor_nf=sale.nf_value or 0,
        imposto=sale.tax_amount or 0,
        lucro_total=sale.profit_total or 0,
        forma_pagamento=sale.payment_method,
        vendedor_id=sale.salesperson_id,
        criado_em=sale.criado_em,
    )


@router.get("", response_model=PaginacaoResponse[VendaResponse])
async def listar_vendas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busca: str | None = Query(None),
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    vendedor_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista vendas com paginacao e filtros."""
    query = select(Sale).where(Sale.tenant_id == tenant_id)

    if data_inicio:
        query = query.where(Sale.date >= data_inicio)
    if data_fim:
        query = query.where(Sale.date <= data_fim)
    if vendedor_id:
        query = query.where(Sale.salesperson_id == vendedor_id)
    if busca:
        termo = f"%{busca}%"
        query = query.where(
            Sale.client_name.ilike(termo) | Sale.product_name.ilike(termo)
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(Sale.date.desc(), Sale.id.desc())
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    vendas = [_sale_to_response(s) for s in result.scalars().all()]

    return PaginacaoResponse(
        itens=vendas, total=total, pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/resumo", response_model=ResumoVendas)
async def resumo_vendas(
    data_inicio: date | None = Query(None),
    data_fim: date | None = Query(None),
    vendedor_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Resumo de vendas por periodo."""
    query = select(
        func.coalesce(func.sum(Sale.total_value), 0).label("total_vendas"),
        func.coalesce(func.sum(Sale.cost_total), 0).label("total_custos"),
        func.coalesce(func.sum(Sale.tax_amount), 0).label("total_impostos"),
        func.coalesce(func.sum(Sale.profit_total), 0).label("total_lucro"),
        func.count(Sale.id).label("quantidade_vendas"),
    ).where(Sale.tenant_id == tenant_id)

    if data_inicio:
        query = query.where(Sale.date >= data_inicio)
    if data_fim:
        query = query.where(Sale.date <= data_fim)
    if vendedor_id:
        query = query.where(Sale.salesperson_id == vendedor_id)

    result = (await db.execute(query)).first()

    return ResumoVendas(
        total_vendas=result.total_vendas,
        total_custos=result.total_custos,
        total_impostos=result.total_impostos,
        total_lucro=result.total_lucro,
        quantidade_vendas=result.quantidade_vendas,
    )
