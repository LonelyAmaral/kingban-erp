"""API de Relatorios — DRE simplificado."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.models.sale import Sale
from app.models.cashflow import CashFlowEntry
from app.models.user import User

router = APIRouter()


@router.get("/dre")
async def dre_simplificado(
    data_inicio: str = Query(None, description="YYYY-MM-DD"),
    data_fim: str = Query(None, description="YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    DRE Simplificado — Demonstracao do Resultado do Exercicio.

    Receita bruta (vendas)
    (-) Impostos (NF * 8.5%)
    (-) Custo dos produtos vendidos
    (=) Lucro bruto
    (-) Despesas operacionais (do fluxo de caixa)
    (=) Lucro liquido
    """
    tenant_id = user.tenant_id
    start = date.fromisoformat(data_inicio) if data_inicio else None
    end = date.fromisoformat(data_fim) if data_fim else None

    # --- Vendas ---
    sales_query = select(
        func.coalesce(func.sum(Sale.total_value), 0).label("receita_bruta"),
        func.coalesce(func.sum(Sale.tax_amount), 0).label("impostos"),
        func.coalesce(func.sum(Sale.cost_total), 0).label("custo_produtos"),
        func.coalesce(func.sum(Sale.profit_total), 0).label("lucro_vendas"),
        func.count(Sale.id).label("qtd_vendas"),
    ).where(Sale.tenant_id == tenant_id)

    if start:
        sales_query = sales_query.where(Sale.date >= start)
    if end:
        sales_query = sales_query.where(Sale.date <= end)

    sales_result = (await db.execute(sales_query)).one()
    receita_bruta = float(sales_result.receita_bruta)
    impostos = float(sales_result.impostos)
    custo_produtos = float(sales_result.custo_produtos)
    qtd_vendas = int(sales_result.qtd_vendas)

    lucro_bruto = receita_bruta - impostos - custo_produtos

    # --- Despesas operacionais (saidas do fluxo de caixa que sao despesas) ---
    despesas_query = select(
        func.coalesce(func.sum(CashFlowEntry.amount), 0)
    ).where(
        CashFlowEntry.tenant_id == tenant_id,
        CashFlowEntry.type == "SAIDA",
        CashFlowEntry.category == "Despesa",
    )
    if start:
        despesas_query = despesas_query.where(CashFlowEntry.date >= start)
    if end:
        despesas_query = despesas_query.where(CashFlowEntry.date <= end)

    despesas = float((await db.execute(despesas_query)).scalar())
    lucro_liquido = lucro_bruto - despesas

    return {
        "periodo": {
            "inicio": data_inicio,
            "fim": data_fim,
        },
        "receita_bruta": round(receita_bruta, 2),
        "impostos": round(impostos, 2),
        "custo_produtos": round(custo_produtos, 2),
        "lucro_bruto": round(lucro_bruto, 2),
        "despesas_operacionais": round(despesas, 2),
        "lucro_liquido": round(lucro_liquido, 2),
        "quantidade_vendas": qtd_vendas,
        "margem_bruta": round((lucro_bruto / receita_bruta * 100) if receita_bruta > 0 else 0, 1),
        "margem_liquida": round((lucro_liquido / receita_bruta * 100) if receita_bruta > 0 else 0, 1),
    }
