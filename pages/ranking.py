import pandas as pd


TOP_N_OPTIONS = [
    {"label": "Top 5", "value": 5},
    {"label": "Top 10", "value": 10},
    {"label": "Top 20", "value": 20},
    {"label": "Top 50", "value": 50},
    {"label": "Top 100", "value": 100},
    {"label": "Todos", "value": 0},
]


def obter_top_perfis_por_seguidores(
    df_atual,
    cargo=None,
    subgrupo=None,
    rede=None,
    top_n=10,
):
    """
    Retorna os perfis mais seguidos dentro dos filtros selecionados.

    top_n=10: retorna os 10 primeiros.
    top_n=0: retorna todos.
    """

    if df_atual is None or df_atual.empty:
        return []

    colunas = {
        "Profile_padronizado",
        "Seguidores",
        "Cargo",
        "Subgrupo",
        "Social network",
    }

    if not colunas.issubset(df_atual.columns):
        return []

    dados = df_atual.copy()

    if cargo is not None:
        dados = dados[dados["Cargo"] == cargo]

    if subgrupo is not None:
        dados = dados[dados["Subgrupo"] == subgrupo]

    if rede is not None:
        dados = dados[dados["Social network"] == rede]

    if dados.empty:
        return []

    dados = dados.dropna(
        subset=["Profile_padronizado"]
    ).copy()

    dados["Profile_padronizado"] = (
        dados["Profile_padronizado"]
        .astype(str)
        .str.strip()
    )

    dados = dados[
        dados["Profile_padronizado"] != ""
    ]

    dados["Seguidores"] = pd.to_numeric(
        dados["Seguidores"],
        errors="coerce",
    ).fillna(0)

    ranking = (
        dados
        .groupby(
            "Profile_padronizado",
            as_index=False,
        )
        .agg(
            Seguidores=("Seguidores", "max")
        )
        .sort_values(
            ["Seguidores", "Profile_padronizado"],
            ascending=[False, True],
        )
    )

    # A ausência de valor equivale ao padrão Top 10.
    if top_n is None:
        top_n = 10

    top_n = int(top_n)

    # O valor 0 significa "Todos".
    if top_n > 0:
        ranking = ranking.head(top_n)

    return ranking["Profile_padronizado"].tolist()