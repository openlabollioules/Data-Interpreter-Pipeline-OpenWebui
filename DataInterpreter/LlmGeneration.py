from SqlTool import execute_sql_query
from PythonTool import parse_and_execute_python_code
import re

def command_r_plus_plan(question, schema, contextualisation_model):
    """
    Génère un plan d'action basé sur la question et le schéma fourni.
    """
    schema_description = "Voici le schéma de la base de données :\n"
    for table_name, columns in schema.items():
        schema_description += f"Table '{table_name}' contient les colonnes suivantes :\n"
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    print("voici le schema : ", schema_description)

    prompt = (
        f'The request is: "{question}"\n\n'
        "**Instructions to generate the action plan:**\n"
        "1. Identify if information can be directly extracted from the columns mentioned in the schema. If possible, provide a plan to directly extract this data.\n"
        f"2. If data extraction is necessary, propose a simple and precise SQL query to retrieve only the relevant data. Ensure that this query strictly adheres to the provided schema, without making assumptions about unspecified columns or tables. You must not invent tables or columns; use only this schema: {schema_description}\n"
        "3. If the request involves interpretation, calculation, visualization, or content generation (e.g., charts, mathematical calculations, or documents), produce only executable code without including unnecessary explanations or comments.\n"
        "4. If the request involves correcting or improving existing code, provide the necessary corrections or improvements directly without referencing the technological context (e.g., Python). Focus on the precise adjustments needed to address the request.\n"
        "5. Do not propose unnecessary technologies or methods unless explicitly required. For instance, when analyzing a document or extracting textual information, limit the steps to necessary extraction or processing, unless the request specifies a specific type of output (chart, plot, graph, calculation, etc.).\n"
        "6. If a type conversion or adjustment (e.g., between INTEGER and VARCHAR) is required to resolve errors, explicitly include these adjustments in the plan.\n\n"
        "**Expected Plan:**\n"
        "- Provide a method (SQL or action steps) based on the nature of the question.\n"
        "- If SQL is sufficient to answer the question, do not propose other unnecessary methods.\n"
        "- If the question involves visualization or calculation, include an appropriate method to produce the final result.\n"
        "- If the request includes code correction or improvement, provide only the necessary steps to correct or improve the code, without referencing the technological context.\n"
        "- The plan must be clear, concise, and strictly limited to the information available in the schema and the question.\n"
    )

    print(f"Generating plan for question: {question}")
    plan = contextualisation_model.invoke(prompt)
    print(f"Generated Plan: {plan}")
    return plan

def adjust_sql_query_with_duckdb(sql_query, schema, duckdb_model):
    """
    Ajuste une requête SQL en fonction du moteur DuckDB, en gérant les erreurs de types.
    """
    schema_description = "Voici le schéma de la base de données pour DuckDB :\n"
    for table_name, columns in schema.items():
        schema_description += f"Table '{table_name}' contient les colonnes suivantes :\n"
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    prompt = (
        f"{schema_description}\n\n"
        f"Here is an initially generated SQL query:\n```sql\n{sql_query}\n```\n\n"
        "**Instructions for DuckDB:**\n"
        "- Fix any errors by validating the columns and relationships between tables.\n"
        "- If a type mismatch is detected (e.g., INTEGER vs VARCHAR), add explicit casting.\n"
        "- Provide only a corrected and optimized SQL query within a ```sql``` block."
    )

    print("Adjusting SQL query with DuckDB model...")
    try:
        adjusted_query = duckdb_model.invoke(prompt)
        print(f"Adjusted SQL query: {adjusted_query}")
        return adjusted_query
    except Exception as e:
        print(f"Erreur lors de l'ajustement de la requête SQL : {e}")
        raise

def validate_sql_with_schema(schema, query):
    """
    Valide que les colonnes utilisées dans la requête existent dans les tables référencées.
    """
    print("Validating SQL query against schema...")
    try:
        column_map = {table: [col['name'] for col in cols] for table, cols in schema.items()}

        # Extraire les tables utilisées dans la requête
        tables_in_query = set(re.findall(r"\bFROM\s+(\w+)|\bJOIN\s+(\w+)", query, flags=re.IGNORECASE))
        tables_in_query = {table for match in tables_in_query for table in match if table}

        # Vérifier les colonnes référencées dans les tables utilisées
        missing_columns = []
        for table in tables_in_query:
            if table in column_map:
                for column in re.findall(rf"{table}\.(\w+)", query):
                    if column not in column_map[table]:
                        missing_columns.append(f"{table}.{column}")
            else:
                missing_columns.append(f"Table inconnue référencée : {table}")

        if missing_columns:
            raise ValueError(f"Colonnes ou tables manquantes dans le schéma : {missing_columns}")

        print("SQL query validation successful.")
        return True
    except Exception as e:
        print(f"Erreur de validation SQL : {e}")
        raise


def clean_sql_query(sql_query, schema):
    """
    Nettoie et simplifie une requête SQL générée :
    - Supprime les alias inutiles.
    - Remplace les colonnes ambiguës par leur nom complet uniquement si elles sont utilisées dans la requête.
    """
    print("Cleaning SQL query...")
    try:
        # Construire une map des colonnes par table
        column_map = {table: [col['name'] for col in cols] for table, cols in schema.items()}

        # Supprimer les alias inutiles
        #sql_query = re.sub(r"\bAS\s+\w+\b", "", sql_query, flags=re.IGNORECASE)

        # Ajouter les noms complets uniquement pour les colonnes ambiguës
        for table, columns in column_map.items():
            for column in columns:
                pattern = rf"(?<!\.)\b{column}\b(?!\.)"  # Colonne sans préfixe
                replacement = f"{table}.{column}"
                if re.search(pattern, sql_query):  # Vérifier si la colonne existe
                    sql_query = re.sub(pattern, replacement, sql_query)

        # Supprimer les espaces multiples et extra blancs
        sql_query = re.sub(r"\s+", " ", sql_query).strip()
        print("Cleaned SQL query:", sql_query)
        return sql_query
    except Exception as e:
        print(f"Erreur lors du nettoyage de la requête SQL : {e}")
        raise


def extract_sql_from_plan(plan_text):
    """
    Extrait toutes les requêtes SQL d'un plan.
    """
    print("Extracting SQL queries from plan...")
    sql_pattern = re.compile(r"```sql(.*?)```", re.DOTALL)
    matches = sql_pattern.findall(plan_text)
    if matches:
        print(f"Extracted SQL queries: {matches}")
        return [match.strip() for match in matches]
    raise ValueError("Aucune requête SQL trouvée dans le plan.")


def generate_tools_with_llm(plan, schema, context, sql_results, python_results, database_model, reasoning_model):
    """
    Génère les outils nécessaires en fonction du plan.
    """
    print("Generating tools based on the plan...")
    files_generated = []

    if "SQL" in plan:
        try:
            # Extraction de la requête SQL depuis le plan
            sql_query = extract_sql_from_plan(plan)[-1]
            print(f"Initial SQL Query: {sql_query}")

            # Nettoyage et validation des étapes SQL
            sql_query = clean_sql_query(sql_query, schema)
            print(f"Cleaned SQL Query: {sql_query}")

            validate_sql_with_schema(schema, sql_query)

            # Ajustement avec DuckDB (type casting ou corrections spécifiques)
            sql_query = adjust_sql_query_with_duckdb(sql_query, schema, database_model)
            print(f"Adjusted SQL Query: {sql_query}")

            # Exécuter la requête ajustée
            sql_results = execute_sql_query(sql_query)
            print(f"SQL Query Results: {sql_results}")
            context["sql_results"] = sql_results

        except Exception as e:
            print(f"Erreur lors de l'exécution de la requête SQL : {e}")
            context["sql_results"] = None

    if "Python" in plan or "python" in plan:
        print("Génération de code Python...")
        print("les voila:", sql_results)
        prompt = (
            f'The initial request is: "{context["question"]}"\n\n'
            f"The defined action plan is as follows:\n{plan}\n\n"
            "**Instructions for the code:**\n"
            "1. Use only the exact data provided in the results below, without generating any fictitious or additional values.\n"
            "2. Do not generate default values to compensate for missing data; **strictly limit yourself to the provided data**.\n"
            "3. Ensure the code is **complete, functional, and ready to use**, with no incomplete sections or requiring manual intervention.\n"
            "4. Limit any **conditional logic** or **assumptions**. If data is missing, do not attempt to complete or guess it; use only the provided results.\n"
            "5. You are working in a **Docker environment without a graphical interface**. Any visualization, such as a graph using matplotlib, must be **saved to a file** (e.g., PNG for graphs).\n"
            "6. **No use of plt.show()** is allowed, as graphical results cannot be displayed directly.\n"
            "7. If the task involves **simple calculations or non-visual operations** (e.g., calculating averages), generate the appropriate code without attempting to produce files.\n"
            "8. For graphical results, ensure that files are saved without worrying about format or naming (e.g., use default names).\n\n"
            "9. Whether the request involves a graph, a calculation, or another operation, generate the code using only the extracted values, maximizing the included elements to provide a complete view, without inventing data.\n"
            "10. Whether the request involves a graph, a calculation, or another operation, generate the code using only the extracted values, maximizing the included elements to provide a complete view, without inventing data.\n"
            f"Here are the available SQL results:\n{sql_results}\n\n"
            "**Generate complete Python code that uses these results as static data.** The code must directly address the request (graph, calculation, or other) and **never** make calls to databases such as SQLite or external services to retrieve data."
        )

        python_tool = reasoning_model.invoke(prompt)
        context, python_results, files_generated = parse_and_execute_python_code(
            python_tool, context, sql_results
        )

    return context, python_results, sql_results, files_generated

def generate_final_response_with_llama(
    context, sql_results, python_results, reasoning_model, files_generated
):
    print("avant la réponse", files_generated)
    # Créer la section des fichiers générés
    files_section = ""
    if files_generated:
        files_section = "\nFichiers générés :\n" + "\n".join(
            [f"- {file}" for file in files_generated]
        )

    # Construction du prompt
    print(f"Generating final response with context: {context}")
    prompt = (
        f"Final context:\n\n"
        f"Question: \"{context['question']}\"\n"
        f"SQL Results: {sql_results}\n"
        f"Python Results: {python_results}\n\n"
        f"{files_section}\n\n"
        "**Final Answer:**\n"
        "- Summarize the content concisely by explaining what the document is about or by precisely answering the request.\n"
        "- Avoid intermediate reasoning or speculative additions. Use only the information provided in the final context to formulate the response.\n\n"
        "**Specific Guidelines:**\n"
        "1. If files have been generated (mentioned above), briefly explain their content and relevance to the request.\n"
        "2. If the response includes numerical results, ensure they are well-contextualized for immediate understanding.\n"
        "3. Do not provide any technical explanations not requested by the initial question. Focus on delivering an explanation understandable to the end user.\n"
        "4. Explicitly mention the links to the created files (listed above) in the response."
    )

    # Appel au modèle pour générer la réponse finale
    final_response = reasoning_model.invoke(prompt)
    print("après la réponse", files_generated)

    # Ajouter les liens des fichiers générés à la fin de la réponse, s'ils existent
    if files_generated:
        links_section = "\n\nLiens des fichiers générés :\n" + "\n".join(
            [f"- {file}" for file in files_generated]
        )
        final_response += links_section

    # Afficher la réponse finale
    print(f"Final response: {final_response}")
    return final_response

