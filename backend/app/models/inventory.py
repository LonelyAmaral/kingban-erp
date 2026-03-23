"""Inventory models: stock, entries, exits."""

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, Date
from app.models.base import TenantModel


class Inventory(TenantModel):
    __tablename__ = "inventory"

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True, index=True)
    current_qty = Column(Integer, default=0)
    min_qty = Column(Integer, default=0)
    location = Column(String(100))  # NEW: multi-location support
    last_entry_date = Column(Date)
    last_exit_date = Column(Date)


class InventoryEntry(TenantModel):
    __tablename__ = "inventory_entries"

    date = Column(Date, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_code = Column(String(20))
    product_name = Column(String(300))
    quantity = Column(Integer, nullable=False)
    entry_type = Column(String(50), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))  # NEW: link to supplier
    notes = Column(Text)


class InventoryExit(TenantModel):
    __tablename__ = "inventory_exits"

    date = Column(Date, nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_code = Column(String(20))
    product_name = Column(String(300))
    quantity = Column(Integer, nullable=False)
    client_name = Column(String(300))
    exit_type = Column(String(50), nullable=False)
    sale_id = Column(Integer, ForeignKey("sales.id"))
    notes = Column(Text, index=True)
