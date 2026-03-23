"""API Dashboard — KPIs e indicadores gerenciais."""

from datetime import date, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, literal_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.models.client import Client
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.salesperson import Salesperson
from app.models.order import Order
from app.models.sale import Sale
from app.models.inventory import Inventory
from app.models.account import Account
from app.models.user import User

router = APIRouter()


@router.get("")
async def dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """KPIs principais do dashboard."""
    tid = user.tenant_id

    # Contadores de cadastros
    clientes = (await db.execute(select(func.count(Client.id)).where(Client.tenant_id == tid, Client.ativo == True))).scalar()
    fornecedores = (await db.execute(select(func.count(Supplier.id)).where(Supplier.tenant_id == tid, Supplier.ativo == True))).scalar()
    produtos = (await db.execute(select(func.count(Product.id)).where(Product.tenant_id == tid, Product.ativo == True))).scalar()
    vendedores = (await db.execute(select(func.count(Salesperson.id)).where(Salesperson.tenant_id == tid, Salesperson.ativo == True))).scalar()

    # Orcamentos abertos (status ORCAMENTO)
    orcamentos_abertos = (await db.execute(
        select(func.count(Order.id)).where(Order.tenant_id == tid, Order.status == "ORCAMENTO")
    )).scalar()

    # Pedidos em andamento (CONFIRMADO, RESERVAR ESTOQUE, PRODUCAO, EXPEDIDO)
    pedidos_andamento = (await db.execute(
        select(func.count(Order.id)).where(
            Order.tenant_id == tid,
            Order.status.in_(["CONFIRMADO", "RESERVAR ESTOQUE", "PRODUCAO", "EXPEDIDO"]),
        )
    )).scalar()

    # Contas a receber pendentes
    contas_receber = (await db.execute(
        select(func.coalesce(func.sum(Account.amount - Account.paid_amount), 0)).where(
            Account.tenant_id == tid,
            Account.type == "RECEIVABLE",
            Account.status.in_(["PENDING", "PARTIAL"]),
        )
    )).scalar()

    # Contas a pagar pendentes
    contas_pagar = (await db.execute(
        select(func.coalesce(func.sum(Account.amount - Account.paid_amount), 0)).where(
            Account.tenant_id == tid,
            Account.type == "PAYABLE",
            Account.status.in_(["PENDING", "PARTIAL"]),
        )
    )).scalar()

    # Vendas do mes atual
    hoje = date.today()
    primeiro_dia_mes = hoje.replace(day=1)
    vendas_mes = (await db.execute(
        select(
            func.coalesce(func.sum(Sale.total_value), 0).label("faturamento"),
            func.coalesce(func.sum(Sale.profit_total), 0).label("lucro"),
            func.count(Sale.id).label("qtd"),
        ).where(Sale.tenant_id == tid, Sale.date >= primeiro_dia_mes)
    )).one()

    faturamento_mes = float(vendas_mes.faturamento)
    lucro_mes = float(vendas_mes.lucro)
    qtd_vendas_mes = int(vendas_mes.qtd)
    ticket_medio = faturamento_mes / qtd_vendas_mes if qtd_vendas_mes > 0 else 0

    # Estoque critico (abaixo do minimo)
    estoque_critico = (await db.execute(
        select(func.count(Inventory.id)).where(
            Inventory.tenant_id == tid,
            Inventory.current_qty <= Inventory.min_qty,
        )
    )).scalar()

    return {
        "cadastros": {
            "clientes": clientes,
            "fornecedores": fornecedores,
            "produtos": produtos,
            "vendedores": vendedores,
        },
        "operacional": {
            "orcamentos_abertos": orcamentos_abertos,
            "pedidos_andamento": pedidos_andamento,
            "estoque_critico": estoque_critico,
        },
        "financeiro": {
            "faturamento_mes": round(faturamento_mes, 2),
            "lucro_mes": round(lucro_mes, 2),
            "ticket_medio": round(ticket_medio, 2),
            "qtd_vendas_mes": qtd_vendas_mes,
            "contas_receber": round(float(contas_receber), 2),
            "contas_pagar": round(float(contas_pagar), 2),
        },
    }


@router.get("/vendas-mensal")
async def vendas_por_mes(
    meses: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Faturamento e lucro agrupado por mes (ultimos N meses)."""
    tid = user.tenant_id
    hoje = date.today()
    data_inicio = (hoje.replace(day=1) - timedelta(days=(meses - 1) * 30)).replace(day=1)

    # strftime compativel com SQLite e PostgreSQL
    mes_expr = func.strftime("%Y-%m", Sale.date)
    result = await db.execute(
        select(
            mes_expr.label("mes"),
            func.coalesce(func.sum(Sale.total_value), 0).label("faturamento"),
            func.coalesce(func.sum(Sale.profit_total), 0).label("lucro"),
            func.count(Sale.id).label("qtd"),
        )
        .where(Sale.tenant_id == tid, Sale.date >= data_inicio)
        .group_by(mes_expr)
        .order_by(mes_expr)
    )
    rows = result.all()

    return [
        {
            "mes": row.mes or "",
            "faturamento": round(float(row.faturamento), 2),
            "lucro": round(float(row.lucro), 2),
            "quantidade": int(row.qtd),
        }
        for row in rows
    ]


@router.get("/top-clientes")
async def top_clientes(
    limite: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Top clientes por faturamento."""
    tid = user.tenant_id
    result = await db.execute(
        select(
            Sale.client_name,
            func.sum(Sale.total_value).label("total"),
            func.count(Sale.id).label("qtd"),
        )
        .where(Sale.tenant_id == tid)
        .group_by(Sale.client_name)
        .order_by(desc("total"))
        .limit(limite)
    )
    return [
        {"cliente": r.client_name or "N/A", "total": round(float(r.total), 2), "qtd": int(r.qtd)}
        for r in result.all()
    ]


@router.get("/top-produtos")
async def top_produtos(
    limite: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Top produtos por quantidade vendida."""
    tid = user.tenant_id
    result = await db.execute(
        select(
            Sale.product_code,
            Sale.product_name,
            func.sum(Sale.quantity).label("qtd"),
            func.sum(Sale.total_value).label("total"),
        )
        .where(Sale.tenant_id == tid)
        .group_by(Sale.product_code, Sale.product_name)
        .order_by(desc("qtd"))
        .limit(limite)
    )
    return [
        {
            "codigo": r.product_code or "",
            "produto": r.product_name or "N/A",
            "quantidade": int(r.qtd),
            "total": round(float(r.total), 2),
        }
        for r in result.all()
    ]
