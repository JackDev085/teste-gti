# Gerenciamento de Pedidos

API REST em FastAPI para gerenciamento de pedidos, com frontend estático servido pela própria aplicação.

## Funcionalidades

- Criar pedido com múltiplos itens
- Listar pedidos com paginação (`skip` e `limit`)
- Buscar pedido por ID
- Atualizar status do pedido
- Excluir pedido
- Frontend web simples para consumo da API

## Stack

- Python 3.10+
- FastAPI + Uvicorn
- SQLModel (ORM)
- SQLite (desenvolvimento) / PostgreSQL (produção)
- Pytest

## Estrutura do Projeto

```text
.
├── main.py
├── requirements.txt
├── api/
├── db/
├── frontend/
├── models/
├── repository/
├── routes/
└── tests/
```

## Pré-requisitos

- Python 3.10 ou superior
- `pip`

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração de Ambiente

A aplicação usa a variável `PROD` para decidir o banco:

- `PROD=False`: usa SQLite local (`database.db`)
- Qualquer outro valor: usa PostgreSQL com `POSTGRES_URL_FASTAPI`

Exemplo para desenvolvimento local:

```bash
export PROD=False
```

Exemplo para produção:

```bash
export PROD=True
export POSTGRES_URL_FASTAPI="postgresql+psycopg2://usuario:senha@host:5432/banco"
```

## Como Executar

```bash
fastapi dev main.py
```

Após iniciar:

- API e frontend: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints Principais

- `POST /pedidos/` - cria pedido
- `GET /pedidos/` - lista pedidos paginados
- `GET /pedidos/{pedido_id}` - busca pedido por ID
- `PATCH /pedidos/{pedido_id}/status` - atualiza status
- `DELETE /pedidos/{pedido_id}` - exclui pedido

### Exemplo de payload para criação

```json
{
  "name_client": "João da Silva",
  "items": [
    { "name": "Camiseta", "price": 49.9 },
    { "name": "Bermuda", "price": 79.9 }
  ]
}
```

## Testes

Executar toda a suíte:

```bash
pytest
```

Os testes cobrem:

- fluxo CRUD de pedidos
- paginação e validações de query params
- cenários de erro (404/422)
- atualização de `updated_at`

## Observações

- O frontend está em `frontend/` e é servido via `StaticFiles` na raiz.
- Em desenvolvimento, as tabelas são criadas automaticamente no startup da aplicação.
