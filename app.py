import os

from dash import Dash, dcc, html

from data_loader import (
    carregar_dados_gerais,
    carregar_historico,
    carregar_posts
)

from pages import geral
from pages import posts as posts_page


# =========================
# 📊 Dados
# =========================

df = carregar_dados_gerais()
historico = carregar_historico()
posts = carregar_posts()


# =========================
# 🔎 FILTROS INICIAIS
# =========================

cargos = sorted(
    df["Cargo"]
    .dropna()
    .unique()
)

redes = sorted(
    df["Social network"]
    .dropna()
    .unique()
)


# =========================
# 🎨 ESTILO GLOBAL
# =========================

TAB_STYLE = {
    "padding": "12px",
    "fontWeight": "bold",
    "backgroundColor": "#e9ecef",
    "border": "none"
}

TAB_SELECTED_STYLE = {
    "padding": "12px",
    "fontWeight": "bold",
    "backgroundColor": "#ffffff",
    "borderTop": "3px solid #007bff"
}


# =========================
# 🧩 LAYOUT
# =========================

app = Dash(__name__)

server = app.server


app.layout = html.Div([

    # =========================
    # 🔝 HEADER
    # =========================

    html.Div([

        html.H1(
            "📊 Análise de Redes Sociais - Eleições",
            style={"margin": 0}
        ),

        html.P(
            "Dashboard analítico de desempenho digital por candidato",
            style={
                "margin": 0,
                "color": "#666"
            }
        )

    ], style={
        "backgroundColor": "#ffffff",
        "padding": "20px",
        "borderRadius": "10px",
        "boxShadow": "0px 2px 8px rgba(0,0,0,0.1)",
        "marginBottom": "20px"
    }),


    # =========================
    # 📑 TABS
    # =========================

    dcc.Tabs([

        dcc.Tab(
            label="📊 Geral",

            children=geral.layout(
                redes,
                cargos
            ),

            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE
        ),

        dcc.Tab(
            label="📝 Posts",

            children=posts_page.layout(),

            style=TAB_STYLE,
            selected_style=TAB_SELECTED_STYLE
        )

    ], style={
        "backgroundColor": "#f4f6f9",
        "padding": "10px",
        "borderRadius": "10px"
    })

], style={
    "backgroundColor": "#f4f6f9",
    "padding": "20px",
    "fontFamily": "Arial, sans-serif"
})


# =========================
# 🔄 CALLBACKS
# =========================

geral.register_callbacks(
    app,
    df,
    historico
)

posts_page.register_callbacks(
    app,
    posts
)


# =========================
# ▶️ RUN
# =========================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            8050
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )