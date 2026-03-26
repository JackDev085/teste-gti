from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from db.connection import create_db_and_tables, engine
from routes.order import router as order_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables(engine)
    yield


app = FastAPI(
    title="Gerenciamento de Pedidos",
    description=(
        "API REST para gerenciamento de pedidos. "
        "Permite criar, listar, buscar, atualizar status e excluir pedidos."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas da API
app.include_router(order_router)

# Servir frontend estático
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
