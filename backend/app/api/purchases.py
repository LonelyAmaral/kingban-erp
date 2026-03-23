"""API de Compras — CRUD + auto conta a pagar + auto entrada estoque."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_action
from app.models.purchase import Purchase, PurchaseItem
from app.models.account import Account
from app.models.user import User
from app.schemas.purchase import CompraCriar, CompraAtualizar
from app.services.inventory_service import add_entry

router = APIRouter()


def _purchase_to_response(p: Purchase) -> dict:
    """Converte model Purchase para dict de resposta PT."""
    itens = []
    if p.items:
        for item in p.items:
            itens.append({
                "id": item.id,
                "produto_id": item.product_id,
                "codigo_produto": item.product_code,
                "nome_produto": item.product_name,
                "quantidade": item.quantity,
                "preco_unitario": item.unit_price,
                "total": item.total,
            })

    return {
        "id": p.id,
        "numero": p.purchase_number,
        "data": p.date,
        "fornecedor_id": p.supplier_id,
        "nome_fornecedor": p.supplier_name,
        "status": p.status,
        "subtotal": p.subtotal or 0,
        "frete": p.freight or 0,
        "desconto": p.discount or 0,
        "total": p.total or 0,
        "forma_pagamento": p.payment_method,
        "observacoes": p.notes,
        "itens": itens,
        "criado_em": p.criado_em,
    }


@router.get("")
async def listar_compras(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    status: str = Query(None),
    busca: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista compras com filtros."""
    tenant_id = user.tenant_id
    query = select(Purchase).options(selectinload(Purchase.items)).where(Purchase.tenant_id == tenant_id)

    if status:
        query = query.where(Purchase.status == status)
    if busca:
        query = query.where(Purchase.supplier_name.ilike(f"%{busca}%"))

    count_query = select(func.count()).select_from(
        select(Purchase.id).where(Purchase.tenant_id == tenant_id).subquery()
    )
    total = (await db.execute(count_query)).scalar()

    query = query.order_by(Purchase.date.desc())
    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    compras = result.scalars().unique().all()

    return {
        "itens": [_purchase_to_response(c) for c in compras],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina if total > 0 else 1,
    }


@router.get("/proximo-numero")
async def proximo_numero(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retorna proximo numero de compra."""
    result = await db.execute(
        select(func.coalesce(func.max(Purchase.purchase_number), 0))
        .where(Purchase.tenant_id == user.tenant_id)
    )
    return {"proximo_numero": result.scalar() + 1}


@router.post("")
async def criar_compra(
    dados: CompraCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cria compra + conta a pagar automatica."""
    tenant_id = user.tenant_id

    # Proximo numero
    result = await db.execute(
        select(func.coalesce(func.max(Purchase.purchase_number), 0))
        .where(Purchase.tenant_id == tenant_id)
    )
    next_num = result.scalar() + 1

    # Calcular subtotal
    subtotal = sum(item.quantidade * item.preco_unitario for item in dados.itens)
    total = subtotal + dados.frete - dados.desconto

    compra = Purchase(
        tenant_id=tenant_id,
        purchase_number=next_num,
        date=dados.data,
        supplier_id=dados.fornecedor_id,
        supplier_name=dados.nome_fornecedor,
        status="PENDENTE",
        subtotal=round(subtotal, 2),
        freight=dados.frete,
        discount=dados.desconto,
        total=round(total, 2),
        payment_method=dados.forma_pagamento,
        notes=dados.observacoes,
    )
    db.add(compra)
    await db.flush()

    # Criar itens
    for item_data in dados.itens:
        item_total = item_data.quantidade * item_data.preco_unitario
        item = PurchaseItem(
            tenant_id=tenant_id,
            purchase_id=compra.id,
            product_id=item_data.produto_id,
            product_code=item_data.codigo_produto,
            product_name=item_data.nome_produto,
            quantity=item_data.quantidade,
            unit_price=item_data.preco_unitario,
            total=round(item_total, 2),
        )
        db.add(item)

    # Criar conta a pagar automatica
    conta = Account(
        tenant_id=tenant_id,
        type="PAYABLE",
        description=f"Compra #{next_num} - {dados.nome_fornecedor or ''}",
        related_purchase_id=compra.id,
        client_or_supplier=dados.nome_fornecedor,
        due_date=dados.data,
        amount=round(total, 2),
        paid_amount=0,
        status="PENDING",
    )
    db.add(conta)

    await db.flush()
    await log_action(db, user.id, tenant_id, "purchases", compra.id, "CREATE")

    # Recarregar com itens
    result = await db.execute(
        select(Purchase).options(selectinload(Purchase.items)).where(Purchase.id == compra.id)
    )
    compra = result.scalar_one()
    return _purchase_to_response(compra)


@router.post("/{compra_id}/receber")
async def receber_compra(
    compra_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Marca compra como recebida — gera entradas de estoque automaticas."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(Purchase).options(selectinload(Purchase.items))
        .where(Purchase.id == compra_id, Purchase.tenant_id == tenant_id)
    )
    compra = result.scalar_one_or_none()
    if not compra:
        raise HTTPException(404, "Compra nao encontrada")
    if compra.status == "RECEBIDA":
        raise HTTPException(400, "Compra ja foi recebida")
    if compra.status == "CANCELADA":
        raise HTTPException(400, "Compra cancelada nao pode ser recebida")

    compra.status = "RECEBIDA"

    # Gerar entradas de estoque para cada item
    for item in compra.items:
        if item.product_id:
            await add_entry(
                db=db,
                tenant_id=tenant_id,
                product_id=item.product_id,
                quantity=item.quantity,
                entry_type="Compra",
                supplier_id=compra.supplier_id,
                notes=f"Compra #{compra.purchase_number}",
            )

    await db.flush()
    await log_action(db, user.id, tenant_id, "purchases", compra.id, "RECEIVE")
    return _purchase_to_response(compra)


@router.post("/{compra_id}/cancelar")
async def cancelar_compra(
    compra_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cancela compra (apenas se PENDENTE)."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(Purchase).options(selectinload(Purchase.items))
        .where(Purchase.id == compra_id, Purchase.tenant_id == tenant_id)
    )
    compra = result.scalar_one_or_none()
    if not compra:
        raise HTTPException(404, "Compra nao encontrada")
    if compra.status != "PENDENTE":
        raise HTTPException(400, "Apenas compras pendentes podem ser canceladas")

    compra.status = "CANCELADA"

    # Cancelar conta a pagar associada
    conta_result = await db.execute(
        select(Account).where(
            Account.related_purchase_id == compra.id,
            Account.tenant_id == tenant_id,
            Account.status == "PENDING",
        )
    )
    conta = conta_result.scalar_one_or_none()
    if conta:
        await db.delete(conta)

    await db.flush()
    await log_action(db, user.id, tenant_id, "purchases", compra.id, "CANCEL")
    return _purchase_to_response(compra)
