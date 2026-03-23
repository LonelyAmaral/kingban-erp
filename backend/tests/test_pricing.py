"""Testes do motor de precos."""

import pytest
from unittest.mock import MagicMock
from app.services.pricing import resolve_price, calculate_line_total, calculate_order_totals


def _make_product(**kwargs):
    """Cria mock de Product com valores padrao."""
    p = MagicMock()
    p.preco_nf_integral = kwargs.get("preco_nf_integral", 1000.0)
    p.preco_nf_baixa_1_3 = kwargs.get("preco_nf_baixa_1_3", 900.0)
    p.preco_nf_baixa_4 = kwargs.get("preco_nf_baixa_4", 850.0)
    p.desconto_nf_baixa_4 = kwargs.get("desconto_nf_baixa_4", 50.0)
    p.preco_nf_cheia_4 = kwargs.get("preco_nf_cheia_4", 880.0)
    p.desconto_nf_cheia_4 = kwargs.get("desconto_nf_cheia_4", 30.0)
    p.preco_nf_integral_10 = kwargs.get("preco_nf_integral_10", 800.0)
    p.preco_nf_baixa_10 = kwargs.get("preco_nf_baixa_10", 750.0)
    p.desconto_nf_baixa_10 = kwargs.get("desconto_nf_baixa_10", 100.0)
    p.preco_fabrica_10 = kwargs.get("preco_fabrica_10", 700.0)
    p.desconto_fabrica_10 = kwargs.get("desconto_fabrica_10", 150.0)
    p.desconto_nf_baixa_1_3 = kwargs.get("desconto_nf_baixa_1_3", 40.0)
    return p


class TestResolvePrice:
    """Testes para resolve_price — 6 faixas de preco."""

    def test_nf_integral_default(self):
        """NF INTEGRAL retorna preco cheio."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF INTEGRAL", 1, "DEPOSITO")
        assert preco == 1000.0
        assert desc == 0.0

    def test_nf_baixa_1_3_unidades(self):
        """NF BAIXA com 1-3 unidades."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF BAIXA", 2, "DEPOSITO")
        assert preco == 900.0

    def test_nf_baixa_4_mais(self):
        """NF BAIXA com 4+ unidades."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF BAIXA", 5, "DEPOSITO")
        assert preco == 850.0
        assert desc == 50.0

    def test_nf_cheia_4_mais(self):
        """NF CHEIA com 4+ unidades."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF CHEIA", 6, "DEPOSITO")
        assert preco == 880.0
        assert desc == 30.0

    def test_nf_integral_10_mais(self):
        """NF INTEGRAL com 10+ unidades — volume."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF INTEGRAL", 12, "DEPOSITO")
        assert preco == 800.0

    def test_nf_baixa_10_mais(self):
        """NF BAIXA com 10+ unidades — volume."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF BAIXA", 15, "DEPOSITO")
        assert preco == 750.0
        assert desc == 100.0

    def test_fabrica_10_mais(self):
        """FABRICA com 10+ unidades."""
        p = _make_product()
        preco, desc = resolve_price(p, "NF BAIXA", 10, "FABRICA")
        assert preco == 700.0
        assert desc == 150.0

    def test_fallback_nf_integral_sem_preco(self):
        """Sem preco cadastrado, volta para NF INTEGRAL."""
        p = _make_product(preco_nf_baixa_1_3=0)
        preco, desc = resolve_price(p, "NF BAIXA", 1, "DEPOSITO")
        assert preco == 1000.0
        assert desc == 0.0

    def test_fabrica_sem_preco_cai_para_nf_baixa(self):
        """FABRICA sem preco 10+ cai para NF BAIXA 10+."""
        p = _make_product(preco_fabrica_10=0)
        preco, desc = resolve_price(p, "NF BAIXA", 10, "FABRICA")
        assert preco == 750.0


class TestCalculateLineTotal:
    def test_calculo_simples(self):
        assert calculate_line_total(100.0, 5) == 500.0

    def test_arredondamento(self):
        assert calculate_line_total(33.33, 3) == 99.99

    def test_zero(self):
        assert calculate_line_total(0.0, 10) == 0.0


class TestCalculateOrderTotals:
    def test_pedido_simples(self):
        items = [
            {"unit_price": 1000, "quantity": 2, "discount": 0, "cost_per_unit": 300},
            {"unit_price": 500, "quantity": 3, "discount": 50, "cost_per_unit": 150},
        ]
        result = calculate_order_totals(items, freight=200.0)
        assert result["subtotal"] == 3500.0  # 2000 + 1500
        assert result["total_discount"] == 150.0  # 0 + 150
        assert result["total_cost"] == 1050.0  # 600 + 450
        assert result["freight"] == 200.0
        assert result["total"] == 3700.0  # 3500 + 200
        assert result["profit"] == 2450.0  # 3500 - 1050

    def test_pedido_vazio(self):
        result = calculate_order_totals([])
        assert result["subtotal"] == 0
        assert result["total"] == 0
