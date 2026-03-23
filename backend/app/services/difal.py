"""Motor de calculo DIFAL (Diferencial de Aliquota).

Portado do desktop: kingban/services/difal.py
Adaptado para SQLAlchemy async.

Formula padrao:
  DIFAL = (valor / (1 - (aliq_interna + fcp))) * (aliq_interna - aliq_inter + fcp)

Formula especial MG:
  DIFAL = (valor * 1/3) * (aliq_interna - aliq_inter + fcp)

Taxa NF: 8.5% (TAX_RATE_NF = 0.085)
"""

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.difal_rate import DifalRate

logger = logging.getLogger("kingban.difal")

# Estado de origem (Sao Paulo)
ORIGIN_STATE = "SP"


async def load_difal_rates(db: AsyncSession, tenant_id: int) -> dict:
    """
    Carrega aliquotas DIFAL do banco de dados.
    Retorna dict: {(UF, NCM): {aliq_interna, aliq_inter, fcp, formula_especial, nome}}
    """
    result = await db.execute(
        select(DifalRate).where(DifalRate.tenant_id == tenant_id)
    )
    rates = {}
    for r in result.scalars().all():
        rates[(r.state_code, r.ncm)] = {
            "aliq_interna": r.aliq_interna,
            "aliq_inter": r.aliq_inter,
            "fcp": r.fcp or 0,
            "formula_especial": r.formula_especial,
            "nome": r.state_name or r.state_code,
        }
    return rates


def calculate_difal(
    value: float,
    state_code: str,
    ncm: str,
    rate_info: dict,
) -> dict:
    """
    Calcula DIFAL para um valor, estado destino e NCM.

    Args:
        value: valor do produto (sem impostos)
        state_code: UF destino (ex: 'MG', 'RJ')
        ncm: codigo NCM (ex: '94037000')
        rate_info: dict com aliq_interna, aliq_inter, fcp, formula_especial

    Returns:
        dict com valor_difal, valor_fcp, valor_total, formula_usada
    """
    # Venda dentro de SP — sem DIFAL
    if state_code == ORIGIN_STATE:
        return {
            "valor_difal": 0.0,
            "valor_fcp": 0.0,
            "valor_total": 0.0,
            "formula_usada": "isento_sp",
        }

    aliq_interna = rate_info["aliq_interna"]
    aliq_inter = rate_info["aliq_inter"]
    fcp = rate_info.get("fcp", 0)
    formula_especial = rate_info.get("formula_especial")

    if formula_especial == "MG":
        # Formula especial Minas Gerais: (valor * 1/3) * diferencial
        base = value * (1 / 3)
        diferencial = aliq_interna - aliq_inter + fcp
        difal_total = base * diferencial
        difal_fcp = base * fcp if fcp > 0 else 0
        difal_value = difal_total - difal_fcp
        formula = "MG"
    else:
        # Formula padrao: (valor / (1 - (aliq_interna + fcp))) * diferencial
        divisor = 1 - (aliq_interna + fcp)
        if divisor <= 0:
            logger.warning(f"Divisor invalido para estado {state_code}: {divisor}")
            return {"valor_difal": 0, "valor_fcp": 0, "valor_total": 0, "formula_usada": "erro"}

        base = value / divisor
        diferencial = aliq_interna - aliq_inter + fcp
        difal_total = base * diferencial
        difal_fcp = base * fcp if fcp > 0 else 0
        difal_value = difal_total - difal_fcp
        formula = "padrao"

    return {
        "valor_difal": round(difal_value, 2),
        "valor_fcp": round(difal_fcp, 2),
        "valor_total": round(difal_total, 2),
        "formula_usada": formula,
    }


def should_apply_difal(state_code: str) -> bool:
    """Retorna True se DIFAL deve ser aplicado (vendas interestaduais)."""
    return state_code != ORIGIN_STATE


async def get_all_states(db: AsyncSession, tenant_id: int) -> list[dict]:
    """Retorna todos os estados com aliquotas cadastradas."""
    result = await db.execute(
        select(DifalRate)
        .where(DifalRate.tenant_id == tenant_id)
        .order_by(DifalRate.state_code)
    )
    states = []
    for r in result.scalars().all():
        states.append({
            "uf": r.state_code,
            "nome": r.state_name or r.state_code,
            "ncm": r.ncm,
            "aliq_interna": r.aliq_interna,
            "aliq_inter": r.aliq_inter,
            "fcp": r.fcp or 0,
            "formula_especial": r.formula_especial,
        })
    return states
