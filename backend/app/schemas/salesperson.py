"""Schemas para Vendedores."""

from pydantic import BaseModel
from datetime import datetime


class VendedorBase(BaseModel):
    nome: str
    telefone: str | None = None
    email: str | None = None
    salario_fixo: float = 1500.0
    ativo: bool = True


class VendedorCriar(VendedorBase):
    pass


class VendedorAtualizar(BaseModel):
    nome: str | None = None
    telefone: str | None = None
    email: str | None = None
    salario_fixo: float | None = None
    ativo: bool | None = None


class VendedorResponse(VendedorBase):
    id: int
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    model_config = {"from_attributes": True}
