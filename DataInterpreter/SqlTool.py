import duckdb


def execute_sql_query(query):
    """
    Exécute une requête SQL sur une base DuckDB et retourne les résultats formatés.
    """
    try:
        print(f"Exécution de la requête SQL : {query}")
        connection = duckdb.connect("my_database.duckdb")

        # Exécution de la requête SQL
        cursor = connection.execute(query)
        results = cursor.fetchall()

        # Récupération des noms de colonnes
        column_names = [desc[0] for desc in cursor.description]

        # Formatage des résultats sous forme de liste de dictionnaires
        formatted_results = [dict(zip(column_names, row)) for row in results]

        print(f"Résultats de la requête SQL : {formatted_results}")
        return formatted_results

    except Exception as e:
        print(f"Erreur lors de l'exécution de la requête SQL : {e}")
        return None

    finally:
        connection.close()


def get_schema(con):
    schema_info = {}
    try:
        table_names = con.execute("SHOW TABLES").fetchall()
        # Récupération des colones présentes dans chaque tables
        for table in table_names:
            table_name = table[0]

            columns_info = con.execute(f"PRAGMA table_info('{table_name}')").fetchall()

            schema_info[table_name] = [
                {"name": column[1], "type": column[2]} for column in columns_info
            ]

            # Afficher le schéma pour le débogage
            print(f"Schéma de la table '{table_name}':")
            for column in columns_info:
                print(f"- Colonne: {column[1]}, Type: {column[2]}")

    except Exception as e:
        print(f"Error fetching schema: {e}")

    return schema_info
