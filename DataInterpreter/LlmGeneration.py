from SqlTool import execute_sql_query
from PythonTool import parse_and_execute_python_code
import re


def command_r_plus_plan(question, schema, contextualisation_model):
    """
    Génère un plan d'action basé sur la question et le schéma fourni.
    """
    schema_description = "Voici le schéma de la base de données :\n"
    for table_name, columns in schema.items():
        schema_description += (
            f"Table '{table_name}' contient les colonnes suivantes :\n"
        )
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    print("voici le schema : ", schema_description)

    prompt = (
        f"{schema_description}\n"
        f'La demande est : "{question}"\n\n'
        "**Instructions pour générer le plan d'action :**\n"
        "1. Identifiez si des informations peuvent être extraites directement des colonnes mentionnées dans le schéma. Si c'est possible, fournissez un plan pour extraire ces données directement.\n"
        "2. Si une extraction de données est nécessaire, proposez une requête SQL simple et précise pour obtenir uniquement les données pertinentes. Assurez-vous que cette requête respecte strictement le schéma fourni, sans faire d'hypothèses sur des colonnes ou des données non mentionnées.\n"
        "3. Si la demande implique une interprétation, un calcul, une visualisation ou une génération de contenu (par exemple, graphiques, calculs mathématiques, ou documents), produisez uniquement un code prêt à être exécuté, sans inclure d'explications ou de commentaires superflus.\n"
        "4. Si la demande concerne la correction ou l'amélioration d'un code existant, fournissez directement les corrections ou améliorations nécessaires sans mentionner le contexte technologique (ex. Python). Concentrez-vous sur les ajustements précis nécessaires pour répondre à la demande.\n"
        "5. Ne proposez pas de technologie ou de méthodes inutiles si ce n'est pas explicitement requis. Par exemple, pour analyser un document ou extraire des informations textuelles, limitez-vous aux étapes d'extraction ou de traitement nécessaires, sauf si la demande précise un type de sortie spécifique (chart, plot, graph, calcul, etc.).\n"
        "6. Si une conversion ou un ajustement de type (par exemple entre INTEGER et VARCHAR) est nécessaire pour résoudre des erreurs, incluez explicitement ces ajustements dans le plan.\n\n"
        "**Plan attendu :**\n"
        "- Fournissez une méthode (SQL ou étapes d'action) basée sur la nature de la question.\n"
        "- Si SQL suffit pour répondre à la question, ne proposez pas d'autres méthodes inutilement.\n"
        "- Si la question implique une visualisation ou un calcul, incluez une méthode appropriée pour produire le résultat final.\n"
        "- Si la demande inclut une correction ou amélioration de code, fournissez uniquement les étapes nécessaires pour corriger ou améliorer le code, sans mentionner le contexte technologique.\n"
        "- Le plan doit être clair, concis et strictement limité aux informations disponibles dans le schéma et la question.\n"
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
        schema_description += (
            f"Table '{table_name}' contient les colonnes suivantes :\n"
        )
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    prompt = (
        f"{schema_description}\n\n"
        f"Voici une requête SQL générée initialement :\n```sql\n{sql_query}\n```\n\n"
        "**Instructions pour DuckDB :**\n"
        "- Corrigez les erreurs éventuelles en validant les colonnes et les relations entre les tables.\n"
        "- Si une incompatibilité de types est détectée (par exemple, INTEGER vs VARCHAR), ajoutez un casting explicite.\n"
        "- Fournissez uniquement une requête SQL corrigée et optimisée dans un bloc ```sql```."
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
        column_map = {
            table: [col["name"] for col in cols] for table, cols in schema.items()
        }

        # Extraire les tables utilisées dans la requête
        tables_in_query = set(
            re.findall(r"\bFROM\s+(\w+)|\bJOIN\s+(\w+)", query, flags=re.IGNORECASE)
        )
        tables_in_query = {
            table for match in tables_in_query for table in match if table
        }

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
            raise ValueError(
                f"Colonnes ou tables manquantes dans le schéma : {missing_columns}"
            )

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
        column_map = {
            table: [col["name"] for col in cols] for table, cols in schema.items()
        }

        # Supprimer les alias inutiles
        sql_query = re.sub(r"\bAS\s+\w+\b", "", sql_query, flags=re.IGNORECASE)

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


def generate_tools_with_llm(
    plan, schema, context, sql_results, python_results, database_model, reasoning_model
):
    """
    Génère les outils nécessaires en fonction du plan.
    """
    print("Generating tools based on the plan...")
    files_generated = []

    if "SQL" in plan:
        try:
            # Extraction de la requête SQL depuis le plan
            sql_query = extract_sql_from_plan(plan)[0]
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
            f"La demande initiale est : \"{context['question']}\"\n\n"
            f"Le plan d’action défini est le suivant :\n{plan}\n\n"
            "**Instructions pour le code :**\n"
            "1. Utilisez uniquement les données exactes fournies dans les résultats ci-dessous, sans générer de valeurs fictives ou supplémentaires. "
            "2. Ne générez aucune valeur par défaut pour compenser des données manquantes ; **limitez-vous strictement aux données fournies**.\n"
            "3. Assurez-vous que le code est **complet, fonctionnel et prêt à l'emploi**, sans sections incomplètes ou nécessitant une intervention manuelle.\n"
            "4. Limitez toute **logique conditionnelle** ou **supposition**. Si une donnée est manquante, ne tentez pas de la compléter ou de la deviner ; utilisez uniquement les résultats fournis.\n"
            "5. Vous travaillez dans un **environnement Docker sans interface graphique**. Toute visualisation, comme un graphique avec matplotlib, doit être **sauvegardée dans un fichier** (par exemple, PNG pour les graphiques).\n"
            "6. **Aucune utilisation de plt.show()** n'est autorisée, car les résultats graphiques ne peuvent pas être affichés directement.\n"
            "7. Si la tâche implique des **calculs simples ou des opérations non visuelles** (par exemple, calcul de moyennes), générez simplement le code approprié sans tenter de produire des fichiers.\n"
            "8. Pour les résultats graphiques, assurez-vous que les fichiers sont sauvegardés sans vous soucier du format ou du nom (ex. utilisez des noms par défaut).\n\n"
            "9. Que la demande porte sur un graphique, un calcul, ou une autre opération, générez le code en utilisant exclusivement les valeurs extraites, en maximisant les éléments inclus pour offrir une vue complète, et sans inventer de données.\n"
            "10. Que la demande porte sur un graphique, un calcul, ou une autre opération, générez le code en utilisant exclusivement les valeurs extraites, en maximisant les éléments inclus pour offrir une vue complète, et sans inventer de données.\n"
            f"Voici les résultats SQL disponibles :\n{sql_results}\n\n"
            "**Générez un code Python complet qui exploite ces résultats comme données statiques**. Le code doit répondre directement à la demande (graphique, calcul, ou autre) et **ne jamais** faire d'appels à des bases de données comme SQLite ou des services externes pour récupérer des données."
        )

        """prompt = (
            f"Demande initiale : \"{context['question']}\"\n\n"
            f"Plan d’action défini :\n{plan}\n\n"
            "**Instructions strictes pour le code Python :**\n"
            "1. Utilisez uniquement les **données exactes** fournies dans les résultats SQL ci-dessous, sans générer de valeurs fictives ou supplémentaires.\n"
            "2. Ne générez aucune valeur par défaut pour compenser des données manquantes ; **limitez-vous strictement aux données fournies**.\n"
            "3. Assurez-vous que le code est **complet, fonctionnel et prêt à l'emploi**, sans sections incomplètes ou nécessitant une intervention manuelle.\n"
            "4. Limitez toute **logique conditionnelle** ou **supposition**. Si une donnée est manquante, ne tentez pas de la compléter ou de la deviner ; utilisez uniquement les résultats fournis.\n"
            "5. Vous travaillez dans un **environnement Docker sans interface graphique**. Toute visualisation, comme un graphique avec matplotlib, doit être **sauvegardée dans un fichier** (par exemple, PNG pour les graphiques).\n"
            "6. **Aucune utilisation de plt.show()** n'est autorisée, car les résultats graphiques ne peuvent pas être affichés directement.\n"
            "7. Si la tâche implique des **calculs simples ou des opérations non visuelles** (par exemple, calcul de moyennes), générez simplement le code approprié sans tenter de produire des fichiers.\n"
            "8. Pour les résultats graphiques, assurez-vous que les fichiers sont sauvegardés sans vous soucier du format ou du nom (ex. utilisez des noms par défaut).\n\n"
            f"Voici les résultats SQL disponibles :\n{sql_results}\n\n"
            "**Générez un code Python complet qui exploite ces résultats comme données statiques**. Le code doit répondre directement à la demande (graphique, calcul, ou autre) et **ne jamais** faire d'appels à des bases de données comme SQLite ou des services externes pour récupérer des données."
        )"""

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
        f"Contexte final :\n\n"
        f"Question : \"{context['question']}\"\n"
        f"Résultats SQL : {sql_results}\n"
        f"Résultats Python : {python_results}\n\n"
        f"{files_section}\n\n"
        "**Réponse finale :**\n"
        "- Résumez le contenu de manière concise en expliquant de quoi traite le document ou en répondant précisément à la demande.\n"
        "- Ne faites pas de raisonnement intermédiaire ni d'ajouts spéculatifs. Utilisez uniquement les informations fournies dans le contexte final pour formuler la réponse.\n\n"
        "**Directives spécifiques :**\n"
        "1. Si des fichiers ont été générés (mentionnés ci-dessus), expliquez brièvement leur contenu et leur utilité en lien avec la demande.\n"
        "2. Si la réponse contient des résultats chiffrés, assurez-vous qu'ils sont bien contextualisés pour une compréhension immédiate.\n"
        "3. Ne donnez aucune explication technique non demandée par la question initiale. Limitez-vous à une explication compréhensible pour l'utilisateur final.\n"
        "4. Mentionnez les liens des fichiers créés (listés ci-dessus) de manière explicite dans la réponse.\n"
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
