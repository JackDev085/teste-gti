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


def test_criar_pedido(client: TestClient):
    response = client.post("/pedidos/", json=PEDIDO_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["name_client"] == "João da Silva"
    assert data["status"] == "pendente"
    assert data["value"] == pytest.approx(179.70, abs=0.01)
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
    assert data["total"] == 5
    assert len(data["orders"]) == 2
    assert data["skip"] == 0
    assert data["limit"] == 2
