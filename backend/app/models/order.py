"""Order and OrderItem models."""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.models.base import TenantModel


class Order(TenantModel):
    __tablename__ = "orders"

    order_number = Column(Integer, nullable=False, index=True)
    document_type = Column(String(20), default="ORCAMENTO")
    status = Column(String(30), default="ORCAMENTO", index=True)
    status_changed_at = Column(DateTime, server_default=func.now())

    # References
    company_id = Column(Integer, ForeignKey("tenants.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    salesperson_id = Column(Integer, ForeignKey("salespeople.id"))

    # Terms
    nf_type = Column(String(30))
    shipping_origin = Column(String(20))
    payment_method = Column(String(100))
    payment_terms = Column(String(200))
    availability = Column(String(200))
    observations = Column(Text)

    # Totals
    subtotal = Column(Float, default=0)
    freight_value = Column(Float, default=0)
    total_discount = Column(Float, default=0)
    total = Column(Float, default=0)
    total_cost = Column(Float, default=0)
    nf_value = Column(Float, default=0)
    difal_value = Column(Float, default=0)
    profit = Column(Float, default=0)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    client = relationship("Client")
    salesperson = relationship("Salesperson")


class OrderItem(TenantModel):
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    item_order = Column(Integer, default=0)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_code = Column(String(20))
    product_name = Column(String(300))
    quantity = Column(Integer, default=1)
    unit = Column(String(10), default="UN")
    unit_price = Column(Float, default=0)
    discount = Column(Float, default=0)
    total = Column(Float, default=0)
    cost_per_unit = Column(Float, default=0)
    cost_total = Column(Float, default=0)
    nf_unit_value = Column(Float, default=0)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
