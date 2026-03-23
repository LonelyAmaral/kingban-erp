"""Testes do motor DIFAL."""

import pytest
from app.services.difal import calculate_difal, should_apply_difal


class TestShouldApplyDifal:
    def test_sp_nao_aplica(self):
        assert should_apply_difal("SP") is False

    def test_outros_estados_aplica(self):
        assert should_apply_difal("MG") is True
        assert should_apply_difal("RJ") is True
        assert should_apply_difal("BA") is True


class TestCalculateDifal:
    """Testes para calculate_difal — formulas padrao e MG."""

    def test_venda_sp_isenta(self):
        """Venda dentro de SP — DIFAL zero."""
        result = calculate_difal(
            value=1000.0,
            state_code="SP",
            ncm="94037000",
            rate_info={"aliq_interna": 0.18, "aliq_inter": 0.12, "fcp": 0},
        )
        assert result["valor_difal"] == 0
        assert result["valor_fcp"] == 0
        assert result["valor_total"] == 0
        assert result["formula_usada"] == "isento_sp"

    def test_formula_padrao_rj(self):
        """Formula padrao para RJ — NCM 94037000."""
        # RJ: aliq_interna=0.20, aliq_inter=0.12, fcp=0.02
        rate = {"aliq_interna": 0.20, "aliq_inter": 0.12, "fcp": 0.02}
        result = calculate_difal(
            value=1000.0,
            state_code="RJ",
            ncm="94037000",
            rate_info=rate,
        )
        # base = 1000 / (1 - (0.20 + 0.02)) = 1000 / 0.78 = 1282.05
        # diferencial = 0.20 - 0.12 + 0.02 = 0.10
        # difal_total = 1282.05 * 0.10 = 128.21
        # difal_fcp = 1282.05 * 0.02 = 25.64
        # difal_value = 128.21 - 25.64 = 102.56
        assert result["formula_usada"] == "padrao"
        assert result["valor_total"] > 0
        assert result["valor_fcp"] > 0
        assert result["valor_difal"] > 0
        # difal_total = difal + fcp
        assert abs(result["valor_total"] - (result["valor_difal"] + result["valor_fcp"])) < 0.02

    def test_formula_mg_especial(self):
        """Formula especial MG: (valor * 1/3) * diferencial."""
        # MG: aliq_interna=0.18, aliq_inter=0.12, fcp=0.02, formula_especial='MG'
        rate = {"aliq_interna": 0.18, "aliq_inter": 0.12, "fcp": 0.02, "formula_especial": "MG"}
        result = calculate_difal(
            value=3000.0,
            state_code="MG",
            ncm="94037000",
            rate_info=rate,
        )
        # base = 3000 * (1/3) = 1000
        # diferencial = 0.18 - 0.12 + 0.02 = 0.08
        # difal_total = 1000 * 0.08 = 80
        # difal_fcp = 1000 * 0.02 = 20
        # difal_value = 80 - 20 = 60
        assert result["formula_usada"] == "MG"
        assert result["valor_total"] == 80.0
        assert result["valor_fcp"] == 20.0
        assert result["valor_difal"] == 60.0

    def test_sem_fcp(self):
        """Estado sem FCP — valor_fcp deve ser zero."""
        rate = {"aliq_interna": 0.17, "aliq_inter": 0.12, "fcp": 0}
        result = calculate_difal(
            value=1000.0,
            state_code="PR",
            ncm="94037000",
            rate_info=rate,
        )
        assert result["valor_fcp"] == 0
        assert result["valor_total"] == result["valor_difal"]

    def test_valor_zero(self):
        """Valor zero — DIFAL zero."""
        rate = {"aliq_interna": 0.18, "aliq_inter": 0.12, "fcp": 0.02}
        result = calculate_difal(
            value=0.0,
            state_code="RJ",
            ncm="94037000",
            rate_info=rate,
        )
        assert result["valor_difal"] == 0
        assert result["valor_total"] == 0

    def test_ncm_diferente(self):
        """NCM 94069090 com aliquotas diferentes."""
        rate = {"aliq_interna": 0.19, "aliq_inter": 0.12, "fcp": 0.01}
        result = calculate_difal(
            value=500.0,
            state_code="BA",
            ncm="94069090",
            rate_info=rate,
        )
        assert result["formula_usada"] == "padrao"
        assert result["valor_total"] > 0
