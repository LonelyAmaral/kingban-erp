"""Motor de calculo de comissoes.

Portado do desktop: kingban/services/commission.py
Adaptado para SQLAlchemy async.

Formula:
CUSTO_TOTAL_UNI = VLOOKUP(produto, CUSTO) + IF(saida="DEPOSITO", 65, 0) + VLR_NF * 8.5%
LIQUIDO_UNI = VALOR_UNI - CUSTO_TOTAL_UNI
LIQUIDO_TOTAL = LIQUIDO_UNI * QTD
COMISSAO = LIQUIDO_TOTAL * taxa (15% ou 20%)
"""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import TAX_RATE_NF, DEPOSITO_SURCHARGE
from app.models.commission import CommissionCost
from app.models.sale import Sale
from app.models.salesperson import Salesperson

logger = logging.getLogger("kingban.commission")


def calculate_commission_line(
    unit_price: float,
    quantity: int,
    nf_unit_value: float,
    shipping_origin: str,
    base_cost: float,
    commission_rate: float = 0.15,
) -> dict:
    """
    Calcula comissao para um unico item de venda.

    Args:
        unit_price: preco de venda unitario (VALOR UNI)
        quantity: quantidade (QTDE)
        nf_unit_value: valor NF unitario (VLR UNIT NOTA)
        shipping_origin: 'FABRICA' ou 'DEPOSITO'
        base_cost: custo base do produto da tabela CUSTO
        commission_rate: 0.15 para produtos principais, 0.20 para acessorios
    """
    total_sale = unit_price * quantity
    nf_total = nf_unit_value * quantity

    deposito = DEPOSITO_SURCHARGE if shipping_origin == "DEPOSITO" else 0.0
    tax_on_nf = nf_unit_value * TAX_RATE_NF

    cost_total_unit = base_cost + deposito + tax_on_nf
    liquid_per_unit = unit_price - cost_total_unit
    liquid_total = liquid_per_unit * quantity
    commission_value = liquid_total * commission_rate

    return {
        "total_sale": round(total_sale, 2),
        "nf_total": round(nf_total, 2),
        "cost_total_unit": round(cost_total_unit, 2),
        "liquid_per_unit": round(liquid_per_unit, 2),
        "liquid_total": round(liquid_total, 2),
        "commission_rate": commission_rate,
        "commission_value": round(commission_value, 2),
    }


async def generate_commission_report(
    db: AsyncSession,
    tenant_id: int,
    salesperson_id: int,
    period_start: date,
    period_end: date,
    gratification: float = 0.0,
    advances: float = 0.0,
    other_commission: float = 0.0,
) -> dict:
    """
    Gera relatorio completo de comissao para um vendedor em um periodo.
    """
    # Buscar vendedor
    sp_result = await db.execute(
        select(Salesperson).where(Salesperson.id == salesperson_id, Salesperson.tenant_id == tenant_id)
    )
    sp = sp_result.scalar_one_or_none()
    if not sp:
        raise ValueError(f"Vendedor {salesperson_id} nao encontrado")

    # Buscar vendas no periodo
    sales_result = await db.execute(
        select(Sale)
        .where(
            Sale.tenant_id == tenant_id,
            Sale.salesperson_id == salesperson_id,
            Sale.date >= period_start,
            Sale.date <= period_end,
        )
        .order_by(Sale.date)
    )
    sales = sales_result.scalars().all()

    # Carregar custos de comissao
    costs_result = await db.execute(
        select(CommissionCost).where(CommissionCost.tenant_id == tenant_id)
    )
    cost_table = {c.product_code: {"cost": c.base_cost, "rate": c.commission_rate}
                  for c in costs_result.scalars().all()}

    # Calcular linhas
    line_items = []
    total_sales = 0.0
    total_nf = 0.0
    total_liquid = 0.0
    total_commission = 0.0

    for sale in sales:
        cost_info = cost_table.get(sale.product_code, {})
        base_cost = cost_info.get("cost", sale.cost_per_unit or 0)
        rate = cost_info.get("rate", 0.15)

        nf_unit = sale.nf_value / sale.quantity if sale.quantity > 0 else 0

        calc = calculate_commission_line(
            unit_price=sale.unit_price or 0,
            quantity=sale.quantity or 0,
            nf_unit_value=nf_unit,
            shipping_origin=sale.shipping_origin or "FABRICA",
            base_cost=base_cost,
            commission_rate=rate,
        )

        line_items.append({
            "sale_id": sale.id,
            "date": sale.date.isoformat() if sale.date else "",
            "product_code": sale.product_code or "",
            "product_name": sale.product_name or "",
            "quantity": sale.quantity,
            "unit_price": sale.unit_price,
            "total_sale": calc["total_sale"],
            "nf_unit_value": nf_unit,
            "nf_total": calc["nf_total"],
            "client_name": sale.client_name or "",
            "shipping_origin": sale.shipping_origin or "",
            "cost_total_unit": calc["cost_total_unit"],
            "liquid_per_unit": calc["liquid_per_unit"],
            "liquid_total": calc["liquid_total"],
            "commission_rate": calc["commission_rate"],
            "commission_value": calc["commission_value"],
        })

        total_sales += calc["total_sale"]
        total_nf += calc["nf_total"]
        total_liquid += calc["liquid_total"]
        total_commission += calc["commission_value"]

    fixed_salary = sp.salario_fixo or 0
    gross_total = total_commission + other_commission + fixed_salary + gratification
    balance = gross_total - advances

    return {
        "salesperson_id": salesperson_id,
        "salesperson_name": sp.nome,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "total_sales": round(total_sales, 2),
        "total_nf": round(total_nf, 2),
        "total_liquid": round(total_liquid, 2),
        "total_commission": round(total_commission, 2),
        "other_commission": round(other_commission, 2),
        "fixed_salary": fixed_salary,
        "gratification": gratification,
        "advances": advances,
        "gross_total": round(gross_total, 2),
        "balance": round(balance, 2),
        "items": line_items,
    }
