
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine
from database.preprocess import (
    preparar_metrics,
    localizar_arquivo,
    extrair_periodo,
    identificar_grupo_subgrupo,
)


# ============================================================
# BUSCAR COLETA
# ============================================================

def buscar_coleta(
    connection,
    grupo,
    subgrupo,
    data_inicio,
    data_fim
):
    """
    Localiza a coleta correspondente ao período informado.
    """

    sql = text("""
        SELECT id
        FROM coletas
        WHERE grupo = :grupo
          AND (
              subgrupo = :subgrupo
              OR (
                  subgrupo IS NULL
                  AND :subgrupo IS NULL
              )
          )
          AND data_inicio = :data_inicio
          AND data_fim = :data_fim
    """)

    resultado = connection.execute(
        sql,
        {
            "grupo": grupo,
            "subgrupo": subgrupo,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        }
    )

    coleta_id = resultado.scalar_one_or_none()

    if coleta_id is None:
        raise ValueError(
            "Coleta não encontrada no banco.\n"
            f"Grupo: {grupo}\n"
            f"Subgrupo: {subgrupo}\n"
            f"Data inicial: {data_inicio}\n"
            f"Data final: {data_fim}\n\n"
            "Execute primeiro o importador de coletas."
        )

    return coleta_id


# ============================================================
# CARREGAR PERFIS
# ============================================================

def carregar_perfis(connection):
    """
    Carrega todos os perfis sociais uma única vez.

    Retorna:

        {
            (profile_id, network): perfil_id
        }
    """

    sql = text("""
        SELECT id, profile_id, network
        FROM perfis_sociais
        WHERE profile_id IS NOT NULL
    """)

    resultado = connection.execute(sql)

    perfis = {}

    for linha in resultado:

        profile_id = str(
            linha.profile_id
        ).strip()

        network = str(
            linha.network
        ).strip()

        perfis[
            (profile_id, network)
        ] = linha.id

    return perfis


# ============================================================
# CONVERSÃO DE VALORES
# ============================================================

def valor_inteiro(valor):
    """
    Converte valores numéricos para inteiro ou None.
    """

    if pd.isna(valor):
        return None

    valor = pd.to_numeric(
        valor,
        errors="coerce"
    )

    if pd.isna(valor):
        return None

    return int(round(valor))


def valor_decimal(valor):
    """
    Converte valores numéricos para float ou None.
    """

    if pd.isna(valor):
        return None

    valor = pd.to_numeric(
        valor,
        errors="coerce"
    )

    if pd.isna(valor):
        return None

    return float(valor)


def valor_texto(valor):
    """
    Converte valores textuais para string ou None.
    """

    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    return valor


# ============================================================
# IMPORTAR LOTE
# ============================================================

def importar_lote(connection, sql, dados):
    """
    Insere/atualiza um lote de métricas.
    """

    if not dados:
        return 0

    connection.execute(
        sql,
        dados
    )

    return len(dados)


# ============================================================
# SQL DAS MÉTRICAS
# ============================================================

SQL_METRICAS = text("""
    INSERT INTO metricas_perfil (
        perfil_id,
        coleta_id,
        seguidores,
        numero_posts,
        likes,
        comentarios,
        taxa_interacao,
        alcance_dia,
        page_performance_index,
        reacoes_comentarios_compartilhamentos,
        visualizacoes_perfil,
        external_links,
        image_link
    )
    VALUES (
        :perfil_id,
        :coleta_id,
        :seguidores,
        :numero_posts,
        :likes,
        :comentarios,
        :taxa_interacao,
        :alcance_dia,
        :page_performance_index,
        :reacoes_comentarios_compartilhamentos,
        :visualizacoes_perfil,
        :external_links,
        :image_link
    )
    ON CONFLICT (
        perfil_id,
        coleta_id
    )
    DO UPDATE SET
        seguidores =
            EXCLUDED.seguidores,

        numero_posts =
            EXCLUDED.numero_posts,

        likes =
            EXCLUDED.likes,

        comentarios =
            EXCLUDED.comentarios,

        taxa_interacao =
            EXCLUDED.taxa_interacao,

        alcance_dia =
            EXCLUDED.alcance_dia,

        page_performance_index =
            EXCLUDED.page_performance_index,

        reacoes_comentarios_compartilhamentos =
            EXCLUDED.reacoes_comentarios_compartilhamentos,

        visualizacoes_perfil =
            EXCLUDED.visualizacoes_perfil,

        external_links =
            EXCLUDED.external_links,

        image_link =
            EXCLUDED.image_link
""")


# ============================================================
# IMPORTAÇÃO VIA DATAFRAME
# ============================================================

def importar_metricas_perfil_dataframe(
    metrics,
    grupo,
    subgrupo,
    data_inicio,
    data_fim
):
    """
    Importa métricas de perfil a partir de um DataFrame
    já preparado.

    Parâmetros
    ----------
    metrics : pandas.DataFrame
        DataFrame preparado do Metrics Overview.

    grupo : str
        Grupo da coleta.

    subgrupo : str ou None
        Subgrupo da coleta.

    data_inicio : date
        Data inicial da coleta.

    data_fim : date
        Data final da coleta.
    """

    if metrics.empty:
        raise ValueError(
            "DataFrame de Metrics está vazio."
        )

    colunas_obrigatorias = {
        "Profile-ID",
        "Network",
        "Follower",
        "Number of posts",
        "Number of Likes",
        "Number of comments",
        "Post interaction rate",
        "Reach per day",
        "Page Performance Index",
        "Reactions, Comments & Shares",
        "Profile Views",
        "External Links",
        "Image Link",
    }

    colunas_faltantes = (
        colunas_obrigatorias
        - set(metrics.columns)
    )

    if colunas_faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes no Metrics: "
            + ", ".join(
                sorted(colunas_faltantes)
            )
        )

    print(
        f"Registros encontrados: {len(metrics)}"
    )

    # --------------------------------------------------------
    # Banco
    # --------------------------------------------------------

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Coleta
        # ----------------------------------------------------

        coleta_id = buscar_coleta(
            connection,
            grupo,
            subgrupo,
            data_inicio,
            data_fim
        )

        print(
            f"Coleta ID: {coleta_id}"
        )

        # ----------------------------------------------------
        # Carregar perfis
        # ----------------------------------------------------

        perfis = carregar_perfis(
            connection
        )

        print(
            f"Perfis carregados em memória: "
            f"{len(perfis)}"
        )

        # ----------------------------------------------------
        # Preparar registros
        # ----------------------------------------------------

        dados_lote = []

        ignorados = 0

        for _, linha in metrics.iterrows():

            profile_id = valor_texto(
                linha.get("Profile-ID")
            )

            network = valor_texto(
                linha.get("Network")
            )

            # ------------------------------------------------
            # Identificação mínima
            # ------------------------------------------------

            if not profile_id or not network:

                ignorados += 1

                print(
                    "Ignorado: "
                    "Profile-ID ou Network vazio."
                )

                continue

            # ------------------------------------------------
            # Buscar perfil
            # ------------------------------------------------

            perfil_id = perfis.get(
                (profile_id, network)
            )

            if perfil_id is None:

                raise ValueError(
                    "Perfil social não encontrado.\n"
                    f"Profile-ID: {profile_id}\n"
                    f"Network: {network}\n"
                    "Execute primeiro o importador "
                    "de candidatos/perfis."
                )

            # ------------------------------------------------
            # Preparar dados
            # ------------------------------------------------

            dados_lote.append({

                "perfil_id":
                    perfil_id,

                "coleta_id":
                    coleta_id,

                "seguidores":
                    valor_inteiro(
                        linha.get("Follower")
                    ),

                "numero_posts":
                    valor_inteiro(
                        linha.get("Number of posts")
                    ),

                "likes":
                    valor_inteiro(
                        linha.get("Number of Likes")
                    ),

                "comentarios":
                    valor_inteiro(
                        linha.get("Number of comments")
                    ),

                "taxa_interacao":
                    valor_decimal(
                        linha.get(
                            "Post interaction rate"
                        )
                    ),

                "alcance_dia":
                    valor_decimal(
                        linha.get("Reach per day")
                    ),

                "page_performance_index":
                    valor_decimal(
                        linha.get(
                            "Page Performance Index"
                        )
                    ),

                "reacoes_comentarios_compartilhamentos":
                    valor_inteiro(
                        linha.get(
                            "Reactions, Comments & Shares"
                        )
                    ),

                "visualizacoes_perfil":
                    valor_inteiro(
                        linha.get(
                            "Profile Views"
                        )
                    ),

                "external_links":
                    valor_texto(
                        linha.get(
                            "External Links"
                        )
                    ),

                "image_link":
                    valor_texto(
                        linha.get(
                            "Image Link"
                        )
                    ),
            })

        # ----------------------------------------------------
        # Inserção
        # ----------------------------------------------------

        importados = importar_lote(
            connection,
            SQL_METRICAS,
            dados_lote
        )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print(
        "\n" + "=" * 70
    )

    print(
        "IMPORTAÇÃO DE MÉTRICAS CONCLUÍDA"
    )

    print(
        "=" * 70
    )

    print(
        f"Registros importados/atualizados: "
        f"{importados}"
    )

    print(
        f"Registros ignorados: {ignorados}"
    )

    return importados, ignorados


# ============================================================
# IMPORTAÇÃO VIA PASTA LOCAL
# ============================================================

def importar_metricas_perfil(pasta):

    pasta = Path(pasta)

    # --------------------------------------------------------
    # Arquivo
    # --------------------------------------------------------

    benchmarking = localizar_arquivo(
        pasta,
        "Benchmarking"
    )

    print(
        f"\nArquivo: {benchmarking.name}"
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    metrics = preparar_metrics(
        benchmarking
    )

    # --------------------------------------------------------
    # Período
    # --------------------------------------------------------

    periodo = extrair_periodo(
        pasta
    )

    # --------------------------------------------------------
    # Grupo / subgrupo
    # --------------------------------------------------------

    grupo, subgrupo = (
        identificar_grupo_subgrupo(
            pasta
        )
    )

    # --------------------------------------------------------
    # Importação
    # --------------------------------------------------------

    return importar_metricas_perfil_dataframe(
        metrics=metrics,
        grupo=grupo,
        subgrupo=subgrupo,
        data_inicio=periodo["data_inicio"],
        data_fim=periodo["data_fim"],
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta semanal: "
    ).strip()

    importar_metricas_perfil(
        pasta
    )