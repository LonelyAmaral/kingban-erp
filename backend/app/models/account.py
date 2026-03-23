"""Accounts Receivable / Payable model."""

from sqlalchemy import Column, Integer, String, Float, Text, Date, ForeignKey
from app.models.base import TenantModel


class Account(TenantModel):
    __tablename__ = "accounts"

    type = Column(String(20), nullable=False, index=True)  # RECEIVABLE, PAYABLE
    description = Column(String(300))
    related_order_id = Column(Integer, ForeignKey("orders.id"))
    related_purchase_id = Column(Integer)
    client_or_supplier = Column(String(300))
    due_date = Column(Date, index=True)
    amount = Column(Float, default=0)
    paid_amount = Column(Float, default=0)
    status = Column(String(20), default="PENDING", index=True)
    payment_date = Column(Date)
    notes = Column(Text)
