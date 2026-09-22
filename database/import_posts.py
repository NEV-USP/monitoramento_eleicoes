from pathlib import Path

import pandas as pd

from sqlalchemy import text, bindparam
# from sqlalchemy.dialects.postgresql import insert

from database.connection import engine
from database.preprocess import (
    preparar_posts,
    localizar_arquivo,
    extrair_periodo,
    identificar_grupo_subgrupo,
)


TAMANHO_LOTE = 500


def buscar_coleta(connection, pasta):
    periodo = extrair_periodo(pasta)
    grupo, subgrupo = identificar_grupo_subgrupo(pasta)

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
            "data_inicio": periodo["data_inicio"],
            "data_fim": periodo["data_fim"],
        },
    )

    coleta_id = resultado.scalar_one_or_none()

    if coleta_id is None:
        raise ValueError("Coleta não encontrada no banco.")

    return coleta_id


def carregar_perfis(connection):
    sql = text("""
        SELECT
            id,
            profile_id,
            network
        FROM perfis_sociais
        WHERE profile_id IS NOT NULL
    """)

    resultado = connection.execute(sql)

    perfis = {}

    for linha in resultado:
        chave = (
            str(linha.profile_id).strip(),
            str(linha.network).strip(),
        )

        perfis[chave] = linha.id

    return perfis


def valor_texto(valor):
    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    return valor


def valor_inteiro(valor):
    if pd.isna(valor):
        return None

    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor):
        return None

    return int(round(valor))


def valor_decimal(valor):
    if pd.isna(valor):
        return None

    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor):
        return None

    return float(valor)


def valor_data(valor):
    if pd.isna(valor):
        return None

    data = pd.to_datetime(valor, errors="coerce")

    if pd.isna(data):
        return None

    return data.to_pydatetime()


def preparar_linha(linha, perfis):
    profile_id = valor_texto(linha.get("Profile-ID"))
    network = valor_texto(linha.get("Network"))

    if not profile_id or not network:
        return None

    perfil_id = perfis.get((profile_id, network))

    if perfil_id is None:
        raise ValueError(
            "Perfil social não encontrado.\n"
            f"Profile-ID: {profile_id}\n"
            f"Network: {network}"
        )

    return {
        "perfil_id": perfil_id,
        "message_id": valor_texto(linha.get("Message-ID")),
        "data": valor_data(linha.get("Date")),
        "message": valor_texto(linha.get("Message")),
        "link": valor_texto(linha.get("Link")),
        "external_links": valor_texto(linha.get("External Links")),
        "image_link": valor_texto(linha.get("Image Link")),
        "likes": valor_inteiro(linha.get("Number of Likes")),
        "comentarios": valor_inteiro(linha.get("Number of comments")),
        "reacoes_comentarios_compartilhamentos": valor_inteiro(
            linha.get("Reactions, Comments & Shares")
        ),
        "taxa_interacao": valor_decimal(
            linha.get("Post interaction rate")
        ),
        "alcance_post": valor_decimal(
            linha.get("Reach per post")
        ),
        "interacoes_impressao_visualizacao": valor_decimal(
            linha.get("Interactions per impression/view")
        ),
        "sentimento_negativo_comentarios": valor_decimal(
            linha.get("Post comments negative sentiment share")
        ),
    }


def importar_lote(connection, lote, coleta_id):
    """
    Insere/atualiza um lote de posts e suas métricas.

    Estratégia:
    1. Upsert dos posts em lote.
    2. Busca dos IDs dos posts em uma única consulta.
    3. Upsert das métricas em lote.
    """

    # ==============================================================
    # 1. POSTS
    # ==============================================================

    dados_posts = [
        {
            "perfil_id": item["perfil_id"],
            "message_id": item["message_id"],
            "data": item["data"],
            "message": item["message"],
            "link": item["link"],
            "external_links": item["external_links"],
            "image_link": item["image_link"],
        }
        for item in lote
        if item["message_id"] is not None
    ]

    if not dados_posts:
        return 0, 0

    sql_posts = text("""
        INSERT INTO posts (
            perfil_id,
            message_id,
            data,
            message,
            link,
            external_links,
            image_link
        )
        VALUES (
            :perfil_id,
            :message_id,
            :data,
            :message,
            :link,
            :external_links,
            :image_link
        )
        ON CONFLICT (message_id)
        DO UPDATE SET
            perfil_id = EXCLUDED.perfil_id,
            data = EXCLUDED.data,
            message = EXCLUDED.message,
            link = EXCLUDED.link,
            external_links = EXCLUDED.external_links,
            image_link = EXCLUDED.image_link
    """)

    connection.execute(
        sql_posts,
        dados_posts
    )

    # ==============================================================
    # 2. RECUPERAR IDS DOS POSTS
    # ==============================================================

    message_ids = [
        item["message_id"]
        for item in dados_posts
    ]

    sql_buscar_ids = text("""
        SELECT
            id,
            message_id
        FROM posts
        WHERE message_id IN :message_ids
    """).bindparams(
        bindparam(
            "message_ids",
            expanding=True
        )
    )

    resultado = connection.execute(
        sql_buscar_ids,
        {
            "message_ids": message_ids
        }
    )

    posts_ids = {
        row.message_id: row.id
        for row in resultado
    }

    # ==============================================================
    # 3. PREPARAR MÉTRICAS
    # ==============================================================

    dados_metricas = []

    for item in lote:

        message_id = item["message_id"]

        if message_id is None:
            continue

        post_id = posts_ids.get(message_id)

        if post_id is None:
            raise ValueError(
                "Não foi possível encontrar o post após a importação.\n"
                f"Message-ID: {message_id}"
            )

        dados_metricas.append(
            {
                "post_id": post_id,
                "coleta_id": coleta_id,
                "likes": item["likes"],
                "comentarios": item["comentarios"],
                "reacoes_comentarios_compartilhamentos":
                    item[
                        "reacoes_comentarios_compartilhamentos"
                    ],
                "taxa_interacao":
                    item["taxa_interacao"],
                "alcance_post":
                    item["alcance_post"],
                "interacoes_impressao_visualizacao":
                    item[
                        "interacoes_impressao_visualizacao"
                    ],
                "sentimento_negativo_comentarios":
                    item[
                        "sentimento_negativo_comentarios"
                    ],
            }
        )

    # ==============================================================
    # 4. MÉTRICAS EM LOTE
    # ==============================================================

    if dados_metricas:

        sql_metricas = text("""
            INSERT INTO metricas_posts (
                post_id,
                coleta_id,
                likes,
                comentarios,
                reacoes_comentarios_compartilhamentos,
                taxa_interacao,
                alcance_post,
                interacoes_impressao_visualizacao,
                sentimento_negativo_comentarios
            )
            VALUES (
                :post_id,
                :coleta_id,
                :likes,
                :comentarios,
                :reacoes_comentarios_compartilhamentos,
                :taxa_interacao,
                :alcance_post,
                :interacoes_impressao_visualizacao,
                :sentimento_negativo_comentarios
            )
            ON CONFLICT (post_id, coleta_id)
            DO UPDATE SET
                likes = EXCLUDED.likes,
                comentarios = EXCLUDED.comentarios,
                reacoes_comentarios_compartilhamentos =
                    EXCLUDED.reacoes_comentarios_compartilhamentos,
                taxa_interacao =
                    EXCLUDED.taxa_interacao,
                alcance_post =
                    EXCLUDED.alcance_post,
                interacoes_impressao_visualizacao =
                    EXCLUDED.interacoes_impressao_visualizacao,
                sentimento_negativo_comentarios =
                    EXCLUDED.sentimento_negativo_comentarios
        """)

        connection.execute(
            sql_metricas,
            dados_metricas
        )

    return len(dados_posts), len(dados_metricas)


def importar_posts(pasta):
    pasta = Path(pasta)

    content = localizar_arquivo(pasta, "Content")

    print(f"\nArquivo: {content.name}")

    posts_df = preparar_posts(content)

    print(f"Registros encontrados: {len(posts_df)}")

    with engine.begin() as connection:

        coleta_id = buscar_coleta(
            connection,
            pasta,
        )

        print(f"Coleta ID: {coleta_id}")

        perfis = carregar_perfis(connection)

        print(
            f"Perfis carregados em memória: {len(perfis)}"
        )

        lote = []

        posts_processados = 0
        metricas_processadas = 0
        ignorados = 0

        for _, linha in posts_df.iterrows():

            item = preparar_linha(
                linha,
                perfis,
            )

            if item is None:
                ignorados += 1
                continue

            lote.append(item)

            if len(lote) >= TAMANHO_LOTE:

                posts, metricas = importar_lote(
                    connection,
                    lote,
                    coleta_id,
                )

                posts_processados += posts
                metricas_processadas += metricas

                print(
                    f"  Lote processado: "
                    f"{posts_processados}/{len(posts_df)}"
                )

                lote = []

        # Último lote
        if lote:

            posts, metricas = importar_lote(
                connection,
                lote,
                coleta_id,
            )

            posts_processados += posts
            metricas_processadas += metricas

    print()
    print("=" * 70)
    print("IMPORTAÇÃO DE POSTS CONCLUÍDA")
    print("=" * 70)
    print(f"Posts processados: {posts_processados}")
    print(f"Métricas processadas: {metricas_processadas}")
    print(f"Registros ignorados: {ignorados}")


if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta semanal: "
    ).strip()

    importar_posts(pasta)