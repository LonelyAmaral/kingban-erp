"""Testes de validacao CNPJ/CPF."""

import pytest
from app.utils.validators import validate_cpf, validate_cnpj, validate_document, format_cpf, format_cnpj


class TestValidateCPF:
    def test_cpf_valido(self):
        assert validate_cpf("529.982.247-25") is True

    def test_cpf_valido_sem_formatacao(self):
        assert validate_cpf("52998224725") is True

    def test_cpf_invalido(self):
        assert validate_cpf("123.456.789-00") is False

    def test_cpf_todos_iguais(self):
        assert validate_cpf("111.111.111-11") is False
        assert validate_cpf("00000000000") is False

    def test_cpf_tamanho_errado(self):
        assert validate_cpf("123456") is False
        assert validate_cpf("") is False


class TestValidateCNPJ:
    def test_cnpj_kingban(self):
        """CNPJ da KING BAN: 96.453.840/0001-89"""
        assert validate_cnpj("96.453.840/0001-89") is True

    def test_cnpj_valido_sem_formatacao(self):
        assert validate_cnpj("96453840000189") is True

    def test_cnpj_invalido(self):
        assert validate_cnpj("12.345.678/0001-00") is False

    def test_cnpj_todos_iguais(self):
        assert validate_cnpj("11111111111111") is False

    def test_cnpj_tamanho_errado(self):
        assert validate_cnpj("123456") is False


class TestValidateDocument:
    def test_auto_detecta_cpf(self):
        valido, tipo = validate_document("52998224725")
        assert tipo == "CPF"
        assert valido is True

    def test_auto_detecta_cnpj(self):
        valido, tipo = validate_document("96453840000189")
        assert tipo == "CNPJ"
        assert valido is True

    def test_tamanho_invalido(self):
        valido, tipo = validate_document("12345")
        assert tipo == "INVALIDO"
        assert valido is False


class TestFormatacao:
    def test_format_cpf(self):
        assert format_cpf("52998224725") == "529.982.247-25"

    def test_format_cnpj(self):
        assert format_cnpj("96453840000189") == "96.453.840/0001-89"
