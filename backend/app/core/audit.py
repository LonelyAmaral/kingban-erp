"""Audit logging for database operations."""

import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("kingban.audit")


async def log_action(
    db: AsyncSession,
    user_id: int,
    tenant_id: int,
    table_name: str,
    record_id: int,
    action: str,
    old_values: dict = None,
    new_values: dict = None,
):
    """Record an audit log entry."""
    from app.models.audit_log import AuditLog

    entry = AuditLog(
        user_id=user_id,
        tenant_id=tenant_id,
        table_name=table_name,
        record_id=record_id,
        action=action,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
    )
    db.add(entry)
    logger.info("%s %s #%d by user #%d", action, table_name, record_id, user_id)
