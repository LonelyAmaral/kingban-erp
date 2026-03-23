"""Endpoints da API de Vendedores — CRUD completo."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.salesperson import Salesperson
from app.models.user import User
from app.schemas.salesperson import VendedorCriar, VendedorAtualizar, VendedorResponse
from app.schemas.base import PaginacaoResponse, MensagemResponse

logger = logging.getLogger("kingban.api.vendedores")
router = APIRouter()


@router.get("", response_model=PaginacaoResponse[VendedorResponse])
async def listar_vendedores(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busca: str | None = Query(None, description="Busca por nome, telefone ou email"),
    ordenar: str = Query("nome"),
    direcao: str = Query("asc"),
    ativo: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista vendedores com paginacao e busca."""
    query = select(Salesperson).where(Salesperson.tenant_id == tenant_id)

    if ativo is not None:
        query = query.where(Salesperson.ativo == ativo)

    if busca:
        termo = f"%{busca}%"
        query = query.where(
            or_(
                Salesperson.nome.ilike(termo),
                Salesperson.telefone.ilike(termo),
                Salesperson.email.ilike(termo),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    campo = getattr(Salesperson, ordenar, Salesperson.nome)
    if direcao == "desc":
        query = query.order_by(campo.desc())
    else:
        query = query.order_by(campo.asc())

    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    vendedores = result.scalars().all()

    return PaginacaoResponse(
        itens=vendedores,
        total=total,
        pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/{vendedor_id}", response_model=VendedorResponse)
async def obter_vendedor(
    vendedor_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Obtem um vendedor pelo ID."""
    result = await db.execute(
        select(Salesperson).where(Salesperson.id == vendedor_id, Salesperson.tenant_id == tenant_id)
    )
    vendedor = result.scalar_one_or_none()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor nao encontrado")
    return vendedor


@router.post("", response_model=VendedorResponse, status_code=status.HTTP_201_CREATED)
async def criar_vendedor(
    dados: VendedorCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria um novo vendedor."""
    vendedor = Salesperson(tenant_id=tenant_id, **dados.model_dump())
    db.add(vendedor)
    await db.flush()

    await log_action(db, user.id, tenant_id, "salespeople", vendedor.id, "CREATE",
                     new_values=dados.model_dump())

    logger.info("Vendedor criado: %s (ID %d)", dados.nome, vendedor.id)
    return vendedor


@router.put("/{vendedor_id}", response_model=VendedorResponse)
async def atualizar_vendedor(
    vendedor_id: int,
    dados: VendedorAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Atualiza um vendedor existente."""
    result = await db.execute(
        select(Salesperson).where(Salesperson.id == vendedor_id, Salesperson.tenant_id == tenant_id)
    )
    vendedor = result.scalar_one_or_none()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor nao encontrado")

    old_values = {}
    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        old_values[campo] = getattr(vendedor, campo)
        setattr(vendedor, campo, valor)

    if update_data:
        await db.flush()
        await log_action(db, user.id, tenant_id, "salespeople", vendedor.id, "UPDATE",
                         old_values=old_values, new_values=update_data)

    return vendedor


@router.delete("/{vendedor_id}", response_model=MensagemResponse)
async def excluir_vendedor(
    vendedor_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Exclui um vendedor (soft delete)."""
    result = await db.execute(
        select(Salesperson).where(Salesperson.id == vendedor_id, Salesperson.tenant_id == tenant_id)
    )
    vendedor = result.scalar_one_or_none()
    if not vendedor:
        raise HTTPException(status_code=404, detail="Vendedor nao encontrado")

    vendedor.ativo = False
    await db.flush()

    await log_action(db, user.id, tenant_id, "salespeople", vendedor.id, "DELETE",
                     old_values={"ativo": True}, new_values={"ativo": False})

    return MensagemResponse(mensagem=f"Vendedor '{vendedor.nome}' desativado com sucesso")
