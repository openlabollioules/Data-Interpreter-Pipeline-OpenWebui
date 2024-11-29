import duckdb


def execute_sql_query(query):
    try:
        print(f"Execution requete sql: {query}")
        connection = duckdb.connect("/app/db/my_database.duckdb")
        # Execution requete SQL
        results = connection.execute(query).fetchall()
        # Récupération des colones utilisées
        column_names = [desc[0] for desc in connection.description]
        formatted_results = [dict(zip(column_names, row)) for row in results]

        print(f"resultat requete SQL: {formatted_results}")
        return formatted_results
    except Exception as e:
        print(f"Error during SQL execution: {e}")
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
