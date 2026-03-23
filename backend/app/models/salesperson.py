"""Modelo de Vendedor."""

from sqlalchemy import Column, String, Float, Boolean
from app.models.base import TenantModel


class Salesperson(TenantModel):
    __tablename__ = "salespeople"

    nome = Column(String(200), nullable=False)
    telefone = Column(String(30))
    email = Column(String(200))
    salario_fixo = Column(Float, default=1500.0)
    ativo = Column(Boolean, default=True)
