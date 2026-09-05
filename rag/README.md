# RAG & Expérimentation MLflow — Hafsa Elhilali (Sprint 3)

## Ce qui a été fait

- Module RAG complet (retrieval + génération) construit sur le Vector Store d'El Betti Jihad
- LLM : `openai/gpt-oss-20b` via l'API Groq (gratuit, rapide, pas de dépendance machine)
- Toutes les expérimentations tracées dans MLflow (expérience `pipelineforge-rag`)
- 8 questions de test exécutées, réponses cohérentes et sourcées (voir `Rapport_Evaluation_RAG.md`)

## Structure du dossier

| Fichier | Rôle |
|---------|------|
| `retriever.py` | Charge le Vector Store Chroma, encode les questions (BGE + préfixe), retourne les chunks pertinents |
| `generation.py` | Construit le prompt à partir des chunks et appelle le LLM (Groq) |
| `rag_chain.py` | **Point d'entrée unique** : `answer_question()`, avec tracking MLflow intégré |
| `test_rag.py` | Jeu de 8 questions de test représentatives du domaine |
| `Rapport_Evaluation_RAG.md` | Évaluation qualitative des résultats |

## Pour Chbab Brahim (FastAPI & Docker, Sprint 4)

### Utilisation

```python
from rag.rag_chain import answer_question

result = answer_question("How is diabetes diagnosed?", top_k=5)

result["answer"]    # str — réponse générée, sourcée, en français
result["sources"]   # list[dict] — [{"title": ..., "section": ..., "distance": ...}, ...]
```

### Paramètres de `answer_question()`

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|--------------|
| `question` | str | — | Question de l'utilisateur (fonctionne en anglais ou français, réponse toujours en français) |
| `top_k` | int | 5 | Nombre de chunks récupérés pour la génération |
| `where` | dict \| None | None | Filtre optionnel sur les métadonnées Chroma, ex. `{"restricted_license": False}` |

### Dépendances Python nécessaires
sentence-transformers
chromadb
transformers
torch
groq
python-dotenv
mlflow

### Variables d'environnement requises

Le module lit la clé API Groq depuis un fichier `.env` à la racine du projet :
GROQ_API_KEY=votre_clé_ici
**Ce fichier n'est pas versionné** (`.gitignore`) — chaque membre de l'équipe doit
créer le sien avec sa propre clé Groq (gratuite sur console.groq.com).

### Prérequis avant le premier appel

Le Vector Store (`embeddings/output/chroma_db/`) doit exister en local — voir
`embeddings/README.md` (El Betti Jihad) pour la régénération si besoin.

### Point d'attention pour le déploiement (Docker)

- Le premier appel à `retriever.py` télécharge le modèle `BAAI/bge-base-en-v1.5`
  depuis Hugging Face Hub (mis en cache ensuite) — prévoir un accès réseau sortant
  au premier démarrage du conteneur, ou précharger le modèle dans l'image Docker.
- Le modèle d'embedding est chargé une seule fois au niveau du module (variable
  `_model` dans `retriever.py`), pas à chaque appel — donc les appels suivants
  dans une même session FastAPI seront rapides (~1-2s), contrairement au tout
  premier appel qui inclut le chargement du modèle.
- MLflow trace chaque appel automatiquement (pas d'action requise côté API), mais
  suppose qu'un serveur de tracking MLflow soit accessible (local ou sur l'infra
  partagée du groupe).

## Limites connues

- Réponses forcées en français par consigne de prompt — à adapter si l'API doit
  supporter d'autres langues de réponse.
- Pas de gestion d'erreur explicite si l'API Groq est indisponible ou si le quota
  gratuit est dépassé — à ajouter côté FastAPI si nécessaire pour la robustesse
  en production.
- Voir `Rapport_Evaluation_RAG.md` pour les limites détaillées de la qualité du
  retrieval sur certains sujets périphériques au corpus.