# import matplotlib.pyplot as plt  # plt.show(block=False) plt.savefig(path)
import re
import subprocess
import sys
import time
import os
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import shutil

observed_directories = set()
created_paths = []  # Liste pour stocker les chemins des fichiers et dossiers créés


def move_and_create_links(source_files, target_directory, base_url):
    # Créer le répertoire cible s'il n'existe pas déjà
    os.makedirs(target_directory, exist_ok=True)

    # Liste pour stocker les liens générés
    generated_links = []

    for file in source_files:
        # Extraire le nom du fichier à partir du chemin complet
        file_name = os.path.basename(file)

        # Créer le chemin complet du fichier dans le répertoire cible
        target_path = os.path.join(target_directory, file_name)

        # Déplacer le fichier vers le répertoire cible
        shutil.move(file, target_path)

        # Construire l'URL locale pour le fichier déplacé
        file_url = os.path.join(
            base_url, os.path.relpath(target_path, start=target_directory)
        )

        # Ajouter le lien généré à la liste
        generated_links.append(file_url)

        # Afficher le lien local
        print(f"Fichier déplacé vers {target_path}")
        print(f"URL locale pour accéder au fichier : {file_url}")

    return generated_links


class FileCreationHandler(FileSystemEventHandler):
    def on_created(self, event):
        # Si c'est un fichier (et non un dossier), on l'ajoute à la liste
        path = os.path.abspath(event.src_path)
        if not event.is_directory and path not in created_paths:
            created_paths.append(path)  # Ajouter le chemin absolu du fichier créé
            print(f"Fichier créé: {event.src_path}")

    def on_modified(self, event):
        # Si c'est un fichier (et non un dossier), on l'ajoute à la liste
        path = os.path.abspath(event.src_path)
        if not event.is_directory and path not in created_paths:
            created_paths.append(
                os.path.abspath(event.src_path)
            )  # Ajouter le chemin absolu du fichier modifié
            print(f"Fichier modifié: {event.src_path}")


# Fonction de surveillance
def watch_directories(directories, stop_event):
    observers = []
    for directory in directories:
        if directory in observed_directories:
            print(f"Le répertoire {directory} est déjà surveillé.")
            continue

        observed_directories.add(directory)
        event_handler = FileCreationHandler()
        observer = Observer()
        observer.schedule(event_handler, directory, recursive=True)
        observer.start()
        observers.append(observer)

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        for observer in observers:
            observer.stop()
    for observer in observers:
        observer.stop()
        observer.join()


def parse_and_execute_python_code(tool, context, sql_results):
    global created_paths
    created_paths = (
        []
    )  # Réinitialiser la liste des chemins créés avant chaque exécution

    code_match = re.search(r"```python\n([\s\S]*?)```", tool)
    if not code_match:
        context["error"] = "No valid Python code found."
        return context, "", []

    code = code_match.group(1).strip()
    print(f"Parsed Python code: {code}")

    stop_event = threading.Event()
    directories_to_watch = ["./"]  # Ajouter tous les répertoires à surveiller ici
    watch_thread = threading.Thread(
        target=watch_directories, args=(directories_to_watch, stop_event)
    )
    watch_thread.daemon = True
    watch_thread.start()

    # Attendre un peu pour être sûr que le thread de surveillance est en cours
    time.sleep(1)

    # Analyser les imports du code
    imports = re.findall(
        r"^\s*import (\S+)|^\s*from (\S+) import (\S+)", code, re.MULTILINE
    )
    modules = set()
    for imp in imports:
        if imp[0]:
            modules.add(imp[0])  # import <module>
        elif imp[1]:
            modules.add(imp[1])  # from <module> import <submodule>

    # Installer les modules manquants
    for module in modules:
        try:
            __import__(module)
        except ImportError:
            print(f"Module {module} not found, attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
            except subprocess.CalledProcessError as e:
                print(f"Failed to install module {module}. Error: {e}")
                context["error"] = f"Failed to install module {module}. Error: {e}"
                return context, "", []

    exec_context = globals()
    if sql_results:
        exec_context["sql_results"] = sql_results
        print(f"Injecting SQL results into Python code execution: {sql_results}")

    try:
        print(f"Executing Python code: {code}")
        exec(code, exec_context)
        context["python_results"] = "Python results obtained"
        python_res = "Python results obtained"
        print("Python results obtained")
    except Exception as e:
        print(f"Error executing Python: {e}")
        context["error"] = f"Python error: {e}"
        python_res = ""

    # Attendre un peu plus longtemps pour donner le temps aux nouveaux fichiers/dossiers d'être créés et détectés
    time.sleep(5)  # Ajustez la durée si nécessaire

    # Arrêter la surveillance après le délai
    stop_event.set()
    watch_thread.join()

    # Ajouter les chemins créés au contexte et les retourner
    # context["created_paths"] = created_paths
    print(f"Chemins créés ou modifiés pendant l'exécution: {created_paths}")

    context["created_paths"] = move_and_create_links(
        created_paths,
        "/app/shared_data",
        "http://localhost:8080",
    )

    print(f"Liens créés: {created_paths}")

    return context, python_res, context["created_paths"]
