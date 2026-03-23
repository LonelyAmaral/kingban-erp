"""Modelo de Fornecedor."""

from sqlalchemy import Column, String, Text, Boolean
from app.models.base import TenantModel


class Supplier(TenantModel):
    __tablename__ = "suppliers"

    nome = Column(String(300), nullable=False, index=True)
    cnpj = Column(String(20), index=True)
    ie = Column(String(20))
    endereco = Column(Text)
    cidade = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(30))
    email = Column(String(200))
    contato = Column(String(200))
    categoria = Column(String(100))
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
