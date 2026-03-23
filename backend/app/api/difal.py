"""API DIFAL — calculadora interativa + gestao de aliquotas."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_action
from app.models.difal_rate import DifalRate
from app.models.user import User
from app.schemas.difal import DifalCalculoRequest, DifalCalculoResponse, DifalRateCriar
from app.services.difal import calculate_difal, load_difal_rates, get_all_states

router = APIRouter()


@router.post("/calcular", response_model=DifalCalculoResponse)
async def calcular_difal(
    dados: DifalCalculoRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Calcula DIFAL para um valor, estado e NCM."""
    rates = await load_difal_rates(db, user.tenant_id)
    key = (dados.estado_destino.upper(), dados.ncm)

    if key not in rates:
        raise HTTPException(404, f"Aliquota nao encontrada para {dados.estado_destino} / NCM {dados.ncm}")

    rate_info = rates[key]
    result = calculate_difal(
        value=dados.valor,
        state_code=dados.estado_destino.upper(),
        ncm=dados.ncm,
        rate_info=rate_info,
    )

    return {
        "estado": dados.estado_destino.upper(),
        "valor_produto": dados.valor,
        "ncm": dados.ncm,
        "aliq_interna": rate_info["aliq_interna"],
        "aliq_inter": rate_info["aliq_inter"],
        "fcp": rate_info["fcp"],
        "valor_difal": result["valor_difal"],
        "valor_fcp": result["valor_fcp"],
        "valor_total": result["valor_total"],
        "formula_usada": result["formula_usada"],
    }


@router.get("/estados")
async def listar_estados(
    ncm: str = Query("94037000", description="Filtrar por NCM"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista estados com aliquotas cadastradas."""
    states = await get_all_states(db, user.tenant_id)
    if ncm:
        states = [s for s in states if s["ncm"] == ncm]
    return states


@router.post("/aliquotas")
async def criar_aliquota(
    dados: DifalRateCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cria ou atualiza aliquota DIFAL para um estado/NCM."""
    tenant_id = user.tenant_id
    uf = dados.uf.upper()

    # Verifica se ja existe
    result = await db.execute(
        select(DifalRate).where(
            DifalRate.tenant_id == tenant_id,
            DifalRate.state_code == uf,
            DifalRate.ncm == dados.ncm,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.aliq_interna = dados.aliq_interna
        existing.aliq_inter = dados.aliq_inter
        existing.fcp = dados.fcp
        existing.formula_especial = dados.formula_especial
        if dados.nome_estado:
            existing.state_name = dados.nome_estado
        await db.flush()
        await log_action(db, user.id, tenant_id, "difal_rates", existing.id, "UPDATE")
        rate = existing
    else:
        rate = DifalRate(
            tenant_id=tenant_id,
            state_code=uf,
            state_name=dados.nome_estado,
            ncm=dados.ncm,
            aliq_interna=dados.aliq_interna,
            aliq_inter=dados.aliq_inter,
            fcp=dados.fcp,
            formula_especial=dados.formula_especial,
        )
        db.add(rate)
        await db.flush()
        await log_action(db, user.id, tenant_id, "difal_rates", rate.id, "CREATE")

    return {
        "id": rate.id,
        "uf": rate.state_code,
        "nome": rate.state_name,
        "ncm": rate.ncm,
        "aliq_interna": rate.aliq_interna,
        "aliq_inter": rate.aliq_inter,
        "fcp": rate.fcp,
        "formula_especial": rate.formula_especial,
    }


@router.delete("/aliquotas/{aliquota_id}")
async def excluir_aliquota(
    aliquota_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Exclui aliquota DIFAL."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(DifalRate).where(DifalRate.id == aliquota_id, DifalRate.tenant_id == tenant_id)
    )
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(404, "Aliquota nao encontrada")

    await db.delete(rate)
    await log_action(db, user.id, tenant_id, "difal_rates", aliquota_id, "DELETE")
    return {"message": "Aliquota excluida com sucesso"}
