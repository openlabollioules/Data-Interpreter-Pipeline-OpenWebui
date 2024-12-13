import duckdb
import os
import json
import numpy as np
import pandas as pd
import re
import io
from PdfExtension import extract_pdf
from PythonExtension import extract_python


def remove_database_file():
    database_path = "/app/db/my_database.duckdb"
    if os.path.exists(database_path):
        os.remove(database_path)
        print(f"Fichier '{database_path}' supprimé avec succès.")
    else:
        print(f"Le fichier '{database_path}' n'existe pas.")


def clean_column_name(column_name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", column_name).lower()


def prepare_database(filepaths=None, ollama_model=None, start=False):

    if filepaths is not None and start == True:
        remove_database_file()

    all_filepaths = []
    for path in filepaths:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    all_filepaths.append(os.path.join(root, file))
        else:
            all_filepaths.append(path)

    conn = duckdb.connect("/app/db/my_database.duckdb")
    print(f"Files to be processed: {all_filepaths}")
    if all_filepaths:

        for filepath in all_filepaths:
            print(f"Processing file: {filepath}")

            # Déterminer le type de fichier et charger les données
            data = {}
            if filepath.endswith(".xls"):
                print("Loading Excel (.xls) file...")
                data = pd.read_excel(filepath, sheet_name=None, engine="xlrd")
            elif filepath.endswith(".xlsx"):
                print("Loading Excel (.xlsx) file...")
                data = pd.read_excel(filepath, sheet_name=None, engine="openpyxl")
            elif filepath.endswith(".xlsm"):
                print("Loading Excel (.xlsm) file...")
                data = pd.read_excel(filepath, sheet_name=None, engine="openpyxl")
            elif filepath.endswith(".csv"):
                print("Loading CSV file...")
                data = {"sheet1": pd.read_csv(filepath, sep=";")}
            elif filepath.endswith(".json"):
                print("Loading JSON file...")
                with open(filepath, "r", encoding="utf-8") as f:
                    json_data = json.load(f)
                data = {"main": pd.json_normalize(json_data, sep="_")}
            elif filepath.endswith(".pdf"):
                print("Processing PDF file...")
                try:
                    extracted_text, images_data = extract_pdf(filepath, ollama_model)

                    # Conversion des données extraites en DataFrame
                    if extracted_text:
                        text_json = json.dumps(extracted_text)
                        text_df = pd.read_json(io.StringIO(text_json))
                        data["text"] = text_df

                    if images_data:
                        images_json = json.dumps(images_data)
                        images_df = pd.read_json(io.StringIO(images_json))
                        data["images"] = images_df

                except Exception as e:
                    print(f"Unexpected error processing PDF file '{filepath}': {e}")
                    continue
            elif filepath.endswith(".py"):
                print("Processing Python file...")
                try:
                    extracted_data = extract_python(filepath)

                    # Imprimer le contenu complet extrait du fichier Python avant la conversion en DataFrame
                    print("\n--- Extracted Python Data ---")
                    print(json.dumps(extracted_data, indent=4, ensure_ascii=False))

                    # Conversion des données extraites en DataFrames distincts
                    if "functions" in extracted_data and extracted_data["functions"]:
                        functions_df = pd.DataFrame(extracted_data["functions"])
                        data["functions"] = functions_df
                        print("Functions DataFrame created.")

                    if "classes" in extracted_data and extracted_data["classes"]:
                        classes_df = pd.DataFrame(extracted_data["classes"])
                        data["classes"] = classes_df
                        print("Classes DataFrame created.")

                    if "imports" in extracted_data and extracted_data["imports"]:
                        imports_df = pd.DataFrame(extracted_data["imports"])
                        data["imports"] = imports_df
                        print("Imports DataFrame created.")

                    # Ajouter le code brut du module dans un DataFrame
                    if "module_code" in extracted_data:
                        module_code_df = pd.DataFrame(
                            [{"module_code": extracted_data["module_code"]}]
                        )
                        data["module_code"] = module_code_df
                        print("Module code DataFrame created.")

                except Exception as e:
                    print(f"Unexpected error processing Python file '{filepath}': {e}")
                    continue
            else:
                raise ValueError(
                    "Le fichier n'est ni un fichier .xls, .xlsx, .xlsm, .csv, .json, .pdf, ni un fichier Python."
                )

            # Traiter chaque feuille ou table du fichier
            for sheet_name, df in data.items():
                base_table_name = re.sub(
                    r"[^a-zA-Z0-9_]",
                    "_",
                    os.path.splitext(os.path.basename(filepath))[0].strip().lower(),
                )
                table_name = f"{base_table_name}_{clean_column_name(sheet_name)}"
                print(f"Creating table '{table_name}' for sheet '{sheet_name}'.")

                # Créer la table principale
                create_table_from_dataframe(conn, df, table_name)
                print(
                    f"Base data from '{sheet_name}' loaded into table '{table_name}'."
                )

                # Gérer les données imbriquées si elles existent
                handle_nested_data(conn, df, table_name)

    return conn


def create_table_from_dataframe(conn, df, table_name):
    # Déterminer le schéma des colonnes avec des types explicites
    column_definitions = []
    for column_name, dtype in df.dtypes.items():
        column_name_cleaned = clean_column_name(column_name)
        column_type = map_dtype_to_duckdb_type(dtype, df[column_name])
        column_definitions.append(f'"{column_name_cleaned}" {column_type}')

    column_definitions_str = ", ".join(column_definitions)

    # Créer la table en DuckDB
    create_table_query = (
        f"CREATE TABLE IF NOT EXISTS {table_name} ({column_definitions_str})"
    )
    conn.execute(create_table_query)

    # Insérer les données par morceaux
    chunks = np.array_split(df, np.ceil(len(df) / 500))
    for chunk in chunks:
        conn.register("temp_chunk", chunk)
        conn.execute(f"INSERT INTO {table_name} SELECT * FROM temp_chunk")


def handle_nested_data(conn, df, base_table_name):
    """Gère les colonnes qui contiennent des données imbriquées (listes ou dictionnaires) de manière dynamique et relationnelle."""
    for column in df.columns:
        if df[column].apply(lambda x: isinstance(x, (list, dict))).any():
            nested_entries = []

            # Chercher un champ clé potentiellement existant dans la table principale
            parent_key_column = None
            for col in df.columns:
                if col.endswith("_id"):
                    parent_key_column = col
                    break

            for index, row in df.iterrows():
                value = row[column]
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            if parent_key_column:
                                item[parent_key_column] = row[parent_key_column]
                            else:
                                item["parent_id"] = index
                            nested_entries.append(item)
                elif isinstance(value, dict):
                    if parent_key_column:
                        value[parent_key_column] = row[parent_key_column]
                    else:
                        value["parent_id"] = index
                    nested_entries.append(value)

            # Créer une table pour les données imbriquées
            if nested_entries:
                nested_df = pd.json_normalize(nested_entries, sep="_")
                nested_table_name = f"{base_table_name}_{clean_column_name(column)}"
                create_table_from_dataframe(conn, nested_df, nested_table_name)
                print(
                    f"Nested data from '{column}' loaded into table '{nested_table_name}'."
                )


def map_dtype_to_duckdb_type(dtype, column_data):
    """Mappe le type de données Pandas au type de données DuckDB avec vérification des valeurs."""
    if np.issubdtype(dtype, np.integer):
        return "INTEGER"
    elif np.issubdtype(dtype, np.floating):
        return "DOUBLE"
    elif np.issubdtype(dtype, np.bool_):
        return "BOOLEAN"
    elif np.issubdtype(dtype, np.datetime64):
        return "TIMESTAMP"
    elif dtype == object:
        # Vérifier si les données sont des chiffres, des booléens ou des dates même si elles sont considérées comme 'object'
        if column_data.apply(lambda x: isinstance(x, bool)).all():
            return "BOOLEAN"
        elif column_data.apply(lambda x: is_float(x)).all():
            return "DOUBLE"
        elif column_data.apply(lambda x: is_integer(x)).all():
            return "INTEGER"
        elif column_data.apply(lambda x: is_date(x)).all():
            return "TIMESTAMP"
        else:
            return "TEXT"
    else:
        return "TEXT"


def is_float(value):
    """Vérifie si une valeur peut être convertie en float."""
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def is_integer(value):
    """Vérifie si une valeur peut être convertie en entier."""
    try:
        return float(value).is_integer()
    except (ValueError, TypeError):
        return False


def is_date(value):
    """Vérifie si une valeur est une date."""
    try:
        pd.to_datetime(value)
        return True
    except (ValueError, TypeError):
        return False
