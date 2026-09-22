from pathlib import Path

from database.import_coletas import importar_coleta
from database.import_perfis import importar_perfis
from database.import_metricas_perfil import importar_metricas_perfil
from database.import_posts import importar_posts


def encontrar_semanas(pasta_raiz):
    """
    Encontra todas as pastas semanais dentro da pasta raiz.
    """

    pasta_raiz = Path(pasta_raiz)

    if not pasta_raiz.exists():
        raise FileNotFoundError(
            f"Pasta não encontrada: {pasta_raiz}"
        )

    semanas = [
        pasta
        for pasta in pasta_raiz.rglob("*")
        if pasta.is_dir()
        and pasta.name.lower().startswith("semana ")
    ]

    return sorted(semanas)


def importar_diretorio(pasta_raiz):

    semanas = encontrar_semanas(pasta_raiz)

    if not semanas:
        print("Nenhuma pasta semanal encontrada.")
        return

    print("=" * 70)
    print("IMPORTAÇÃO DO DIRETÓRIO")
    print("=" * 70)
    print(f"Pasta raiz: {Path(pasta_raiz).resolve()}")
    print(f"Semanas encontradas: {len(semanas)}")

    sucessos = 0
    erros = []

    for numero, pasta in enumerate(semanas, start=1):

        print()
        print("=" * 70)
        print(f"SEMANA {numero}/{len(semanas)}")
        print("=" * 70)
        print(f"Pasta: {pasta}")

        try:

            # ----------------------------------------------------------
            # 1. COLETA
            # ----------------------------------------------------------

            print("\n[1/4] Importando coleta...")
            importar_coleta(pasta)

            # ----------------------------------------------------------
            # 2. CANDIDATOS E PERFIS
            # ----------------------------------------------------------

            print("\n[2/4] Importando candidatos e perfis...")
            importar_perfis(pasta)

            # ----------------------------------------------------------
            # 3. MÉTRICAS DE PERFIL
            # ----------------------------------------------------------

            print("\n[3/4] Importando métricas de perfil...")
            importar_metricas_perfil(pasta)

            # ----------------------------------------------------------
            # 4. POSTS E MÉTRICAS
            # ----------------------------------------------------------

            print("\n[4/4] Importando posts e métricas...")
            importar_posts(pasta)

            sucessos += 1

            print("\n✓ Semana importada com sucesso.")

        except Exception as erro:

            erros.append({
                "pasta": str(pasta),
                "erro": str(erro),
            })

            print("\n✗ ERRO NA IMPORTAÇÃO")
            print(erro)

    # ------------------------------------------------------------------
    # RELATÓRIO FINAL
    # ------------------------------------------------------------------

    print()
    print("=" * 70)
    print("IMPORTAÇÃO FINALIZADA")
    print("=" * 70)

    print(f"Semanas encontradas: {len(semanas)}")
    print(f"Importadas com sucesso: {sucessos}")
    print(f"Com erro: {len(erros)}")

    if erros:

        print()
        print("SEMANAS COM ERRO")
        print("-" * 70)

        for erro in erros:
            print(f"\nPasta: {erro['pasta']}")
            print(f"Erro:  {erro['erro']}")


if __name__ == "__main__":

    pasta = input(
        "Digite o caminho da pasta raiz das coletas: "
    ).strip()

    importar_diretorio(pasta)