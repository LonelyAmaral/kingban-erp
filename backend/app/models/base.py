"""Modelos base para todas as entidades SQLAlchemy."""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, func
from app.database import Base


class TimestampMixin:
    """Mixin que adiciona colunas criado_em e atualizado_em."""
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class TenantModel(Base, TimestampMixin):
    """Base abstrata para todos os modelos com tenant."""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
