"""Schemas para Clientes."""

from pydantic import BaseModel
from datetime import datetime


class ClienteBase(BaseModel):
    """Campos comuns de cliente."""
    nome: str
    cnpj_cpf: str | None = None
    ie: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None
    observacoes: str | None = None
    ativo: bool = True


class ClienteCriar(ClienteBase):
    """Schema para criar cliente."""
    pass


class ClienteAtualizar(BaseModel):
    """Schema para atualizar cliente (todos opcionais)."""
    nome: str | None = None
    cnpj_cpf: str | None = None
    ie: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None
    telefone: str | None = None
    email: str | None = None
    contato: str | None = None
    observacoes: str | None = None
    ativo: bool | None = None


class ClienteResponse(ClienteBase):
    """Schema de resposta do cliente."""
    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
