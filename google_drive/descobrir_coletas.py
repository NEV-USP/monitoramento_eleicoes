from google_drive.drive import (
    encontrar_pasta,
    listar_pastas,
    encontrar_arquivos_por_prefixo,
)

import os

from dotenv import load_dotenv


load_dotenv()


def descobrir_semanas(pasta_id):
    """
    Descobre todas as pastas cujo nome começa com 'Semana '.
    """

    pastas = listar_pastas(pasta_id)

    return sorted(
        [
            pasta
            for pasta in pastas
            if pasta["name"].lower().startswith("semana ")
        ],
        key=lambda pasta: pasta["name"]
    )


def descobrir_arquivos_semana(semana_id):
    """
    Localiza os arquivos Benchmarking e Content dentro de uma semana.
    """

    benchmarking = encontrar_arquivos_por_prefixo(
        semana_id,
        "Benchmarking"
    )

    content = encontrar_arquivos_por_prefixo(
        semana_id,
        "Content"
    )

    return {
        "benchmarking": benchmarking,
        "content": content,
    }


def main():

    raiz_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    if not raiz_id:
        raise ValueError(
            "GOOGLE_DRIVE_FOLDER_ID não configurado no .env"
        )

    coletas = encontrar_pasta(
        raiz_id,
        "Coletas"
    )

    if not coletas:
        raise ValueError(
            "Pasta 'Coletas' não encontrada."
        )

    grupos = listar_pastas(coletas["id"])

    for grupo in grupos:

        print("\n" + "=" * 60)
        print(f"GRUPO: {grupo['name']}")
        print("=" * 60)

        # Primeiro nível
        semanas = descobrir_semanas(grupo["id"])

        # Caso o grupo tenha subgrupos, como Governos
        if not semanas:

            subgrupos = listar_pastas(grupo["id"])

            for subgrupo in subgrupos:

                print(f"\n  SUBGRUPO: {subgrupo['name']}")

                semanas = descobrir_semanas(
                    subgrupo["id"]
                )

                for semana in semanas:

                    print(f"\n    {semana['name']}")

                    arquivos = descobrir_arquivos_semana(
                        semana["id"]
                    )

                    for arquivo in arquivos["benchmarking"]:
                        print(
                            f"      Benchmarking: "
                            f"{arquivo['name']}"
                        )

                    for arquivo in arquivos["content"]:
                        print(
                            f"      Content: "
                            f"{arquivo['name']}"
                        )

        else:

            for semana in semanas:

                print(f"\n  {semana['name']}")

                arquivos = descobrir_arquivos_semana(
                    semana["id"]
                )

                for arquivo in arquivos["benchmarking"]:
                    print(
                        f"    Benchmarking: "
                        f"{arquivo['name']}"
                    )

                for arquivo in arquivos["content"]:
                    print(
                        f"    Content: "
                        f"{arquivo['name']}"
                    )


if __name__ == "__main__":
    main()