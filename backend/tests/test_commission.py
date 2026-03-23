"""Testes do motor de comissoes."""

import pytest
from app.services.commission import calculate_commission_line
from app.core.constants import TAX_RATE_NF, DEPOSITO_SURCHARGE


class TestCalculateCommissionLine:
    """Testes para calculate_commission_line — formula de comissao."""

    def test_produto_principal_deposito(self):
        """Produto principal saindo do deposito — 15%."""
        result = calculate_commission_line(
            unit_price=1000.0,
            quantity=2,
            nf_unit_value=800.0,
            shipping_origin="DEPOSITO",
            base_cost=300.0,
            commission_rate=0.15,
        )
        # custo_total_uni = 300 + 65 + 800*0.085 = 300 + 65 + 68 = 433
        expected_cost = 300 + DEPOSITO_SURCHARGE + (800 * TAX_RATE_NF)
        assert result["cost_total_unit"] == round(expected_cost, 2)

        # liquido_uni = 1000 - 433 = 567
        expected_liquid = 1000 - expected_cost
        assert result["liquid_per_unit"] == round(expected_liquid, 2)

        # liquido_total = 567 * 2 = 1134
        assert result["liquid_total"] == round(expected_liquid * 2, 2)

        # comissao = 1134 * 0.15 = 170.10
        assert result["commission_value"] == round(expected_liquid * 2 * 0.15, 2)
        assert result["commission_rate"] == 0.15

    def test_acessorio_fabrica(self):
        """Acessorio saindo da fabrica — 20%, sem sobretaxa deposito."""
        result = calculate_commission_line(
            unit_price=200.0,
            quantity=5,
            nf_unit_value=200.0,
            shipping_origin="FABRICA",
            base_cost=50.0,
            commission_rate=0.20,
        )
        # custo_total_uni = 50 + 0 + 200*0.085 = 50 + 17 = 67
        expected_cost = 50 + (200 * TAX_RATE_NF)
        assert result["cost_total_unit"] == round(expected_cost, 2)

        # Sem deposito surcharge
        assert DEPOSITO_SURCHARGE not in [50, expected_cost]

        # liquido_uni = 200 - 67 = 133
        expected_liquid = 200 - expected_cost
        assert result["liquid_per_unit"] == round(expected_liquid, 2)

        # comissao = 133 * 5 * 0.20
        expected_commission = expected_liquid * 5 * 0.20
        assert result["commission_value"] == round(expected_commission, 2)

    def test_totais_venda_e_nf(self):
        """Verifica totais de venda e NF."""
        result = calculate_commission_line(
            unit_price=500.0,
            quantity=3,
            nf_unit_value=500.0,
            shipping_origin="FABRICA",
            base_cost=100.0,
        )
        assert result["total_sale"] == 1500.0  # 500 * 3
        assert result["nf_total"] == 1500.0  # 500 * 3

    def test_nf_baixa_valor_diferente(self):
        """NF BAIXA — valor NF diferente do preco de venda."""
        result = calculate_commission_line(
            unit_price=1000.0,
            quantity=1,
            nf_unit_value=600.0,  # NF baixa
            shipping_origin="FABRICA",
            base_cost=300.0,
            commission_rate=0.15,
        )
        # custo_total_uni = 300 + 0 + 600*0.085 = 300 + 51 = 351
        expected_cost = 300 + (600 * TAX_RATE_NF)
        assert result["cost_total_unit"] == round(expected_cost, 2)

        # liquido melhor com NF baixa: 1000 - 351 = 649 (vs 1000 - 385 com NF cheia)
        assert result["liquid_per_unit"] > 600  # lucro alto

    def test_comissao_negativa(self):
        """Produto com custo maior que preco — comissao negativa."""
        result = calculate_commission_line(
            unit_price=100.0,
            quantity=1,
            nf_unit_value=100.0,
            shipping_origin="DEPOSITO",
            base_cost=200.0,
            commission_rate=0.15,
        )
        # custo = 200 + 65 + 8.5 = 273.5 > 100
        assert result["liquid_per_unit"] < 0
        assert result["commission_value"] < 0

    def test_quantidade_zero(self):
        """Quantidade zero resulta em totais zero."""
        result = calculate_commission_line(
            unit_price=1000.0,
            quantity=0,
            nf_unit_value=1000.0,
            shipping_origin="FABRICA",
            base_cost=300.0,
        )
        assert result["total_sale"] == 0
        assert result["liquid_total"] == 0
        assert result["commission_value"] == 0
