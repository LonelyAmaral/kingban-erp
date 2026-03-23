"""Servico de gestao de estoque.

Portado do desktop: kingban/services/inventory_service.py
Adaptado para SQLAlchemy async.
"""

import logging
from datetime import date

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.inventory import Inventory, InventoryEntry, InventoryExit
from app.models.product import Product

logger = logging.getLogger("kingban.inventory")


async def _update_stock(db: AsyncSession, product_id: int, quantity: int, sign: int, op_date: date, tenant_id: int):
    """Atualiza saldo do estoque. sign=+1 para entrada, -1 para saida."""
    result = await db.execute(
        select(Inventory).where(Inventory.product_id == product_id, Inventory.tenant_id == tenant_id)
    )
    inv = result.scalar_one_or_none()

    delta = sign * quantity
    if inv:
        inv.current_qty += delta
        if sign > 0:
            inv.last_entry_date = op_date
        else:
            inv.last_exit_date = op_date
    else:
        inv = Inventory(
            tenant_id=tenant_id,
            product_id=product_id,
            current_qty=delta,
            last_entry_date=op_date if sign > 0 else None,
            last_exit_date=op_date if sign < 0 else None,
        )
        db.add(inv)


async def add_entry(
    db: AsyncSession,
    tenant_id: int,
    product_id: int,
    product_code: str,
    product_name: str,
    quantity: int,
    entry_type: str,
    entry_date: date = None,
    supplier_id: int = None,
    notes: str = "",
):
    """Adiciona uma entrada de estoque e atualiza saldo."""
    if quantity <= 0:
        logger.warning("Tentativa de entrada com quantidade <= 0: product_id=%s qty=%s", product_id, quantity)
        return None
    d = entry_date or date.today()
    entry = InventoryEntry(
        tenant_id=tenant_id,
        date=d,
        product_id=product_id,
        product_code=product_code,
        product_name=product_name,
        quantity=quantity,
        entry_type=entry_type,
        supplier_id=supplier_id,
        notes=notes,
    )
    db.add(entry)
    await _update_stock(db, product_id, quantity, +1, d, tenant_id)
    logger.info("Entrada: %s x%d (%s)", product_code, quantity, entry_type)
    return entry


async def add_exit(
    db: AsyncSession,
    tenant_id: int,
    product_id: int,
    product_code: str,
    product_name: str,
    quantity: int,
    exit_type: str,
    client_name: str = "",
    sale_id: int = None,
    exit_date: date = None,
    notes: str = "",
):
    """Adiciona uma saida de estoque e atualiza saldo."""
    if quantity <= 0:
        logger.warning("Tentativa de saida com quantidade <= 0: product_id=%s qty=%s", product_id, quantity)
        return None
    d = exit_date or date.today()
    exit_rec = InventoryExit(
        tenant_id=tenant_id,
        date=d,
        product_id=product_id,
        product_code=product_code,
        product_name=product_name,
        quantity=quantity,
        client_name=client_name,
        exit_type=exit_type,
        sale_id=sale_id,
        notes=notes,
    )
    db.add(exit_rec)
    await _update_stock(db, product_id, quantity, -1, d, tenant_id)
    logger.info("Saida: %s x%d (%s) cliente=%s", product_code, quantity, exit_type, client_name or "-")
    return exit_rec


async def get_current_stock(db: AsyncSession, tenant_id: int) -> list:
    """Retorna estoque atual com detalhes do produto."""
    result = await db.execute(
        select(
            Product.codigo,
            Product.nome,
            Product.categoria,
            func.coalesce(Inventory.current_qty, 0).label("current_qty"),
            Product.preco_nf_integral,
            func.coalesce(Inventory.min_qty, 0).label("min_qty"),
            Inventory.last_entry_date,
            Inventory.last_exit_date,
        )
        .outerjoin(Inventory, (Product.id == Inventory.product_id) & (Inventory.tenant_id == tenant_id))
        .where(Product.tenant_id == tenant_id, Product.ativo == True)
        .order_by(Product.codigo)
    )
    return result.all()


async def recalculate_inventory(db: AsyncSession, product_id: int, tenant_id: int):
    """Recalcula estoque de um produto a partir do historico de entradas e saidas."""
    entries_total = (await db.execute(
        select(func.coalesce(func.sum(InventoryEntry.quantity), 0))
        .where(InventoryEntry.product_id == product_id, InventoryEntry.tenant_id == tenant_id)
    )).scalar()

    exits_total = (await db.execute(
        select(func.coalesce(func.sum(InventoryExit.quantity), 0))
        .where(InventoryExit.product_id == product_id, InventoryExit.tenant_id == tenant_id)
    )).scalar()

    current = entries_total - exits_total

    result = await db.execute(
        select(Inventory).where(Inventory.product_id == product_id, Inventory.tenant_id == tenant_id)
    )
    inv = result.scalar_one_or_none()
    if inv:
        inv.current_qty = current
    else:
        inv = Inventory(tenant_id=tenant_id, product_id=product_id, current_qty=current)
        db.add(inv)

    logger.info("Estoque recalculado: product_id=%s qty=%d", product_id, current)
