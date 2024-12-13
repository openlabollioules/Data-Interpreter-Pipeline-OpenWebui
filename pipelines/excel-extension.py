import os
import sys
import typing
import duckdb
from langchain_community.llms import Ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from SetupDatabase import prepare_database
from SqlTool import get_schema
from langchain_ollama import OllamaLLM
from LlmGeneration import (
    generate_tools_with_llm,
    command_r_plus_plan,
    generate_final_response_with_llama,
)
import io
import uuid
import pandas as pd
import json
import shutil
import base64

# Add application path to system path
sys.path.append("/app/DataInterpreter")


def test_ollama_connection():
    try:
        model = OllamaLLM(
            model="llama3.2:latest", base_url="http://host.docker.internal:11434"
        )
        # Corriger en passant une liste de chaînes
        response = model.generate(prompts=["Test message"])
        print("Response from Ollama:", response)
    except Exception as e:
        print(f"Test failed: {e}")


def test_ollama_no_image(prompts, ollama_model):
    """
    Teste une invocation avec Ollama Vision sans image.
    """
    try:
        # Tester l'invocation avec seulement un prompt textuel
        response = ollama_model.generate(prompt=[prompts])
        print("Ollama Vision Response (Text Only):")
        print(response["text"] if "text" in response else "No response available.")
    except Exception as e:
        print(f"Error during Ollama Vision test without image: {e}")


class Pipeline:
    class Valves(BaseModel):
        LLAMAINDEX_OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        LLAMAINDEX_MODEL_NAME: str = "llama3.2:latest"
        LLAMAINDEX_RAG_MODEL_NAME: str = "duckdb-nsql:latest"
        LLAMAINDEX_CONTEXT_MODEL_NAME: str = "llama3.2:latest"
        LLAMAINDEX_IMAGE_DECODER_NAME: str = "llama3.2-vision:latest"
        # FICHIERS: str = ""

    def __init__(self):
        self.sql_results = None
        self.python_results = None
        self.known_files = set()
        self.valves = self.Valves(
            LLAMAINDEX_OLLAMA_BASE_URL=os.getenv(
                "LLAMAINDEX_OLLAMA_BASE_URL", "http://host.docker.internal:11434"
            ),
            LLAMAINDEX_MODEL_NAME=os.getenv("LLAMAINDEX_MODEL_NAME", "llama3.2:latest"),
            LLAMAINDEX_RAG_MODEL_NAME=os.getenv(
                "LLAMAINDEX_RAG_MODEL_NAME", "duckdb-nsql:latest"
            ),
            LLAMAINDEX_CONTEXT_MODEL_NAME=os.getenv(
                "LLAMAINDEX_CONTEXT_MODEL_NAME", "command-r-plus:latest"
            ),
            LLAMAINDEX_IMAGE_DECODER_NAME=os.getenv(
                "LLAMAINDEX_IMAGE_DECODER_NAME", "llama3.2-vision:latest"
            ),
            # fichiers=Valves.Files(description="Téléchargez des fichiers à traiter")
            # FICHIERS = os.getenv("FICHIERS", ""),
        )
        print(f"Valves initialized: {self.valves}")

        try:
            self.database_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_RAG_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
            self.reasoning_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
            self.contextualisation_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_CONTEXT_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
            self.image_decoder_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_IMAGE_DECODER_NAME,
                base_url="http://host.docker.internal:11434",
            )
            test_ollama_connection()
            print("Models initialized successfully.")
        except NewConnectionError as conn_error:
            print(f"Connection to Ollama failed: {conn_error}")
            raise RuntimeError(
                "Failed to connect to Ollama. Check the service URL and availability."
            )
        except Exception as e:
            print(f"Error initializing models: {e}")
            raise RuntimeError("General error during model initialization.")

    async def on_startup(self):
        directory = "/app/data"
        all_places_to_set = [directory]
        print(f"Loading files from directory: {directory}")
        prepare_database(all_places_to_set, self.image_decoder_model, True)
        # Mettre à jour les fichiers connus
        self.known_files = self.scan_directory(directory)
        print(f"Known files after startup: {self.known_files}")

    def scan_directory(self, directory: str) -> set:
        """Scanne le répertoire pour obtenir une liste des fichiers valides."""
        return {
            os.path.join(directory, f)
            for f in os.listdir(directory)
            if os.path.isfile(os.path.join(directory, f))
            and f.endswith((".xls", ".xlsx", ".csv", ".json", ".pdf", ".py"))
        }

    def detect_and_process_changes(self, directory: str, ollama_model=None):
        """Détecte les ajouts et suppressions de fichiers et traite uniquement les nouveaux ou supprimés."""
        current_files = self.scan_directory(directory)
        added_files = current_files - self.known_files
        removed_files = self.known_files - current_files

        # Traiter les fichiers ajoutés
        if added_files:
            print(f"New files detected: {added_files}")
            for new_file in added_files:
                print(f"Adding {new_file} to database.")
                try:
                    prepare_database([new_file], ollama_model, False)
                except Exception as e:
                    print(f"Error processing file {new_file}: {e}")

        # Traiter les fichiers supprimés
        if removed_files:
            print(f"Files removed: {removed_files}")
            conn = duckdb.connect("/app/db/my_database.duckdb")
            for removed_file in removed_files:
                file_prefix = os.path.splitext(os.path.basename(removed_file))[
                    0
                ].lower()
                print(f"Removing data related to {file_prefix} from database.")
                try:
                    # Lister toutes les tables dans la base de données
                    existing_tables = conn.execute("SHOW TABLES").fetchall()
                    for table in existing_tables:
                        table_name = table[0]  # Récupérer le nom de la table
                        # Vérifier si le nom de la table commence par le préfixe du fichier
                        if table_name.startswith(file_prefix):
                            print(f"Dropping table: {table_name}")
                            conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                except Exception as e:
                    print(f"Error removing data for {removed_file}: {e}")

        # Mettre à jour la liste des fichiers connus
        self.known_files = current_files

    async def inlet(self, body: dict, user: typing.Optional[dict] = None) -> dict:
        if self.valves.LLAMAINDEX_RAG_MODEL_NAME is not None:
            self.database_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_RAG_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
        if self.valves.LLAMAINDEX_MODEL_NAME is not None:
            self.reasoning_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
        if self.valves.LLAMAINDEX_CONTEXT_MODEL_NAME is not None:
            self.contextualisation_model = OllamaLLM(
                model=self.valves.LLAMAINDEX_CONTEXT_MODEL_NAME,
                base_url="http://host.docker.internal:11434",
            )
        directory = "/app/data"
        # Détecter et traiter les modifications
        self.detect_and_process_changes(directory, ollama_model=None)

        # Mettre à jour la liste des fichiers connus après traitement
        self.known_files = self.scan_directory(directory)
        print(f"Updated known files: {self.known_files}")

        # Extraire les fichiers du corps de la requête
        return body

    async def on_shutdown(self):
        print("Server shutting down...")

    def verify_and_reflect(self, context, schema):
        if self.sql_results:
            return (
                "Terminé"
                if "requires_python_analysis" not in context
                else "Passer à Python"
            )
        elif self.python_results:
            return "Terminé"
        return "Continuer"

    def llm_data_interpreter(self, question, schema, initial_context):
        context = initial_context
        self.python_results = None
        self.sql_results = None
        schema = get_schema(duckdb.connect("/app/db/my_database.duckdb"))
        while True:
            plan = command_r_plus_plan(question, schema, self.contextualisation_model)
            context, python_results, sql_results, files_generated = (
                generate_tools_with_llm(
                    plan,
                    schema,
                    context,
                    self.sql_results,
                    self.python_results,
                    self.database_model,
                    self.reasoning_model,
                )
            )
            reflection = self.verify_and_reflect(context, schema)
            break
        return generate_final_response_with_llama(
            context, sql_results, python_results, self.reasoning_model, files_generated
        )

    def pipe(
        self,
        user_message: str,
        model_id: str = None,
        messages: typing.List[dict] = None,
        body: dict = None,
    ) -> typing.Union[str, typing.Generator, typing.Iterator]:
        try:
            schema = get_schema(duckdb.connect("/app/db/my_database.duckdb"))
            initial_context = {"question": user_message}
            return self.llm_data_interpreter(user_message, schema, initial_context)
        except Exception as e:
            print(f"Error executing request: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


pipeline = Pipeline()
