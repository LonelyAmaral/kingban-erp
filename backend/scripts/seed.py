"""
Seed de dados iniciais — KING BAN ERP.

Uso: python -m scripts.seed (a partir do diretorio backend/)

Cria:
- Tenant KING BAN
- Usuario admin
- Aliquotas DIFAL (27 estados x 2 NCMs)
- 244 Produtos reais (do desktop via fixtures/products.json)
- Vendedores
- Custos de comissao
"""

import asyncio
import json
import logging
import sys
import os

# Adicionar backend ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import engine, async_session, Base
from app.models import *
from app.core.auth import hash_password

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")

# ============================================================
# DADOS DIFAL — 27 estados brasileiros
# NCM 94037000 (Banheiro Quimico) e 94069090 (Outros)
# ============================================================
DIFAL_STATES = [
    # (UF, Nome, NCM, aliq_interna, aliq_inter, fcp, formula_especial)
    ("AC", "Acre", "94037000", 0.19, 0.12, 0.0, None),
    ("AL", "Alagoas", "94037000", 0.19, 0.12, 0.01, None),
    ("AM", "Amazonas", "94037000", 0.20, 0.12, 0.02, None),
    ("AP", "Amapa", "94037000", 0.18, 0.12, 0.0, None),
    ("BA", "Bahia", "94037000", 0.20, 0.12, 0.02, None),
    ("CE", "Ceara", "94037000", 0.20, 0.12, 0.02, None),
    ("DF", "Distrito Federal", "94037000", 0.20, 0.12, 0.02, None),
    ("ES", "Espirito Santo", "94037000", 0.17, 0.12, 0.0, None),
    ("GO", "Goias", "94037000", 0.19, 0.12, 0.01, None),
    ("MA", "Maranhao", "94037000", 0.22, 0.12, 0.02, None),
    ("MG", "Minas Gerais", "94037000", 0.18, 0.12, 0.02, "MG"),
    ("MS", "Mato Grosso do Sul", "94037000", 0.17, 0.12, 0.0, None),
    ("MT", "Mato Grosso", "94037000", 0.17, 0.12, 0.0, None),
    ("PA", "Para", "94037000", 0.19, 0.12, 0.01, None),
    ("PB", "Paraiba", "94037000", 0.20, 0.12, 0.02, None),
    ("PE", "Pernambuco", "94037000", 0.20, 0.12, 0.02, None),
    ("PI", "Piaui", "94037000", 0.21, 0.12, 0.02, None),
    ("PR", "Parana", "94037000", 0.19, 0.12, 0.0, None),
    ("RJ", "Rio de Janeiro", "94037000", 0.20, 0.12, 0.02, None),
    ("RN", "Rio Grande do Norte", "94037000", 0.20, 0.12, 0.02, None),
    ("RO", "Rondonia", "94037000", 0.19, 0.12, 0.01, None),
    ("RR", "Roraima", "94037000", 0.20, 0.12, 0.02, None),
    ("RS", "Rio Grande do Sul", "94037000", 0.19, 0.12, 0.01, None),
    ("SC", "Santa Catarina", "94037000", 0.17, 0.12, 0.0, None),
    ("SE", "Sergipe", "94037000", 0.19, 0.12, 0.01, None),
    ("TO", "Tocantins", "94037000", 0.20, 0.12, 0.02, None),
    # NCM 94069090 — mesmas aliquotas (simplificado)
    ("AC", "Acre", "94069090", 0.19, 0.12, 0.0, None),
    ("AL", "Alagoas", "94069090", 0.19, 0.12, 0.01, None),
    ("AM", "Amazonas", "94069090", 0.20, 0.12, 0.02, None),
    ("AP", "Amapa", "94069090", 0.18, 0.12, 0.0, None),
    ("BA", "Bahia", "94069090", 0.20, 0.12, 0.02, None),
    ("CE", "Ceara", "94069090", 0.20, 0.12, 0.02, None),
    ("DF", "Distrito Federal", "94069090", 0.20, 0.12, 0.02, None),
    ("ES", "Espirito Santo", "94069090", 0.17, 0.12, 0.0, None),
    ("GO", "Goias", "94069090", 0.19, 0.12, 0.01, None),
    ("MA", "Maranhao", "94069090", 0.22, 0.12, 0.02, None),
    ("MG", "Minas Gerais", "94069090", 0.18, 0.12, 0.02, "MG"),
    ("MS", "Mato Grosso do Sul", "94069090", 0.17, 0.12, 0.0, None),
    ("MT", "Mato Grosso", "94069090", 0.17, 0.12, 0.0, None),
    ("PA", "Para", "94069090", 0.19, 0.12, 0.01, None),
    ("PB", "Paraiba", "94069090", 0.20, 0.12, 0.02, None),
    ("PE", "Pernambuco", "94069090", 0.20, 0.12, 0.02, None),
    ("PI", "Piaui", "94069090", 0.21, 0.12, 0.02, None),
    ("PR", "Parana", "94069090", 0.19, 0.12, 0.0, None),
    ("RJ", "Rio de Janeiro", "94069090", 0.20, 0.12, 0.02, None),
    ("RN", "Rio Grande do Norte", "94069090", 0.20, 0.12, 0.02, None),
    ("RO", "Rondonia", "94069090", 0.19, 0.12, 0.01, None),
    ("RR", "Roraima", "94069090", 0.20, 0.12, 0.02, None),
    ("RS", "Rio Grande do Sul", "94069090", 0.19, 0.12, 0.01, None),
    ("SC", "Santa Catarina", "94069090", 0.17, 0.12, 0.0, None),
    ("SE", "Sergipe", "94069090", 0.19, 0.12, 0.01, None),
    ("TO", "Tocantins", "94069090", 0.20, 0.12, 0.02, None),
]

# Vendedores
VENDEDORES = [
    ("Nadia", "nadia@kingban.com.br", "(14) 99999-0001", 0.0),
    ("Matheus", "matheus@kingban.com.br", "(14) 99999-0002", 0.0),
    ("Carlos", "carlos@kingban.com.br", "(14) 99999-0003", 0.0),
]


def load_products_from_fixtures() -> list[dict]:
    """Carrega 244 produtos do arquivo JSON gerado pelo extract_desktop_data.py."""
    fixtures_file = os.path.join(FIXTURES_DIR, "products.json")
    if os.path.exists(fixtures_file):
        with open(fixtures_file, "r", encoding="utf-8") as f:
            products = json.load(f)
        logger.info(f"Fixtures: {len(products)} produtos carregados de {fixtures_file}")
        return products
    logger.warning(f"Fixtures nao encontrado: {fixtures_file}")
    return []


async def seed():
    """Executa seed completo."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        try:
            # Verificar se ja existe tenant
            existing = await db.execute(select(Tenant).where(Tenant.name == "KING BAN"))
            if existing.scalar_one_or_none():
                logger.warning("Seed ja executado — pulando.")
                return

            # 1. Tenant
            tenant = Tenant(
                code="kb",
                name="KING BAN",
                cnpj="96453840000189",
                trade_name="KING BAN Banheiros Quimicos",
                address="Avare - SP",
                city="Avare",
                state="SP",
            )
            db.add(tenant)
            await db.flush()
            tid = tenant.id
            logger.info(f"Tenant criado: KING BAN (id={tid})")

            # 2. Usuario admin
            admin = User(
                tenant_id=tid,
                username="admin",
                hashed_password=hash_password("admin123"),
                full_name="Administrador",
                role="admin",
            )
            db.add(admin)
            await db.flush()
            logger.info("Usuario admin criado (admin / admin123)")

            # 3. DIFAL rates
            for uf, nome, ncm, ai, ainter, fcp, formula in DIFAL_STATES:
                db.add(DifalRate(
                    tenant_id=tid,
                    state_code=uf,
                    state_name=nome,
                    ncm=ncm,
                    aliq_interna=ai,
                    aliq_inter=ainter,
                    fcp=fcp,
                    formula_especial=formula,
                ))
            await db.flush()
            logger.info(f"DIFAL: {len(DIFAL_STATES)} aliquotas inseridas")

            # 4. Produtos — 244 reais do desktop (via fixtures)
            products_data = load_products_from_fixtures()
            if not products_data:
                logger.error("Nenhum produto encontrado! Execute primeiro: python scripts/extract_desktop_data.py")
                await db.rollback()
                return

            for p in products_data:
                db.add(Product(
                    tenant_id=tid,
                    codigo=p["codigo"],
                    nome=p["nome"],
                    categoria=p.get("categoria", ""),
                    unidade=p.get("unidade", "UN"),
                    ncm=p.get("ncm", "94037000"),
                    custo=p.get("custo", 0),
                    frete=p.get("frete", 0),
                    preco_nf_integral=p.get("preco_nf_integral", 0),
                    preco_nf_baixa_1_3=p.get("preco_nf_baixa_1_3", 0),
                    desconto_nf_baixa_1_3=p.get("desconto_nf_baixa_1_3", 0),
                    preco_nf_baixa_4=p.get("preco_nf_baixa_4", 0),
                    desconto_nf_baixa_4=p.get("desconto_nf_baixa_4", 0),
                    preco_nf_cheia_4=p.get("preco_nf_cheia_4", 0),
                    desconto_nf_cheia_4=p.get("desconto_nf_cheia_4", 0),
                    preco_nf_integral_10=p.get("preco_nf_integral_10", 0),
                    preco_nf_baixa_10=p.get("preco_nf_baixa_10", 0),
                    desconto_nf_baixa_10=p.get("desconto_nf_baixa_10", 0),
                    preco_fabrica_10=p.get("preco_fabrica_10", 0),
                    desconto_fabrica_10=p.get("desconto_fabrica_10", 0),
                    taxa_comissao=p.get("taxa_comissao", 0.15),
                    ativo=p.get("ativo", True),
                ))
            await db.flush()
            logger.info(f"Produtos: {len(products_data)} inseridos (244 reais do desktop)")

            # 5. Custos de comissao (gerados a partir dos produtos)
            products_result = await db.execute(
                select(Product).where(Product.tenant_id == tid)
            )
            for p in products_result.scalars().all():
                db.add(CommissionCost(
                    tenant_id=tid,
                    product_id=p.id,
                    product_code=p.codigo,
                    product_name=p.nome,
                    base_cost=p.custo,
                    commission_rate=p.taxa_comissao,
                ))
            await db.flush()
            logger.info("Custos de comissao criados para todos os produtos")

            # 6. Vendedores
            for nome, email, telefone, salario in VENDEDORES:
                db.add(Salesperson(
                    tenant_id=tid,
                    nome=nome,
                    email=email,
                    telefone=telefone,
                    salario_fixo=salario,
                    ativo=True,
                ))
            await db.flush()
            logger.info(f"Vendedores: {len(VENDEDORES)} inseridos")

            await db.commit()
            logger.info("=== SEED COMPLETO ===")
            logger.info(f"  {len(products_data)} produtos")
            logger.info(f"  {len(DIFAL_STATES)} DIFAL rates")
            logger.info(f"  {len(VENDEDORES)} vendedores")
            logger.info("Login: admin / admin123")

        except Exception as e:
            await db.rollback()
            logger.error(f"Erro no seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())
