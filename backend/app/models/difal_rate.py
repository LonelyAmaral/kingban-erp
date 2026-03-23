"""Modelo de aliquotas DIFAL por estado."""

from sqlalchemy import Column, Integer, String, Float
from app.models.base import TenantModel


class DifalRate(TenantModel):
    """Aliquota DIFAL por estado e NCM."""
    __tablename__ = "difal_rates"

    state_code = Column(String(2), nullable=False, index=True)  # UF: SP, MG, RJ, etc.
    state_name = Column(String(100))
    ncm = Column(String(20), nullable=False)  # 94037000, 94069090
    aliq_interna = Column(Float, nullable=False)  # Aliquota interna do estado destino
    aliq_inter = Column(Float, nullable=False, default=0.12)  # Aliquota interestadual (12%)
    fcp = Column(Float, default=0)  # Fundo de Combate a Pobreza
    formula_especial = Column(String(20))  # 'MG' para formula especial de Minas Gerais
