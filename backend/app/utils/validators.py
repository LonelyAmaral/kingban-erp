"""Validadores de documentos brasileiros — CNPJ e CPF."""

import re


def _only_digits(value: str) -> str:
    """Remove tudo exceto digitos."""
    return re.sub(r"[^\d]", "", value)


def validate_cpf(cpf: str) -> bool:
    """
    Valida CPF brasileiro (11 digitos + 2 verificadores).

    Aceita com ou sem formatacao (123.456.789-09 ou 12345678909).
    """
    cpf = _only_digits(cpf)
    if len(cpf) != 11:
        return False

    # CPFs invalidos conhecidos (todos iguais)
    if cpf == cpf[0] * 11:
        return False

    # Primeiro digito verificador
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if int(cpf[9]) != d1:
        return False

    # Segundo digito verificador
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    if int(cpf[10]) != d2:
        return False

    return True


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ brasileiro (14 digitos + 2 verificadores).

    Aceita com ou sem formatacao (12.345.678/0001-90 ou 12345678000190).
    """
    cnpj = _only_digits(cnpj)
    if len(cnpj) != 14:
        return False

    # CNPJs invalidos (todos iguais)
    if cnpj == cnpj[0] * 14:
        return False

    # Primeiro digito verificador
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    d1 = 0 if resto < 2 else 11 - resto
    if int(cnpj[12]) != d1:
        return False

    # Segundo digito verificador
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    d2 = 0 if resto < 2 else 11 - resto
    if int(cnpj[13]) != d2:
        return False

    return True


def validate_document(doc: str) -> tuple[bool, str]:
    """
    Valida CPF ou CNPJ automaticamente.

    Returns:
        (valido, tipo) — tipo e 'CPF', 'CNPJ' ou 'INVALIDO'
    """
    digits = _only_digits(doc)
    if len(digits) == 11:
        return validate_cpf(digits), "CPF"
    elif len(digits) == 14:
        return validate_cnpj(digits), "CNPJ"
    return False, "INVALIDO"


def format_cpf(cpf: str) -> str:
    """Formata CPF: 123.456.789-09"""
    d = _only_digits(cpf)
    if len(d) != 11:
        return cpf
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ: 12.345.678/0001-90"""
    d = _only_digits(cnpj)
    if len(d) != 14:
        return cnpj
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"
