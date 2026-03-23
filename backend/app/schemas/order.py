"""Schemas para Orcamentos/Pedidos."""

from pydantic import BaseModel
from datetime import datetime
from typing import List


class ItemPedidoBase(BaseModel):
    """Campos de um item do pedido."""
    ordem: int = 0
    produto_id: int | None = None
    codigo_produto: str | None = None
    nome_produto: str | None = None
    quantidade: int = 1
    unidade: str = "UN"
    preco_unitario: float = 0
    desconto: float = 0
    total: float = 0
    custo_unitario: float = 0
    custo_total: float = 0
    valor_nf_unitario: float = 0


class ItemPedidoCriar(ItemPedidoBase):
    pass


class ItemPedidoResponse(ItemPedidoBase):
    id: int
    order_id: int
    model_config = {"from_attributes": True}


class PedidoBase(BaseModel):
    """Campos comuns de pedido."""
    numero: int | None = None
    tipo_documento: str = "ORCAMENTO"
    status: str = "ORCAMENTO"

    empresa_id: int | None = None
    cliente_id: int | None = None
    vendedor_id: int | None = None

    tipo_nf: str | None = None
    origem_frete: str | None = None
    forma_pagamento: str | None = None
    condicao_pagamento: str | None = None
    disponibilidade: str | None = None
    observacoes: str | None = None

    subtotal: float = 0
    valor_frete: float = 0
    desconto_total: float = 0
    total: float = 0
    custo_total: float = 0
    valor_nf: float = 0
    valor_difal: float = 0
    lucro: float = 0


class PedidoCriar(PedidoBase):
    itens: List[ItemPedidoCriar] = []


class PedidoAtualizar(BaseModel):
    numero: int | None = None
    tipo_documento: str | None = None
    empresa_id: int | None = None
    cliente_id: int | None = None
    vendedor_id: int | None = None
    tipo_nf: str | None = None
    origem_frete: str | None = None
    forma_pagamento: str | None = None
    condicao_pagamento: str | None = None
    disponibilidade: str | None = None
    observacoes: str | None = None
    subtotal: float | None = None
    valor_frete: float | None = None
    desconto_total: float | None = None
    total: float | None = None
    custo_total: float | None = None
    valor_nf: float | None = None
    valor_difal: float | None = None
    lucro: float | None = None
    itens: List[ItemPedidoCriar] | None = None


class MudarStatus(BaseModel):
    """Schema para mudar status do pedido."""
    novo_status: str


class PedidoResponse(PedidoBase):
    id: int
    itens: List[ItemPedidoResponse] = []
    nome_cliente: str | None = None
    nome_vendedor: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None
    status_alterado_em: datetime | None = None

    model_config = {"from_attributes": True}
