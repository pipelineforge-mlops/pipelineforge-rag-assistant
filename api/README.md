# API & Docker — Chbab Brahim (Sprint 4)

## Ce qui a été fait

- API FastAPI exposant le module RAG d'Hafsa Elhilali (`rag.rag_chain.answer_question`)
- Endpoints `/ask` (question → réponse RAG sourcée) et `/health` (vérification de disponibilité)
- Schémas de requête/réponse validés avec Pydantic, alignés sur le format exact renvoyé par `answer_question()`
- Dockerfile de l'API + `docker-compose.yml` à la racine du repo, orchestrant API + MLflow
- Testé en local avec un stub simulant `answer_question()` (endpoints `/health` et `/ask` répondent en `200`) — **le test avec le vrai module RAG et le vrai vector store reste à faire**, voir section Limites connues

## Structure du dossier

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée FastAPI : déclare `/health` et `/ask`, appelle `answer_question()` |
| `schemas.py` | Modèles Pydantic (`AskRequest`, `AskResponse`, `Source`, `HealthResponse`) |
| `Dockerfile` | Image de l'API, construite depuis la racine du repo (copie `api/` et `rag/`) |
| `requirements.txt` | Dépendances propres à l'API (FastAPI, Uvicorn, Pydantic, MLflow) |

Le `docker-compose.yml` orchestrant l'ensemble (API + MLflow) se trouve à la **racine du repo**, pas dans `api/`, car il assemble plusieurs composants du projet.

## Pour Bouazza Amina (CI/CD, Déploiement & Monitoring, Sprint 4)

### Utilisation

```bash
docker compose up --build
```

L'API est alors disponible sur `http://localhost:8000`.

```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How is diabetes diagnosed?", "top_k": 5}'
```

### Format de réponse de `/ask`

```json
{
  "answer": "...",
  "sources": [
    {"title": "...", "section": "...", "distance": 0.12}
  ],
  "latency_ms": 842.3
}
```

### Variables d'environnement requises

Le fichier `.env` (non versionné, voir `.env.example`) doit contenir :

```
GROQ_API_KEY=votre_clé_ici
MLFLOW_TRACKING_URI=http://mlflow:5000
```

`GROQ_API_KEY` est lue directement par `rag/generation.py` (via `python-dotenv`), pas par l'API elle-même — mais elle doit être présente dans le même environnement d'exécution.

### Prérequis avant de lancer le conteneur

Le vector store Chroma (`embeddings/output/chroma_db/`, généré par El Betti Jihad) doit **déjà exister sur la machine hôte** avant de lancer `docker compose up`. Il est monté en lecture seule dans le conteneur API via un volume — ce n'est pas un service réseau séparé. Voir `embeddings/README.md` si le dossier est manquant.

## Point d'attention pour le déploiement (Docker)

- **Dépendances du module RAG non encore intégrées au build** : le `Dockerfile` copie le dossier `rag/` mais n'installe pas encore ses dépendances (`sentence-transformers`, `chromadb`, `transformers`, `torch`, `groq`, `python-dotenv`). Si `rag/requirements.txt` n'existe pas encore, il faut le créer avec ces paquets avant de builder en production.
- **Premier appel plus lent** : le premier appel à `/ask` télécharge le modèle d'embedding (`BAAI/bge-base-en-v1.5`) depuis Hugging Face Hub s'il n'est pas déjà mis en cache dans l'image — prévoir un accès réseau sortant au démarrage du conteneur, ou précharger le modèle dans l'image Docker pour accélérer le cold start.
- **MLflow** : chaque appel à `/ask` déclenche un run MLflow automatiquement (géré par `rag_chain.py`, pas par l'API). Le service `mlflow` du `docker-compose.yml` doit donc être démarré et accessible avant tout appel à `/ask`, sinon `answer_question()` échouera.

## Limites connues

- L'API n'a pas encore été testée avec le vrai module RAG (seulement avec un stub) ni avec un vrai vector store Chroma — reste à valider en conditions réelles avant la Definition of Done.
- Pas de service d'orchestration (DAG de Maroua Karroum) dans le `docker-compose.yml` actuel — à ajouter une fois son Dockerfile disponible.
- Pas d'authentification sur les endpoints `/ask` et `/health` — à voir avec Bouazza Amina si nécessaire avant exposition sur le domaine public.
- `generate_answer()` gère déjà en interne les pannes de l'API Groq (message de repli renvoyé), donc l'API ne lève une `HTTPException 500` que pour des erreurs plus graves (retriever, vector store, MLflow indisponible).
