import os
import pandas as pd

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
# =========================
# DADOS DOS DOIS SCHEMAS
# =========================

SCHEMAS = ["public", "monitoramento_extra"]


def carregar_dados_completos(funcao):
    dataframes = []

    for schema in SCHEMAS:
        df_schema = funcao(schema=schema)
        dataframes.append(df_schema)

    return pd.concat(
        dataframes,
        ignore_index=True
    )


df = carregar_dados_completos(carregar_dados_gerais)
historico = carregar_dados_completos(carregar_historico)
posts = carregar_dados_completos(carregar_posts)


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


# =========================
# 🏛️ RODAPÉ / LOGOS
# =========================

FOOTER_STYLE = {
    "backgroundColor": "#ffffff",
    "borderTop": "1px solid #dee2e6",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "gap": "50px",
    "padding": "25px 20px",
    "marginTop": "30px",
    "boxShadow": "0px -2px 8px rgba(0,0,0,0.05)"
}

LOGO_STYLE = {
    "height": "70px",
    "width": "auto",
    "maxWidth": "180px",
    "objectFit": "contain"
}

footer = html.Footer([
    html.A(
        html.Img(
            src="/assets/logos/nev.png",
            style=LOGO_STYLE
        ),
        href="https://nev.prp.usp.br/",
        target="_blank"
    ),
    html.A(
        html.Img(
            src="/assets/logos/obcom.png",
            style=LOGO_STYLE
        ),
        href="https://obcom.net.br/",
        target="_blank"
    ),
    html.A(
        html.Img(
            src="/assets/logos/icmc.png",
            style=LOGO_STYLE
        ),
        href="https://www.icmc.usp.br/",
        target="_blank"
    )
], style=FOOTER_STYLE)


app.layout = html.Div([

    # HEADER
    html.Div([
        html.H1(
            "📊 Análise de Redes Sociais - Eleições",
            style={"margin": 0}
        ),

        html.P(
            "Dashboard analítico de desempenho digital",
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

    # ABAS
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
    }),

    # LOGOS
    footer

], style={
    "backgroundColor": "#f4f6f9",
    "padding": "20px",
    "fontFamily": "Arial, sans-serif",
    "minHeight": "100vh"
})


# =========================
# 🔄 CALLBACKS
# =========================

geral.register_callbacks(
    app,
    df,
    historico
)

posts_page.register_callbacks(app, posts, df)

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