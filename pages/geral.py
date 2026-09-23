
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ============================================================
# ESTILOS
# ============================================================

CARD_STYLE = {
    "backgroundColor": "#ffffff",
    "padding": "20px",
    "borderRadius": "10px",
    "boxShadow": "0px 2px 8px rgba(0,0,0,0.08)",
    "marginBottom": "20px"
}

FILTER_LABEL_STYLE = {
    "fontWeight": "bold",
    "marginBottom": "5px",
    "display": "block"
}


# ============================================================
# GRÁFICO TEMPORAL
# ============================================================

def criar_grafico_temporal(
    df,
    coluna,
    titulo,
    ylabel=None
):
    if df.empty:
        return go.Figure()

    dados = (
        df.groupby(
            ["Data_Inicio", "Profile_padronizado"],
            as_index=False
        )[coluna]
        .sum()
    )

    fig = px.line(
        dados,
        x="Data_Inicio",
        y=coluna,
        color="Profile_padronizado",
        markers=True,
        title=titulo
    )

    fig.update_layout(
        xaxis_title="Período",
        yaxis_title=ylabel or coluna,
        legend_title="Candidato",
        hovermode="x unified"
    )

    return fig


# ============================================================
# LAYOUT
# ============================================================

def layout(redes, cargos):

    cargo_inicial = (
        sorted(cargos)[0]
        if len(cargos) > 0
        else None
    )

    rede_inicial = (
        sorted(redes)[0]
        if len(redes) > 0
        else None
    )

    return html.Div([

        # ====================================================
        # FILTROS
        # ====================================================

        html.Div([

            html.H3(
                "Filtros",
                style={
                    "marginTop": 0,
                    "marginBottom": "20px"
                }
            ),

            # ------------------------------------------------
            # CARGO
            # ------------------------------------------------

            html.Div([
                html.Label(
                    "Cargo",
                    style=FILTER_LABEL_STYLE
                ),

                dcc.Dropdown(
                    id="filtro_cargo",
                    options=[
                        {
                            "label": cargo,
                            "value": cargo
                        }
                        for cargo in sorted(cargos)
                    ],
                    value=cargo_inicial,
                    clearable=False
                )

            ], style={"marginBottom": "15px"}),

            # ------------------------------------------------
            # SUBGRUPO
            # ------------------------------------------------

            html.Div(
                id="container_subgrupo",
                children=[

                    html.Label(
                        "Subgrupo",
                        style=FILTER_LABEL_STYLE
                    ),

                    dcc.Dropdown(
                        id="filtro_subgrupo",
                        options=[],
                        value=None,
                        clearable=False
                    )

                ],
                style={
                    "display": "none",
                    "marginBottom": "15px"
                }
            ),

            # ------------------------------------------------
            # REDE SOCIAL
            # ------------------------------------------------

            html.Div([

                html.Label(
                    "Rede Social",
                    style=FILTER_LABEL_STYLE
                ),

                dcc.Dropdown(
                    id="filtro_rede",
                    options=[
                        {
                            "label": rede,
                            "value": rede
                        }
                        for rede in sorted(redes)
                    ],
                    value=rede_inicial,
                    clearable=False
                )

            ], style={"marginBottom": "15px"}),

            # ------------------------------------------------
            # CANDIDATO
            # ------------------------------------------------

            html.Div([

                html.Label(
                    "Candidato",
                    style=FILTER_LABEL_STYLE
                ),

                dcc.Dropdown(
                    id="filtro_candidato",
                    options=[],
                    value=[],
                    multi=True,
                    clearable=True,
                    placeholder="Selecione um ou mais candidatos"
                )

            ], style={"marginBottom": "15px"}),

            # ------------------------------------------------
            # PERÍODO
            # ------------------------------------------------

            html.Div([

                html.Label(
                    "Período",
                    style=FILTER_LABEL_STYLE
                ),

                dcc.Dropdown(
                    id="filtro_periodo",
                    options=[],
                    value=[],
                    multi=True,
                    clearable=True,
                    placeholder="Selecione um ou mais períodos"
                )

            ])

        ], style=CARD_STYLE),

        # ====================================================
        # EVOLUÇÃO TEMPORAL
        # ====================================================

        html.Div([

            html.H3(
                "Evolução temporal",
                style={"marginTop": 0}
            ),

            dcc.Graph(
                id="grafico_seguidores_temporal"
            ),

            dcc.Graph(
                id="grafico_interacoes_temporal"
            ),

            dcc.Graph(
                id="grafico_engajamento_temporal"
            )

        ], style=CARD_STYLE),

        # ====================================================
        # DESEMPENHO ATUAL
        # ====================================================

        html.Div([

            html.H3(
                "Desempenho atual",
                style={"marginTop": 0}
            ),

            dcc.Graph(
                id="grafico_seguidores_atual"
            ),

            dcc.Graph(
                id="grafico_interacoes_atual"
            ),

            dcc.Graph(
                id="grafico_engajamento_atual"
            ),

            dcc.Graph(
                id="grafico_scatter_atual"
            ),

            dcc.Graph(
                id="grafico_heatmap_atual"
            ),

            dcc.Graph(
                id="grafico_rede_atual"
            ),

            dcc.Graph(
                id="grafico_cargo_atual"
            )

        ], style=CARD_STYLE)

    ])


# ============================================================
# CALLBACKS
# ============================================================

def register_callbacks(app, df, historico):

    # ========================================================
    # 1. CARGO → SUBGRUPO
    # ========================================================

    @app.callback(
        Output("container_subgrupo", "style"),
        Output("filtro_subgrupo", "options"),
        Output("filtro_subgrupo", "value"),

        Input("filtro_cargo", "value")
    )
    def atualizar_subgrupos(cargo):

        if not cargo:
            return (
                {"display": "none"},
                [],
                None
            )

        dados = historico[
            historico["Cargo"] == cargo
        ].copy()

        subgrupos = sorted(
            dados["Subgrupo"]
            .dropna()
            .unique()
        )

        # Cargo sem subgrupo
        if not subgrupos:
            return (
                {"display": "none"},
                [],
                None
            )

        opcoes = [
            {
                "label": subgrupo,
                "value": subgrupo
            }
            for subgrupo in subgrupos
        ]

        return (
            {
                "display": "block",
                "marginBottom": "15px"
            },
            opcoes,
            subgrupos[0]
        )


    # ========================================================
    # 2. CARGO + SUBGRUPO → REDE SOCIAL
    # ========================================================

    @app.callback(
        Output("filtro_rede", "options"),
        Output("filtro_rede", "value"),

        Input("filtro_cargo", "value"),
        Input("filtro_subgrupo", "value")
    )
    def atualizar_redes(cargo, subgrupo):

        if not cargo:
            return [], None

        dados = historico[
            historico["Cargo"] == cargo
        ].copy()

        # Se o cargo possuir subgrupo, aplica o filtro.
        subgrupos = (
            dados["Subgrupo"]
            .dropna()
            .unique()
        )

        if len(subgrupos) > 0:

            if not subgrupo:
                return [], None

            dados = dados[
                dados["Subgrupo"] == subgrupo
            ]

        redes_disponiveis = sorted(
            dados["Social network"]
            .dropna()
            .unique()
        )

        opcoes = [
            {
                "label": rede,
                "value": rede
            }
            for rede in redes_disponiveis
        ]

        valor = (
            redes_disponiveis[0]
            if redes_disponiveis
            else None
        )

        return opcoes, valor


    # ========================================================
    # 3. CARGO + SUBGRUPO + REDE
    #    → CANDIDATOS + PERÍODOS
    # ========================================================

    @app.callback(
        Output("filtro_candidato", "options"),
        Output("filtro_candidato", "value"),
        Output("filtro_periodo", "options"),
        Output("filtro_periodo", "value"),

        Input("filtro_cargo", "value"),
        Input("filtro_subgrupo", "value"),
        Input("filtro_rede", "value")
    )
    def atualizar_candidatos_periodos(
        cargo,
        subgrupo,
        rede
    ):

        if not cargo or not rede:
            return [], [], [], []

        dados = historico[
            historico["Cargo"] == cargo
        ].copy()

        # ----------------------------------------------------
        # SUBGRUPO
        # ----------------------------------------------------

        subgrupos = (
            dados["Subgrupo"]
            .dropna()
            .unique()
        )

        if len(subgrupos) > 0:

            if not subgrupo:
                return [], [], [], []

            dados = dados[
                dados["Subgrupo"] == subgrupo
            ]

        # ----------------------------------------------------
        # REDE
        # ----------------------------------------------------

        dados = dados[
            dados["Social network"] == rede
        ].copy()

        if dados.empty:
            return [], [], [], []

        # ----------------------------------------------------
        # CANDIDATOS
        # ----------------------------------------------------

        candidatos = sorted(
            dados["Profile_padronizado"]
            .dropna()
            .unique()
        )

        opcoes_candidatos = [
            {
                "label": candidato,
                "value": candidato
            }
            for candidato in candidatos
        ]

        # ----------------------------------------------------
        # PERÍODOS
        # ----------------------------------------------------

        periodos = (
            dados[
                ["Data_Inicio", "Data_Fim"]
            ]
            .dropna()
            .drop_duplicates()
            .sort_values("Data_Inicio")
        )

        opcoes_periodos = []

        for _, periodo in periodos.iterrows():

            inicio = periodo["Data_Inicio"]
            fim = periodo["Data_Fim"]

            opcoes_periodos.append({
                "label": (
                    f"Semana {inicio.strftime('%d/%m')} "
                    f"— {fim.strftime('%d/%m/%Y')}"
                ),
                "value": inicio.strftime("%Y-%m-%d")
            })

        return (
            opcoes_candidatos,
            [],
            opcoes_periodos,
            []
        )


    # ========================================================
    # 4. EVOLUÇÃO TEMPORAL
    # ========================================================

    @app.callback(
        Output(
            "grafico_seguidores_temporal",
            "figure"
        ),
        Output(
            "grafico_interacoes_temporal",
            "figure"
        ),
        Output(
            "grafico_engajamento_temporal",
            "figure"
        ),

        Input("filtro_cargo", "value"),
        Input("filtro_subgrupo", "value"),
        Input("filtro_rede", "value"),
        Input("filtro_candidato", "value"),
        Input("filtro_periodo", "value")
    )
    def atualizar_graficos_temporais(
        cargo,
        subgrupo,
        rede,
        candidatos,
        periodos
    ):

        dados = historico.copy()

        # ----------------------------------------------------
        # CARGO
        # ----------------------------------------------------

        if cargo:
            dados = dados[
                dados["Cargo"] == cargo
            ]

        # ----------------------------------------------------
        # SUBGRUPO
        # ----------------------------------------------------

        if subgrupo:
            dados = dados[
                dados["Subgrupo"] == subgrupo
            ]

        # ----------------------------------------------------
        # REDE
        # ----------------------------------------------------

        if rede:
            dados = dados[
                dados["Social network"] == rede
            ]

        # ----------------------------------------------------
        # CANDIDATOS
        # ----------------------------------------------------

        if candidatos:
            dados = dados[
                dados["Profile_padronizado"].isin(
                    candidatos
                )
            ]

        # ----------------------------------------------------
        # PERÍODOS
        # ----------------------------------------------------

        if periodos:

            periodos_datas = pd.to_datetime(
                periodos,
                errors="coerce"
            )

            dados = dados[
                dados["Data_Inicio"].isin(
                    periodos_datas
                )
            ]

        # ----------------------------------------------------
        # GRÁFICOS
        # ----------------------------------------------------

        grafico_seguidores = criar_grafico_temporal(
            dados,
            "Seguidores",
            "Evolução de seguidores",
            "Seguidores"
        )

        grafico_interacoes = criar_grafico_temporal(
            dados,
            "Interacoes",
            "Evolução de interações",
            "Interações"
        )

        grafico_engajamento = criar_grafico_temporal(
            dados,
            "Taxa_Interacao",
            "Evolução da taxa de interação",
            "Taxa de interação"
        )

        return (
            grafico_seguidores,
            grafico_interacoes,
            grafico_engajamento
        )


    # ========================================================
    # 5. DESEMPENHO ATUAL
    # ========================================================

    @app.callback(
        Output(
            "grafico_seguidores_atual",
            "figure"
        ),
        Output(
            "grafico_interacoes_atual",
            "figure"
        ),
        Output(
            "grafico_engajamento_atual",
            "figure"
        ),
        Output(
            "grafico_scatter_atual",
            "figure"
        ),
        Output(
            "grafico_heatmap_atual",
            "figure"
        ),
        Output(
            "grafico_rede_atual",
            "figure"
        ),
        Output(
            "grafico_cargo_atual",
            "figure"
        ),

        Input("filtro_cargo", "value"),
        Input("filtro_subgrupo", "value"),
        Input("filtro_rede", "value"),
        Input("filtro_candidato", "value")
    )
    def atualizar_desempenho_atual(
        cargo,
        subgrupo,
        rede,
        candidatos
    ):

        dados = df.copy()

        # ----------------------------------------------------
        # CARGO
        # ----------------------------------------------------

        if cargo:
            dados = dados[
                dados["Cargo"] == cargo
            ]

        # ----------------------------------------------------
        # SUBGRUPO
        # ----------------------------------------------------

        if subgrupo:
            dados = dados[
                dados["Subgrupo"] == subgrupo
            ]

        # ----------------------------------------------------
        # REDE
        # ----------------------------------------------------

        if rede:
            dados = dados[
                dados["Social network"] == rede
            ]

        # ----------------------------------------------------
        # CANDIDATOS
        # ----------------------------------------------------

        if candidatos:
            dados = dados[
                dados["Profile_padronizado"].isin(
                    candidatos
                )
            ]

        # ----------------------------------------------------
        # DATAFRAME VAZIO
        # ----------------------------------------------------

        if dados.empty:

            vazio = go.Figure()

            return (
                vazio,
                vazio,
                vazio,
                vazio,
                vazio,
                vazio,
                vazio
            )

        # ====================================================
        # SEGUIDORES
        # ====================================================

        seguidores = (
            dados
            .sort_values("Seguidores", ascending=False)
        )

        grafico_seguidores = px.bar(
            seguidores,
            x="Profile_padronizado",
            y="Seguidores",
            title="Seguidores"
        )

        grafico_seguidores.update_layout(
            xaxis_title="Candidato",
            yaxis_title="Seguidores"
        )

        # ====================================================
        # INTERAÇÕES
        # ====================================================

        interacoes = (
            dados
            .sort_values("Interacoes", ascending=False)
        )

        grafico_interacoes = px.bar(
            interacoes,
            x="Profile_padronizado",
            y="Interacoes",
            title="Interações"
        )

        grafico_interacoes.update_layout(
            xaxis_title="Candidato",
            yaxis_title="Interações"
        )

        # ====================================================
        # ENGAJAMENTO
        # ====================================================

        engajamento = (
            dados
            .sort_values("Engajamento", ascending=False)
        )

        grafico_engajamento = px.bar(
            engajamento,
            x="Profile_padronizado",
            y="Engajamento",
            title="Engajamento"
        )

        grafico_engajamento.update_layout(
            xaxis_title="Candidato",
            yaxis_title="Engajamento"
        )

        # ====================================================
        # SCATTER
        # ====================================================

        grafico_scatter = px.scatter(
            dados,
            x="Seguidores",
            y="Interacoes",
            size="Engajamento",
            hover_name="Profile_padronizado",
            title="Seguidores × Interações"
        )

        grafico_scatter.update_layout(
            xaxis_title="Seguidores",
            yaxis_title="Interações"
        )

        # ====================================================
        # HEATMAP
        # ====================================================

        dados_heatmap = dados[
            [
                "Profile_padronizado",
                "Seguidores",
                "Interacoes",
                "Engajamento"
            ]
        ].copy()

        dados_heatmap = dados_heatmap.set_index(
            "Profile_padronizado"
        )

        grafico_heatmap = px.imshow(
            dados_heatmap,
            text_auto=True,
            aspect="auto",
            title="Indicadores por candidato"
        )

        # ====================================================
        # DESEMPENHO DA REDE SELECIONADA
        # ====================================================

        dados_rede = (
            dados
            .groupby(
                "Social network",
                as_index=False
            )[
                [
                    "Seguidores",
                    "Interacoes"
                ]
            ]
            .sum()
        )

        grafico_rede = px.bar(
            dados_rede,
            x="Social network",
            y=[
                "Seguidores",
                "Interacoes"
            ],
            barmode="group",
            title="Desempenho da Rede Selecionada"
        )

        # ====================================================
        # DESEMPENHO POR CARGO
        # ====================================================

        dados_cargo = (
            dados
            .groupby(
                "Cargo",
                as_index=False
            )[
                [
                    "Seguidores",
                    "Interacoes"
                ]
            ]
            .sum()
        )

        grafico_cargo = px.bar(
            dados_cargo,
            x="Cargo",
            y=[
                "Seguidores",
                "Interacoes"
            ],
            barmode="group",
            title="Desempenho por Cargo"
        )

        return (
            grafico_seguidores,
            grafico_interacoes,
            grafico_engajamento,
            grafico_scatter,
            grafico_heatmap,
            grafico_rede,
            grafico_cargo
        )
