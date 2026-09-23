
from dash import html, dcc, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go

from wordcloud import WordCloud, STOPWORDS

import base64
from io import BytesIO
import re
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

FILTER_STYLE = {
    "backgroundColor": "#f8f9fa",
    "padding": "20px",
    "borderRadius": "10px",
    "marginBottom": "20px"
}

FILTER_LABEL_STYLE = {
    "fontWeight": "bold",
    "marginBottom": "5px",
    "display": "block"
}

GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(350px, 1fr))",
    "gap": "20px"
}


# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS_PT = {
    "de", "da", "do", "e", "a", "o", "que", "em",
    "para", "com", "na", "no", "um", "uma", "os",
    "as", "por", "pra", "https", "http", "www",
    "tiktok", "instagram", "reel", "video", "é",
    "se", "mas", "esse", "essa", "isso", "este",
    "esta", "isto", "são", "ser", "foi", "vai",
    "vamos", "tem", "ter", "como", "mais", "muito",
    "muita", "sobre", "também", "já", "aqui",
    "hoje", "nos", "nas", "dos", "das"
}

STOPWORDS_ALL = STOPWORDS.union(STOPWORDS_PT)


# ============================================================
# LIMPEZA DE TEXTO
# ============================================================

def limpar_texto(texto):

    if not texto:
        return ""

    texto = str(texto).lower()

    texto = re.sub(
        r"http\S+",
        "",
        texto
    )

    texto = re.sub(
        r"@\w+",
        "",
        texto
    )

    texto = re.sub(
        r"#\w+",
        "",
        texto
    )

    texto = re.sub(
        r"[^a-zà-ú0-9\s]",
        "",
        texto
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    return texto.strip()


# ============================================================
# WORDCLOUD
# ============================================================

def gerar_wordcloud(texto):

    texto = limpar_texto(texto)

    if not texto:
        return None

    wc = WordCloud(
        width=800,
        height=400,
        background_color="white",
        stopwords=STOPWORDS_ALL,
        min_font_size=10,
        collocations=False
    ).generate(texto)

    buffer = BytesIO()

    wc.to_image().save(
        buffer,
        format="PNG"
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return (
        f"data:image/png;base64,{encoded}"
    )


# ============================================================
# FIGURA VAZIA
# ============================================================

def figura_vazia(mensagem="Nenhum dado disponível"):

    fig = go.Figure()

    fig.add_annotation(
        text=mensagem,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"size": 16}
    )

    fig.update_xaxes(
        visible=False
    )

    fig.update_yaxes(
        visible=False
    )

    fig.update_layout(
        template="plotly_white"
    )

    return fig


# ============================================================
# LAYOUT
# ============================================================

def layout():

    return html.Div([

        html.H2(
            "📝 Análise de Posts",
            style={
                "marginTop": 0,
                "marginBottom": "20px"
            }
        ),

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
                    id="posts_filtro_cargo",
                    options=[],
                    value=None,
                    clearable=False
                )

            ], style={"marginBottom": "15px"}),

            # ------------------------------------------------
            # SUBGRUPO
            # ------------------------------------------------

            html.Div(
                id="posts_container_subgrupo",
                children=[

                    html.Label(
                        "Subgrupo",
                        style=FILTER_LABEL_STYLE
                    ),

                    dcc.Dropdown(
                        id="posts_filtro_subgrupo",
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
            # REDE
            # ------------------------------------------------

            html.Div([

                html.Label(
                    "Rede Social",
                    style=FILTER_LABEL_STYLE
                ),

                dcc.Dropdown(
                    id="posts_filtro_rede",
                    options=[],
                    value=None,
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
                    id="posts_filtro_candidato",
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
                    id="posts_filtro_periodo",
                    options=[],
                    value=[],
                    multi=True,
                    clearable=True,
                    placeholder="Selecione um ou mais períodos"
                )

            ])

        ], style=FILTER_STYLE),

        # ====================================================
        # RESUMO
        # ====================================================

        html.Div(
            id="posts_resumo",
            style={
                "display": "grid",
                "gridTemplateColumns":
                    "repeat(auto-fit, minmax(180px, 1fr))",
                "gap": "15px",
                "marginBottom": "20px"
            }
        ),

        # ====================================================
        # VOLUME DE POSTS
        # ====================================================

        html.Div([

            dcc.Graph(
                id="grafico_posts"
            )

        ], style=CARD_STYLE),

        # ====================================================
        # EVOLUÇÃO
        # ====================================================

        html.Div([

            dcc.Graph(
                id="grafico_posts_temporal"
            )

        ], style=CARD_STYLE),

        # ====================================================
        # INTERAÇÕES
        # ====================================================

        html.Div(
            [

                html.Div(
                    dcc.Graph(
                        id="grafico_interacoes_posts"
                    ),
                    style=CARD_STYLE
                ),

                html.Div(
                    dcc.Graph(
                        id="grafico_engajamento_posts"
                    ),
                    style=CARD_STYLE
                ),

                html.Div(
                    dcc.Graph(
                        id="grafico_sentimento_posts"
                    ),
                    style=CARD_STYLE
                )

            ],
            style=GRID_STYLE
        ),

        # ====================================================
        # TOP POSTS
        # ====================================================

        html.Div([

            html.H3(
                "Posts com maior número de interações",
                style={"marginTop": 0}
            ),

            dash_table.DataTable(
                id="tabela_top_posts",

                columns=[
                    {
                        "name": "Candidato",
                        "id": "Profile_padronizado"
                    },
                    {
                        "name": "Data",
                        "id": "Date"
                    },
                    {
                        "name": "Post",
                        "id": "Message"
                    },
                    {
                        "name": "Interações",
                        "id": "Interacoes"
                    },
                    {
                        "name": "Likes",
                        "id": "Likes"
                    },
                    {
                        "name": "Comentários",
                        "id": "Comentarios"
                    },
                    {
                        "name": "Taxa de interação",
                        "id": "Taxa_Interacao"
                    },
                    {
                        "name": "Link",
                        "id": "Link",
                        "presentation": "markdown"
                    }
                ],

                data=[],

                page_size=10,

                sort_action="native",

                style_table={
                    "overflowX": "auto"
                },

                style_cell={
                    "textAlign": "left",
                    "padding": "10px",
                    "maxWidth": "400px",
                    "whiteSpace": "normal"
                },

                style_header={
                    "fontWeight": "bold",
                    "backgroundColor": "#f1f3f5"
                }
            )

        ], style=CARD_STYLE),

        # ====================================================
        # WORDCLOUDS
        # ====================================================

        html.Div([

            html.H3(
                "Termos mais frequentes nas publicações",
                style={"marginTop": 0}
            ),

            html.Div(
                id="wordclouds_container",
                style=GRID_STYLE
            )

        ], style=CARD_STYLE)

    ], style={
        "backgroundColor": "#f4f6f9",
        "padding": "20px",
        "fontFamily": "Arial, sans-serif"
    })


# ============================================================
# CALLBACKS
# ============================================================

def register_callbacks(app, posts):

    # ========================================================
    # 1. INICIALIZA CARGOS
    # ========================================================

    @app.callback(
        Output(
            "posts_filtro_cargo",
            "options"
        ),
        Output(
            "posts_filtro_cargo",
            "value"
        ),
        Input(
            "posts_filtro_cargo",
            "id"
        )
    )
    def inicializar_cargos(_):

        cargos = sorted(
            posts["Cargo"]
            .dropna()
            .unique()
        )

        opcoes = [
            {
                "label": cargo,
                "value": cargo
            }
            for cargo in cargos
        ]

        valor = (
            cargos[0]
            if cargos
            else None
        )

        return opcoes, valor


    # ========================================================
    # 2. CARGO → SUBGRUPO
    # ========================================================

    @app.callback(
        Output(
            "posts_container_subgrupo",
            "style"
        ),
        Output(
            "posts_filtro_subgrupo",
            "options"
        ),
        Output(
            "posts_filtro_subgrupo",
            "value"
        ),

        Input(
            "posts_filtro_cargo",
            "value"
        )
    )
    def atualizar_subgrupos(cargo):

        if not cargo:
            return (
                {"display": "none"},
                [],
                None
            )

        dados = posts[
            posts["Cargo"] == cargo
        ]

        subgrupos = sorted(
            dados["Subgrupo"]
            .dropna()
            .unique()
        )

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
    # 3. CARGO + SUBGRUPO → REDE
    # ========================================================

    @app.callback(
        Output(
            "posts_filtro_rede",
            "options"
        ),
        Output(
            "posts_filtro_rede",
            "value"
        ),

        Input(
            "posts_filtro_cargo",
            "value"
        ),
        Input(
            "posts_filtro_subgrupo",
            "value"
        )
    )
    def atualizar_redes(
        cargo,
        subgrupo
    ):

        if not cargo:
            return [], None

        dados = posts[
            posts["Cargo"] == cargo
        ]

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

        redes = sorted(
            dados["Social network"]
            .dropna()
            .unique()
        )

        opcoes = [
            {
                "label": rede,
                "value": rede
            }
            for rede in redes
        ]

        valor = (
            redes[0]
            if redes
            else None
        )

        return opcoes, valor


    # ========================================================
    # 4. REDE → CANDIDATOS + PERÍODOS
    # ========================================================

    @app.callback(
        Output(
            "posts_filtro_candidato",
            "options"
        ),
        Output(
            "posts_filtro_candidato",
            "value"
        ),
        Output(
            "posts_filtro_periodo",
            "options"
        ),
        Output(
            "posts_filtro_periodo",
            "value"
        ),

        Input(
            "posts_filtro_cargo",
            "value"
        ),
        Input(
            "posts_filtro_subgrupo",
            "value"
        ),
        Input(
            "posts_filtro_rede",
            "value"
        )
    )
    def atualizar_candidatos_periodos(
        cargo,
        subgrupo,
        rede
    ):

        if not cargo or not rede:
            return [], [], [], []

        dados = posts[
            posts["Cargo"] == cargo
        ]

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

        dados = dados[
            dados["Social network"] == rede
        ]

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
    # 5. ATUALIZA TODOS OS GRÁFICOS
    # ========================================================

    @app.callback(

        Output(
            "posts_resumo",
            "children"
        ),

        Output(
            "grafico_posts",
            "figure"
        ),

        Output(
            "grafico_posts_temporal",
            "figure"
        ),

        Output(
            "grafico_interacoes_posts",
            "figure"
        ),

        Output(
            "grafico_engajamento_posts",
            "figure"
        ),

        Output(
            "grafico_sentimento_posts",
            "figure"
        ),

        Output(
            "tabela_top_posts",
            "data"
        ),

        Output(
            "wordclouds_container",
            "children"
        ),

        Input(
            "posts_filtro_cargo",
            "value"
        ),

        Input(
            "posts_filtro_subgrupo",
            "value"
        ),

        Input(
            "posts_filtro_rede",
            "value"
        ),

        Input(
            "posts_filtro_candidato",
            "value"
        ),

        Input(
            "posts_filtro_periodo",
            "value"
        )
    )
    def atualizar_posts(

        cargo,
        subgrupo,
        rede,
        candidatos,
        periodos
    ):

        dados = posts.copy()

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
        # CANDIDATO
        # ----------------------------------------------------

        if candidatos:
            dados = dados[
                dados["Profile_padronizado"].isin(
                    candidatos
                )
            ]

        # ----------------------------------------------------
        # PERÍODO
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
        # SEM DADOS
        # ----------------------------------------------------

        if dados.empty:

            resumo = [
                html.Div([
                    html.H4("0"),
                    html.P("Posts")
                ], style=CARD_STYLE)
            ]

            vazio = figura_vazia(
                "Nenhum post encontrado para os filtros selecionados."
            )

            return (
                resumo,
                vazio,
                vazio,
                vazio,
                vazio,
                vazio,
                [],
                []
            )

        # ====================================================
        # RESUMO
        # ====================================================

        quantidade_posts = len(dados)

        candidatos_unicos = (
            dados["Profile_padronizado"]
            .nunique()
        )

        interacoes_total = (
            dados["Interacoes"]
            .sum()
        )

        media_interacoes = (
            dados["Interacoes"]
            .mean()
        )

        taxa_media = (
            dados["Taxa_Interacao"]
            .mean()
        )

        resumo = [

            html.Div([
                html.H3(
                    f"{quantidade_posts:,}"
                ),
                html.P("Posts analisados")
            ], style=CARD_STYLE),

            html.Div([
                html.H3(
                    f"{candidatos_unicos:,}"
                ),
                html.P("Candidatos")
            ], style=CARD_STYLE),

            html.Div([
                html.H3(
                    f"{interacoes_total:,.0f}"
                ),
                html.P("Interações")
            ], style=CARD_STYLE),

            html.Div([
                html.H3(
                    f"{media_interacoes:,.1f}"
                ),
                html.P("Interações/post")
            ], style=CARD_STYLE),

            html.Div([
                html.H3(
                    f"{taxa_media:.2f}"
                ),
                html.P("Taxa média de interação")
            ], style=CARD_STYLE)
        ]

        # ====================================================
        # 1. QUANTIDADE DE POSTS
        # ====================================================

        df_count = (
            dados
            .groupby(
                "Profile_padronizado",
                as_index=False
            )
            .size()
            .rename(
                columns={"size": "Qtd_Posts"}
            )
            .sort_values(
                "Qtd_Posts",
                ascending=False
            )
        )

        fig_posts = px.bar(
            df_count,
            x="Profile_padronizado",
            y="Qtd_Posts",
            title="Quantidade de publicações por candidato",
            text="Qtd_Posts"
        )

        fig_posts.update_layout(
            template="plotly_white",
            xaxis_title="Candidato",
            yaxis_title="Publicações",
            title_x=0.5
        )

        # ====================================================
        # 2. EVOLUÇÃO DE POSTS
        # ====================================================

        dados_temporal = (
            dados
            .groupby(
                [
                    "Data_Inicio",
                    "Profile_padronizado"
                ],
                as_index=False
            )
            .size()
            .rename(
                columns={"size": "Qtd_Posts"}
            )
        )

        fig_temporal = px.line(
            dados_temporal,
            x="Data_Inicio",
            y="Qtd_Posts",
            color="Profile_padronizado",
            markers=True,
            title="Evolução do volume de publicações"
        )

        fig_temporal.update_layout(
            template="plotly_white",
            xaxis_title="Período",
            yaxis_title="Publicações",
            title_x=0.5
        )

        # ====================================================
        # 3. INTERAÇÕES
        # ====================================================

        dados_interacoes = (
            dados
            .groupby(
                "Profile_padronizado",
                as_index=False
            )["Interacoes"]
            .sum()
            .sort_values(
                "Interacoes",
                ascending=False
            )
        )

        fig_interacoes = px.bar(
            dados_interacoes,
            x="Profile_padronizado",
            y="Interacoes",
            title="Interações acumuladas por candidato"
        )

        fig_interacoes.update_layout(
            template="plotly_white",
            xaxis_title="Candidato",
            yaxis_title="Interações",
            title_x=0.5
        )

        # ====================================================
        # 4. TAXA DE INTERAÇÃO
        # ====================================================

        dados_engajamento = (
            dados
            .groupby(
                "Profile_padronizado",
                as_index=False
            )["Taxa_Interacao"]
            .mean()
            .sort_values(
                "Taxa_Interacao",
                ascending=False
            )
        )

        fig_engajamento = px.bar(
            dados_engajamento,
            x="Profile_padronizado",
            y="Taxa_Interacao",
            title="Taxa média de interação por candidato"
        )

        fig_engajamento.update_layout(
            template="plotly_white",
            xaxis_title="Candidato",
            yaxis_title="Taxa de interação",
            title_x=0.5
        )

        # ====================================================
        # 5. SENTIMENTO NEGATIVO
        # ====================================================

        dados_sentimento = (
            dados
            .groupby(
                "Profile_padronizado",
                as_index=False
            )["Sentimento_Negativo"]
            .mean()
            .sort_values(
                "Sentimento_Negativo",
                ascending=False
            )
        )

        fig_sentimento = px.bar(
            dados_sentimento,
            x="Profile_padronizado",
            y="Sentimento_Negativo",
            title="Participação média de comentários negativos"
        )

        fig_sentimento.update_layout(
            template="plotly_white",
            xaxis_title="Candidato",
            yaxis_title="Sentimento negativo",
            title_x=0.5
        )

        # ====================================================
        # 6. TOP POSTS
        # ====================================================

        top_posts = (
            dados
            .sort_values(
                "Interacoes",
                ascending=False
            )
            .head(50)
            .copy()
        )

        top_posts["Date"] = (
            top_posts["Date"]
            .dt.strftime("%d/%m/%Y %H:%M")
            .fillna("")
        )

        top_posts["Message"] = (
            top_posts["Message"]
            .str.slice(0, 300)
        )

        top_posts["Link"] = top_posts["Link"].fillna("")

        top_posts["Interacoes"] = (
            pd.to_numeric(
                top_posts["Interacoes"],
                errors="coerce"
            )
            .fillna(0)
            .round(0)
            .astype(int)
        )

        top_posts["Likes"] = (
            pd.to_numeric(
                top_posts["Likes"],
                errors="coerce"
            )
            .fillna(0)
            .round(0)
            .astype(int)
        )

        top_posts["Comentarios"] = (
            pd.to_numeric(
                top_posts["Comentarios"],
                errors="coerce"
            )
            .fillna(0)
            .round(0)
            .astype(int)
        )

        top_posts["Taxa_Interacao"] = (
            pd.to_numeric(
                top_posts["Taxa_Interacao"],
                errors="coerce"
            )
            .fillna(0)
            .round(4)
        )

        tabela = top_posts[
            [
                "Profile_padronizado",
                "Date",
                "Message",
                "Interacoes",
                "Likes",
                "Comentarios",
                "Taxa_Interacao",
                "Link"
            ]
        ].to_dict("records")

        # ====================================================
        # 7. WORDCLOUDS
        # ====================================================

        candidatos_wordcloud = (
            dados["Profile_padronizado"]
            .dropna()
            .unique()
        )

        wordclouds = []

        for candidato in candidatos_wordcloud:

            dados_candidato = dados[
                dados["Profile_padronizado"]
                == candidato
            ]

            texto = " ".join(
                dados_candidato["Message"]
                .dropna()
                .astype(str)
                .tolist()
            )

            imagem = gerar_wordcloud(texto)

            if not imagem:
                continue

            wordclouds.append(
                html.Div([

                    html.H4(
                        candidato,
                        style={
                            "textAlign": "center",
                            "marginBottom": "10px"
                        }
                    ),

                    html.Img(
                        src=imagem,
                        style={
                            "width": "100%",
                            "borderRadius": "8px"
                        }
                    )

                ], style=CARD_STYLE)
            )

        return (
            resumo,
            fig_posts,
            fig_temporal,
            fig_interacoes,
            fig_engajamento,
            fig_sentimento,
            tabela,
            wordclouds
        )