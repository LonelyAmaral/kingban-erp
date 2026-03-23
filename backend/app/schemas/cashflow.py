"""Schemas Pydantic para fluxo de caixa."""

from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class LancamentoCriar(BaseModel):
    """Criar lancamento de fluxo de caixa."""
    data: date
    tipo: str  # ENTRADA ou SAIDA
    categoria: str  # Venda, Compra, Despesa, Aporte, Retirada, etc.
    descricao: Optional[str] = None
    valor: float
    conta_id: Optional[int] = None
    pedido_id: Optional[int] = None
    observacoes: Optional[str] = None


class LancamentoResponse(BaseModel):
    """Resposta de lancamento."""
    id: int
    data: date
    tipo: str
    categoria: str
    descricao: Optional[str] = None
    valor: float
    conta_id: Optional[int] = None
    pedido_id: Optional[int] = None
    auto_gerado: str
    observacoes: Optional[str] = None
    criado_em: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ResumoFluxoCaixa(BaseModel):
    """Resumo do fluxo de caixa por periodo."""
    total_entradas: float
    total_saidas: float
    saldo_periodo: float
    saldo_acumulado: float
    quantidade_lancamentos: int
