"""Seed data for initial setup."""

import asyncio
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session, engine
from app.database import Base
from app.models.tenant import Tenant
from app.models.user import User
from app.core.auth import hash_password

logger = logging.getLogger("kingban.seed")


async def seed_initial_data():
    """Create initial tenant and admin user if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # Check if tenant exists
        result = await db.execute(select(Tenant).where(Tenant.code == "kb"))
        tenant = result.scalar_one_or_none()

        if not tenant:
            tenant = Tenant(
                code="kb",
                name="KING BAN",
                trade_name="KING BAN INDUSTRIA E COMERCIO DE PLASTICOS LTDA",
                cnpj="96.453.840/0001-89",
                city="Avare",
                state="SP",
                bank_name="Itau",
                bank_agency="0168",
                bank_account="27284-7",
                pix_key="96.453.840/0001-89",
            )
            db.add(tenant)
            await db.flush()
            logger.info("Tenant KING BAN criado (id=%d)", tenant.id)

        # Check if admin exists
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()

        if not admin:
            admin = User(
                username="admin",
                full_name="Administrador",
                email="admin@kingban.com.br",
                hashed_password=hash_password("admin123"),
                role="admin",
                tenant_id=tenant.id,
            )
            db.add(admin)
            logger.info("Usuario admin criado")

        # KING PLAST tenant
        result = await db.execute(select(Tenant).where(Tenant.code == "KP"))
        if not result.scalar_one_or_none():
            kp = Tenant(code="KP", name="KING PLAST", city="Avare", state="SP")
            db.add(kp)
            logger.info("Tenant KING PLAST criado")

        await db.commit()
        logger.info("Seed inicial concluido.")


if __name__ == "__main__":
    asyncio.run(seed_initial_data())
