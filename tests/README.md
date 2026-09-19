# Suite de tests : PipelineForge

Ce dossier contient les tests d'intégration et les invariants de qualité du pipeline de transformation des données.

## Prérequis

Assurez-vous d'avoir généré les données transformées et d'avoir installé `pytest` :
```bash
pip install pytest
```

## Exécution

Depuis la racine du projet, exécutez tous les tests avec :
```bash
python -m pytest tests/test_transformation.py -v
```

## Invariants vérifiés
Le fichier `test_transformation.py` valide :
1. L'unicité des `chunk_id`.
2. La préservation de tous les documents (aucun document de l'index n'est perdu).
3. La non-vacuité des textes.
4. La taille minimale des chunks (hors flags `undersized`).
5. La contiguïté des index de chunks par document.
6. La validité des licences.
7. La cohérence du flag de licence restreinte (TDM).
8. L'appartenance des titres de sections au vocabulaire fermé attendu.
