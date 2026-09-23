from google_drive.client import criar_cliente


FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"


def listar_itens(pasta_id):
    """
    Lista arquivos e pastas diretamente dentro de uma pasta.
    """

    drive = criar_cliente()

    resultado = drive.files().list(
        q=f"'{pasta_id}' in parents and trashed = false",
        fields="files(id,name,mimeType,parents)",
        orderBy="folder,name",
        pageSize=1000
    ).execute()

    return resultado.get("files", [])


def listar_pastas(pasta_id):
    """
    Retorna apenas as subpastas de uma pasta.
    """

    return [
        item
        for item in listar_itens(pasta_id)
        if item["mimeType"] == FOLDER_MIME_TYPE
    ]


def listar_arquivos(pasta_id):
    """
    Retorna apenas os arquivos de uma pasta.
    """

    return [
        item
        for item in listar_itens(pasta_id)
        if item["mimeType"] != FOLDER_MIME_TYPE
    ]


def encontrar_pasta(pasta_id, nome):
    """
    Procura uma subpasta pelo nome exato.
    """

    for pasta in listar_pastas(pasta_id):
        if pasta["name"] == nome:
            return pasta

    return None


def encontrar_arquivo(pasta_id, nome):
    """
    Procura um arquivo pelo nome exato.
    """

    for arquivo in listar_arquivos(pasta_id):
        if arquivo["name"] == nome:
            return arquivo

    return None


def encontrar_arquivos_por_prefixo(pasta_id, prefixo):
    """
    Procura arquivos cujo nome começa com determinado prefixo.
    """

    arquivos = listar_arquivos(pasta_id)

    return [
        arquivo
        for arquivo in arquivos
        if arquivo["name"].lower().startswith(prefixo.lower())
    ]