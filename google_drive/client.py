
import json
import os
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build


BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "service_account.json"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly"
]


def criar_cliente():
    credenciais_json = os.getenv(
        "GOOGLE_SERVICE_ACCOUNT_JSON"
    )

    if credenciais_json:
        # Railway / ambiente de produção
        dados = json.loads(credenciais_json)

        credenciais = (
            service_account.Credentials
            .from_service_account_info(
                dados,
                scopes=SCOPES
            )
        )

    else:
        # Ambiente local
        if not CREDENTIALS_FILE.exists():
            raise FileNotFoundError(
                "Credenciais do Google Drive não encontradas. "
                "Configure GOOGLE_SERVICE_ACCOUNT_JSON "
                "ou coloque service_account.json em "
                "google_drive/."
            )

        credenciais = (
            service_account.Credentials
            .from_service_account_file(
                CREDENTIALS_FILE,
                scopes=SCOPES
            )
        )

    return build(
        "drive",
        "v3",
        credentials=credenciais
    )