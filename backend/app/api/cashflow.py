"""API de Fluxo de Caixa — lancamentos manuais e automaticos."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.audit import log_action
from app.models.cashflow import CashFlowEntry
from app.models.user import User
from app.schemas.cashflow import LancamentoCriar, LancamentoResponse, ResumoFluxoCaixa
from app.services.cashflow_service import create_entry, get_summary

router = APIRouter()

# Categorias validas
CATEGORIAS_ENTRADA = ["Venda", "Recebimento", "Aporte", "Outros"]
CATEGORIAS_SAIDA = ["Compra", "Pagamento", "Despesa", "Retirada", "Outros"]


def _entry_to_response(e: CashFlowEntry) -> dict:
    """Converte model CashFlowEntry para dict de resposta PT."""
    return {
        "id": e.id,
        "data": e.date,
        "tipo": e.type,
        "categoria": e.category,
        "descricao": e.description,
        "valor": e.amount,
        "conta_id": e.related_account_id,
        "pedido_id": e.related_order_id,
        "auto_gerado": e.auto_generated or "NAO",
        "observacoes": e.notes,
        "criado_em": e.criado_em,
    }


@router.get("")
async def listar_lancamentos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    tipo: str = Query(None, description="ENTRADA ou SAIDA"),
    categoria: str = Query(None),
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista lancamentos de fluxo de caixa com filtros."""
    tenant_id = user.tenant_id
    query = select(CashFlowEntry).where(CashFlowEntry.tenant_id == tenant_id)

    if tipo:
        query = query.where(CashFlowEntry.type == tipo)
    if categoria:
        query = query.where(CashFlowEntry.category == categoria)
    if data_inicio:
        query = query.where(CashFlowEntry.date >= date.fromisoformat(data_inicio))
    if data_fim:
        query = query.where(CashFlowEntry.date <= date.fromisoformat(data_fim))

    # Contagem
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginacao
    query = query.order_by(CashFlowEntry.date.desc(), CashFlowEntry.id.desc())
    query = query.offset((pagina - 1) * por_pagina).limit(por_pagina)
    result = await db.execute(query)
    lancamentos = result.scalars().all()

    return {
        "itens": [_entry_to_response(e) for e in lancamentos],
        "total": total,
        "pagina": pagina,
        "paginas": (total + por_pagina - 1) // por_pagina if total > 0 else 1,
    }


@router.get("/resumo", response_model=ResumoFluxoCaixa)
async def resumo_fluxo(
    data_inicio: str = Query(None),
    data_fim: str = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retorna resumo do fluxo de caixa no periodo."""
    start = date.fromisoformat(data_inicio) if data_inicio else None
    end = date.fromisoformat(data_fim) if data_fim else None
    return await get_summary(db, user.tenant_id, start, end)


@router.post("")
async def criar_lancamento(
    dados: LancamentoCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Cria lancamento manual de fluxo de caixa."""
    if dados.tipo not in ("ENTRADA", "SAIDA"):
        raise HTTPException(400, "Tipo deve ser ENTRADA ou SAIDA")

    tenant_id = user.tenant_id
    entry = await create_entry(
        db=db,
        tenant_id=tenant_id,
        entry_date=dados.data,
        entry_type=dados.tipo,
        category=dados.categoria,
        amount=dados.valor,
        description=dados.descricao or "",
        account_id=dados.conta_id,
        order_id=dados.pedido_id,
        auto_generated=False,
        notes=dados.observacoes or "",
    )
    await log_action(db, user.id, tenant_id, "cashflow_entries", entry.id, "CREATE")
    return _entry_to_response(entry)


@router.delete("/{lancamento_id}")
async def excluir_lancamento(
    lancamento_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Exclui lancamento manual (nao permite excluir automaticos)."""
    tenant_id = user.tenant_id
    result = await db.execute(
        select(CashFlowEntry).where(
            CashFlowEntry.id == lancamento_id,
            CashFlowEntry.tenant_id == tenant_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(404, "Lancamento nao encontrado")
    if entry.auto_generated == "SIM":
        raise HTTPException(400, "Lancamentos automaticos nao podem ser excluidos manualmente")

    await db.delete(entry)
    await log_action(db, user.id, tenant_id, "cashflow_entries", lancamento_id, "DELETE")
    return {"message": "Lancamento excluido com sucesso"}


@router.get("/categorias")
async def listar_categorias():
    """Retorna categorias validas para lancamentos."""
    return {
        "entrada": CATEGORIAS_ENTRADA,
        "saida": CATEGORIAS_SAIDA,
    }
