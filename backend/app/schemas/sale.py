"""Schemas para Vendas."""

from pydantic import BaseModel
from datetime import date, datetime


class VendaResponse(BaseModel):
    """Resposta de uma venda."""
    id: int
    data: date
    numero_pedido: int | None = None
    nome_cliente: str | None = None
    cnpj_cpf_cliente: str | None = None
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int = 0
    unidade: str = "UN"
    origem_frete: str | None = None
    preco_unitario: float = 0
    valor_total: float = 0
    desconto: float = 0
    custo_unitario: float = 0
    custo_total: float = 0
    valor_nf: float = 0
    imposto: float = 0
    lucro_total: float = 0
    forma_pagamento: str | None = None
    vendedor_id: int | None = None
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}


class ResumoVendas(BaseModel):
    """Resumo de vendas por periodo."""
    total_vendas: float = 0
    total_custos: float = 0
    total_impostos: float = 0
    total_lucro: float = 0
    quantidade_vendas: int = 0
