from pathlib import Path
import re

import pandas as pd


# ============================================================
# LOCALIZAÇÃO DOS ARQUIVOS
# ============================================================

def localizar_arquivo(pasta, prefixo):
    """
    Localiza um único arquivo .xlsx cujo nome começa
    com o prefixo informado.
    """

    arquivos = [
        arquivo
        for arquivo in Path(pasta).iterdir()
        if arquivo.is_file()
        and arquivo.name.lower().startswith(prefixo.lower())
        and arquivo.suffix.lower() == ".xlsx"
    ]

    if not arquivos:
        raise FileNotFoundError(
            f"Nenhum arquivo '{prefixo}*.xlsx' encontrado em: {pasta}"
        )

    if len(arquivos) > 1:
        raise ValueError(
            f"Mais de um arquivo '{prefixo}*.xlsx' encontrado em {pasta}:\n"
            + "\n".join(str(a) for a in arquivos)
        )

    return arquivos[0]


# ============================================================
# LEITURA DO EXCEL
# ============================================================

def encontrar_cabecalho(df, coluna_procurada):
    """
    Procura a linha que contém a coluna esperada.
    """

    for indice, linha in df.iterrows():

        valores = [
            str(valor).strip()
            for valor in linha.tolist()
        ]

        if coluna_procurada in valores:
            return indice

    raise ValueError(
        f"Não foi encontrada a coluna '{coluna_procurada}'."
    )

def preparar_metrics_dataframe(bruto):
    linha_cabecalho = encontrar_cabecalho(
        bruto,
        "Profile"
    )

    df = bruto.iloc[linha_cabecalho + 1:].copy()
    df.columns = bruto.iloc[linha_cabecalho]

    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    df.columns = [
        str(coluna).strip()
        for coluna in df.columns
    ]

    return df.reset_index(drop=True)

def preparar_metrics(caminho):
    bruto = pd.read_excel(
        caminho,
        sheet_name="Metrics Overview",
        header=None
    )

    return preparar_metrics_dataframe(bruto)

def preparar_posts_dataframe(bruto):
    linha_cabecalho = encontrar_cabecalho(
        bruto,
        "Date"
    )

    df = bruto.iloc[linha_cabecalho + 1:].copy()
    df.columns = bruto.iloc[linha_cabecalho]

    df = df.dropna(axis=1, how="all")
    df = df.dropna(axis=0, how="all")

    df.columns = [
        str(coluna).strip()
        for coluna in df.columns
    ]

    return df.reset_index(drop=True)

def preparar_posts(caminho):
    bruto = pd.read_excel(
        caminho,
        sheet_name="Top 5000 Posts Overview",
        header=None
    )

    return preparar_posts_dataframe(bruto)


# ============================================================
# CONVERSÃO DE TIPOS
# ============================================================

def converter_inteiro(df, colunas):
    """
    Converte colunas numéricas para inteiros anuláveis.
    """

    for coluna in colunas:

        if coluna in df.columns:
            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            ).round()

    return df


def converter_decimal(df, colunas):
    """
    Converte colunas numéricas para decimal.
    """

    for coluna in colunas:

        if coluna in df.columns:
            df[coluna] = pd.to_numeric(
                df[coluna],
                errors="coerce"
            )

    return df


def converter_data(df, coluna):
    """
    Converte uma coluna para datetime.
    """

    if coluna in df.columns:
        df[coluna] = pd.to_datetime(
            df[coluna],
            errors="coerce"
        )

    return df


# ============================================================
# PADRONIZAÇÃO DOS DADOS
# ============================================================

def padronizar_metrics(df):
    """
    Padroniza tipos das métricas dos perfis.
    """

    colunas_inteiras = [
        "Follower",
        "Number of posts",
        "Number of Likes",
        "Number of comments",
        "Reactions, Comments & Shares",
        "Profile Views",
    ]

    colunas_decimais = [
        "Post interaction rate",
        "Reach per day",
        "Page Performance Index",
    ]

    df = converter_inteiro(
        df,
        colunas_inteiras
    )

    df = converter_decimal(
        df,
        colunas_decimais
    )

    # IDs devem permanecer como texto
    if "Profile-ID" in df.columns:
        df["Profile-ID"] = (
            df["Profile-ID"]
            .astype("string")
            .str.strip()
        )

    # Textos
    for coluna in [
        "Profile",
        "Network",
        "Link",
        "External Links",
        "Image Link",
    ]:
        if coluna in df.columns:
            df[coluna] = (
                df[coluna]
                .astype("string")
                .str.strip()
            )

    return df


def padronizar_posts(df):
    """
    Padroniza tipos dos posts.
    """

    df = converter_data(
        df,
        "Date"
    )

    colunas_inteiras = [
        "Number of Likes",
        "Number of comments",
        "Reactions, Comments & Shares",
    ]

    colunas_decimais = [
        "Post interaction rate",
        "Reach per post",
        "Interactions per impression/view",
        "Post comments negative sentiment share",
    ]

    df = converter_inteiro(
        df,
        colunas_inteiras
    )

    df = converter_decimal(
        df,
        colunas_decimais
    )

    # IDs
    for coluna in [
        "Message-ID",
        "Profile-ID",
    ]:
        if coluna in df.columns:
            df[coluna] = (
                df[coluna]
                .astype("string")
                .str.strip()
            )

    # Textos
    for coluna in [
        "Message",
        "Profile",
        "Network",
        "Link",
        "External Links",
        "Image Link",
    ]:
        if coluna in df.columns:
            df[coluna] = (
                df[coluna]
                .astype("string")
                .str.strip()
            )

    return df


# ============================================================
# INFORMAÇÕES DA COLETA
# ============================================================

def extrair_periodo(pasta):
    """
    Extrai semana, data inicial e data final do nome da pasta.

    Exemplo:

    Semana 1 (16_08 - 22_08)

    retorna:

    semana = 1
    data_inicio = 16/08
    data_fim = 22/08
    """

    nome = Path(pasta).name

    separador = r"[_\-/:]"
    padrao = re.search(
        rf"Semana\s+(\d+)\s*"
        rf"\(\s*"
        rf"(\d{{1,2}})\s*{separador}\s*(\d{{1,2}})"
        rf"\s*-\s*"
        rf"(\d{{1,2}})\s*{separador}\s*(\d{{1,2}})"
        rf"\s*\)",
        nome,
        re.IGNORECASE
    )

    if not padrao:
        raise ValueError(
            f"Não foi possível identificar o período da pasta: {nome}"
        )

    semana = int(padrao.group(1))

    dia_inicio = int(padrao.group(2))
    mes_inicio = int(padrao.group(3))

    dia_fim = int(padrao.group(4))
    mes_fim = int(padrao.group(5))

    # Ano atual.
    # Posteriormente podemos tornar isso configurável.
    ano = pd.Timestamp.now().year

    data_inicio = pd.Timestamp(
        year=ano,
        month=mes_inicio,
        day=dia_inicio
    ).date()

    data_fim = pd.Timestamp(
        year=ano,
        month=mes_fim,
        day=dia_fim
    ).date()

    return {
        "semana": semana,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    }


def identificar_grupo_subgrupo(pasta):
    """
    Identifica grupo e subgrupo a partir da estrutura:

    data/
    ├── Presidenciáveis/
    │   └── Semana 1 (...)
    │
    └── Governos/
        └── Governo RJ/
            └── Semana 1 (...)
    """

    caminho = Path(pasta)

    partes = list(caminho.parts)

    indice_semana = None

    for i, parte in enumerate(partes):
        if parte.lower().startswith("semana "):
            indice_semana = i
            break

    if indice_semana is None:
        raise ValueError(
            f"Pasta semanal não identificada: {pasta}"
        )

    if indice_semana < 1:
        raise ValueError(
            f"Estrutura de pasta inválida: {pasta}"
        )

    # Pasta imediatamente anterior à semana
    anterior = partes[indice_semana - 1]

    # Verifica se existe uma pasta intermediária.
    #
    # Exemplo:
    # data / Governos / Governo RJ / Semana
    #
    # Nesse caso:
    # grupo = Governos
    # subgrupo = Governo RJ

    if indice_semana >= 2:

        possivel_grupo = partes[indice_semana - 2]

        # Identificamos alguns grupos que possuem subgrupo.
        grupos_com_subgrupo = {
            "Governos",
            "Deputados Federais",
        }

        if possivel_grupo in grupos_com_subgrupo:

            return (
                possivel_grupo,
                anterior
            )

    # Exemplo:
    # data / Presidenciáveis / Semana
    #
    # grupo = Presidenciáveis
    # subgrupo = None

    return (
        anterior,
        None
    )


# ============================================================
# VALIDAÇÃO
# ============================================================

def validar_metrics(df):

    colunas_obrigatorias = [
        "Profile",
        "Network",
        "Profile-ID",
    ]

    faltantes = [
        coluna
        for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes em Metrics Overview: "
            + ", ".join(faltantes)
        )


def validar_posts(df):

    colunas_obrigatorias = [
        "Date",
        "Message",
        "Profile",
        "Network",
        "Message-ID",
        "Profile-ID",
    ]

    faltantes = [
        coluna
        for coluna in colunas_obrigatorias
        if coluna not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Colunas obrigatórias ausentes em Top 5000 Posts Overview: "
            + ", ".join(faltantes)
        )


# ============================================================
# PROCESSAMENTO COMPLETO
# ============================================================

def processar_pasta_semana(pasta):

    pasta = Path(pasta)

    print("=" * 70)
    print(f"PROCESSANDO: {pasta}")
    print("=" * 70)

    benchmarking = localizar_arquivo(
        pasta,
        "Benchmarking"
    )

    content = localizar_arquivo(
        pasta,
        "Content"
    )

    print(f"\nBenchmarking: {benchmarking.name}")
    print(f"Content:      {content.name}")

    # --------------------------------------------------------
    # Arquivos
    # --------------------------------------------------------

    metrics = preparar_metrics(
        benchmarking
    )

    posts = preparar_posts(
        content
    )

    # --------------------------------------------------------
    # Padronização
    # --------------------------------------------------------

    metrics = padronizar_metrics(
        metrics
    )

    posts = padronizar_posts(
        posts
    )

    # --------------------------------------------------------
    # Validação
    # --------------------------------------------------------

    validar_metrics(metrics)
    validar_posts(posts)

    # --------------------------------------------------------
    # Informações da coleta
    # --------------------------------------------------------

    periodo = extrair_periodo(
        pasta
    )

    grupo, subgrupo = identificar_grupo_subgrupo(
        pasta
    )

    coleta = {
        "grupo": grupo,
        "subgrupo": subgrupo,
        **periodo,
        "benchmarking_arquivo": benchmarking.name,
        "content_arquivo": content.name,
    }

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("COLETA")
    print("=" * 70)

    for chave, valor in coleta.items():
        print(f"{chave}: {valor}")

    print("\n" + "=" * 70)
    print("METRICS PADRONIZADO")
    print("=" * 70)

    print(f"Linhas:   {len(metrics)}")
    print(f"Colunas:  {len(metrics.columns)}")

    print("\nTipos:")
    print(metrics.dtypes)

    print("\nPrimeiras linhas:")
    print(metrics.head().to_string())

    print("\n" + "=" * 70)
    print("POSTS PADRONIZADOS")
    print("=" * 70)

    print(f"Linhas:   {len(posts)}")
    print(f"Colunas:  {len(posts.columns)}")

    print("\nTipos:")
    print(posts.dtypes)

    print("\nPrimeiras linhas:")
    print(posts.head().to_string())

    return {
        "coleta": coleta,
        "metrics": metrics,
        "posts": posts,
    }


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta semanal: "
    ).strip()

    resultado = processar_pasta_semana(
        pasta
    )