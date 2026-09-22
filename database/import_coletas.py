from database.connection import engine
from database.preprocess import (
    localizar_arquivo,
    extrair_periodo,
    identificar_grupo_subgrupo,
)

from pathlib import Path
from sqlalchemy import text


def importar_coleta(pasta):
    """
    Importa os metadados de uma pasta semanal
    para a tabela coletas.
    """

    pasta = Path(pasta)

    # --------------------------------------------------------
    # Localizar arquivos
    # --------------------------------------------------------

    benchmarking = localizar_arquivo(
        pasta,
        "Benchmarking"
    )

    content = localizar_arquivo(
        pasta,
        "Content"
    )

    # --------------------------------------------------------
    # Informações da pasta
    # --------------------------------------------------------

    periodo = extrair_periodo(pasta)

    grupo, subgrupo = identificar_grupo_subgrupo(
        pasta
    )

    # --------------------------------------------------------
    # Dados da coleta
    # --------------------------------------------------------

    dados = {
        "grupo": grupo,
        "subgrupo": subgrupo,
        "semana": periodo["semana"],
        "data_inicio": periodo["data_inicio"],
        "data_fim": periodo["data_fim"],
        "benchmarking_arquivo": benchmarking.name,
        "content_arquivo": content.name,
    }

    print("\n" + "=" * 70)
    print("COLETA IDENTIFICADA")
    print("=" * 70)

    for chave, valor in dados.items():
        print(f"{chave}: {valor}")

    # --------------------------------------------------------
    # Inserção
    # --------------------------------------------------------

    sql = text("""
        INSERT INTO coletas (
            grupo,
            subgrupo,
            semana,
            data_inicio,
            data_fim,
            benchmarking_arquivo,
            content_arquivo
        )
        VALUES (
            :grupo,
            :subgrupo,
            :semana,
            :data_inicio,
            :data_fim,
            :benchmarking_arquivo,
            :content_arquivo
        )
        ON CONFLICT (
            grupo,
            subgrupo,
            data_inicio,
            data_fim
        )
        DO UPDATE SET
            semana = EXCLUDED.semana,
            benchmarking_arquivo = EXCLUDED.benchmarking_arquivo,
            content_arquivo = EXCLUDED.content_arquivo
        RETURNING id;
    """)

    with engine.begin() as connection:

        resultado = connection.execute(
            sql,
            dados
        )

        coleta_id = resultado.scalar_one()

    print("\nColeta importada com sucesso.")
    print(f"ID da coleta: {coleta_id}")

    return coleta_id


if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta semanal: "
    ).strip()

    importar_coleta(pasta)