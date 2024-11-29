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


class Pipeline:
    class Valves(BaseModel):
        LLAMAINDEX_OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
        LLAMAINDEX_MODEL_NAME: str = "llama3.2:latest"
        LLAMAINDEX_RAG_MODEL_NAME: str = "duckdb-nsql:latest"
        LLAMAINDEX_CONTEXT_MODEL_NAME: str = "llama3.2:latest"
        # FICHIERS: str = ""

    def __init__(self):
        self.sql_results = None
        self.python_results = None
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
        print(f"Loading files from directory: {directory}")
        prepare_database(directory)

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
        # print(f"voila la valve actuelle pour le plan : {self.valves.LLAMAINDEX_CONTEXT_MODEL_NAME}")
        # print(body)

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
