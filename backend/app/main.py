"""KING BAN ERP - FastAPI Application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api import auth, clients, suppliers, products, salespeople
from app.api import orders, sales, inventory
from app.api import purchases, accounts, commissions, difal, dashboard, cashflow, reports, audit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("kingban")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("KING BAN ERP starting...")
    # Auto-criar tabelas no startup (dev com SQLite)
    from app.database import engine, Base
    import app.models  # noqa: importa todos os models para metadata
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tabelas criadas/verificadas.")
    yield
    logger.info("KING BAN ERP shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
app.include_router(suppliers.router, prefix="/api/suppliers", tags=["Suppliers"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(salespeople.router, prefix="/api/salespeople", tags=["Salespeople"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])
app.include_router(inventory.router, prefix="/api/inventory", tags=["Inventory"])
app.include_router(purchases.router, prefix="/api/purchases", tags=["Purchases"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(commissions.router, prefix="/api/commissions", tags=["Commissions"])
app.include_router(difal.router, prefix="/api/difal", tags=["DIFAL"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(cashflow.router, prefix="/api/cashflow", tags=["Cash Flow"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(audit.router, prefix="/api/audit", tags=["Audit"])


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.APP_VERSION}
