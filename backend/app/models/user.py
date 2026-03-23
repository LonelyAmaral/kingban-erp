"""User model with role-based access control."""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import TenantModel


class User(TenantModel):
    __tablename__ = "users"

    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200))
    full_name = Column(String(200), nullable=False)
    hashed_password = Column(String(300), nullable=False)
    role = Column(String(50), nullable=False, default="vendedor")
    is_active = Column(Boolean, default=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
