"""Sale model."""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date
from app.models.base import TenantModel


class Sale(TenantModel):
    __tablename__ = "sales"

    date = Column(Date, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    order_number = Column(Integer)
    company_id = Column(Integer, ForeignKey("tenants.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    client_name = Column(String(300))
    client_cnpj_cpf = Column(String(20))
    product_id = Column(Integer, ForeignKey("products.id"))
    product_code = Column(String(20))
    product_name = Column(String(300))
    quantity = Column(Integer, default=1)
    unit = Column(String(10), default="UN")
    shipping_origin = Column(String(20))
    unit_price = Column(Float, default=0)
    total_value = Column(Float, default=0)
    discount = Column(Float, default=0)
    cost_per_unit = Column(Float, default=0)
    cost_total = Column(Float, default=0)
    nf_value = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    profit_total = Column(Float, default=0)
    payment_method = Column(String(100))
    salesperson_id = Column(Integer, ForeignKey("salespeople.id"), index=True)
