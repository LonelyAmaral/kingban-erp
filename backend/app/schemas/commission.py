"""Schemas Pydantic para comissoes."""

from pydantic import BaseModel
from datetime import date
from typing import Optional


class RelatorioComissaoRequest(BaseModel):
    """Requisicao para gerar relatorio de comissao."""
    vendedor_id: int
    data_inicio: date
    data_fim: date
    gratificacao: float = 0.0
    adiantamentos: float = 0.0
    outras_comissoes: float = 0.0


class LinhaComissao(BaseModel):
    """Linha individual do relatorio de comissao."""
    venda_id: int
    data: str
    codigo_produto: str
    nome_produto: str
    quantidade: int
    preco_unitario: float
    total_venda: float
    valor_nf_unitario: float
    total_nf: float
    nome_cliente: str
    origem_envio: str
    custo_total_unitario: float
    liquido_unitario: float
    liquido_total: float
    taxa_comissao: float
    valor_comissao: float


class RelatorioComissaoResponse(BaseModel):
    """Resposta do relatorio de comissao."""
    vendedor_id: int
    nome_vendedor: str
    data_inicio: str
    data_fim: str
    total_vendas: float
    total_nf: float
    total_liquido: float
    total_comissao: float
    outras_comissoes: float
    salario_fixo: float
    gratificacao: float
    adiantamentos: float
    bruto_total: float
    saldo: float
    itens: list[LinhaComissao]


class CustoComissaoCriar(BaseModel):
    """Criar/atualizar custo de comissao de um produto."""
    produto_id: int
    codigo_produto: Optional[str] = None
    nome_produto: Optional[str] = None
    custo_base: float
    taxa_comissao: float = 0.15


class CustoComissaoResponse(BaseModel):
    """Resposta de custo de comissao."""
    id: int
    produto_id: int
    codigo_produto: Optional[str] = None
    nome_produto: Optional[str] = None
    custo_base: float
    taxa_comissao: float

    model_config = {"from_attributes": True}
