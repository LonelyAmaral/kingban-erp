"""Endpoints da API de Fornecedores — CRUD completo."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import FornecedorCriar, FornecedorAtualizar, FornecedorResponse
from app.schemas.base import PaginacaoResponse, MensagemResponse

logger = logging.getLogger("kingban.api.fornecedores")
router = APIRouter()


@router.get("", response_model=PaginacaoResponse[FornecedorResponse])
async def listar_fornecedores(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busca: str | None = Query(None, description="Busca por nome, CNPJ, cidade ou email"),
    ordenar: str = Query("nome"),
    direcao: str = Query("asc"),
    ativo: bool | None = Query(None),
    categoria: str | None = Query(None, description="Filtrar por categoria"),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista fornecedores com paginacao e busca."""
    query = select(Supplier).where(Supplier.tenant_id == tenant_id)

    if ativo is not None:
        query = query.where(Supplier.ativo == ativo)

    if categoria:
        query = query.where(Supplier.categoria == categoria)

    if busca:
        termo = f"%{busca}%"
        query = query.where(
            or_(
                Supplier.nome.ilike(termo),
                Supplier.cnpj.ilike(termo),
                Supplier.cidade.ilike(termo),
                Supplier.email.ilike(termo),
                Supplier.contato.ilike(termo),
            )
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    campo = getattr(Supplier, ordenar, Supplier.nome)
    if direcao == "desc":
        query = query.order_by(campo.desc())
    else:
        query = query.order_by(campo.asc())

    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    fornecedores = result.scalars().all()

    return PaginacaoResponse(
        itens=fornecedores,
        total=total,
        pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/{fornecedor_id}", response_model=FornecedorResponse)
async def obter_fornecedor(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Obtem um fornecedor pelo ID."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == fornecedor_id, Supplier.tenant_id == tenant_id)
    )
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")
    return fornecedor


@router.post("", response_model=FornecedorResponse, status_code=status.HTTP_201_CREATED)
async def criar_fornecedor(
    dados: FornecedorCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria um novo fornecedor."""
    fornecedor = Supplier(tenant_id=tenant_id, **dados.model_dump())
    db.add(fornecedor)
    await db.flush()

    await log_action(db, user.id, tenant_id, "suppliers", fornecedor.id, "CREATE",
                     new_values=dados.model_dump())

    logger.info("Fornecedor criado: %s (ID %d)", dados.nome, fornecedor.id)
    return fornecedor


@router.put("/{fornecedor_id}", response_model=FornecedorResponse)
async def atualizar_fornecedor(
    fornecedor_id: int,
    dados: FornecedorAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Atualiza um fornecedor existente."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == fornecedor_id, Supplier.tenant_id == tenant_id)
    )
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")

    old_values = {}
    update_data = dados.model_dump(exclude_unset=True)

    for campo, valor in update_data.items():
        old_values[campo] = getattr(fornecedor, campo)
        setattr(fornecedor, campo, valor)

    if update_data:
        await db.flush()
        await log_action(db, user.id, tenant_id, "suppliers", fornecedor.id, "UPDATE",
                         old_values=old_values, new_values=update_data)

    return fornecedor


@router.delete("/{fornecedor_id}", response_model=MensagemResponse)
async def excluir_fornecedor(
    fornecedor_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Exclui um fornecedor (soft delete)."""
    result = await db.execute(
        select(Supplier).where(Supplier.id == fornecedor_id, Supplier.tenant_id == tenant_id)
    )
    fornecedor = result.scalar_one_or_none()
    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor nao encontrado")

    fornecedor.ativo = False
    await db.flush()

    await log_action(db, user.id, tenant_id, "suppliers", fornecedor.id, "DELETE",
                     old_values={"ativo": True}, new_values={"ativo": False})

    return MensagemResponse(mensagem=f"Fornecedor '{fornecedor.nome}' desativado com sucesso")
