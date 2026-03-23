"""Schemas base para paginacao e respostas padrao."""

from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")


class PaginacaoParams(BaseModel):
    """Parametros de paginacao padrao."""
    pagina: int = 1
    por_pagina: int = 50
    busca: str | None = None
    ordenar: str | None = None
    direcao: str = "asc"  # asc ou desc


class PaginacaoResponse(BaseModel, Generic[T]):
    """Resposta paginada padrao."""
    itens: List[T]
    total: int
    pagina: int
    paginas: int


class MensagemResponse(BaseModel):
    """Resposta simples com mensagem."""
    mensagem: str
