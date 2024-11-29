from SqlTool import execute_sql_query
from PythonTool import parse_and_execute_python_code


def command_r_plus_plan(question, schema, contextualisation_model):
    schema_description = "Voici le schéma de la base de données :\n"
    # Mise en forme du schéma de la base de donnée
    for table_name, columns in schema.items():
        schema_description += (
            f"Table '{table_name}' contient les colonnes suivantes :\n"
        )
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    prompt = (
        f"{schema_description}\n"
        f'La demande est : "{question}"\n\n'
        "**Plan d'action :**\n"
        "- Étape 1 : Identifiez si des informations sont disponibles directement dans les colonnes, et précisez les valeurs de colonne ou types d’information à extraire.\n"
        "- Étape 2 : Si la demande requiert une extraction de données (comme texte, OCR, code), suggérez des requêtes SQL simples et précises pour obtenir un échantillon représentatif de chaque type de donnée disponible, ou pour répondre à des questions spécifiques. Cette requete doit uniquement se baser sur le schéma que je te fournis. Tu ne dois rien ajouter qui ne soit pas mentionné dans le schéma de la base de donnée.\n"
        "- Étape 3 : Si la demande implique une interprétation (par exemple, analyser le contenu ou trouver des mots-clés), expliquez brièvement comment interpréter les résultats SQL sans utiliser d'étapes de réflexion intermédiaires ou de raisonnement complexe.\n"
        "Répondez uniquement aux besoins précis de la question sans suggérer de code Python, sauf si spécifiquement requis pour traiter un type de donnée extrait. **Si la demande inclut des termes comme chart, plot, graph, ou fait référence à un calcul ou une visualisation, générez du code pour créer un graphique ou effectuer le calcul.  Le plan doit contenir une seule méthode (SQL ou autre) en fonction de ce qui est nécessaire pour traiter la demande."
    )

    print(
        f"Generating plan from Command R Plus for question: {question} with schema: {schema_description}"
    )
    plan = contextualisation_model.invoke(prompt)
    print(f"Plan généré par Command R Plus : {plan}")
    return plan


def generate_tools_with_llm(
    plan,
    schema,
    context,
    sql_results,
    python_results,
    database_model,
    reasoning_model,
):
    print("Génération des outils en fonction du plan...")
    schema_description = "Voici le schéma de la base de données :\n"
    # Mise en forme du schéma de la base de donnée
    for table_name, columns in schema.items():
        schema_description += (
            f"Table '{table_name}' contient les colonnes suivantes :\n"
        )
        for column in columns:
            schema_description += f"  - '{column['name']}' (type: {column['type']})\n"
        schema_description += "\n"

    if "SQL" in plan:
        print("Génération d'une requête SQL...")
        prompt = (
            f"{schema_description}\n\n"
            f"Plan d’action :\n{plan}\n\n"
            f"Demande : \"{context['question']}\"\n\n"
            "**Requête SQL :**\n"
            "- Formulez une requête SQL simple qui extrait uniquement les informations nécessaires du schéma de la base de données pour répondre à la question ou aux étapes du plan.\n"
            "- La requête doit être directe, sans clauses complexes (comme des agrégations avancées ou des jointures inutiles), sauf si spécifiquement nécessaire.\n"
            "Le point majeur est de rester fidèle, ce que dit exactement le plan pour les requetes SQL il faut le faire à l'identique, tu prends la requete qu'il y a souvent dans une partie souvent nommé dans le plan : (Voici une requête SQL) ou autre chose de ce genre"
        )
        sql_tool = database_model.invoke(prompt)
        sql_results = execute_sql_query(sql_tool)
        context["sql_results"] = sql_results

    if "Python" or "python" in plan:
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
