"""API de Comissoes — relatorio por vendedor/periodo + custos."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_action
from app.models.commission import CommissionCost
from app.models.salesperson import Salesperson
from app.models.user import User
from app.schemas.commission import (
    RelatorioComissaoRequest, RelatorioComissaoResponse,
    CustoComissaoCriar, CustoComissaoResponse,
)
from app.services.commission import generate_commission_report

router = APIRouter()


@router.post("/relatorio", response_model=RelatorioComissaoResponse)
async def gerar_relatorio(
    dados: RelatorioComissaoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Gera relatorio de comissao para um vendedor em um periodo."""
    try:
        report = await generate_commission_report(
            db=db,
            tenant_id=user.tenant_id,
            salesperson_id=dados.vendedor_id,
            period_start=dados.data_inicio,
            period_end=dados.data_fim,
            gratification=dados.gratificacao,
            advances=dados.adiantamentos,
            other_commission=dados.outras_comissoes,
        )
    except ValueError as e:
        raise HTTPException(404, str(e))

    # Mapear chaves EN para PT
    itens_pt = []
    for item in report["items"]:
        itens_pt.append({
            "venda_id": item["sale_id"],
            "data": item["date"],
            "codigo_produto": item["product_code"],
            "nome_produto": item["product_name"],
            "quantidade": item["quantity"],
            "preco_unitario": item["unit_price"],
            "total_venda": item["total_sale"],
            "valor_nf_unitario": item["nf_unit_value"],
            "total_nf": item["nf_total"],
            "nome_cliente": item["client_name"],
            "origem_envio": item["shipping_origin"],
            "custo_total_unitario": item["cost_total_unit"],
            "liquido_unitario": item["liquid_per_unit"],
            "liquido_total": item["liquid_total"],
            "taxa_comissao": item["commission_rate"],
            "valor_comissao": item["commission_value"],
        })

    return {
        "vendedor_id": report["salesperson_id"],
        "nome_vendedor": report["salesperson_name"],
        "data_inicio": report["period_start"],
        "data_fim": report["period_end"],
        "total_vendas": report["total_sales"],
        "total_nf": report["total_nf"],
        "total_liquido": report["total_liquid"],
        "total_comissao": report["total_commission"],
        "outras_comissoes": report["other_commission"],
        "salario_fixo": report["fixed_salary"],
        "gratificacao": report["gratification"],
        "adiantamentos": report["advances"],
        "bruto_total": report["gross_total"],
        "saldo": report["balance"],
        "itens": itens_pt,
    }


@router.get("/vendedores")
async def listar_vendedores(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista vendedores ativos para selecao no relatorio."""
    result = await db.execute(
        select(Salesperson)
        .where(Salesperson.tenant_id == user.tenant_id, Salesperson.ativo == True)
        .order_by(Salesperson.nome)
    )
    vendedores = result.scalars().all()
    return [{"id": v.id, "nome": v.nome} for v in vendedores]


# --- Custos de Comissao (tabela de custo base por produto) ---

@router.get("/custos")
async def listar_custos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(100, ge=1, le=500),
    busca: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista custos de comissao cadastrados."""
    tenant_id = user.tenant_id
    query = select(CommissionCost).where(CommissionCost.tenant_id == tenant_id)

    if busca:
        query = query.where(
            CommissionCost.product_name.ilike(f"%{busca}%")
            | CommissionCost.product_code.ilike(f"%{busca}%")
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(CommissionCost.product_code)
    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    custos = result.scalars().all()

    return {
        "itens": [
            {
                "id": c.id,
                "produto_id": c.product_id,
                "codigo_produto": c.product_code,
                "nome_produto": c.product_name,
                "custo_base": c.base_cost,
                "taxa_comissao": c.commission_rate,
            }
            for c in custos
        ],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina if total > 0 else 1,
    }


@router.post("/custos")
async def criar_custo(
    dados: CustoComissaoCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cria ou atualiza custo de comissao para um produto."""
    tenant_id = user.tenant_id

    # Verifica se ja existe para o produto
    result = await db.execute(
        select(CommissionCost).where(
            CommissionCost.tenant_id == tenant_id,
            CommissionCost.product_id == dados.produto_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.base_cost = dados.custo_base
        existing.commission_rate = dados.taxa_comissao
        if dados.codigo_produto:
            existing.product_code = dados.codigo_produto
        if dados.nome_produto:
            existing.product_name = dados.nome_produto
        await db.flush()
        await log_action(db, user.id, tenant_id, "commission_costs", existing.id, "UPDATE")
        custo = existing
    else:
        custo = CommissionCost(
            tenant_id=tenant_id,
            product_id=dados.produto_id,
            product_code=dados.codigo_produto,
            product_name=dados.nome_produto,
            base_cost=dados.custo_base,
            commission_rate=dados.taxa_comissao,
        )
        db.add(custo)
        await db.flush()
        await log_action(db, user.id, tenant_id, "commission_costs", custo.id, "CREATE")

    return {
        "id": custo.id,
        "produto_id": custo.product_id,
        "codigo_produto": custo.product_code,
        "nome_produto": custo.product_name,
        "custo_base": custo.base_cost,
        "taxa_comissao": custo.commission_rate,
    }
