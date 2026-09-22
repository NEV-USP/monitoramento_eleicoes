from pathlib import Path

from database.connection import engine
from sqlalchemy import text


SCHEMA_FILE = Path(__file__).parent / "schema.sql"


def criar_tabelas():
    schema = SCHEMA_FILE.read_text(encoding="utf-8")

    # Executa cada comando SQL separadamente
    comandos = [
        comando.strip()
        for comando in schema.split(";")
        if comando.strip()
    ]

    with engine.begin() as connection:
        for comando in comandos:
            connection.execute(text(comando))

    print("Banco de dados inicializado com sucesso.")


if __name__ == "__main__":
    criar_tabelas()