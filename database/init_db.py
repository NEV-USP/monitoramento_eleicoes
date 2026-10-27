
import argparse
from pathlib import Path

from sqlalchemy import text

from database.connection import (
    engine,
    engine_monitoramento_extra,
    testar_conexao,
    testar_conexao_monitoramento_extra,
)


BASE_DIR = Path(__file__).parent

SCHEMAS = {
    "public": {
        "arquivo": BASE_DIR / "schemas/public.sql",
        "engine": engine,
        "teste": testar_conexao,
    },
    "monitoramento_extra": {
        "arquivo": BASE_DIR / "schemas/monitoramento_extra.sql",
        "engine": engine_monitoramento_extra,
        "teste": testar_conexao_monitoramento_extra,
    },
}


def criar_tabelas(schema="public"):
    if schema not in SCHEMAS:
        raise ValueError(
            f"Schema inválido: {schema}. "
            f"Opções disponíveis: {', '.join(SCHEMAS)}"
        )

    configuracao = SCHEMAS[schema]
    arquivo_sql = configuracao["arquivo"]
    engine_schema = configuracao["engine"]
    testar_conexao_schema = configuracao["teste"]

    if not arquivo_sql.exists():
        raise FileNotFoundError(
            f"Arquivo SQL não encontrado: {arquivo_sql}"
        )

    # Cria o schema somente quando necessário.
    # O nome é validado pela lista SCHEMAS acima.
    if schema != "public":
        with engine.begin() as connection:
            connection.execute(
                text(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
            )

    schema_sql = arquivo_sql.read_text(encoding="utf-8")

    comandos = [
        comando.strip()
        for comando in schema_sql.split(";")
        if comando.strip()
    ]

    with engine_schema.begin() as connection:
        for comando in comandos:
            connection.execute(text(comando))

    if not testar_conexao_schema():
        raise RuntimeError(
            f"Não foi possível validar a conexão "
            f"com o schema {schema}."
        )

    print(f"Schema {schema} inicializado com sucesso.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inicializa as tabelas de um schema PostgreSQL."
    )

    parser.add_argument(
        "--schema",
        default="public",
        choices=list(SCHEMAS.keys()),
        help="Schema a inicializar (padrão: public).",
    )

    args = parser.parse_args()
    criar_tabelas(args.schema)
