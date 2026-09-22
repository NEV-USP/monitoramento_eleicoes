from dash import html, dcc, Input, Output
import plotly.express as px
import pandas as pd


# =========================
# 🎨 ESTILO
# =========================

CARD_STYLE = {
    "backgroundColor": "#ffffff",
    "padding": "15px",
    "borderRadius": "10px",
    "boxShadow": "0px 2px 8px rgba(0,0,0,0.1)",
}

ROW_STYLE = {
    "display": "flex",
    "gap": "20px",
    "marginBottom": "20px"
}

COL_STYLE = {
    "flex": "1"
}

FILTER_STYLE = {
    "backgroundColor": "#f8f9fa",
    "padding": "15px",
    "borderRadius": "10px",
    "marginBottom": "20px"
}


# =========================
# 📊 Layout
# =========================

def layout(redes, cargos):

    redes = list(redes)
    cargos = list(cargos)

    return html.Div([

        html.H1(
            "📊 Dashboard de Redes Sociais",
            style={"marginBottom": "20px"}
        ),

        # =========================
        # 🎛️ Filtros
        # =========================

        html.Div([

            html.H3("Filtros"),

            html.Label("Cargo"),

            dcc.Dropdown(
                options=[
                    {
                        "label": cargo,
                        "value": cargo
                    }
                    for cargo in cargos
                ] + [
                    {
                        "label": "Todos",
                        "value": "Todos"
                    }
                ],
                value="Todos",
                id="filtro_cargo"
            ),

            html.Br(),

            html.Label("Rede Social"),

            dcc.Dropdown(
                options=[
                    {
                        "label": rede,
                        "value": rede
                    }
                    for rede in redes
                ],
                value=redes[0] if redes else None,
                id="filtro_rede"
            ),

            html.Br(),

            html.Label("Buscar Profile"),

            dcc.Input(
                id="filtro_nome",
                placeholder="Digite o nome do candidato...",
                style={"width": "100%"}
            ),

            html.Br(),
            html.Br(),

            html.Label("Top N"),

            dcc.Slider(
                min=5,
                max=30,
                step=5,
                value=10,
                id="top_n",
                marks={
                    i: str(i)
                    for i in range(5, 31, 5)
                }
            )

        ], style=FILTER_STYLE),

        # =========================
        # 📊 LINHA 1
        # =========================

        html.Div([

            html.Div(
                dcc.Graph(id="grafico_seguidores"),
                style=CARD_STYLE | COL_STYLE
            ),

            html.Div(
                dcc.Graph(id="grafico_interacoes"),
                style=CARD_STYLE | COL_STYLE
            ),

        ], style=ROW_STYLE),

        # =========================
        # 📊 LINHA 2
        # =========================

        html.Div([

            html.Div(
                dcc.Graph(id="grafico_engajamento"),
                style=CARD_STYLE | COL_STYLE
            ),

            html.Div(
                dcc.Graph(id="grafico_scatter"),
                style=CARD_STYLE | COL_STYLE
            ),

        ], style=ROW_STYLE),

        # =========================
        # 📊 LINHA 3
        # =========================

        html.Div([

            html.Div(
                dcc.Graph(id="grafico_heatmap"),
                style=CARD_STYLE | COL_STYLE
            ),

            html.Div(
                dcc.Graph(id="grafico_comparativo"),
                style=CARD_STYLE | COL_STYLE
            ),

        ], style=ROW_STYLE),

        # =========================
        # 📊 LINHA 4
        # =========================

        html.Div([

            html.Div(
                dcc.Graph(id="grafico_cargo"),
                style=CARD_STYLE
            ),

        ])

    ], style={
        "backgroundColor": "#f4f6f9",
        "padding": "20px",
        "fontFamily": "Arial, sans-serif"
    })


# =========================
# 🔄 Callback
# =========================

def register_callbacks(app, df):

    @app.callback(
        Output("grafico_seguidores", "figure"),
        Output("grafico_interacoes", "figure"),
        Output("grafico_engajamento", "figure"),
        Output("grafico_scatter", "figure"),
        Output("grafico_heatmap", "figure"),
        Output("grafico_comparativo", "figure"),
        Output("grafico_cargo", "figure"),
        Input("filtro_cargo", "value"),
        Input("filtro_rede", "value"),
        Input("filtro_nome", "value"),
        Input("top_n", "value")
    )
    def atualizar(cargo, rede, nome, top_n):

        df_filtrado = df.copy()

        # =========================
        # 🔢 Garantir tipos numéricos
        # =========================

        colunas_numericas = [
            "Seguidores",
            "Interacoes",
            "Engajamento"
        ]

        for coluna in colunas_numericas:

            if coluna in df_filtrado.columns:

                df_filtrado[coluna] = pd.to_numeric(
                    df_filtrado[coluna],
                    errors="coerce"
                ).fillna(0)

        # =========================
        # 🔎 Filtro por cargo
        # =========================

        if cargo and cargo != "Todos":

            df_filtrado = df_filtrado[
                df_filtrado["Cargo"] == cargo
            ]

        # =========================
        # 🔎 Filtro por rede
        # =========================

        if rede:

            df_filtrado = df_filtrado[
                df_filtrado["Social network"] == rede
            ]

        # =========================
        # 🔎 Filtro por candidato
        # =========================

        if nome:

            nome = str(nome).strip()

            df_filtrado = df_filtrado[
                df_filtrado["Profile_padronizado"]
                .fillna("")
                .astype(str)
                .str.contains(
                    nome,
                    case=False,
                    na=False
                )
            ]

        # =========================
        # 🔢 Top N
        # =========================

        df_top = (
            df_filtrado
            .sort_values(
                "Seguidores",
                ascending=False
            )
            .head(int(top_n))
        )

        # =========================
        # 🎨 Estilo
        # =========================

        def estilizar(fig):

            fig.update_layout(
                template="plotly_white",
                title_x=0.5,
                margin=dict(
                    l=20,
                    r=20,
                    t=50,
                    b=20
                )
            )

            return fig

        # =========================
        # 🚫 Sem dados
        # =========================

        if df_filtrado.empty:

            fig_vazio = px.scatter(
                title="Nenhum dado encontrado para os filtros selecionados"
            )

            fig_vazio.update_layout(
                template="plotly_white",
                title_x=0.5
            )

            return (
                fig_vazio,
                fig_vazio,
                fig_vazio,
                fig_vazio,
                fig_vazio,
                fig_vazio,
                fig_vazio
            )

        # =========================
        # 📊 Seguidores
        # =========================

        fig_seguidores = estilizar(
            px.bar(
                df_top,
                x="Profile_padronizado",
                y="Seguidores",
                title=f"Top {top_n} Seguidores - {rede}"
            )
        )

        # =========================
        # 📊 Interações
        # =========================

        fig_interacoes = estilizar(
            px.bar(
                df_top,
                x="Profile_padronizado",
                y="Interacoes",
                title=f"Top {top_n} Interações - {rede}"
            )
        )

        # =========================
        # 📊 Engajamento
        # =========================

        df_engajamento = (
            df_top
            .sort_values(
                "Engajamento",
                ascending=False
            )
        )

        fig_engajamento = estilizar(
            px.bar(
                df_engajamento,
                x="Profile_padronizado",
                y="Engajamento",
                title="Taxa de Engajamento"
            )
        )

        # =========================
        # 📊 Scatter
        # =========================

        df_scatter = df_filtrado[
            (df_filtrado["Seguidores"] > 0) &
            (df_filtrado["Interacoes"] > 0)
        ].copy()

        # Escala exclusivamente visual para o tamanho
        # dos pontos.
        df_scatter["Tamanho_Ponto"] = (
            df_scatter["Engajamento"] * 1000
        ).clip(lower=5)

        if df_scatter.empty:

            fig_scatter = px.scatter(
                title="Seguidores vs Interações"
            )

        else:

            fig_scatter = px.scatter(
                df_scatter,
                x="Seguidores",
                y="Interacoes",
                size="Tamanho_Ponto",
                color="Engajamento",
                hover_data=[
                    "Profile_padronizado",
                    "Seguidores",
                    "Interacoes",
                    "Engajamento"
                ],
                title="Seguidores vs Interações",
                log_x=True,
                log_y=True
            )

        fig_scatter = estilizar(fig_scatter)

        # =========================
        # 📊 Heatmap
        # =========================

        df_heatmap = df_filtrado[
            (df_filtrado["Seguidores"] > 0) &
            (df_filtrado["Interacoes"] > 0)
        ].copy()

        if df_heatmap.empty:

            fig_heatmap = px.density_heatmap(
                title="Densidade de Perfis"
            )

        else:

            fig_heatmap = px.density_heatmap(
                df_heatmap,
                x="Seguidores",
                y="Interacoes",
                title="Densidade de Perfis"
            )

        fig_heatmap = estilizar(fig_heatmap)

        # =========================
        # 📊 Comparação entre redes
        # =========================
        #
        # Aqui usamos o dataframe original,
        # mas respeitando o filtro de cargo e
        # candidato. O filtro de rede não é
        # aplicado porque o objetivo deste
        # gráfico é justamente comparar redes.

        df_comparativo = df.copy()

        if cargo and cargo != "Todos":

            df_comparativo = df_comparativo[
                df_comparativo["Cargo"] == cargo
            ]

        if nome:

            nome = str(nome).strip()

            df_comparativo = df_comparativo[
                df_comparativo["Profile_padronizado"]
                .fillna("")
                .astype(str)
                .str.contains(
                    nome,
                    case=False,
                    na=False
                )
            ]

        df_agg = (
            df_comparativo
            .groupby("Social network", as_index=False)
            .agg({
                "Seguidores": "sum",
                "Interacoes": "sum"
            })
        )

        fig_comparativo = estilizar(
            px.bar(
                df_agg,
                x="Social network",
                y=[
                    "Seguidores",
                    "Interacoes"
                ],
                barmode="group",
                title="Comparação entre Redes"
            )
        )

        # =========================
        # 📊 Comparação por cargo
        # =========================

        df_cargo = (
            df
            .groupby("Cargo", as_index=False)
            .agg({
                "Seguidores": "sum",
                "Interacoes": "sum",
                "Engajamento": "mean"
            })
        )

        fig_cargo = estilizar(
            px.bar(
                df_cargo,
                x="Cargo",
                y=[
                    "Seguidores",
                    "Interacoes"
                ],
                barmode="group",
                title="Desempenho por Cargo"
            )
        )

        return (
            fig_seguidores,
            fig_interacoes,
            fig_engajamento,
            fig_scatter,
            fig_heatmap,
            fig_comparativo,
            fig_cargo
        )