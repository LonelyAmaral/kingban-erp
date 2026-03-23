"""Schemas para Produtos."""

from pydantic import BaseModel
from datetime import datetime


class ProdutoBase(BaseModel):
    """Campos comuns de produto."""
    codigo: str
    nome: str
    categoria: str | None = None
    unidade: str = "UN"
    ncm: str | None = None

    # Custos
    custo: float = 0
    frete: float = 0

    # 6 faixas de preco
    preco_nf_integral: float = 0
    preco_nf_baixa_1_3: float = 0
    desconto_nf_baixa_1_3: float = 0
    preco_nf_baixa_4: float = 0
    desconto_nf_baixa_4: float = 0
    preco_nf_cheia_4: float = 0
    desconto_nf_cheia_4: float = 0
    preco_nf_integral_10: float = 0
    preco_nf_baixa_10: float = 0
    desconto_nf_baixa_10: float = 0
    preco_fabrica_10: float = 0
    desconto_fabrica_10: float = 0

    # Comissao
    taxa_comissao: float = 0.15

    ativo: bool = True


class ProdutoCriar(ProdutoBase):
    pass


class ProdutoAtualizar(BaseModel):
    codigo: str | None = None
    nome: str | None = None
    categoria: str | None = None
    unidade: str | None = None
    ncm: str | None = None
    custo: float | None = None
    frete: float | None = None
    preco_nf_integral: float | None = None
    preco_nf_baixa_1_3: float | None = None
    desconto_nf_baixa_1_3: float | None = None
    preco_nf_baixa_4: float | None = None
    desconto_nf_baixa_4: float | None = None
    preco_nf_cheia_4: float | None = None
    desconto_nf_cheia_4: float | None = None
    preco_nf_integral_10: float | None = None
    preco_nf_baixa_10: float | None = None
    desconto_nf_baixa_10: float | None = None
    preco_fabrica_10: float | None = None
    desconto_fabrica_10: float | None = None
    taxa_comissao: float | None = None
    ativo: bool | None = None


class ProdutoResponse(ProdutoBase):
    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
