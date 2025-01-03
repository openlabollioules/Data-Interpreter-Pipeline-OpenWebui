# Récapitulatif des versions du Data Interpreter

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