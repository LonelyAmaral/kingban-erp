"""Tenant (empresa) model — multi-company support."""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, func
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False)       # e.g. "kb", "KP"
    name = Column(String(200), nullable=False)       # e.g. "KING BAN"
    trade_name = Column(String(200))                 # e.g. "KING BAN INDUSTRIA..."
    cnpj = Column(String(20))
    ie = Column(String(20))                          # Inscricao Estadual
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(2))
    zip_code = Column(String(10))
    phone = Column(String(20))
    email = Column(String(200))
    bank_name = Column(String(100))
    bank_agency = Column(String(20))
    bank_account = Column(String(30))
    pix_key = Column(String(100))
    active = Column(Boolean, default=True)

    # Relationships
    users = relationship("User", back_populates="tenant")
