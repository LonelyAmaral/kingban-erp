"""Endpoints da API de Orcamentos/Pedidos — CRUD + pipeline de status + PDF + duplicar."""

import logging
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlalchemy import select, func, String
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.auth import get_current_user
from app.core.tenant import get_tenant_id
from app.core.audit import log_action
from app.models.order import Order, OrderItem
from app.models.client import Client
from app.models.salesperson import Salesperson
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.order import (
    PedidoCriar, PedidoAtualizar, PedidoResponse, MudarStatus,
    ItemPedidoResponse,
)
from app.schemas.base import PaginacaoResponse, MensagemResponse
from app.services.order_workflow import change_order_status
from app.services.pdf_generator import generate_order_pdf

logger = logging.getLogger("kingban.api.pedidos")
router = APIRouter()


def _order_to_response(order: Order, client_name: str = None, salesperson_name: str = None) -> PedidoResponse:
    """Converte model Order para resposta com nomes PT."""
    itens = []
    for item in (order.items or []):
        itens.append(ItemPedidoResponse(
            id=item.id, order_id=item.order_id,
            ordem=item.item_order or 0,
            produto_id=item.product_id,
            codigo_produto=item.product_code,
            nome_produto=item.product_name,
            quantidade=item.quantity or 0,
            unidade=item.unit or "UN",
            preco_unitario=item.unit_price or 0,
            desconto=item.discount or 0,
            total=item.total or 0,
            custo_unitario=item.cost_per_unit or 0,
            custo_total=item.cost_total or 0,
            valor_nf_unitario=item.nf_unit_value or 0,
        ))

    return PedidoResponse(
        id=order.id,
        numero=order.order_number,
        tipo_documento=order.document_type or "ORCAMENTO",
        status=order.status or "ORCAMENTO",
        empresa_id=order.company_id,
        cliente_id=order.client_id,
        vendedor_id=order.salesperson_id,
        tipo_nf=order.nf_type,
        origem_frete=order.shipping_origin,
        forma_pagamento=order.payment_method,
        condicao_pagamento=order.payment_terms,
        disponibilidade=order.availability,
        observacoes=order.observations,
        subtotal=order.subtotal or 0,
        valor_frete=order.freight_value or 0,
        desconto_total=order.total_discount or 0,
        total=order.total or 0,
        custo_total=order.total_cost or 0,
        valor_nf=order.nf_value or 0,
        valor_difal=order.difal_value or 0,
        lucro=order.profit or 0,
        itens=itens,
        nome_cliente=client_name,
        nome_vendedor=salesperson_name,
        criado_em=order.criado_em,
        atualizado_em=order.atualizado_em,
        status_alterado_em=order.status_changed_at,
    )


@router.get("", response_model=PaginacaoResponse[PedidoResponse])
async def listar_pedidos(
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=1, le=200),
    busca: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    direcao: str = Query("desc"),
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Lista pedidos com paginacao e filtros."""
    base = select(Order).where(Order.tenant_id == tenant_id)

    if status_filter:
        base = base.where(Order.status == status_filter)

    # Contagem
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar()

    # Query com joins
    query = (
        select(Order, Client.nome.label("cn"), Salesperson.nome.label("sn"))
        .outerjoin(Client, Order.client_id == Client.id)
        .outerjoin(Salesperson, Order.salesperson_id == Salesperson.id)
        .where(Order.tenant_id == tenant_id)
    )
    if status_filter:
        query = query.where(Order.status == status_filter)
    if busca:
        termo = f"%{busca}%"
        query = query.where(Client.nome.ilike(termo))

    if direcao == "desc":
        query = query.order_by(Order.order_number.desc())
    else:
        query = query.order_by(Order.order_number.asc())

    offset = (pagina - 1) * por_pagina
    query = query.offset(offset).limit(por_pagina)

    result = await db.execute(query)
    rows = result.all()

    pedidos = []
    for order, cn, sn in rows:
        items_r = await db.execute(
            select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.item_order)
        )
        order.items = items_r.scalars().all()
        pedidos.append(_order_to_response(order, cn, sn))

    return PaginacaoResponse(
        itens=pedidos, total=total, pagina=pagina,
        paginas=math.ceil(total / por_pagina) if total > 0 else 1,
    )


@router.get("/proximo-numero")
async def proximo_numero(
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Retorna o proximo numero de pedido disponivel."""
    result = await db.execute(
        select(func.max(Order.order_number)).where(Order.tenant_id == tenant_id)
    )
    return {"proximo_numero": (result.scalar() or 0) + 1}


@router.get("/{pedido_id}", response_model=PedidoResponse)
async def obter_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Obtem um pedido pelo ID com itens."""
    result = await db.execute(
        select(Order, Client.nome.label("cn"), Salesperson.nome.label("sn"))
        .outerjoin(Client, Order.client_id == Client.id)
        .outerjoin(Salesperson, Order.salesperson_id == Salesperson.id)
        .where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    order, cn, sn = row
    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.item_order)
    )
    order.items = items_r.scalars().all()
    return _order_to_response(order, cn, sn)


@router.post("", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def criar_pedido(
    dados: PedidoCriar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Cria um novo pedido/orcamento com itens."""
    numero = dados.numero
    if not numero:
        r = await db.execute(select(func.max(Order.order_number)).where(Order.tenant_id == tenant_id))
        numero = (r.scalar() or 0) + 1

    order = Order(
        tenant_id=tenant_id, order_number=numero,
        document_type=dados.tipo_documento, status=dados.status,
        company_id=dados.empresa_id or tenant_id,
        client_id=dados.cliente_id, salesperson_id=dados.vendedor_id,
        nf_type=dados.tipo_nf, shipping_origin=dados.origem_frete,
        payment_method=dados.forma_pagamento, payment_terms=dados.condicao_pagamento,
        availability=dados.disponibilidade, observations=dados.observacoes,
        subtotal=dados.subtotal, freight_value=dados.valor_frete,
        total_discount=dados.desconto_total, total=dados.total,
        total_cost=dados.custo_total, nf_value=dados.valor_nf,
        difal_value=dados.valor_difal, profit=dados.lucro,
    )
    db.add(order)
    await db.flush()

    for idx, item_data in enumerate(dados.itens):
        item = OrderItem(
            tenant_id=tenant_id, order_id=order.id,
            item_order=item_data.ordem or idx,
            product_id=item_data.produto_id,
            product_code=item_data.codigo_produto, product_name=item_data.nome_produto,
            quantity=item_data.quantidade, unit=item_data.unidade,
            unit_price=item_data.preco_unitario, discount=item_data.desconto,
            total=item_data.total, cost_per_unit=item_data.custo_unitario,
            cost_total=item_data.custo_total, nf_unit_value=item_data.valor_nf_unitario,
        )
        db.add(item)

    await db.flush()
    await log_action(db, user.id, tenant_id, "orders", order.id, "CREATE",
                     new_values={"numero": numero, "total": dados.total})

    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.item_order)
    )
    order.items = items_r.scalars().all()
    logger.info("Pedido #%d criado (ID %d)", numero, order.id)
    return _order_to_response(order)


@router.put("/{pedido_id}", response_model=PedidoResponse)
async def atualizar_pedido(
    pedido_id: int,
    dados: PedidoAtualizar,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Atualiza um pedido existente (campos + itens)."""
    result = await db.execute(
        select(Order).where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    field_map = {
        "numero": "order_number", "tipo_documento": "document_type",
        "empresa_id": "company_id", "cliente_id": "client_id",
        "vendedor_id": "salesperson_id", "tipo_nf": "nf_type",
        "origem_frete": "shipping_origin", "forma_pagamento": "payment_method",
        "condicao_pagamento": "payment_terms", "disponibilidade": "availability",
        "observacoes": "observations", "subtotal": "subtotal",
        "valor_frete": "freight_value", "desconto_total": "total_discount",
        "total": "total", "custo_total": "total_cost",
        "valor_nf": "nf_value", "valor_difal": "difal_value", "lucro": "profit",
    }

    update_data = dados.model_dump(exclude_unset=True, exclude={"itens"})
    for campo_pt, valor in update_data.items():
        setattr(order, field_map.get(campo_pt, campo_pt), valor)

    if dados.itens is not None:
        old_items = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
        for old in old_items.scalars().all():
            await db.delete(old)

        for idx, item_data in enumerate(dados.itens):
            item = OrderItem(
                tenant_id=tenant_id, order_id=order.id,
                item_order=item_data.ordem or idx,
                product_id=item_data.produto_id,
                product_code=item_data.codigo_produto, product_name=item_data.nome_produto,
                quantity=item_data.quantidade, unit=item_data.unidade,
                unit_price=item_data.preco_unitario, discount=item_data.desconto,
                total=item_data.total, cost_per_unit=item_data.custo_unitario,
                cost_total=item_data.custo_total, nf_unit_value=item_data.valor_nf_unitario,
            )
            db.add(item)

    await db.flush()
    await log_action(db, user.id, tenant_id, "orders", order.id, "UPDATE")

    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.item_order)
    )
    order.items = items_r.scalars().all()
    return _order_to_response(order)


@router.post("/{pedido_id}/status", response_model=MensagemResponse)
async def mudar_status(
    pedido_id: int,
    dados: MudarStatus,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Muda o status do pedido e executa acoes automaticas (workflow)."""
    result = await db.execute(
        select(Order).where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    old_status = order.status
    wf_result = await change_order_status(db, order, dados.novo_status, tenant_id)

    if not wf_result.success:
        raise HTTPException(status_code=400, detail=wf_result.message)

    await log_action(db, user.id, tenant_id, "orders", order.id, "STATUS_CHANGE",
                     old_values={"status": old_status},
                     new_values={"status": dados.novo_status})

    return MensagemResponse(mensagem=wf_result.message)


@router.delete("/{pedido_id}", response_model=MensagemResponse)
async def excluir_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Exclui um pedido (apenas se estiver em ORCAMENTO)."""
    result = await db.execute(
        select(Order).where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    if order.status != "ORCAMENTO":
        raise HTTPException(status_code=400,
                            detail="Apenas orcamentos podem ser excluidos. Cancele o pedido primeiro.")

    items = await db.execute(select(OrderItem).where(OrderItem.order_id == order.id))
    for item in items.scalars().all():
        await db.delete(item)
    await db.delete(order)

    await log_action(db, user.id, tenant_id, "orders", pedido_id, "DELETE")
    return MensagemResponse(mensagem=f"Orcamento #{order.order_number} excluido")


@router.get("/{pedido_id}/pdf")
async def gerar_pdf(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    tenant_id: int = Depends(get_tenant_id),
):
    """Gera PDF do orcamento/pedido."""
    # Buscar pedido com joins
    result = await db.execute(
        select(Order, Client, Salesperson, Tenant)
        .outerjoin(Client, Order.client_id == Client.id)
        .outerjoin(Salesperson, Order.salesperson_id == Salesperson.id)
        .outerjoin(Tenant, Order.company_id == Tenant.id)
        .where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    order, client_obj, salesperson_obj, tenant_obj = row

    # Buscar itens
    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == order.id).order_by(OrderItem.item_order)
    )
    items_list = items_r.scalars().all()

    # Montar dicts para o gerador
    order_data = {
        'order_number': order.order_number,
        'date': order.criado_em.date() if order.criado_em else None,
        'document_type': order.document_type or 'ORCAMENTO',
        'nf_type': order.nf_type or '',
        'shipping_origin': order.shipping_origin or '',
        'payment_method': order.payment_method or 'PIX OU DEPOSITO BANCARIO',
        'payment_terms': order.payment_terms or '',
        'availability': order.availability or 'A PRONTA ENTREGA',
        'subtotal': order.subtotal or 0,
        'freight_value': order.freight_value or 0,
        'total': order.total or 0,
        'total_discount': order.total_discount or 0,
        'nf_value': order.nf_value or 0,
        'difal_value': order.difal_value or 0,
        'observations': order.observations or '',
        'salesperson_name': salesperson_obj.nome if salesperson_obj else '',
    }

    company = {}
    if tenant_obj:
        company = {
            'name': tenant_obj.name or 'KING BAN',
            'cnpj': tenant_obj.cnpj or '96.453.840/0001-89',
            'ie': getattr(tenant_obj, 'ie', '') or '',
            'address': getattr(tenant_obj, 'address', '') or '',
            'city': getattr(tenant_obj, 'city', 'Avare') or 'Avare',
            'state': getattr(tenant_obj, 'state', 'SP') or 'SP',
            'cep': getattr(tenant_obj, 'cep', '') or '',
        }

    client = {}
    if client_obj:
        client = {
            'id': client_obj.id,
            'nome': client_obj.nome or '',
            'cnpj_cpf': getattr(client_obj, 'cnpj_cpf', '') or '',
            'ie': getattr(client_obj, 'ie', '') or '',
            'endereco': getattr(client_obj, 'endereco', '') or '',
            'bairro': getattr(client_obj, 'bairro', '') or '',
            'cidade': getattr(client_obj, 'cidade', '') or '',
            'estado': getattr(client_obj, 'estado', '') or '',
            'cep': getattr(client_obj, 'cep', '') or '',
            'telefone': getattr(client_obj, 'telefone', '') or '',
        }

    items = []
    for item in items_list:
        items.append({
            'product_code': item.product_code or '',
            'product_name': item.product_name or '',
            'quantity': item.quantity or 0,
            'unit': item.unit or 'UN',
            'unit_price': item.unit_price or 0,
            'total': item.total or 0,
        })

    pdf_bytes = generate_order_pdf(order_data, items, company, client)

    filename = f"orcamento_{order.order_number:05d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/{pedido_id}/duplicar", response_model=PedidoResponse, status_code=status.HTTP_201_CREATED)
async def duplicar_pedido(
    pedido_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
    tenant_id: int = Depends(get_tenant_id),
):
    """Duplica um pedido existente com novo numero."""
    # Buscar pedido original
    result = await db.execute(
        select(Order, Client.nome.label("cn"), Salesperson.nome.label("sn"))
        .outerjoin(Client, Order.client_id == Client.id)
        .outerjoin(Salesperson, Order.salesperson_id == Salesperson.id)
        .where(Order.id == pedido_id, Order.tenant_id == tenant_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Pedido nao encontrado")

    original, cn, sn = row

    # Proximo numero
    r = await db.execute(select(func.max(Order.order_number)).where(Order.tenant_id == tenant_id))
    novo_numero = (r.scalar() or 0) + 1

    # Copiar pedido
    novo = Order(
        tenant_id=tenant_id,
        order_number=novo_numero,
        document_type=original.document_type,
        status="ORCAMENTO",
        company_id=original.company_id,
        client_id=original.client_id,
        salesperson_id=original.salesperson_id,
        nf_type=original.nf_type,
        shipping_origin=original.shipping_origin,
        payment_method=original.payment_method,
        payment_terms=original.payment_terms,
        availability=original.availability,
        observations=original.observations,
        subtotal=original.subtotal,
        freight_value=original.freight_value,
        total_discount=original.total_discount,
        total=original.total,
        total_cost=original.total_cost,
        nf_value=original.nf_value,
        difal_value=original.difal_value,
        profit=original.profit,
    )
    db.add(novo)
    await db.flush()

    # Copiar itens
    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == original.id).order_by(OrderItem.item_order)
    )
    for item in items_r.scalars().all():
        novo_item = OrderItem(
            tenant_id=tenant_id,
            order_id=novo.id,
            item_order=item.item_order,
            product_id=item.product_id,
            product_code=item.product_code,
            product_name=item.product_name,
            quantity=item.quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            discount=item.discount,
            total=item.total,
            cost_per_unit=item.cost_per_unit,
            cost_total=item.cost_total,
            nf_unit_value=item.nf_unit_value,
        )
        db.add(novo_item)

    await db.flush()
    await log_action(db, user.id, tenant_id, "orders", novo.id, "CREATE",
                     new_values={"duplicado_de": original.order_number, "numero": novo_numero})

    # Carregar itens do novo pedido
    items_r = await db.execute(
        select(OrderItem).where(OrderItem.order_id == novo.id).order_by(OrderItem.item_order)
    )
    novo.items = items_r.scalars().all()

    logger.info("Pedido #%d duplicado -> #%d", original.order_number, novo_numero)
    return _order_to_response(novo, cn, sn)
