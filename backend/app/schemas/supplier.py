"""Schemas para Fornecedores."""

from pydantic import BaseModel
from datetime import datetime


class FornecedorBase(BaseModel):
    """Campos comuns de fornecedor."""
    nome: str
    cnpj: str | None = None
    ie: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None
    categoria: str | None = None
    observacoes: str | None = None
    ativo: bool = True


class FornecedorCriar(FornecedorBase):
    pass


class FornecedorAtualizar(BaseModel):
    nome: str | None = None
    cnpj: str | None = None
    ie: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None
    categoria: str | None = None
    observacoes: str | None = None
    ativo: bool | None = None


class FornecedorResponse(FornecedorBase):
    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
