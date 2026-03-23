"""Audit log model."""

from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False)
    action = Column(String(20), nullable=False)  # CREATE, UPDATE, DELETE
    old_values = Column(Text)  # JSON
    new_values = Column(Text)  # JSON
    timestamp = Column(DateTime, server_default=func.now(), nullable=False, index=True)
