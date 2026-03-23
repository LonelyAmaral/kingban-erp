"""Modelo de Produto com 6 faixas de preco."""

from sqlalchemy import Column, String, Text, Boolean, Float
from app.models.base import TenantModel


class Product(TenantModel):
    __tablename__ = "products"

    codigo = Column(String(20), nullable=False, index=True)
    nome = Column(String(300), nullable=False, index=True)
    categoria = Column(String(100))
    unidade = Column(String(10), default="UN")
    ncm = Column(String(20))

    # Custos
    custo = Column(Float, default=0)
    frete = Column(Float, default=0)

    # 6 faixas de preco
    preco_nf_integral = Column(Float, default=0)
    preco_nf_baixa_1_3 = Column(Float, default=0)
    desconto_nf_baixa_1_3 = Column(Float, default=0)
    preco_nf_baixa_4 = Column(Float, default=0)
    desconto_nf_baixa_4 = Column(Float, default=0)
    preco_nf_cheia_4 = Column(Float, default=0)
    desconto_nf_cheia_4 = Column(Float, default=0)
    preco_nf_integral_10 = Column(Float, default=0)
    preco_nf_baixa_10 = Column(Float, default=0)
    desconto_nf_baixa_10 = Column(Float, default=0)
    preco_fabrica_10 = Column(Float, default=0)
    desconto_fabrica_10 = Column(Float, default=0)

    # Comissao
    taxa_comissao = Column(Float, default=0.15)

    # Foto / Ficha tecnica
    foto_path = Column(Text)
    ficha_tecnica = Column(Text)

    ativo = Column(Boolean, default=True)
