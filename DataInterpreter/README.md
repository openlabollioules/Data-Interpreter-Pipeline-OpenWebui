# Projet de Data Interpreter IA

Ce projet est une application REST qui permet de traiter divers types de fichiers (à savoir .xls, .xlsx, .csv, .json, .pdf, .py) et de générer des analyses sur ces fichiers en utilisant un modèle de langage large (LLM). Il intègre des fonctionnalités d'extraction de texte, d'images, de données relationnelles et de code Python. Il utilise l'écosystème LangChain, des bases de données DuckDB, ainsi que FastAPI pour l'interface utilisateur.

## Prérequis

- Python 3.11 ou plus récent
- `tesseract` pour l'extraction OCR
- Librairies Python listées dans `requirements.txt`
- `ollama` pour utiliser les LLM

### Installation de Tesseract

Ubuntu/Debian :
```bash
sudo apt install tesseract-ocr
```

macOS :
```bash
brew install tesseract
```

### Installation de Ollama

Pour utiliser les modèles LLM avec Ollama, suivez les instructions ci-dessous :

1. Installez Ollama :

    macOS :
    ```bash
    brew install ollama
    ```

    Linux :
    ```bash
    curl -o- https://ollama.com/download.sh | bash
    ```

2. Lancez le service Ollama :

    ```bash
    ollama serve
    ```

3. Téléchargez les modèles LLM requis :

    ```bash
    ollama pull duckdb-nsql:latest
    ollama pull llama3.2:latest
    ollama pull command-r-plus:latest
    ```

## Installation du Projet

1. Clonez le répertoire du projet :

    ```bash
    git clone <URL_DU_PROJET>
    cd <nom_du_répertoire>
    ```

2. Installez les dépendances nécessaires à l'aide de `requirements.txt` :

    ```bash
    pip install -r requirements.txt
    ```

## Lancer l'Application

Pour exécuter l'application, lancez la commande suivante :

```bash
python main.py <chemin_vers_vos_fichiers>
```

- Remplacez `<chemin_vers_vos_fichiers>` par le chemin des fichiers que vous souhaitez traiter.

L'application se lancera sur `http://0.0.0.0:8000`.

## Pour obtenir des indications de lancement dans le terminal


```bash
python main.py --help
```

## Utilisation de l'API REST

L'API REST est développée avec FastAPI. Voici un exemple d'utilisation :

- Endpoint : `/query/`
- Méthode : `POST`
- Corps de la requête :
  ```json
  {
    "complex_query": "<votre_question>"
  }
  ```
- Réponse :
  ```json
  {
    "analysis_result": "<résultat_de_l'analyse>"
  }
  ```

Vous pouvez tester l'API à l'aide d'un outil comme `Postman` ou `curl`.

### Exemple d'Exécution via Curl

```bash
curl -X POST "http://localhost:8000/query/" -H "Content-Type: application/json" -d '{"complex_query": "Donne-moi les statistiques de ventes"}'
```

## Fonctionnalités Clés

1. **Extraction de Texte et Images des PDF :** Le projet utilise `pdfminer.six` pour extraire le texte et `PyMuPDF` pour extraire les images des fichiers PDF.
2. **Extraction de Texte par OCR :** `pytesseract` est utilisé pour extraire le texte des images présentes dans les PDF.
3. **Analyse de Code Python :** Extraction des fonctions, classes, imports et autres éléments d'un fichier `.py` en utilisant le module `ast`.
4. **Chargement de Données dans une Base DuckDB :** Les fichiers CSV, Excel, JSON, et PDF peuvent être chargés dans DuckDB.
5. **Génération Automatique de Réponses et d'Outils :** Utilisation de modèles LLM (à partir de LangChain) pour générer des plans d'action, des requêtes SQL et des analyses complètes.

## Organisation des Fichiers

- `main.py` : Le script principal pour exécuter l'application.
- `requirements.txt` : Liste des dépendances à installer.
- `README.md` : Ce fichier de documentation.

## Exemples de Fichiers Supportés

- **Excel (.xls, .xlsx)** : Chargement de toutes les feuilles disponibles dans une base de données.
- **CSV (.csv)** : Chargement dans une table DuckDB avec traitement préalable.
- **JSON (.json)** : Normalisation des données imbriquées et chargement.
- **PDF (.pdf)** : Extraction de texte et images avec OCR.
- **Python (.py)** : Analyse et extraction du code, des fonctions, classes, et autres éléments Python.
