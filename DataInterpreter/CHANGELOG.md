# Récapitulatif des versions du Data Interpreter

## [1.1.2] - 2025-01-03
### Modifié
- Correction de la détection des requêtes SQL afin de pouvoir exécuter plusieurs requêtes SQL
- Correction de la fonction de détection des noms de colones au moment de la lecture d'un fichier afin de pouvoir utiliser des nombres en guise de nom de colonne
- Correction du prompt pour le modèle de planification afin de s'assurer d'obtenir des requêtes exécutables dans l'immédiat.
- Correction du path pour le fichier duckdb afin d'aller le chercher au bon endroit.

## [1.1.1] - 2025-01-03
### Ajouté
- Initialisation du projet.
- Fonctionnalité de versioning.

### Modifié
- Amélioration de la gestion des erreurs pour la détection des arguments de la ligne de commande.
- Passage de Llama 3.2 à Llama 3.3 pour le modèle de raisonnement et de planification 
- Correction du parsing de la requête SQL pour ne pas supprimer les lignes faisant référence à un alias. 
- Correction dans la gestion des requêtes SQL pour toujours récupérer uniquement la dernière requête SQL générée par le modèle de planification.
- Traduction du prompt des modèles en anglais afin de gagner en efficacité.
- Modification du prompt du modèle de planification pour lui indiquer de ne jamais insérer dans la requête une table ou une colonne inexistante dans le schéma de la base de données.   