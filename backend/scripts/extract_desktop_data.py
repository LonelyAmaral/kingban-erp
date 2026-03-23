"""
Extrai dados do desktop KING BAN para JSON fixtures.

Lê o arquivo SQL de seed (002_product_seed.sql) e o banco SQLite desktop,
exportando para JSON que o seed web pode consumir.

Uso: python scripts/extract_desktop_data.py
"""

import json
import os
import re
import sqlite3
import sys

# Paths
DESKTOP_DIR = os.path.expanduser("~/CLAUDE/kingban")
SQL_SEED = os.path.join(DESKTOP_DIR, "core", "migrations", "002_product_seed.sql")
DB_PATH = os.path.expanduser("~/.kingban/kingban.db")
FIXTURES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fixtures")

# Mapa de campos desktop -> web
PRODUCT_FIELD_MAP = {
    "code": "codigo",
    "name": "nome",
    "category": "categoria",
    "unit": "unidade",
    "ncm": "ncm",
    "cost_price": "custo",
    "freight_cost": "frete",
    "price_nf_integral": "preco_nf_integral",
    "price_nf_baixa_1_3": "preco_nf_baixa_1_3",
    "discount_nf_baixa_1_3": "desconto_nf_baixa_1_3",
    "price_nf_baixa_4plus": "preco_nf_baixa_4",
    "discount_nf_baixa_4plus": "desconto_nf_baixa_4",
    "price_nf_cheia_4plus": "preco_nf_cheia_4",
    "discount_nf_cheia_4plus": "desconto_nf_cheia_4",
    "price_nf_integral_10plus": "preco_nf_integral_10",
    "discount_nf_integral_10plus": "desconto_nf_integral_10",
    "price_nf_baixa_10plus": "preco_nf_baixa_10",
    "discount_nf_baixa_10plus": "desconto_nf_baixa_10",
    "price_fabrica_10plus": "preco_fabrica_10",
    "discount_fabrica_10plus": "desconto_fabrica_10",
    "commission_rate": "taxa_comissao",
    "active": "ativo",
}

# Colunas na ordem do INSERT SQL
SQL_COLUMNS = [
    "code", "name", "category", "unit", "ncm",
    "cost_price", "freight_cost",
    "price_nf_integral",
    "price_nf_baixa_1_3", "discount_nf_baixa_1_3",
    "price_nf_baixa_4plus", "discount_nf_baixa_4plus",
    "price_nf_cheia_4plus", "discount_nf_cheia_4plus",
    "price_nf_integral_10plus", "discount_nf_integral_10plus",
    "price_nf_baixa_10plus", "discount_nf_baixa_10plus",
    "price_fabrica_10plus", "discount_fabrica_10plus",
    "commission_rate", "active",
]

# Campos numericos
NUMERIC_FIELDS = {
    "cost_price", "freight_cost",
    "price_nf_integral", "price_nf_baixa_1_3", "discount_nf_baixa_1_3",
    "price_nf_baixa_4plus", "discount_nf_baixa_4plus",
    "price_nf_cheia_4plus", "discount_nf_cheia_4plus",
    "price_nf_integral_10plus", "discount_nf_integral_10plus",
    "price_nf_baixa_10plus", "discount_nf_baixa_10plus",
    "price_fabrica_10plus", "discount_fabrica_10plus",
    "commission_rate", "active",
}


def parse_sql_values(sql_line: str) -> list:
    """Extrai valores de uma linha INSERT SQL."""
    match = re.search(r"VALUES\s*\((.+)\)\s*;?\s*$", sql_line)
    if not match:
        return []

    values_str = match.group(1)
    values = []
    current = ""
    in_string = False
    escape_next = False

    for ch in values_str:
        if escape_next:
            current += ch
            escape_next = False
            continue
        if ch == "\\":
            escape_next = True
            current += ch
            continue
        if ch == "'" and not in_string:
            in_string = True
            continue
        if ch == "'" and in_string:
            # Check for escaped quote ''
            in_string = False
            continue
        if ch == "," and not in_string:
            values.append(current.strip())
            current = ""
            continue
        current += ch

    if current.strip():
        values.append(current.strip())

    return values


def extract_products_from_sql() -> list[dict]:
    """Extrai produtos do arquivo SQL de seed."""
    if not os.path.exists(SQL_SEED):
        print(f"ERRO: Arquivo SQL nao encontrado: {SQL_SEED}")
        return []

    products = []
    with open(SQL_SEED, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line.startswith("INSERT"):
                continue

            raw_values = parse_sql_values(line)
            if len(raw_values) != len(SQL_COLUMNS):
                print(f"AVISO: Linha com {len(raw_values)} valores (esperado {len(SQL_COLUMNS)}): {line[:80]}...")
                continue

            product = {}
            for col, val in zip(SQL_COLUMNS, raw_values):
                web_field = PRODUCT_FIELD_MAP[col]
                if col in NUMERIC_FIELDS:
                    try:
                        product[web_field] = float(val)
                    except ValueError:
                        product[web_field] = 0.0
                else:
                    product[web_field] = val

            # Converter ativo de 1/0 para bool
            product["ativo"] = bool(product.get("ativo", 1))

            products.append(product)

    return products


def extract_products_from_db() -> list[dict]:
    """Extrai produtos do banco SQLite desktop (fallback)."""
    if not os.path.exists(DB_PATH):
        print(f"AVISO: Banco desktop nao encontrado: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM products ORDER BY code")
        rows = cursor.fetchall()
        products = []
        for row in rows:
            product = {}
            for col in SQL_COLUMNS:
                web_field = PRODUCT_FIELD_MAP[col]
                val = row[col] if col in row.keys() else None
                if col in NUMERIC_FIELDS:
                    product[web_field] = float(val) if val is not None else 0.0
                else:
                    product[web_field] = val or ""
            product["ativo"] = bool(product.get("ativo", 1))
            products.append(product)
        return products
    except Exception as e:
        print(f"ERRO ao ler banco desktop: {e}")
        return []
    finally:
        conn.close()


def extract_difal_from_db() -> list[dict]:
    """Extrai DIFAL rates do banco SQLite desktop."""
    if not os.path.exists(DB_PATH):
        print(f"AVISO: Banco desktop nao encontrado: {DB_PATH}")
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM difal_rates ORDER BY state_code, ncm")
        rows = cursor.fetchall()
        rates = []
        for row in rows:
            rates.append({
                "state_code": row["state_code"],
                "state_name": row["state_name"],
                "ncm": row.get("ncm", "94037000"),
                "aliq_interna": float(row.get("aliq_interna", 0) or 0),
                "aliq_inter": float(row.get("aliq_interestadual", row.get("aliq_inter", 0)) or 0),
                "fcp": float(row.get("fcp", 0) or 0),
                "formula_especial": row.get("special_calc") or row.get("formula_especial"),
            })
        return rates
    except Exception as e:
        print(f"ERRO ao ler DIFAL do banco: {e}")
        return []
    finally:
        conn.close()


def extract_commission_costs_from_db() -> list[dict]:
    """Extrai custos de comissao do banco SQLite desktop."""
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM commission_costs ORDER BY product_label")
        rows = cursor.fetchall()
        costs = []
        for row in rows:
            costs.append({
                "product_label": row["product_label"],
                "cost": float(row["cost"] or 0),
                "commission_rate": float(row["commission_rate"] or 0.15),
            })
        return costs
    except Exception as e:
        print(f"ERRO ao ler commission_costs: {e}")
        return []
    finally:
        conn.close()


def main():
    os.makedirs(FIXTURES_DIR, exist_ok=True)

    # 1. Extrair produtos do SQL (fonte primaria)
    print("=" * 60)
    print("EXTRAINDO DADOS DO DESKTOP KING BAN")
    print("=" * 60)

    print(f"\n1. Produtos (SQL: {SQL_SEED})")
    products = extract_products_from_sql()

    if not products:
        print("   Tentando banco SQLite como fallback...")
        products = extract_products_from_db()

    if products:
        output = os.path.join(FIXTURES_DIR, "products.json")
        with open(output, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
        print(f"   -> {len(products)} produtos exportados para {output}")

        # Categorias encontradas
        cats = set(p["categoria"] for p in products)
        print(f"   Categorias: {', '.join(sorted(cats))}")
    else:
        print("   ERRO: Nenhum produto encontrado!")
        sys.exit(1)

    # 2. DIFAL rates (do banco ou usar defaults do seed)
    print(f"\n2. DIFAL rates (DB: {DB_PATH})")
    difal_rates = extract_difal_from_db()
    if difal_rates:
        output = os.path.join(FIXTURES_DIR, "difal_rates.json")
        with open(output, "w", encoding="utf-8") as f:
            json.dump(difal_rates, f, ensure_ascii=False, indent=2)
        print(f"   -> {len(difal_rates)} DIFAL rates exportados")
    else:
        print("   AVISO: DIFAL rates nao encontrados no banco. Usando dados do seed existente.")

    # 3. Commission costs (do banco)
    print(f"\n3. Commission costs (DB: {DB_PATH})")
    costs = extract_commission_costs_from_db()
    if costs:
        output = os.path.join(FIXTURES_DIR, "commission_costs.json")
        with open(output, "w", encoding="utf-8") as f:
            json.dump(costs, f, ensure_ascii=False, indent=2)
        print(f"   -> {len(costs)} custos de comissao exportados")
    else:
        print("   AVISO: Commission costs serao gerados automaticamente a partir dos produtos.")

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO:")
    print(f"  Produtos: {len(products)}")
    print(f"  DIFAL:    {len(difal_rates)}")
    print(f"  Custos:   {len(costs)}")
    print(f"  Fixtures: {FIXTURES_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
