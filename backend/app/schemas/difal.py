"""Schemas Pydantic para DIFAL."""

from pydantic import BaseModel
from typing import Optional


class DifalCalculoRequest(BaseModel):
    """Requisicao de calculo DIFAL."""
    estado_destino: str  # UF: MG, RJ, etc.
    valor: float
    ncm: str = "94037000"  # NCM padrao banheiro quimico


class DifalCalculoResponse(BaseModel):
    """Resposta do calculo DIFAL."""
    estado: str
    valor_produto: float
    ncm: str
    aliq_interna: float
    aliq_inter: float
    fcp: float
    valor_difal: float
    valor_fcp: float
    valor_total: float
    formula_usada: str  # 'padrao' ou 'MG'


class EstadoResponse(BaseModel):
    """Estado disponivel para calculo DIFAL."""
    uf: str
    nome: str
    ncm: str
    aliq_interna: float
    aliq_inter: float
    fcp: float
    formula_especial: Optional[str] = None


class DifalRateCriar(BaseModel):
    """Criar/atualizar aliquota DIFAL."""
    uf: str
    nome_estado: Optional[str] = None
    ncm: str
    aliq_interna: float
    aliq_inter: float = 0.12
    fcp: float = 0.0
    formula_especial: Optional[str] = None
