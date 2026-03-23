"""Commission models."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date, Text
from app.models.base import TenantModel


class CommissionCost(TenantModel):
    __tablename__ = "commission_costs"

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_code = Column(String(20))
    product_name = Column(String(300))
    base_cost = Column(Float, default=0)
    commission_rate = Column(Float, default=0.15)


class CommissionReport(TenantModel):
    __tablename__ = "commission_reports"

    salesperson_id = Column(Integer, ForeignKey("salespeople.id"), nullable=False)
    date_from = Column(Date, nullable=False)
    date_to = Column(Date, nullable=False)
    total_sales = Column(Float, default=0)
    total_commission = Column(Float, default=0)
    gratification = Column(Float, default=0)
    other_commission = Column(Float, default=0)
    gross_total = Column(Float, default=0)
    advances = Column(Float, default=0)
    fixed_salary = Column(Float, default=0)
    balance = Column(Float, default=0)
    notes = Column(Text)
