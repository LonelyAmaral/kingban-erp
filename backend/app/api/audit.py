"""API de Auditoria — consulta do log de acoes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter()


@router.get("")
async def listar_logs(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    tabela: str = Query(None, description="Filtrar por tabela"),
    acao: str = Query(None, description="CREATE, UPDATE, DELETE, etc."),
    usuario_id: int = Query(None, description="Filtrar por usuario"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista registros de auditoria com filtros."""
    query = select(AuditLog).where(AuditLog.tenant_id == user.tenant_id)

    if tabela:
        query = query.where(AuditLog.table_name == tabela)
    if acao:
        query = query.where(AuditLog.action == acao)
    if usuario_id:
        query = query.where(AuditLog.user_id == usuario_id)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(AuditLog.timestamp.desc())
    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "itens": [
            {
                "id": log.id,
                "usuario_id": log.user_id,
                "tabela": log.table_name,
                "registro_id": log.record_id,
                "acao": log.action,
                "valores_antigos": log.old_values,
                "valores_novos": log.new_values,
                "data_hora": log.timestamp.isoformat() if log.timestamp else None,
            }
            for log in logs
        ],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina if total > 0 else 1,
    }


@router.get("/tabelas")
async def listar_tabelas(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista tabelas com registros de auditoria."""
    result = await db.execute(
        select(AuditLog.table_name)
        .where(AuditLog.tenant_id == user.tenant_id)
        .distinct()
        .order_by(AuditLog.table_name)
    )
    return [r[0] for r in result.all()]


@router.get("/acoes")
async def listar_acoes(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista tipos de acoes registradas."""
    result = await db.execute(
        select(AuditLog.action)
        .where(AuditLog.tenant_id == user.tenant_id)
        .distinct()
        .order_by(AuditLog.action)
    )
    return [r[0] for r in result.all()]
