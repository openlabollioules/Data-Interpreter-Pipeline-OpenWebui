# Guide pour lancer une pipeline Open WebUI

Ce guide présente les étapes détaillées pour configurer et lancer une pipeline dans Open WebUI. En suivant ces instructions, vous serez en mesure de préparer les dossiers nécessaires, insérer les fichiers de données, et démarrer l'interface Open WebUI de manière appropriée. Assurez-vous de suivre attentivement chaque étape afin de minimiser les erreurs pendant l'installation et l'exécution, car la précision dans la configuration est essentielle pour le bon fonctionnement de l'ensemble du système.

### Organisation des dossiers

1. **Dossier Pipelines**
   - Pour insérer une nouvelle pipeline, placez simplement le fichier Python correspondant à la pipeline dans le dossier `pipelines`. Ce fichier sera utilisé par Open WebUI pour exécuter la pipeline. L'ajout du fichier est une opération simple mais cruciale, car Open WebUI se base sur la structure et le contenu de ce dossier pour identifier les pipelines disponibles.
   - Lors du lancement de l'interface Open WebUI, un dossier sera automatiquement créé dans `pipelines`, portant le même nom que votre fichier de pipeline. **Assurez-vous** qu'aucun dossier nommé `failed` ne soit créé, contenant votre fichier de pipeline. La présence d'un dossier `failed` indique une erreur de chargement de la pipeline, ce qui nécessite une vérification et correction immédiate du code de la pipeline.

2. **Dossier DB**
   - Le dossier `db` est utilisé pour stocker la base de données pendant l'utilisation de la pipeline. Il n'est pas nécessaire de pré-remplir ce dossier, mais sa présence est **indispensable**, même s'il est vide. Ce dossier joue un rôle crucial dans la conservation des informations pendant le traitement de la pipeline, et son absence entraînera des erreurs critiques lors de l'exécution.

3. **Dossier Data**
   - **Le dossier `data` est crucial** : il contient les fichiers à analyser par la pipeline. Ces fichiers sont le carburant de la pipeline, et sans eux, aucune analyse ne peut être réalisée.
   - Les types de fichiers acceptés sont : `xls`, `xlsx`, `csv`, `py`, `json`, et `pdf`. **Il est impératif d'insérer ces fichiers dans le dossier `data` avant de lancer Open WebUI.** Sans ces fichiers, l'analyse ne pourra pas être effectuée correctement. Le bon formatage des fichiers et leur disponibilité sont essentiels pour garantir une exécution fluide des pipelines. Toute omission ou mauvaise organisation de ces fichiers risque d'aboutir à des résultats incomplets ou erronés.

4. **Dossier DataInterpreter**
   - Ce dossier contient une partie essentielle du code nécessaire à l'exécution de la pipeline. **Ne le supprimez pas**. Il est conçu pour prendre en charge des opérations spécifiques, souvent internes à la logique des pipelines, et sa suppression entraînera des dysfonctionnements imprévus.

### Installation d'Ollama et Configuration

Avant de lancer Open WebUI, assurez-vous qu'Ollama est actif sur votre machine et que les modèles nécessaires sont disponibles. Voici les étapes, dans l'ordre, pour installer Ollama, le démarrer, et préparer l'environnement pour le fonctionnement optimal de la pipeline.

1. **Installer Ollama sur Mac**
   - Si Ollama n'est pas encore installé, utilisez la commande suivante pour l'installer via Homebrew, un gestionnaire de paquets couramment utilisé sur macOS :
     ```bash
     brew install ollama
     ```
   - Cette commande télécharge et installe Ollama, en veillant à ce que l'environnement soit prêt pour exécuter les modèles requis. Cette étape est essentielle pour garantir que tous les outils nécessaires sont en place avant le démarrage.

2. **Lancer Ollama**
   - Une fois Ollama installé, démarrez-le avec la commande suivante :
     ```bash
     ollama serve
     ```
   - Assurez-vous qu'Ollama reste actif sur votre machine pendant toute la durée d'utilisation d'Open WebUI. Ollama est responsable de servir les modèles, et son arrêt pendant l'utilisation causerait des interruptions dans les fonctionnalités de la pipeline.

3. **Télécharger les Modèles Ollama**
   - Pour que la pipeline fonctionne correctement, téléchargez les modèles Ollama nécessaires avant de lancer Open WebUI. Utilisez les commandes suivantes pour obtenir les versions les plus récentes des modèles requis :
     ```bash
     ollama pull command-r-plus:latest
     ollama pull llama3.2:latest
     ollama pull duckdb-nsql:latest
     ```
   - Ces commandes permettent de télécharger les modèles, qui sont indispensables pour exécuter les fonctions de la pipeline. Chaque modèle a un rôle spécifique : `command-r-plus` est utilisé pour des opérations avancées, `llama3.2` est employé pour la compréhension générale, et `duckdb-nsql` pour l'interaction avec la base de données. **Assurez-vous que chaque modèle est téléchargé correctement** avant de continuer. Des versions incomplètes ou obsolètes peuvent entraîner des résultats imprévisibles ou erronés.

### Lancement de l'Interface Open WebUI

Après avoir organisé les dossiers et téléchargé les modèles nécessaires, vous pouvez lancer l'interface Open WebUI pour utiliser la pipeline.

1. **Construire et Lancer l'Interface**
   - Pour construire et lancer Open WebUI, exécutez la commande suivante dans le terminal :
     ```bash
     docker compose up --build
     ```
   - Cette commande démarre l'interface Open WebUI et construit l'environnement nécessaire, en prenant en compte toutes les modifications apportées au fichier `docker-compose.yml`. Ce processus peut prendre un certain temps, en fonction des modifications et de la puissance de votre machine.
   - Pendant le processus de démarrage, surveillez la console pour vous assurer que votre pipeline est chargée sans erreurs. Un dossier portant le nom de votre fichier de pipeline doit être créé dans `pipelines`. **Attention** : si un dossier `failed` est créé, contenant votre fichier de pipeline, cela signifie qu'il y a une erreur dans le script de la pipeline. Vous devrez vérifier les logs et corriger cette erreur avant de relancer Open WebUI.

2. **Vérification des Modèles Ollama**
   - Assurez-vous qu'Ollama est actif et que les modèles requis sont disponibles. Les modèles mentionnés plus haut doivent être téléchargés et prêts à l'emploi pour que la pipeline puisse traiter les données comme prévu. En cas de problème, vérifiez la connectivité réseau et la configuration de votre environnement, puis essayez à nouveau de télécharger les modèles.

### Récapitulatif des Étapes pour Lancer Open WebUI

1. **Installer Ollama sur Mac** :
   ```bash
   brew install ollama
   ```

2. **Lancer Ollama** :
   ```bash
   ollama serve
   ```

3. **Télécharger les Modèles Ollama** :
   ```bash
   ollama pull command-r-plus:latest
   ollama pull llama3.2:latest
   ollama pull duckdb-nsql:latest
   ```

4. **Organiser les Dossiers** :
   - **Pipelines** : Ajouter votre fichier Python au dossier.
   - **DB** : Assurez-vous que le dossier est présent, même s'il est vide.
   - **Data** : Ajouter les fichiers (`xls`, `xlsx`, `csv`, `py`, `json`, `pdf`) à analyser.

5. **Lancer Open WebUI** :
   ```bash
   docker compose up --build
   ```

6. **Vérifier le Chargement de la Pipeline** :
   - Assurez-vous qu'un dossier portant le nom de votre fichier de pipeline est créé dans `pipelines`.
   - **Pas de dossier `failed`** : Cela signifie qu'il n'y a pas d'erreur de chargement.

En suivant ces instructions détaillées, vous pourrez lancer avec succès l'interface Open WebUI et utiliser votre pipeline sans problème. **Veillez à bien vérifier chaque étape** pour éviter les erreurs qui pourraient survenir pendant l'installation ou l'exécution. Une configuration correcte dès le départ vous permettra de gagner du temps et de maximiser l'efficacité de vos analyses. Bonne chance, et profitez pleinement des fonctionnalités avancées qu'offre Open WebUI !

