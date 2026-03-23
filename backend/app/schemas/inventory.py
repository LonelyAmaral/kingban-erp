"""Schemas para Estoque."""

from pydantic import BaseModel
from datetime import date, datetime


class EstoqueAtual(BaseModel):
    """Saldo atual de estoque."""
    codigo: str
    nome: str
    categoria: str | None = None
    quantidade_atual: int = 0
    preco_unitario: float = 0
    valor_total: float = 0
    quantidade_minima: int = 0
    ultima_entrada: date | None = None
    ultima_saida: date | None = None


class EntradaCriar(BaseModel):
    """Dados para criar entrada de estoque."""
    produto_id: int
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int
    tipo_entrada: str
    fornecedor_id: int | None = None
    data: date | None = None
    observacoes: str = ""


class EntradaResponse(BaseModel):
    id: int
    data: date
    produto_id: int
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int
    tipo_entrada: str
    fornecedor_id: int | None = None
    observacoes: str | None = None
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}


class SaidaCriar(BaseModel):
    """Dados para criar saida de estoque."""
    produto_id: int
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int
    tipo_saida: str
    nome_cliente: str = ""
    data: date | None = None
    observacoes: str = ""


class SaidaResponse(BaseModel):
    id: int
    data: date
    produto_id: int
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int
    nome_cliente: str | None = None
    tipo_saida: str
    venda_id: int | None = None
    observacoes: str | None = None
    criado_em: datetime | None = None

    model_config = {"from_attributes": True}
