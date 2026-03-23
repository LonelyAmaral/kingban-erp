"""Workflow de pedidos — acoes automaticas por mudanca de status.

Portado do desktop: kingban/services/order_workflow.py
Adaptado para SQLAlchemy async.

Acoes:
- CONFIRMADO: cria conta a receber
- RESERVAR ESTOQUE / PRODUCAO: reserva estoque
- ENTREGUE: cria venda + baixa estoque
- CANCELADO: estorna reserva de estoque
"""

import logging
from datetime import date, timedelta
from dataclasses import dataclass, field

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderItem
from app.models.client import Client
from app.models.sale import Sale
from app.models.account import Account
from app.models.inventory import InventoryEntry, InventoryExit, Inventory
from app.core.constants import TAX_RATE_NF

logger = logging.getLogger("kingban.workflow")


@dataclass
class WorkflowResult:
    """Resultado de uma acao de workflow."""
    success: bool = True
    message: str = ""
    data: dict = field(default_factory=dict)


async def execute_order_confirmed(db: AsyncSession, order: Order, tenant_id: int) -> WorkflowResult:
    """Cria conta a receber ao confirmar pedido."""
    # Buscar nome do cliente
    client_name = ""
    if order.client_id:
        result = await db.execute(select(Client.nome).where(Client.id == order.client_id))
        row = result.first()
        client_name = row[0] if row else ""

    due = date.today() + timedelta(days=30)
    account = Account(
        tenant_id=tenant_id,
        type="RECEIVABLE",
        description=f"Pedido #{order.order_number}",
        related_order_id=order.id,
        client_or_supplier=client_name,
        due_date=due,
        amount=order.total or 0,
        paid_amount=0,
        status="PENDING",
    )
    db.add(account)

    # Mudar document_type para PEDIDO
    order.document_type = "PEDIDO"

    logger.info("Conta a receber criada para pedido #%s (R$ %.2f)", order.order_number, order.total or 0)
    return WorkflowResult(message=f"Conta a receber de R$ {order.total or 0:,.2f} criada para {client_name}")


async def execute_stock_reservation(db: AsyncSession, order: Order, tenant_id: int) -> WorkflowResult:
    """Reserva estoque para todos os itens do pedido."""
    # Verificar se ja foi reservado
    existing = await db.execute(
        select(func.count()).select_from(InventoryExit)
        .where(InventoryExit.tenant_id == tenant_id, InventoryExit.notes.like(f"RESERVA_ORDER_{order.id}|%"))
    )
    if existing.scalar() > 0:
        return WorkflowResult(success=False, message="Estoque ja reservado para este pedido.")

    # Buscar itens
    result = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id)
    )
    items = result.scalars().all()
    if not items:
        return WorkflowResult(success=False, message="Pedido sem itens.")

    # Buscar nome do cliente
    client_name = ""
    if order.client_id:
        r = await db.execute(select(Client.nome).where(Client.id == order.client_id))
        row = r.first()
        client_name = row[0] if row else ""

    today = date.today()
    count = 0
    for item in items:
        if not item.product_id or not item.quantity:
            continue

        exit_rec = InventoryExit(
            tenant_id=tenant_id,
            date=today,
            product_id=item.product_id,
            product_code=item.product_code or "",
            product_name=item.product_name or "",
            quantity=item.quantity,
            client_name=client_name,
            exit_type="Reserva de Pedido",
            notes=f"RESERVA_ORDER_{order.id}|Pedido #{order.order_number}",
        )
        db.add(exit_rec)

        # Atualizar saldo
        inv_result = await db.execute(
            select(Inventory).where(Inventory.product_id == item.product_id, Inventory.tenant_id == tenant_id)
        )
        inv = inv_result.scalar_one_or_none()
        if inv:
            inv.current_qty -= item.quantity
            inv.last_exit_date = today
        else:
            inv = Inventory(tenant_id=tenant_id, product_id=item.product_id,
                            current_qty=-item.quantity, last_exit_date=today)
            db.add(inv)
        count += 1

    logger.info("Estoque reservado: %d itens para pedido #%s", count, order.order_number)
    return WorkflowResult(message=f"Estoque reservado para {count} item(ns)")


async def execute_order_delivery(db: AsyncSession, order: Order, tenant_id: int) -> WorkflowResult:
    """Converte pedido entregue em registros de venda + trata estoque."""
    # Verificar se ja tem venda
    existing = await db.execute(
        select(func.count()).select_from(Sale)
        .where(Sale.tenant_id == tenant_id, Sale.order_id == order.id)
    )
    if existing.scalar() > 0:
        return WorkflowResult(success=False, message="Venda ja registrada para este pedido.")

    # Buscar itens
    result = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    items = result.scalars().all()
    if not items:
        return WorkflowResult(success=False, message="Pedido sem itens.")

    # Buscar cliente
    client_name = ""
    client_cnpj = ""
    if order.client_id:
        r = await db.execute(select(Client).where(Client.id == order.client_id))
        client = r.scalar_one_or_none()
        if client:
            client_name = client.nome or ""
            client_cnpj = client.cnpj_cpf or ""

    # Verificar se estoque ja foi reservado
    stock_check = await db.execute(
        select(func.count()).select_from(InventoryExit)
        .where(InventoryExit.tenant_id == tenant_id, InventoryExit.notes.like(f"RESERVA_ORDER_{order.id}|%"))
    )
    stock_reserved = stock_check.scalar() > 0

    today = date.today()
    for item in items:
        if not item.product_id or not item.quantity:
            continue

        nf_val = (item.nf_unit_value or 0) * item.quantity
        tax = nf_val * TAX_RATE_NF
        profit = (item.total or 0) - (item.cost_total or 0) - tax

        sale = Sale(
            tenant_id=tenant_id,
            date=today,
            order_id=order.id,
            order_number=order.order_number,
            company_id=order.company_id,
            client_id=order.client_id,
            client_name=client_name,
            client_cnpj_cpf=client_cnpj,
            product_id=item.product_id,
            product_code=item.product_code or "",
            product_name=item.product_name or "",
            quantity=item.quantity,
            unit=item.unit or "UN",
            shipping_origin=order.shipping_origin,
            unit_price=item.unit_price or 0,
            total_value=item.total or 0,
            discount=item.discount or 0,
            cost_per_unit=item.cost_per_unit or 0,
            cost_total=item.cost_total or 0,
            nf_value=nf_val,
            tax_amount=round(tax, 2),
            profit_total=round(profit, 2),
            payment_method=order.payment_method,
            salesperson_id=order.salesperson_id,
        )
        db.add(sale)
        await db.flush()

        if stock_reserved:
            # Atualizar saidas de reserva para vincular a venda
            exits = await db.execute(
                select(InventoryExit).where(
                    InventoryExit.tenant_id == tenant_id,
                    InventoryExit.notes.like(f"RESERVA_ORDER_{order.id}|%"),
                    InventoryExit.product_id == item.product_id,
                )
            )
            for exit_rec in exits.scalars().all():
                exit_rec.sale_id = sale.id
                exit_rec.exit_type = "BAIXA DE VENDA"
        else:
            # Criar saida de estoque
            exit_rec = InventoryExit(
                tenant_id=tenant_id, date=today,
                product_id=item.product_id,
                product_code=item.product_code or "",
                product_name=item.product_name or "",
                quantity=item.quantity,
                client_name=client_name,
                exit_type="BAIXA DE VENDA",
                sale_id=sale.id,
                notes=f"Venda ref. Pedido #{order.order_number}",
            )
            db.add(exit_rec)

            # Atualizar saldo
            inv_r = await db.execute(
                select(Inventory).where(Inventory.product_id == item.product_id, Inventory.tenant_id == tenant_id)
            )
            inv = inv_r.scalar_one_or_none()
            if inv:
                inv.current_qty -= item.quantity
                inv.last_exit_date = today
            else:
                inv = Inventory(tenant_id=tenant_id, product_id=item.product_id,
                                current_qty=-item.quantity, last_exit_date=today)
                db.add(inv)

    logger.info("Venda registrada para pedido #%s (%d itens)", order.order_number, len(items))
    return WorkflowResult(message=f"Venda registrada com {len(items)} item(ns)")


async def execute_order_cancellation(db: AsyncSession, order: Order, tenant_id: int) -> WorkflowResult:
    """Estorna reserva de estoque ao cancelar pedido."""
    result = await db.execute(
        select(InventoryExit).where(
            InventoryExit.tenant_id == tenant_id,
            InventoryExit.notes.like(f"RESERVA_ORDER_{order.id}|%"),
        )
    )
    reserved = result.scalars().all()

    if not reserved:
        return WorkflowResult(message="Pedido cancelado (sem estoque a estornar)")

    today = date.today()
    for r in reserved:
        entry = InventoryEntry(
            tenant_id=tenant_id, date=today,
            product_id=r.product_id,
            product_code=r.product_code or "",
            product_name=r.product_name or "",
            quantity=r.quantity,
            entry_type="Cancelamento Reserva",
            notes=f"Estorno reserva pedido #{order.order_number}",
        )
        db.add(entry)

        inv_r = await db.execute(
            select(Inventory).where(Inventory.product_id == r.product_id, Inventory.tenant_id == tenant_id)
        )
        inv = inv_r.scalar_one_or_none()
        if inv:
            inv.current_qty += r.quantity
            inv.last_entry_date = today
        else:
            inv = Inventory(tenant_id=tenant_id, product_id=r.product_id,
                            current_qty=r.quantity, last_entry_date=today)
            db.add(inv)

    logger.info("Reserva estornada para pedido #%s (%d itens)", order.order_number, len(reserved))
    return WorkflowResult(message=f"Reserva estornada ({len(reserved)} item(ns) devolvidos ao estoque)")


# Mapa de transicoes validas e acoes automaticas
VALID_TRANSITIONS = {
    "ORCAMENTO": ["CONFIRMADO", "CANCELADO"],
    "CONFIRMADO": ["RESERVAR ESTOQUE", "PRODUCAO", "CANCELADO"],
    "RESERVAR ESTOQUE": ["PRODUCAO", "EXPEDIDO", "CANCELADO"],
    "PRODUCAO": ["EXPEDIDO", "CANCELADO"],
    "EXPEDIDO": ["ENTREGUE", "CANCELADO"],
    "ENTREGUE": [],
    "CANCELADO": [],
}

# Acoes automaticas por status destino
STATUS_ACTIONS = {
    "CONFIRMADO": execute_order_confirmed,
    "RESERVAR ESTOQUE": execute_stock_reservation,
    "PRODUCAO": execute_stock_reservation,  # Tambem reserva estoque se nao foi reservado
    "ENTREGUE": execute_order_delivery,
    "CANCELADO": execute_order_cancellation,
}


async def change_order_status(
    db: AsyncSession, order: Order, new_status: str, tenant_id: int
) -> WorkflowResult:
    """Muda o status do pedido e executa acoes automaticas."""
    current = order.status or "ORCAMENTO"

    # Validar transicao
    valid = VALID_TRANSITIONS.get(current, [])
    if new_status not in valid:
        return WorkflowResult(
            success=False,
            message=f"Transicao invalida: {current} -> {new_status}. Permitidos: {', '.join(valid)}",
        )

    # Executar acao automatica
    action = STATUS_ACTIONS.get(new_status)
    result = WorkflowResult(message=f"Status alterado para {new_status}")
    if action:
        result = await action(db, order, tenant_id)
        if not result.success:
            return result

    # Atualizar status
    order.status = new_status
    from datetime import datetime
    order.status_changed_at = datetime.now()

    logger.info("Pedido #%s: %s -> %s", order.order_number, current, new_status)
    return result
