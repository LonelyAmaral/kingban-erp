"""Modelo de Compras."""

from sqlalchemy import Column, Integer, String, Float, Text, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TenantModel


class Purchase(TenantModel):
    """Compra de produto — gera conta a pagar + entrada de estoque."""
    __tablename__ = "purchases"

    purchase_number = Column(Integer, index=True)
    date = Column(Date, nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    supplier_name = Column(String(300))
    status = Column(String(20), default="PENDENTE", index=True)  # PENDENTE, RECEBIDA, CANCELADA
    subtotal = Column(Float, default=0)
    freight = Column(Float, default=0)
    discount = Column(Float, default=0)
    total = Column(Float, default=0)
    payment_method = Column(String(100))
    notes = Column(Text)

    items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(TenantModel):
    """Item de compra."""
    __tablename__ = "purchase_items"

    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_code = Column(String(20))
    product_name = Column(String(300))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0)
    total = Column(Float, default=0)

    purchase = relationship("Purchase", back_populates="items")
