
import os
import re
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import text

from database.connection import engine
from database.preprocess import (
    preparar_metrics_dataframe,
    preparar_posts_dataframe,
)

from database.import_perfis import (
    importar_perfis_dataframe,
)

from database.import_metricas_perfil import (
    importar_metricas_perfil_dataframe,
)

from database.import_posts import (
    importar_posts_dataframe,
)

from google_drive.drive import (
    listar_pastas,
    encontrar_arquivos_por_prefixo,
)

from google_drive.reader import (
    ler_excel,
)


load_dotenv()


ROOT_FOLDER_ID = os.getenv(
    "GOOGLE_DRIVE_FOLDER_ID"
)


GRUPOS = {
    "Presidenciáveis",
    "Senado",
    "Governos",
    "Deputados Federais",
}

def buscar_status_coleta(coleta_id):
    sql = text("""
        SELECT status_importacao
        FROM coletas
        WHERE id = :id
    """)

    with engine.connect() as connection:
        resultado = connection.execute(
            sql,
            {"id": coleta_id}
        ).fetchone()

    if resultado is None:
        return None

    return resultado[0]

def atualizar_status_coleta(
    coleta_id,
    status,
    mensagem_erro=None,
):
    """
    Atualiza o status de processamento de uma coleta.
    """

    sql = text("""
        UPDATE coletas
        SET
            status_importacao = :status,
            data_processamento = CURRENT_TIMESTAMP,
            mensagem_erro = :mensagem_erro
        WHERE id = :id
    """)

    with engine.begin() as connection:
        connection.execute(
            sql,
            {
                "id": coleta_id,
                "status": status,
                "mensagem_erro": mensagem_erro,
            },
        )


def marcar_processando(coleta_id):
    atualizar_status_coleta(
        coleta_id=coleta_id,
        status="PROCESSANDO",
        mensagem_erro=None,
    )


def marcar_concluida(coleta_id):
    atualizar_status_coleta(
        coleta_id=coleta_id,
        status="CONCLUIDA",
        mensagem_erro=None,
    )


def marcar_erro(coleta_id, erro):
    atualizar_status_coleta(
        coleta_id=coleta_id,
        status="ERRO",
        mensagem_erro=str(erro),
    )

def extrair_periodo_nome(nome):
    """
    Extrai semana, data inicial e data final diretamente
    do nome da pasta do Google Drive.

    Exemplos aceitos:

        Semana 01 (16/08 - 22/08)
        Semana 02 (23-08 - 29-08)
        Semana 03 (30_08 - 05_09)

    Não utiliza pathlib porque o nome do Drive pode conter
    '/'.
    """

    padrao = re.compile(
        r"Semana\s+(\d+)\s*"
        r"\(\s*"
        r"(\d{1,2})\s*[/\-_:]\s*(\d{1,2})"
        r"\s*-\s*"
        r"(\d{1,2})\s*[/\-_:]\s*(\d{1,2})"
        r"\s*\)",
        re.IGNORECASE,
    )

    resultado = padrao.search(nome)

    if not resultado:
        raise ValueError(
            "Não foi possível identificar o período "
            f"da pasta: {nome}"
        )

    semana = int(resultado.group(1))

    dia_inicio = int(resultado.group(2))
    mes_inicio = int(resultado.group(3))

    dia_fim = int(resultado.group(4))
    mes_fim = int(resultado.group(5))

    ano = date.today().year

    try:
        data_inicio = date(
            ano,
            mes_inicio,
            dia_inicio,
        )

        data_fim = date(
            ano,
            mes_fim,
            dia_fim,
        )

    except ValueError as erro:

        raise ValueError(
            f"Datas inválidas na pasta: {nome}"
        ) from erro

    return {
        "semana": semana,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }

def criar_coleta(
    grupo,
    subgrupo,
    semana,
    data_inicio,
    data_fim,
    benchmarking_arquivo,
    content_arquivo,
):
    sql_busca = text("""
        SELECT id
        FROM coletas
        WHERE grupo = :grupo
          AND subgrupo IS NOT DISTINCT FROM :subgrupo
          AND data_inicio = :data_inicio
          AND data_fim = :data_fim
    """)

    with engine.begin() as connection:

        resultado = connection.execute(
            sql_busca,
            {
                "grupo": grupo,
                "subgrupo": subgrupo,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            }
        ).fetchone()

        if resultado:
            coleta_id = resultado[0]

            sql_update = text("""
                UPDATE coletas
                SET
                    semana = :semana,
                    benchmarking_arquivo = :benchmarking_arquivo,
                    content_arquivo = :content_arquivo
                WHERE id = :id
            """)

            connection.execute(
                sql_update,
                {
                    "id": coleta_id,
                    "semana": semana,
                    "benchmarking_arquivo": benchmarking_arquivo,
                    "content_arquivo": content_arquivo,
                }
            )

            return coleta_id

        sql_insert = text("""
            INSERT INTO coletas (
                grupo,
                subgrupo,
                semana,
                data_inicio,
                data_fim,
                benchmarking_arquivo,
                content_arquivo,
                status_importacao
            )
            VALUES (
                :grupo,
                :subgrupo,
                :semana,
                :data_inicio,
                :data_fim,
                :benchmarking_arquivo,
                :content_arquivo,
                'PENDENTE'
            )
        """)

        connection.execute(
            sql_insert,
            {
                "grupo": grupo,
                "subgrupo": subgrupo,
                "semana": semana,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
                "benchmarking_arquivo": benchmarking_arquivo,
                "content_arquivo": content_arquivo,
            }
        )

        resultado = connection.execute(
            sql_busca,
            {
                "grupo": grupo,
                "subgrupo": subgrupo,
                "data_inicio": data_inicio,
                "data_fim": data_fim,
            }
        ).fetchone()

        if resultado is None:
            raise RuntimeError(
                "Não foi possível recuperar a coleta criada."
            )

        return resultado[0]


def encontrar_arquivos_semana(semana_id):
    """
    Localiza os arquivos Benchmarking e Content dentro
    de uma pasta semanal.
    """

    benchmarking = encontrar_arquivos_por_prefixo(
        semana_id,
        "Benchmarking",
    )

    content = encontrar_arquivos_por_prefixo(
        semana_id,
        "Content",
    )

    if not benchmarking:
        raise FileNotFoundError(
            "Arquivo Benchmarking não encontrado."
        )

    if not content:
        raise FileNotFoundError(
            "Arquivo Content não encontrado."
        )

    return benchmarking[0], content[0]


def importar_semana(grupo, subgrupo, semana):
    nome_semana = semana["name"]

    print("\n" + "=" * 70)
    print(f"PROCESSANDO: {grupo} / {subgrupo or '-'} / {nome_semana}")
    print("=" * 70)

    periodo = extrair_periodo_nome(nome_semana)

    benchmarking, content = encontrar_arquivos_semana(
        semana["id"]
    )

    coleta_id = criar_coleta(
        grupo=grupo,
        subgrupo=subgrupo,
        semana=periodo["semana"],
        data_inicio=periodo["data_inicio"],
        data_fim=periodo["data_fim"],
        benchmarking_arquivo=benchmarking["name"],
        content_arquivo=content["name"],
    )

    status_atual = buscar_status_coleta(coleta_id)

    if status_atual == "CONCLUIDA":
        print(
            f"Coleta {coleta_id} já está CONCLUIDA. "
            "Pulando."
        )
        return

    if status_atual == "PROCESSANDO":
        print(
            f"Coleta {coleta_id} está PROCESSANDO. "
            "Pulando para evitar duplicidade."
        )
        return

    marcar_processando(coleta_id)

    try:
        # --------------------------------------------------
        # MÉTRICAS DE PERFIL
        # --------------------------------------------------

        print("Lendo arquivo de métricas...")

        bruto_metrics = ler_excel(
            benchmarking["id"],
            sheet_name="Metrics Overview",
            header=None
        )

        metrics = preparar_metrics_dataframe(
            bruto_metrics
        )

        print(
            f"Métricas encontradas: "
            f"{len(metrics)} registros"
        )

        importar_perfis_dataframe(
            metrics=metrics,
            grupo=grupo
        )

        importar_metricas_perfil_dataframe(
            metrics=metrics,
            grupo=grupo,
            subgrupo=subgrupo,
            data_inicio=periodo["data_inicio"],
            data_fim=periodo["data_fim"],
        )

        # --------------------------------------------------
        # POSTS
        # --------------------------------------------------

        print("Lendo arquivo de posts...")

        bruto_posts = ler_excel(
            content["id"],
            sheet_name="Top 5000 Posts Overview",
            header=None
        )

        posts = preparar_posts_dataframe(
            bruto_posts
        )

        print(
            f"Posts encontrados: "
            f"{len(posts)} registros"
        )

        importar_posts_dataframe(
            posts_df=posts,
            grupo=grupo,
            subgrupo=subgrupo,
            data_inicio=periodo["data_inicio"],
            data_fim=periodo["data_fim"],
        )

        marcar_concluida(coleta_id)

        print(
            f"✓ Coleta {coleta_id} concluída com sucesso."
        )

    except Exception as erro:
        marcar_erro(
            coleta_id,
            erro
        )

        print(
            f"✗ Erro na coleta {coleta_id}: {erro}"
        )

        raise


def processar_subgrupo(
    grupo,
    subgrupo,
    pasta_id,
):
    """
    Processa todas as semanas de um subgrupo.
    """

    semanas = listar_pastas(
        pasta_id
    )

    semanas = [
        pasta
        for pasta in semanas
        if pasta["name"].lower().startswith(
            "semana "
        )
    ]

    semanas.sort(
        key=lambda x: x["name"]
    )

    print()
    print(
        f"Subgrupo: {subgrupo}"
    )

    print(
        f"Semanas encontradas: "
        f"{len(semanas)}"
    )

    for semana in semanas:

        try:

            importar_semana(
                grupo=grupo,
                subgrupo=subgrupo,
                semana=semana,
            )

        except Exception as erro:

            print()
            print(
                "ERRO NA SEMANA:"
            )
            print(
                f"  {semana['name']}"
            )
            print(
                f"  {type(erro).__name__}: "
                f"{erro}"
            )

            # Continua para a próxima semana.
            continue


def processar_grupo(
    grupo,
    pasta_id,
):
    """
    Processa um grupo do Google Drive.

    Grupos com subgrupos:
        Governos
        Deputados Federais

    Grupos sem subgrupos:
        Presidenciáveis
        Senado
    """

    print()
    print("#" * 70)
    print(f"GRUPO: {grupo}")
    print("#" * 70)

    pastas = listar_pastas(
        pasta_id
    )

    # ==============================================================
    # IDENTIFICAR SUBGRUPOS
    # ==============================================================

    subgrupos = [
        pasta
        for pasta in pastas
        if not pasta["name"].lower().startswith(
            "semana "
        )
    ]

    # ==============================================================
    # GRUPO DIRETO COM SEMANAS
    # ==============================================================

    semanas_diretas = [
        pasta
        for pasta in pastas
        if pasta["name"].lower().startswith(
            "semana "
        )
    ]

    if semanas_diretas:

        semanas_diretas.sort(
            key=lambda x: x["name"]
        )

        print(
            f"Semanas encontradas: "
            f"{len(semanas_diretas)}"
        )

        for semana in semanas_diretas:

            try:

                importar_semana(
                    grupo=grupo,
                    subgrupo=None,
                    semana=semana,
                )

            except Exception as erro:

                print()
                print(
                    "ERRO NA SEMANA:"
                )
                print(
                    f"  {semana['name']}"
                )
                print(
                    f"  {type(erro).__name__}: "
                    f"{erro}"
                )

    # ==============================================================
    # GRUPO COM SUBGRUPOS
    # ==============================================================

    for subgrupo in subgrupos:

        processar_subgrupo(
            grupo=grupo,
            subgrupo=subgrupo["name"],
            pasta_id=subgrupo["id"],
        )


def main():

    if not ROOT_FOLDER_ID:
        raise ValueError(
            "GOOGLE_DRIVE_FOLDER_ID não configurado "
            "no arquivo .env."
        )

    print("=" * 70)
    print("IMPORTAÇÃO DE COLETAS DO GOOGLE DRIVE")
    print("=" * 70)

    print(
        f"Folder ID: {ROOT_FOLDER_ID}"
    )

    # ==============================================================
    # LOCALIZAR "COLETAS"
    # ==============================================================

    pastas = listar_pastas(
        ROOT_FOLDER_ID
    )

    coletas = None

    for pasta in pastas:

        if pasta["name"].lower() == "coletas":
            coletas = pasta
            break

    if coletas is None:
        raise ValueError(
            "Pasta 'Coletas' não encontrada "
            "no Google Drive."
        )

    print(
        f"Pasta Coletas: "
        f"{coletas['id']}"
    )

    # ==============================================================
    # LOCALIZAR GRUPOS
    # ==============================================================

    grupos = listar_pastas(
        coletas["id"]
    )

    grupos = [
        grupo
        for grupo in grupos
        if grupo["name"] in GRUPOS
    ]

    grupos.sort(
        key=lambda x: x["name"]
    )

    print(
        f"Grupos encontrados: "
        f"{len(grupos)}"
    )

    # ==============================================================
    # PROCESSAR GRUPOS
    # ==============================================================

    for grupo in grupos:

        processar_grupo(
            grupo=grupo["name"],
            pasta_id=grupo["id"],
        )

    print()
    print("=" * 70)
    print("IMPORTAÇÃO FINALIZADA")
    print("=" * 70)


if __name__ == "__main__":
    main()
