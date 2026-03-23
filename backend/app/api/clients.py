"""Endpoints da API de Clientes — CRUD completo."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClienteCriar, ClienteAtualizar, ClienteResponse
from app.schemas.base import PaginacaoResponse, MensagemResponse

logger = logging.getLogger("kingban.api.clientes")
router = APIRouter()


@router.get("", response_model=PaginacaoResponse[ClienteResponse])
async def listar_clientes(
    pagina: int = Query(1, ge=1, description="Numero da pagina"),
    por_pagina: int = Query(50, ge=1, le=200, description="Itens por pagina"),
    busca: str | None = Query(None, description="Busca por nome, CNPJ/CPF, cidade ou email"),
    ordenar: str = Query("nome", description="Campo para ordenacao"),
    direcao: str = Query("asc", description="Direcao: asc ou desc"),
    ativo: bool | None = Query(None, description="Filtrar por ativo/inativo"),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista clientes com paginacao, busca e filtros."""
    query = select(Client).where(Client.tenant_id == tenant_id)

    # Filtro de status ativo
    if ativo is not None:
        query = query.where(Client.ativo == ativo)

    # Busca em multiplos campos
    if busca:
        termo = f"%{busca}%"
        query = query.where(
            or_(
                Client.nome.ilike(termo),
                Client.cnpj_cpf.ilike(termo),
                Client.cidade.ilike(termo),
                Client.email.ilike(termo),
                Client.contato.ilike(termo),
            )
        )

    # Contagem total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Ordenacao
    campo = getattr(Client, ordenar, Client.nome)
    if direcao == "desc":
        query = query.order_by(campo.desc())
    else:
        query = query.order_by(campo.asc())

    # Paginacao
    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    clientes = result.scalars().all()

    return PaginacaoResponse(
        itens=clientes,
        total=total,
        pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/{cliente_id}", response_model=ClienteResponse)
async def obter_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Obtem um cliente pelo ID."""
    result = await db.execute(
        select(Client).where(Client.id == cliente_id, Client.tenant_id == tenant_id)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")
    return cliente


@router.post("", response_model=ClienteResponse, status_code=status.HTTP_201_CREATED)
async def criar_cliente(
    dados: ClienteCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria um novo cliente."""
    cliente = Client(tenant_id=tenant_id, **dados.model_dump())
    db.add(cliente)
    await db.flush()

    await log_action(db, user.id, tenant_id, "clients", cliente.id, "CREATE",
                     new_values=dados.model_dump())

    logger.info("Cliente criado: %s (ID %d) por usuario %d", dados.nome, cliente.id, user.id)
    return cliente


@router.put("/{cliente_id}", response_model=ClienteResponse)
async def atualizar_cliente(
    cliente_id: int,
    dados: ClienteAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Atualiza um cliente existente."""
    result = await db.execute(
        select(Client).where(Client.id == cliente_id, Client.tenant_id == tenant_id)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    # Salvar valores antigos para auditoria
    old_values = {}
    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        old_values[campo] = getattr(cliente, campo)
        setattr(cliente, campo, valor)

    if update_data:
        await db.flush()
        await log_action(db, user.id, tenant_id, "clients", cliente.id, "UPDATE",
                         old_values=old_values, new_values=update_data)
        logger.info("Cliente atualizado: ID %d por usuario %d", cliente.id, user.id)

    return cliente


@router.delete("/{cliente_id}", response_model=MensagemResponse)
async def excluir_cliente(
    cliente_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Exclui um cliente (soft delete — desativa)."""
    result = await db.execute(
        select(Client).where(Client.id == cliente_id, Client.tenant_id == tenant_id)
    )
    cliente = result.scalar_one_or_none()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente nao encontrado")

    cliente.ativo = False
    await db.flush()

    await log_action(db, user.id, tenant_id, "clients", cliente.id, "DELETE",
                     old_values={"ativo": True}, new_values={"ativo": False})

    logger.info("Cliente desativado: ID %d por usuario %d", cliente.id, user.id)
    return MensagemResponse(mensagem=f"Cliente '{cliente.nome}' desativado com sucesso")
