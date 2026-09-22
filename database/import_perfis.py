
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database.connection import engine
from database.preprocess import (
    preparar_metrics,
    localizar_arquivo,
)


# ============================================================
# CARGO
# ============================================================

def identificar_cargo(grupo):
    """
    Converte o grupo da coleta para o cargo.
    """

    mapa = {
        "Presidenciáveis": "Presidente",
        "Senado": "Senador",
        "Governos": "Governador",
        "Deputados Federais": "Deputado Federal",
    }

    grupo = grupo.strip()

    if grupo not in mapa:
        raise ValueError(
            f"Grupo não reconhecido para identificação do cargo: "
            f"{grupo}"
        )

    return mapa[grupo]


# ============================================================
# CARREGAR CANDIDATOS
# ============================================================

def carregar_candidatos(connection):
    """
    Carrega todos os candidatos existentes em memória.

    Chave:
        (profile_padronizado, cargo)

    Valor:
        id do candidato.
    """

    sql = text("""
        SELECT
            id,
            profile_padronizado,
            cargo
        FROM candidatos
    """)

    resultado = connection.execute(sql)

    candidatos = {}

    for linha in resultado:

        profile = str(
            linha.profile_padronizado
        ).strip()

        cargo = str(
            linha.cargo
        ).strip()

        candidatos[
            (profile, cargo)
        ] = linha.id

    return candidatos


# ============================================================
# CANDIDATOS
# ============================================================

def importar_candidatos(
    connection,
    metrics,
    cargo
):
    """
    Insere os candidatos encontrados no Metrics Overview
    em lote.
    """

    profiles = (
        metrics["Profile"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    profiles = profiles[
        profiles != ""
    ].drop_duplicates()

    if profiles.empty:
        return 0

    dados = [
        {
            "profile_padronizado": profile,
            "cargo": cargo,
        }
        for profile in profiles
    ]

    sql = text("""
        INSERT INTO candidatos (
            profile_padronizado,
            cargo
        )
        VALUES (
            :profile_padronizado,
            :cargo
        )
        ON CONFLICT (
            profile_padronizado,
            cargo
        )
        DO NOTHING
    """)

    connection.execute(
        sql,
        dados
    )

    return len(dados)


# ============================================================
# PERFIS SOCIAIS
# ============================================================

def importar_perfis_sociais(
    connection,
    metrics,
    cargo
):
    """
    Insere/atualiza os perfis sociais em lote.
    """

    # --------------------------------------------------------
    # Carregar candidatos
    # --------------------------------------------------------

    candidatos = carregar_candidatos(
        connection
    )

    print(
        f"Candidatos carregados em memória: "
        f"{len(candidatos)}"
    )

    # --------------------------------------------------------
    # Preparar dados
    # --------------------------------------------------------

    dados = []

    ignorados = 0

    for _, linha in metrics.iterrows():

        profile = linha.get(
            "Profile"
        )

        network = linha.get(
            "Network"
        )

        profile_id = linha.get(
            "Profile-ID"
        )

        link = linha.get(
            "Link"
        )

        # ----------------------------------------------------
        # Validação mínima
        # ----------------------------------------------------

        if pd.isna(profile):
            ignorados += 1
            continue

        if pd.isna(network):
            ignorados += 1
            continue

        profile = str(
            profile
        ).strip()

        network = str(
            network
        ).strip()

        if not profile or not network:
            ignorados += 1
            continue

        # ----------------------------------------------------
        # Profile-ID
        # ----------------------------------------------------

        if pd.isna(profile_id):

            profile_id = None

        else:

            profile_id = str(
                profile_id
            ).strip()

            if not profile_id:
                profile_id = None

        # ----------------------------------------------------
        # Link
        # ----------------------------------------------------

        if pd.isna(link):

            link = None

        else:

            link = str(
                link
            ).strip()

            if not link:
                link = None

        # ----------------------------------------------------
        # Buscar candidato em memória
        # ----------------------------------------------------

        candidato_id = candidatos.get(
            (profile, cargo)
        )

        if candidato_id is None:

            raise ValueError(
                f"Candidato não encontrado: "
                f"profile='{profile}', "
                f"cargo='{cargo}'"
            )

        # ----------------------------------------------------
        # Preparar registro
        # ----------------------------------------------------

        dados.append({
            "candidato_id": candidato_id,
            "profile": profile,
            "network": network,
            "profile_id": profile_id,
            "link": link,
        })

    # --------------------------------------------------------
    # Inserção em lote
    # --------------------------------------------------------

    if dados:

        sql = text("""
            INSERT INTO perfis_sociais (
                candidato_id,
                profile,
                network,
                profile_id,
                link
            )
            VALUES (
                :candidato_id,
                :profile,
                :network,
                :profile_id,
                :link
            )
            ON CONFLICT (
                profile_id,
                network
            )
            DO UPDATE SET
                candidato_id =
                    EXCLUDED.candidato_id,

                profile =
                    EXCLUDED.profile,

                link =
                    EXCLUDED.link
        """)

        connection.execute(
            sql,
            dados
        )

    return len(dados), ignorados


# ============================================================
# IMPORTAÇÃO COMPLETA
# ============================================================

def importar_perfis(pasta):

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

    # Padronização mínima necessária.
    metrics["Profile"] = (
        metrics["Profile"]
        .astype("string")
        .str.strip()
    )

    metrics["Network"] = (
        metrics["Network"]
        .astype("string")
        .str.strip()
    )

    # --------------------------------------------------------
    # Grupo, subgrupo e cargo
    # --------------------------------------------------------

    partes = list(
        pasta.parts
    )

    indice_semana = None

    for i, parte in enumerate(partes):

        if parte.lower().startswith(
            "semana "
        ):

            indice_semana = i
            break

    if indice_semana is None:

        raise ValueError(
            f"Semana não encontrada na pasta: "
            f"{pasta}"
        )

    if indice_semana < 1:

        raise ValueError(
            f"Estrutura de pasta inválida: "
            f"{pasta}"
        )

    pasta_anterior = (
        partes[indice_semana - 1]
    )

    grupos = {
        "Presidenciáveis",
        "Senado",
        "Governos",
        "Deputados Federais",
    }

    if pasta_anterior in grupos:

        grupo = pasta_anterior
        subgrupo = None

    else:

        if indice_semana < 2:

            raise ValueError(
                f"Não foi possível identificar "
                f"o grupo: {pasta}"
            )

        grupo = (
            partes[indice_semana - 2]
        )

        subgrupo = pasta_anterior

        if grupo not in grupos:

            raise ValueError(
                f"Grupo não reconhecido: "
                f"{grupo}"
            )

    cargo = identificar_cargo(
        grupo
    )

    print(
        f"Grupo: {grupo}"
    )

    print(
        f"Subgrupo: {subgrupo}"
    )

    print(
        f"Cargo: {cargo}"
    )

    # --------------------------------------------------------
    # Banco
    # --------------------------------------------------------

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Candidatos
        # ----------------------------------------------------

        candidatos = importar_candidatos(
            connection,
            metrics,
            cargo
        )

        print(
            f"Candidatos processados: "
            f"{candidatos}"
        )

        # ----------------------------------------------------
        # Perfis
        # ----------------------------------------------------

        perfis, ignorados = (
            importar_perfis_sociais(
                connection,
                metrics,
                cargo
            )
        )

        print(
            f"Perfis processados: "
            f"{perfis}"
        )

        print(
            f"Registros ignorados: "
            f"{ignorados}"
        )

    print(
        "\n" + "=" * 70
    )

    print(
        "IMPORTAÇÃO CONCLUÍDA"
    )

    print(
        "=" * 70
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta semanal: "
    ).strip()

    importar_perfis(
        pasta
    )