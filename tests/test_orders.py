import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.orm import sessionmaker

from main import app
from db.connection import get_session

TEST_DATABASE_URL = "sqlite:///./test.db"

test_engine = create_engine(TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
TestSession = sessionmaker(test_engine, class_=Session, expire_on_commit=False)


def override_get_session():
    with TestSession() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)

        
@pytest.fixture
def client():
    return TestClient(app)


PEDIDO_PAYLOAD = {
    "name_client": "João da Silva",
    "items": [
        {"name": "Camiseta", "price": 49.90},
        {"name": "Bermuda", "price": 79.90},
    ],
}


def _load_seed_orders() -> list[dict]:
    seed_path = Path(__file__).with_name("seed.json")
    seed_data = json.loads(seed_path.read_text(encoding="utf-8"))

    total_orders = seed_data["total_orders"]
    clients = seed_data["clients"]
    catalog = seed_data["catalog"]

    orders = []
    for idx in range(total_orders):
        name_client = clients[idx % len(clients)]
        item_count = (idx % 3) + 1
        items = []
        for item_idx in range(item_count):
            catalog_item = catalog[(idx + item_idx) % len(catalog)]
            items.append(
                {
                    "name": catalog_item["name"],
                    "price": catalog_item["price"],
                }
            )

        orders.append({"name_client": name_client, "items": items})

    return orders


def test_criar_pedido(client: TestClient):
    response = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name_client"] == "João da Silva"
    assert data["status"] == "pendente"
    assert data["value"] == pytest.approx(129.80, abs=0.01)
    assert len(data["items"]) == 2


def test_listar_pedidos(client: TestClient):
    # Cria 2 pedidos
    client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    client.post("/pedidos/", json=PEDIDO_PAYLOAD)

    response = client.get("/pedidos/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["orders"]) == 2


def test_buscar_pedido_por_id(client: TestClient):
    create_resp = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    pedido_id = create_resp.json()["id"]

    response = client.get(f"/pedidos/{pedido_id}")
    assert response.status_code == 200
    assert response.json()["id"] == pedido_id


def test_buscar_pedido_inexistente(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/pedidos/{fake_id}")
    assert response.status_code == 404


def test_atualizar_status(client: TestClient):
    create_resp = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    pedido_id = create_resp.json()["id"]

    response = client.patch(
        f"/pedidos/{pedido_id}/status", json={"status": "concluido"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "concluido"


def test_excluir_pedido(client: TestClient):
    create_resp = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    pedido_id = create_resp.json()["id"]

    response = client.delete(f"/pedidos/{pedido_id}")
    assert response.status_code == 204

    # Verifica se foi deletado
    response = client.get(f"/pedidos/{pedido_id}")
    assert response.status_code == 404


def test_paginacao(client: TestClient):
    # Cria 5 pedidos
    for _ in range(5):
        client.post("/pedidos/", json=PEDIDO_PAYLOAD)

    # Pega os 2 primeiros
    response = client.get("/pedidos/?skip=0&limit=2")
    data = response.json()
    assert data["total"] == 2
    assert len(data["orders"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2


def test_criar_mais_de_100_pedidos_com_seed(client: TestClient):
    bulk_orders = _load_seed_orders()
    assert len(bulk_orders) > 100

    for payload in bulk_orders:
        response = client.post("/pedidos/", json=payload)
        assert response.status_code == 201

    # O endpoint retorna a quantidade paginada em "total".
    first_page = client.get("/pedidos/?skip=0&limit=100")
    assert first_page.status_code == 200
    first_page_data = first_page.json()
    assert first_page_data["total"] == 100
    assert len(first_page_data["orders"]) == 100

    second_page = client.get("/pedidos/?skip=100&limit=100")
    assert second_page.status_code == 200
    second_page_data = second_page.json()
    assert second_page_data["total"] == len(bulk_orders) - 100
    assert len(second_page_data["orders"]) == len(bulk_orders) - 100


def test_limite_maximo_da_paginacao(client: TestClient):
    response = client.get("/pedidos/?limit=101")
    assert response.status_code == 422


def test_skip_negativo_retorna_erro(client: TestClient):
    response = client.get("/pedidos/?skip=-1")
    assert response.status_code == 422


def test_criar_pedido_com_preco_negativo(client: TestClient):
    payload_invalido = {
        "name_client": "Cliente Invalido",
        "items": [{"name": "Item X", "price": -10.0}],
    }
    response = client.post("/pedidos/", json=payload_invalido)
    assert response.status_code == 422


def test_atualizar_status_pedido_inexistente(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.patch(f"/pedidos/{fake_id}/status", json={"status": "concluido"})
    assert response.status_code == 404


def test_excluir_pedido_inexistente(client: TestClient):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.delete(f"/pedidos/{fake_id}")
    assert response.status_code == 404


def test_updated_at_muda_ao_atualizar_status(client: TestClient):
    create_resp = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    pedido = create_resp.json()
    pedido_id = pedido["id"]
    updated_at_inicial = pedido["updated_at"]

    update_resp = client.patch(f"/pedidos/{pedido_id}/status", json={"status": "concluido"})
    assert update_resp.status_code == 200
    pedido_atualizado = update_resp.json()

    assert pedido_atualizado["status"] == "concluido"
    assert pedido_atualizado["updated_at"] != updated_at_inicial
