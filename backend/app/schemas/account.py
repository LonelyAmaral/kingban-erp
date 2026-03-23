"""Schemas Pydantic para contas a receber/pagar."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class ContaCriar(BaseModel):
    """Criar conta a receber ou a pagar."""
    tipo: str  # RECEIVABLE ou PAYABLE
    descricao: str
    pedido_id: Optional[int] = None
    compra_id: Optional[int] = None
    cliente_ou_fornecedor: Optional[str] = None
    vencimento: date
    valor: float
    observacoes: Optional[str] = None


class ContaAtualizar(BaseModel):
    """Atualizar conta existente."""
    descricao: Optional[str] = None
    cliente_ou_fornecedor: Optional[str] = None
    vencimento: Optional[date] = None
    valor: Optional[float] = None
    observacoes: Optional[str] = None


class PagamentoConta(BaseModel):
    """Registrar pagamento (parcial ou total)."""
    valor_pago: float
    data_pagamento: Optional[date] = None


class ContaResponse(BaseModel):
    """Resposta de conta."""
    id: int
    tipo: str
    descricao: Optional[str] = None
    pedido_id: Optional[int] = None
    compra_id: Optional[int] = None
    cliente_ou_fornecedor: Optional[str] = None
    vencimento: Optional[date] = None
    valor: float
    valor_pago: float
    status: str
    data_pagamento: Optional[date] = None
    observacoes: Optional[str] = None
    criado_em: Optional[datetime] = None

    model_config = {"from_attributes": True}
