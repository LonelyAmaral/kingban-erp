"""Multi-tenant middleware and utilities."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.models.user import User


async def get_tenant_id(user: User = Depends(get_current_user)) -> int:
    """Dependency that extracts tenant_id from the current user."""
    return user.tenant_id
