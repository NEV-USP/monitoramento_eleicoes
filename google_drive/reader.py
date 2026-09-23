from io import BytesIO

import pandas as pd

from google_drive.client import criar_cliente
from googleapiclient.http import MediaIoBaseDownload


def baixar_arquivo(file_id):
    drive = criar_cliente()

    request = drive.files().get_media(
        fileId=file_id
    )

    arquivo = BytesIO()

    downloader = MediaIoBaseDownload(
        arquivo,
        request
    )

    concluido = False

    while not concluido:
        status, concluido = downloader.next_chunk()

        if status:
            print(
                f"Download: {int(status.progress() * 100)}%"
            )

    arquivo.seek(0)

    return arquivo


def ler_excel(file_id, sheet_name, header=None):
    arquivo = baixar_arquivo(file_id)

    return pd.read_excel(
        arquivo,
        sheet_name=sheet_name,
        header=header,
        engine="openpyxl"
    )
