"""Motor de precos — resolve a faixa correta baseado em tipo NF, quantidade e origem.

Portado do desktop: kingban/services/pricing.py
"""

from app.models.product import Product


def resolve_price(product: Product, nf_type: str, quantity: int, shipping_origin: str) -> tuple:
    """
    Retorna (preco_unitario, desconto_unitario) baseado nas regras de negocio.

    Faixas de preco (da planilha Custos):
    1. NF INTEGRAL — preco cheio
    2. NF BAIXA 1-3 unidades — NF baixa pedidos pequenos
    3. NF BAIXA 4+ unidades — NF baixa pedidos medios
    4. NF CHEIA 4+ unidades — NF cheia pedidos medios
    5. NF INTEGRAL 10+ — volume grande NF integral
    6. NF BAIXA 10+ — volume grande NF baixa
    7. FABRICA 10+ — direto da fabrica volume grande
    """
    # 10+ unidades — faixas de volume
    if quantity >= 10:
        if shipping_origin == "FABRICA" and product.preco_fabrica_10 > 0:
            return (product.preco_fabrica_10, product.desconto_fabrica_10)
        elif nf_type == "NF INTEGRAL" and product.preco_nf_integral_10 > 0:
            return (product.preco_nf_integral_10, 0.0)
        elif nf_type in ("NF BAIXA", "NF CHEIA") and product.preco_nf_baixa_10 > 0:
            return (product.preco_nf_baixa_10, product.desconto_nf_baixa_10)

    # 4+ unidades — faixas medias
    if quantity >= 4:
        if nf_type == "NF BAIXA" and product.preco_nf_baixa_4 > 0:
            return (product.preco_nf_baixa_4, product.desconto_nf_baixa_4)
        elif nf_type == "NF CHEIA" and product.preco_nf_cheia_4 > 0:
            return (product.preco_nf_cheia_4, product.desconto_nf_cheia_4)

    # 1-3 unidades ou fallback
    if nf_type == "NF BAIXA" and product.preco_nf_baixa_1_3 > 0:
        return (product.preco_nf_baixa_1_3, product.desconto_nf_baixa_1_3)

    # Default: NF INTEGRAL
    return (product.preco_nf_integral, 0.0)


def calculate_line_total(unit_price: float, quantity: int) -> float:
    """Calcula total de um item."""
    return round(unit_price * quantity, 2)


def calculate_order_totals(items: list, freight: float = 0.0) -> dict:
    """
    Calcula totais do pedido a partir de uma lista de itens.
    Cada item deve ter: unit_price, quantity, discount, cost_per_unit
    """
    subtotal = 0.0
    total_discount = 0.0
    total_cost = 0.0

    for item in items:
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0)
        discount = item.get("discount", 0)
        cost = item.get("cost_per_unit", 0)

        subtotal += price * qty
        total_discount += discount * qty
        total_cost += cost * qty

    total = subtotal + freight
    profit = subtotal - total_cost

    return {
        "subtotal": round(subtotal, 2),
        "total_discount": round(total_discount, 2),
        "total_cost": round(total_cost, 2),
        "freight": round(freight, 2),
        "total": round(total, 2),
        "profit": round(profit, 2),
    }
