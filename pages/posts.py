from dash import html, dcc, Input, Output
import plotly.express as px
from wordcloud import WordCloud, STOPWORDS
import base64
from io import BytesIO
import re

# =========================
# 🎨 ESTILO
# =========================
CARD_STYLE = {
    "backgroundColor": "#ffffff",
    "padding": "15px",
    "borderRadius": "10px",
    "boxShadow": "0px 2px 8px rgba(0,0,0,0.1)",
}

GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "repeat(auto-fit, minmax(300px, 1fr))",
    "gap": "20px",
}

FILTER_STYLE = {
    "backgroundColor": "#f8f9fa",
    "padding": "15px",
    "borderRadius": "10px",
    "marginBottom": "20px"
}

# =========================
# 🧠 Stopwords
# =========================
STOPWORDS_PT = {
    "de", "da", "do", "e", "a", "o", "que", "em", "para", "com",
    "na", "no", "um", "uma", "os", "as", "por", "pra", "https",
    "http", "www", "tiktok", "instagram", "reel", "video", "é", "se",
    "mas", "esse", "isso"
}

STOPWORDS_ALL = STOPWORDS.union(STOPWORDS_PT)

# =========================
# 🧹 Limpeza
# =========================
def limpar_texto(texto):
    texto = texto.lower()
    texto = re.sub(r"http\S+", "", texto)
    texto = re.sub(r"@\w+", "", texto)
    texto = re.sub(r"[^a-zà-ú0-9\s]", "", texto)
    return texto


# =========================
# 📊 Layout
# =========================
def layout():
    return html.Div([

        html.H2("📝 Análise de Posts", style={"marginBottom": "20px"}),

        # 🎛️ Filtros
        html.Div([
            html.Label("Buscar candidato"),
            dcc.Input(
                id="filtro_nome_posts",
                placeholder="Digite o nome...",
                style={"width": "100%"}
            ),

            html.Br(), html.Br(),

            html.Label("Top N candidatos"),
            dcc.Slider(min=1, max=10, step=1, value=5, id="top_n_posts"),

        ], style=FILTER_STYLE),

        # 📊 Gráfico
        html.Div([
            dcc.Graph(id="grafico_posts")
        ], style=CARD_STYLE),

        html.Br(),

        # ☁️ Wordclouds
        html.Div(id="wordclouds_container", style=GRID_STYLE)

    ], style={
        "backgroundColor": "#f4f6f9",
        "padding": "20px",
        "fontFamily": "Arial, sans-serif"
    })


# =========================
# 🔄 Callback
# =========================
def register_callbacks(app, posts):

    @app.callback(
        Output("grafico_posts", "figure"),
        Output("wordclouds_container", "children"),
        Input("filtro_nome_posts", "value"),
        Input("top_n_posts", "value")
    )
    def atualizar_posts(nome, top_n):

        df_posts = posts.copy()

        if nome:
            df_posts = df_posts[
                df_posts["Profile_padronizado"].str.contains(nome, case=False, na=False)
            ]

        # =========================
        # 📊 CONTAGEM POSTS
        # =========================
        df_count = df_posts.groupby("Profile_padronizado") \
            .size().reset_index(name="Qtd_Posts") \
            .sort_values("Qtd_Posts", ascending=False)

        fig_posts = px.bar(
            df_count.head(top_n),
            x="Profile_padronizado",
            y="Qtd_Posts",
            title="Número de Publicações por Candidato"
        )

        fig_posts.update_layout(
            template="plotly_white",
            title_x=0.5,
            margin=dict(l=20, r=20, t=40, b=20)
        )

        # =========================
        # ☁️ WORDCLOUDS
        # =========================
        candidatos = df_count.head(top_n)["Profile_padronizado"].tolist()

        wordclouds = []

        for candidato in candidatos:

            df_cand = df_posts[df_posts["Profile_padronizado"] == candidato]

            textos = df_cand["Message"].dropna().astype(str).apply(limpar_texto)
            text = " ".join(textos)

            if text.strip() == "":
                continue

            wc = WordCloud(
                width=600,
                height=300,
                background_color="white",
                stopwords=STOPWORDS_ALL
            ).generate(text)

            buffer = BytesIO()
            wc.to_image().save(buffer, format="PNG")
            encoded = base64.b64encode(buffer.getvalue()).decode()

            # 🎨 CARD DO CANDIDATO
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
                        src=f"data:image/png;base64,{encoded}",
                        style={
                            "width": "100%",
                            "borderRadius": "8px"
                        }
                    )
                ], style=CARD_STYLE)
            )

        return fig_posts, wordclouds