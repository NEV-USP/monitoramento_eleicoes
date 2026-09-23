import pandas as pd
import unicodedata
import re

from sqlalchemy import text

from database.connection import engine


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_nome(nome):
    if pd.isna(nome):
        return ""

    nome = str(nome)

    nome = unicodedata.normalize("NFKD", nome)
    nome = nome.encode("ascii", "ignore").decode("utf-8")

    nome = nome.lower()

    nome = re.sub(r"[^a-z0-9\s]", "", nome)
    nome = re.sub(r"\s+", " ", nome).strip()

    return nome


# ============================================================
# DADOS GERAIS
# ============================================================

def carregar_dados_gerais():
    sql = text("""
        WITH metricas_recentes AS (
            SELECT
                mp.perfil_id,
                mp.coleta_id,
                mp.seguidores,
                mp.numero_posts,
                mp.likes,
                mp.comentarios,
                mp.reacoes_comentarios_compartilhamentos,
                mp.taxa_interacao,
                mp.alcance_dia,
                mp.page_performance_index,
                mp.visualizacoes_perfil,

                co.subgrupo,
                co.data_inicio,
                co.data_fim,

                ROW_NUMBER() OVER (
                    PARTITION BY mp.perfil_id
                    ORDER BY
                        co.data_fim DESC,
                        co.id DESC
                ) AS rn

            FROM metricas_perfil mp

            INNER JOIN coletas co
                ON co.id = mp.coleta_id
        )

        SELECT
            c.profile_padronizado AS "Profile_padronizado",
            c.cargo AS "Cargo",

            mr.subgrupo AS "Subgrupo",

            ps.profile AS "Profile",
            ps.network AS "Social network",
            ps.profile_id AS "Profile-ID",
            ps.link AS "Link",

            mr.seguidores AS "Seguidores",
            mr.numero_posts AS "Numero_Posts",
            mr.likes AS "Likes",
            mr.comentarios AS "Comentarios",

            mr.reacoes_comentarios_compartilhamentos
                AS "Interacoes",

            mr.taxa_interacao AS "Taxa_Interacao",
            mr.alcance_dia AS "Alcance_Dia",

            mr.page_performance_index
                AS "Page_Performance_Index",

            mr.visualizacoes_perfil
                AS "Visualizacoes_Perfil",

            mr.data_inicio AS "Data_Inicio",
            mr.data_fim AS "Data_Fim"

        FROM metricas_recentes mr

        INNER JOIN perfis_sociais ps
            ON ps.id = mr.perfil_id

        INNER JOIN candidatos c
            ON c.id = ps.candidato_id

        WHERE mr.rn = 1
    """)

    with engine.connect() as connection:
        df = pd.read_sql(sql, connection)

    df["Seguidores"] = (
        pd.to_numeric(
            df["Seguidores"],
            errors="coerce"
        ).fillna(0)
    )

    df["Interacoes"] = (
        pd.to_numeric(
            df["Interacoes"],
            errors="coerce"
        ).fillna(0)
    )

    df["Engajamento"] = pd.to_numeric(
        (
            df["Interacoes"]
            .div(
                df["Seguidores"].replace(
                    0,
                    pd.NA
                )
            )
            .fillna(0)
        )
    ).fillna(0)

    df["Profile_normalizado"] = (
        df["Profile"]
        .apply(normalizar_nome)
    )

    return df


# ============================================================
# POSTS
# ============================================================

def carregar_posts():
    sql = text("""
        SELECT
            p.id AS "Post-ID",
            p.message_id AS "Message-ID",
            p.data AS "Date",
            p.message AS "Message",
            p.link AS "Link",
            p.external_links AS "External Links",
            p.image_link AS "Image Link",

            ps.profile AS "Profile",
            ps.network AS "Social network",
            ps.profile_id AS "Profile-ID",

            c.profile_padronizado AS "Profile_padronizado",
            c.cargo AS "Cargo",

            co.id AS "Coleta_ID",
            co.semana AS "Semana",
            co.subgrupo AS "Subgrupo",
            co.data_inicio AS "Data_Inicio",
            co.data_fim AS "Data_Fim",

            mp.likes AS "Likes",
            mp.comentarios AS "Comentarios",
            mp.reacoes_comentarios_compartilhamentos
                AS "Interacoes",
            mp.taxa_interacao AS "Taxa_Interacao",
            mp.alcance_post AS "Alcance_Post",
            mp.interacoes_impressao_visualizacao
                AS "Interacoes_Impressao",
            mp.sentimento_negativo_comentarios
                AS "Sentimento_Negativo"

        FROM posts p

        INNER JOIN perfis_sociais ps
            ON ps.id = p.perfil_id

        INNER JOIN candidatos c
            ON c.id = ps.candidato_id

        INNER JOIN metricas_posts mp
            ON mp.post_id = p.id

        INNER JOIN coletas co
            ON co.id = mp.coleta_id

        ORDER BY
            co.data_inicio DESC,
            p.data DESC NULLS LAST
    """)

    with engine.connect() as connection:
        posts = pd.read_sql(sql, connection)

    # --------------------------------------------------------
    # Tipos numéricos
    # --------------------------------------------------------

    colunas_numericas = [
        "Likes",
        "Comentarios",
        "Interacoes",
        "Taxa_Interacao",
        "Alcance_Post",
        "Interacoes_Impressao",
        "Sentimento_Negativo"
    ]

    for coluna in colunas_numericas:
        posts[coluna] = pd.to_numeric(
            posts[coluna],
            errors="coerce"
        ).fillna(0)

    # --------------------------------------------------------
    # Datas
    # --------------------------------------------------------

    posts["Date"] = pd.to_datetime(
        posts["Date"],
        errors="coerce"
    )

    posts["Data_Inicio"] = pd.to_datetime(
        posts["Data_Inicio"],
        errors="coerce"
    )

    posts["Data_Fim"] = pd.to_datetime(
        posts["Data_Fim"],
        errors="coerce"
    )

    # --------------------------------------------------------
    # Texto
    # --------------------------------------------------------

    posts["Message"] = (
        posts["Message"]
        .fillna("")
        .astype(str)
    )

    posts["Profile_padronizado"] = (
        posts["Profile_padronizado"]
        .fillna("")
        .astype(str)
    )

    posts["Profile_normalizado"] = (
        posts["Profile"]
        .fillna("")
        .astype(str)
        .apply(normalizar_nome)
    )

    return posts


def carregar_historico():
    sql = text("""
        SELECT
            c.profile_padronizado AS "Profile_padronizado",
            c.cargo AS "Cargo",

            co.subgrupo AS "Subgrupo",

            ps.profile AS "Profile",
            ps.network AS "Social network",
            ps.profile_id AS "Profile-ID",

            co.id AS "Coleta_ID",
            co.semana AS "Semana",
            co.data_inicio AS "Data_Inicio",
            co.data_fim AS "Data_Fim",

            mp.seguidores AS "Seguidores",
            mp.numero_posts AS "Numero_Posts",
            mp.likes AS "Likes",
            mp.comentarios AS "Comentarios",

            mp.reacoes_comentarios_compartilhamentos
                AS "Interacoes",

            mp.taxa_interacao AS "Taxa_Interacao",
            mp.alcance_dia AS "Alcance_Dia",

            mp.page_performance_index
                AS "Page_Performance_Index",

            mp.visualizacoes_perfil
                AS "Visualizacoes_Perfil"

        FROM metricas_perfil mp

        INNER JOIN coletas co
            ON co.id = mp.coleta_id

        INNER JOIN perfis_sociais ps
            ON ps.id = mp.perfil_id

        INNER JOIN candidatos c
            ON c.id = ps.candidato_id

        ORDER BY
            co.data_inicio,
            c.profile_padronizado,
            ps.network
    """)

    with engine.connect() as connection:
        df = pd.read_sql(sql, connection)

    colunas_numericas = [
        "Seguidores",
        "Numero_Posts",
        "Likes",
        "Comentarios",
        "Interacoes",
        "Taxa_Interacao",
        "Alcance_Dia",
        "Page_Performance_Index",
        "Visualizacoes_Perfil"
    ]

    for coluna in colunas_numericas:
        df[coluna] = pd.to_numeric(
            df[coluna],
            errors="coerce"
        ).fillna(0)

    df["Data_Inicio"] = pd.to_datetime(
        df["Data_Inicio"],
        errors="coerce"
    )

    df["Data_Fim"] = pd.to_datetime(
        df["Data_Fim"],
        errors="coerce"
    )

    return df