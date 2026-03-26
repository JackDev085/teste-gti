import os
from sqlmodel import SQLModel, create_engine, Session
import dotenv

dotenv.load_dotenv()

PROD = os.getenv("PROD")
if PROD == "False":
    DATABASE_URL = "sqlite:///./database.db"
    engine = create_engine(DATABASE_URL)
    print("desenvolvimento")
    
else:
    print("producao")
    DATABASE_URL = os.getenv("POSTGRES_URL_FASTAPI")
    engine = create_engine(DATABASE_URL, echo=False)
    
def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session