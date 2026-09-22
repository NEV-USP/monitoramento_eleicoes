from sqlalchemy import text

from database.connection import engine


def executar_consulta(connection, sql):
    resultado = connection.execute(text(sql))
    return resultado.scalar()


def validar_contagens(connection):
    consultas = {
        "Coletas": "SELECT COUNT(*) FROM coletas",
        "Candidatos": "SELECT COUNT(*) FROM candidatos",
        "Perfis sociais": "SELECT COUNT(*) FROM perfis_sociais",
        "Métricas de perfil": "SELECT COUNT(*) FROM metricas_perfil",
        "Posts": "SELECT COUNT(*) FROM posts",
        "Métricas de posts": "SELECT COUNT(*) FROM metricas_posts",
    }

    print("\nCONTAGENS")
    print("-" * 60)

    for nome, sql in consultas.items():
        quantidade = executar_consulta(connection, sql)
        print(f"{nome:<25} {quantidade}")


def validar_duplicidades(connection):
    consultas = {
        "Coletas duplicadas": """
            SELECT COUNT(*)
            FROM (
                SELECT grupo, subgrupo, data_inicio, data_fim
                FROM coletas
                GROUP BY grupo, subgrupo, data_inicio, data_fim
                HAVING COUNT(*) > 1
            ) duplicadas
        """,

        "Perfis duplicados": """
            SELECT COUNT(*)
            FROM (
                SELECT profile_id, network
                FROM perfis_sociais
                WHERE profile_id IS NOT NULL
                GROUP BY profile_id, network
                HAVING COUNT(*) > 1
            ) duplicados
        """,

        "Posts duplicados": """
            SELECT COUNT(*)
            FROM (
                SELECT message_id
                FROM posts
                WHERE message_id IS NOT NULL
                GROUP BY message_id
                HAVING COUNT(*) > 1
            ) duplicados
        """,

        "Métricas de perfil duplicadas": """
            SELECT COUNT(*)
            FROM (
                SELECT perfil_id, coleta_id
                FROM metricas_perfil
                GROUP BY perfil_id, coleta_id
                HAVING COUNT(*) > 1
            ) duplicadas
        """,

        "Métricas de posts duplicadas": """
            SELECT COUNT(*)
            FROM (
                SELECT post_id, coleta_id
                FROM metricas_posts
                GROUP BY post_id, coleta_id
                HAVING COUNT(*) > 1
            ) duplicadas
        """,
    }

    print("\nDUPLICIDADES")
    print("-" * 60)

    tudo_ok = True

    for nome, sql in consultas.items():
        quantidade = executar_consulta(connection, sql)

        if quantidade == 0:
            status = "✓"
        else:
            status = "✗"
            tudo_ok = False

        print(f"{status} {nome:<35} {quantidade}")

    return tudo_ok


def validar_orfaos(connection):
    consultas = {
        "Métricas de perfil sem perfil": """
            SELECT COUNT(*)
            FROM metricas_perfil mp
            LEFT JOIN perfis_sociais ps
                ON ps.id = mp.perfil_id
            WHERE ps.id IS NULL
        """,

        "Métricas de perfil sem coleta": """
            SELECT COUNT(*)
            FROM metricas_perfil mp
            LEFT JOIN coletas c
                ON c.id = mp.coleta_id
            WHERE c.id IS NULL
        """,

        "Posts sem perfil": """
            SELECT COUNT(*)
            FROM posts p
            LEFT JOIN perfis_sociais ps
                ON ps.id = p.perfil_id
            WHERE ps.id IS NULL
        """,

        "Métricas de posts sem post": """
            SELECT COUNT(*)
            FROM metricas_posts mp
            LEFT JOIN posts p
                ON p.id = mp.post_id
            WHERE p.id IS NULL
        """,

        "Métricas de posts sem coleta": """
            SELECT COUNT(*)
            FROM metricas_posts mp
            LEFT JOIN coletas c
                ON c.id = mp.coleta_id
            WHERE c.id IS NULL
        """,

        "Perfis sem candidato": """
            SELECT COUNT(*)
            FROM perfis_sociais ps
            LEFT JOIN candidatos c
                ON c.id = ps.candidato_id
            WHERE c.id IS NULL
        """,
    }

    print("\nREGISTROS ÓRFÃOS")
    print("-" * 60)

    tudo_ok = True

    for nome, sql in consultas.items():
        quantidade = executar_consulta(connection, sql)

        if quantidade == 0:
            status = "✓"
        else:
            status = "✗"
            tudo_ok = False

        print(f"{status} {nome:<35} {quantidade}")

    return tudo_ok


def validar_coletas(connection):
    sql = """
        SELECT
            grupo,
            subgrupo,
            semana,
            data_inicio,
            data_fim
        FROM coletas
        ORDER BY data_inicio, grupo, subgrupo
    """

    resultado = connection.execute(text(sql))

    print("\nCOLETAS")
    print("-" * 80)

    for linha in resultado:
        grupo = linha.grupo
        subgrupo = linha.subgrupo or "-"
        periodo = (
            f"{linha.data_inicio.strftime('%d/%m/%Y')}"
            f" - "
            f"{linha.data_fim.strftime('%d/%m/%Y')}"
        )

        print(
            f"{grupo:<25} "
            f"{subgrupo:<25} "
            f"Semana {linha.semana:<3} "
            f"{periodo}"
        )


def validar_banco():
    print("=" * 70)
    print("VALIDAÇÃO DO BANCO DE DADOS")
    print("=" * 70)

    with engine.connect() as connection:

        validar_contagens(connection)

        duplicidades_ok = validar_duplicidades(connection)

        orfaos_ok = validar_orfaos(connection)

        validar_coletas(connection)

    print("\n" + "=" * 70)

    if duplicidades_ok and orfaos_ok:
        print("STATUS: ✓ BANCO ÍNTEGRO")
    else:
        print("STATUS: ✗ FORAM ENCONTRADOS PROBLEMAS")

    print("=" * 70)


if __name__ == "__main__":
    validar_banco()