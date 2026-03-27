import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

# ── Modelos de Tabela ───────────────────────────────────────────
class OrderItem(SQLModel, table=True):
    __tablename__ = "order_items"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    order_id: uuid.UUID = Field(foreign_key="orders.id", nullable=False)
    name: str = Field(max_length=150)
    price: float = Field(ge=0)

    order: Optional["Order"] = Relationship(back_populates="items")


class Order(SQLModel, table=True):
    """Pedido de um client."""
    __tablename__ = "orders"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name_client: str = Field(max_length=200)
    value: float = Field(default=0, ge=0)
    status: str = Field(default="pendente")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    items: list[OrderItem] = Relationship(
        back_populates="order",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class OrderItemCreate(SQLModel):
    """Schema para criar um item do pedido."""
    name: str = Field(max_length=150)
    price: float = Field(ge=0)


class OrderItemRead(SQLModel):
    """Schema de leitura de um item do pedido."""
    id: uuid.UUID
    name: str
    price: float


class OrderCreate(SQLModel):
    """Schema para criar um pedido."""
    name_client: str = Field(max_length=200)
    items: list[OrderItemCreate]


class OrderRead(SQLModel):
    """Schema de leitura de um pedido."""
    id: uuid.UUID
    name_client: str
    value: float
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]


class OrderUpdateStatus(SQLModel):
    """Schema para atualizar o status de um pedido."""
    status: str


class PaginatedOrders(SQLModel):
    """Resposta paginada de orders."""
    total: int
    skip: int
    limit: int
    orders: list[OrderRead]
