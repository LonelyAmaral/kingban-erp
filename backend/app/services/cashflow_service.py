"""Servico de Fluxo de Caixa (NOVO — nao existia no desktop).

Gerencia lancamentos automaticos e manuais de fluxo de caixa.
Lancamentos automaticos sao gerados por:
- Pagamento de conta a receber → ENTRADA
- Pagamento de conta a pagar → SAIDA
- Recebimento de compra → SAIDA
"""

import logging
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cashflow import CashFlowEntry

logger = logging.getLogger("kingban.cashflow")


async def create_entry(
    db: AsyncSession,
    tenant_id: int,
    entry_date: date,
    entry_type: str,
    category: str,
    amount: float,
    description: str = "",
    account_id: int = None,
    order_id: int = None,
    auto_generated: bool = False,
    notes: str = "",
) -> CashFlowEntry:
    """Cria um lancamento de fluxo de caixa."""
    entry = CashFlowEntry(
        tenant_id=tenant_id,
        date=entry_date,
        type=entry_type,
        category=category,
        description=description,
        amount=amount,
        related_account_id=account_id,
        related_order_id=order_id,
        auto_generated="SIM" if auto_generated else "NAO",
        notes=notes,
    )
    db.add(entry)
    await db.flush()
    return entry


async def get_summary(
    db: AsyncSession,
    tenant_id: int,
    start_date: date = None,
    end_date: date = None,
) -> dict:
    """Calcula resumo do fluxo de caixa no periodo."""
    query_entradas = select(func.coalesce(func.sum(CashFlowEntry.amount), 0)).where(
        CashFlowEntry.tenant_id == tenant_id,
        CashFlowEntry.type == "ENTRADA",
    )
    query_saidas = select(func.coalesce(func.sum(CashFlowEntry.amount), 0)).where(
        CashFlowEntry.tenant_id == tenant_id,
        CashFlowEntry.type == "SAIDA",
    )

    if start_date:
        query_entradas = query_entradas.where(CashFlowEntry.date >= start_date)
        query_saidas = query_saidas.where(CashFlowEntry.date >= start_date)
    if end_date:
        query_entradas = query_entradas.where(CashFlowEntry.date <= end_date)
        query_saidas = query_saidas.where(CashFlowEntry.date <= end_date)

    # Total de lancamentos
    query_count = select(func.count(CashFlowEntry.id)).where(
        CashFlowEntry.tenant_id == tenant_id,
    )
    if start_date:
        query_count = query_count.where(CashFlowEntry.date >= start_date)
    if end_date:
        query_count = query_count.where(CashFlowEntry.date <= end_date)

    # Saldo acumulado (tudo ate end_date)
    query_acum_entradas = select(func.coalesce(func.sum(CashFlowEntry.amount), 0)).where(
        CashFlowEntry.tenant_id == tenant_id,
        CashFlowEntry.type == "ENTRADA",
    )
    query_acum_saidas = select(func.coalesce(func.sum(CashFlowEntry.amount), 0)).where(
        CashFlowEntry.tenant_id == tenant_id,
        CashFlowEntry.type == "SAIDA",
    )
    if end_date:
        query_acum_entradas = query_acum_entradas.where(CashFlowEntry.date <= end_date)
        query_acum_saidas = query_acum_saidas.where(CashFlowEntry.date <= end_date)

    total_entradas = (await db.execute(query_entradas)).scalar()
    total_saidas = (await db.execute(query_saidas)).scalar()
    count = (await db.execute(query_count)).scalar()
    acum_entradas = (await db.execute(query_acum_entradas)).scalar()
    acum_saidas = (await db.execute(query_acum_saidas)).scalar()

    return {
        "total_entradas": round(total_entradas, 2),
        "total_saidas": round(total_saidas, 2),
        "saldo_periodo": round(total_entradas - total_saidas, 2),
        "saldo_acumulado": round(acum_entradas - acum_saidas, 2),
        "quantidade_lancamentos": count,
    }
