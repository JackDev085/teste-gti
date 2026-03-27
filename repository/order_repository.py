import uuid
from datetime import datetime, timezone
from sqlmodel import Session, select

from models.order import (
    Order,
    OrderItem,
    OrderCreate,
)

class OrderRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_order(self, data: OrderCreate) -> Order:
        """Cria um novo pedido com seus itens e calcula o valor total."""
        valor_total = sum(
            item.price for item in data.items
        )

        order = Order(
            name_client=data.name_client,
            value=valor_total,
            status="pendente",
        )

        self.session.add(order)
        self.session.flush()  # gera o UUID do pedido

        for item_data in data.items:
            item = OrderItem(
                order_id=order.id,
                name=item_data.name,
                price=item_data.price,
            )
            self.session.add(item)

        self.session.commit()
        self.session.refresh(order)
        return order


    def get_all_orders(
        self, skip: int = 0, limit: int = 10
    ) -> tuple[list[Order], int]:
        """Retorna pedidos paginados e o total de registros."""
        orders = self.session.exec(select(Order).offset(skip).limit(limit)).all()
        print(orders)
        total = len(orders)

        return orders, total


    def get_order_by_id(self, order_id: uuid.UUID) -> Order | None:
        """Busca um pedido pelo seu UUID."""
        return  self.session.get(Order, order_id)


    def update_order_status(
        self, order_id: uuid.UUID, status: str
    ) -> Order | None:
        """Atualiza o status de um pedido."""
        order =  self.session.get(Order, order_id)
        if order is None:
            return None

        order.status = status
        order.updated_at = datetime.now(timezone.utc)
        self.session.add(order)
        self.session.commit()
        self.session.refresh(order)
        return order


    def delete_order(self, order_id: uuid.UUID) -> bool:
        """Exclui um pedido pelo UUID. Retorna True se foi excluído."""
        order =  self.session.get(Order, order_id)
        if order is None:
            return False

        self.session.delete(order)
        self.session.commit()
        return True
