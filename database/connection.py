
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


# ============================================================
# CONEXÃO ATUAL — SCHEMA PUBLIC
# ============================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ============================================================
# NOVA CONEXÃO — SCHEMA MONITORAMENTO_EXTRA
# ============================================================

engine_monitoramento_extra = create_engine(
    DATABASE_URL,
    connect_args={
        "options": "-csearch_path=monitoramento_extra"
    },
    pool_pre_ping=True
)


# ============================================================
# TESTES DE CONEXÃO
# ============================================================

def testar_conexao():
    """Testa a conexão com o schema public."""

    with engine.connect() as connection:
        resultado = connection.execute(
            text("SELECT 1")
        )
        return resultado.scalar() == 1


def testar_conexao_monitoramento_extra():
    """Testa a conexão exclusiva com o novo schema."""

    with engine_monitoramento_extra.connect() as connection:
        resultado = connection.execute(
            text("""
                SELECT
                    current_schema(),
                    current_database()
            """)
        )

        schema, banco = resultado.fetchone()

        return (
            schema == "monitoramento_extra"
            and banco is not None
        )

def obter_engine(schema="public"):
    engines = {
        "public": engine,
        "monitoramento_extra": engine_monitoramento_extra,
    }

    if schema not in engines:
        raise ValueError(f"Schema não reconhecido: {schema}")

    return engines[schema]