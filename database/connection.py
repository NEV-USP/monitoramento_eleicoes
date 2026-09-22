import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL não configurada. "
        "Verifique o arquivo .env."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


def testar_conexao():
    """
    Testa a conexão com o PostgreSQL.
    """

    with engine.connect() as connection:
        resultado = connection.execute(text("SELECT 1"))
        return resultado.scalar() == 1