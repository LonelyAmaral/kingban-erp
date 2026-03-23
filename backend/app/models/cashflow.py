"""Modelo de Fluxo de Caixa (NOVO — nao existia no desktop)."""

from sqlalchemy import Column, Integer, String, Float, Text, Date, ForeignKey
from app.models.base import TenantModel


class CashFlowEntry(TenantModel):
    """Lancamento de fluxo de caixa — entradas e saidas financeiras."""
    __tablename__ = "cashflow_entries"

    date = Column(Date, nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # ENTRADA, SAIDA
    category = Column(String(100), nullable=False)  # Venda, Compra, Despesa, Aporte, Retirada, etc.
    description = Column(String(500))
    amount = Column(Float, default=0, nullable=False)
    related_account_id = Column(Integer, ForeignKey("accounts.id"))
    related_order_id = Column(Integer, ForeignKey("orders.id"))
    auto_generated = Column(String(5), default="NAO")  # SIM ou NAO — se foi gerado automaticamente
    notes = Column(Text)
