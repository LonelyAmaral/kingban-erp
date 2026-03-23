"""Schemas Pydantic para compras."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class ItemCompraCriar(BaseModel):
    """Item de compra."""
    produto_id: Optional[int] = None
    codigo_produto: Optional[str] = None
    nome_produto: str
    quantidade: int = 1
    preco_unitario: float = 0


class ItemCompraResponse(BaseModel):
    """Resposta de item de compra."""
    id: int
    produto_id: Optional[int] = None
    codigo_produto: Optional[str] = None
    nome_produto: str
    quantidade: int
    preco_unitario: float
    total: float

    model_config = {"from_attributes": True}


class CompraCriar(BaseModel):
    """Criar compra."""
    data: date
    fornecedor_id: Optional[int] = None
    nome_fornecedor: Optional[str] = None
    frete: float = 0
    desconto: float = 0
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    itens: list[ItemCompraCriar]


class CompraAtualizar(BaseModel):
    """Atualizar compra."""
    data: Optional[date] = None
    nome_fornecedor: Optional[str] = None
    frete: Optional[float] = None
    desconto: Optional[float] = None
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None


class CompraResponse(BaseModel):
    """Resposta de compra."""
    id: int
    numero: Optional[int] = None
    data: date
    fornecedor_id: Optional[int] = None
    nome_fornecedor: Optional[str] = None
    status: str
    subtotal: float
    frete: float
    desconto: float
    total: float
    forma_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    itens: list[ItemCompraResponse] = []
    criado_em: Optional[datetime] = None

    model_config = {"from_attributes": True}
