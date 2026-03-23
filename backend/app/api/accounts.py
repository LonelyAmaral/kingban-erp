"""API de Contas a Receber/Pagar — CRUD completo + pagamento."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_action
from app.models.account import Account
from app.models.user import User
from app.schemas.account import ContaCriar, ContaAtualizar, PagamentoConta, ContaResponse
from app.services.cashflow_service import create_entry

router = APIRouter()


def _account_to_response(a: Account) -> dict:
    """Converte model Account para dict de resposta PT."""
    return {
        "id": a.id,
        "tipo": a.type,
        "descricao": a.description,
        "pedido_id": a.related_order_id,
        "compra_id": a.related_purchase_id,
        "cliente_ou_fornecedor": a.client_or_supplier,
        "vencimento": a.due_date,
        "valor": a.amount or 0,
        "valor_pago": a.paid_amount or 0,
        "status": a.status,
        "data_pagamento": a.payment_date,
        "observacoes": a.notes,
        "criado_em": a.criado_em,
    }


@router.get("")
async def listar_contas(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    tipo: str = Query(None, description="RECEIVABLE ou PAYABLE"),
    status: str = Query(None, description="PENDING, PARTIAL, PAID, OVERDUE"),
    busca: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista contas a receber/pagar com filtros."""
    tenant_id = user.tenant_id
    query = select(Account).where(Account.tenant_id == tenant_id)

    if tipo:
        query = query.where(Account.type == tipo)
    if status:
        query = query.where(Account.status == status)
    if busca:
        query = query.where(
            or_(
                Account.description.ilike(f"%{busca}%"),
                Account.client_or_supplier.ilike(f"%{busca}%"),
            )
        )

    # Contagem total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginacao
    query = query.order_by(Account.due_date.desc())
    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    contas = result.scalars().all()

    return {
        "itens": [_account_to_response(c) for c in contas],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina if total > 0 else 1,
    }


@router.post("")
async def criar_conta(
    dados: ContaCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cria nova conta a receber ou a pagar."""
    if dados.tipo not in ("RECEIVABLE", "PAYABLE"):
        raise HTTPException(400, "Tipo deve ser RECEIVABLE ou PAYABLE")

    tenant_id = user.tenant_id
    conta = Account(
        tenant_id=tenant_id,
        type=dados.tipo,
        description=dados.descricao,
        related_order_id=dados.pedido_id,
        related_purchase_id=dados.compra_id,
        client_or_supplier=dados.cliente_ou_fornecedor,
        due_date=dados.vencimento,
        amount=dados.valor,
        paid_amount=0,
        status="PENDING",
        notes=dados.observacoes,
    )
    db.add(conta)
    await db.flush()
    await log_action(db, user.id, tenant_id, "accounts", conta.id, "CREATE")
    return _account_to_response(conta)


@router.get("/{conta_id}")
async def obter_conta(
    conta_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Obtem conta por ID."""
    result = await db.execute(
        select(Account).where(Account.id == conta_id, Account.tenant_id == user.tenant_id)
    )
    conta = result.scalar_one_or_none()
    if not conta:
        raise HTTPException(404, "Conta nao encontrada")
    return _account_to_response(conta)


@router.put("/{conta_id}")
async def atualizar_conta(
    conta_id: int,
    dados: ContaAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Atualiza dados da conta."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(Account).where(Account.id == conta_id, Account.tenant_id == tenant_id)
    )
    conta = result.scalar_one_or_none()
    if not conta:
        raise HTTPException(404, "Conta nao encontrada")

    if dados.descricao is not None:
        conta.description = dados.descricao
    if dados.cliente_ou_fornecedor is not None:
        conta.client_or_supplier = dados.cliente_ou_fornecedor
    if dados.vencimento is not None:
        conta.due_date = dados.vencimento
    if dados.valor is not None:
        conta.amount = dados.valor
    if dados.observacoes is not None:
        conta.notes = dados.observacoes

    await db.flush()
    await log_action(db, user.id, tenant_id, "accounts", conta.id, "UPDATE")
    return _account_to_response(conta)


@router.post("/{conta_id}/pagamento")
async def registrar_pagamento(
    conta_id: int,
    dados: PagamentoConta,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Registra pagamento parcial ou total de uma conta."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(Account).where(Account.id == conta_id, Account.tenant_id == tenant_id)
    )
    conta = result.scalar_one_or_none()
    if not conta:
        raise HTTPException(404, "Conta nao encontrada")

    if conta.status == "PAID":
        raise HTTPException(400, "Conta ja esta paga")

    conta.paid_amount = (conta.paid_amount or 0) + dados.valor_pago
    conta.payment_date = dados.data_pagamento or date.today()

    # Atualizar status
    if conta.paid_amount >= conta.amount:
        conta.status = "PAID"
        conta.paid_amount = conta.amount
    else:
        conta.status = "PARTIAL"

    # Gerar lancamento de fluxo de caixa automatico
    cf_type = "ENTRADA" if conta.type == "RECEIVABLE" else "SAIDA"
    cf_category = "Recebimento" if conta.type == "RECEIVABLE" else "Pagamento"
    await create_entry(
        db=db,
        tenant_id=tenant_id,
        entry_date=conta.payment_date,
        entry_type=cf_type,
        category=cf_category,
        amount=dados.valor_pago,
        description=f"{cf_category}: {conta.description or ''}",
        account_id=conta.id,
        auto_generated=True,
    )

    await db.flush()
    await log_action(db, user.id, tenant_id, "accounts", conta.id, "PAYMENT")
    return _account_to_response(conta)


@router.delete("/{conta_id}")
async def excluir_conta(
    conta_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Exclui conta (apenas se status PENDING)."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(Account).where(Account.id == conta_id, Account.tenant_id == tenant_id)
    )
    conta = result.scalar_one_or_none()
    if not conta:
        raise HTTPException(404, "Conta nao encontrada")
    if conta.status != "PENDING":
        raise HTTPException(400, "Apenas contas pendentes podem ser excluidas")

    await db.delete(conta)
    await log_action(db, user.id, tenant_id, "accounts", conta_id, "DELETE")
    return {"message": "Conta excluida com sucesso"}
