import uuid
from sqlmodel import Session
from fastapi import APIRouter, Depends, HTTPException, Query

from db.connection import get_session
from models.order import (
    OrderCreate,
    OrderRead,
    OrderUpdateStatus,
    PaginatedOrders,
)
from repository.order_repository import OrderRepository

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])


@router.post("/", response_model=OrderRead, status_code=201, summary="Criar um novo pedido")
async def criar_pedido(data: OrderCreate, session: Session = Depends(get_session)):
    """Cria um novo pedido. O valor total é calculado automaticamente a partir dos itens."""
    order_repo = OrderRepository(session)
    order = order_repo.create_order(data)
    return order


@router.get("/", response_model=PaginatedOrders, summary="Listar todos os pedidos")
async def listar_pedidos(
    skip: int = Query(0, ge=0, description="Registros a pular"),
    limit: int = Query(10, ge=1, le=100, description="Limite de registros"),
    session: Session = Depends(get_session),
):
    """Retorna uma lista paginada de todos os pedidos."""
    order_repo = OrderRepository(session)
    orders, total = order_repo.get_all_orders(skip, limit)
    return PaginatedOrders(total=total, skip=skip, limit=limit, orders=orders)


@router.get("/{pedido_id}", response_model=OrderRead, summary="Buscar pedido por ID")
async def buscar_pedido(pedido_id: uuid.UUID, session: Session = Depends(get_session)):
    """Busca um pedido específico pelo seu UUID."""
    order_repo = OrderRepository(session)
    order = order_repo.get_order_by_id(pedido_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.patch("/{pedido_id}/status", response_model=OrderRead, summary="Atualizar status do pedido")
async def atualizar_status(
    pedido_id: uuid.UUID,
    data: OrderUpdateStatus,
    session: Session = Depends(get_session),
):
    """Atualiza o status de um pedido (pendente ou concluido)."""
    order_repo = OrderRepository(session)
    order = order_repo.update_order_status(pedido_id, data.status)
    if order is None:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order


@router.delete("/{pedido_id}", status_code=204, summary="Excluir um pedido")
async def excluir_pedido(pedido_id: uuid.UUID, session: Session = Depends(get_session)):
    """Exclui um pedido pelo seu UUID."""
    order_repo = OrderRepository(session)
    deleted = order_repo.delete_order(pedido_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
