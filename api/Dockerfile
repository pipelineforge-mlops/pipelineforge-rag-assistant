# Dockerfile — API FastAPI (Chbab Brahim, Sprint 4)
# Construit depuis la racine du repo pour pouvoir copier api/ ET rag/
# Build : docker build -f api/Dockerfile -t pipelineforge-api .

FROM python:3.11-slim

WORKDIR /app

# --- Dépendances de l'API ---
COPY api/requirements.txt ./requirements-api.txt
# --- Dépendances du module RAG (Hafsa Elhilali) : à compléter si un requirements.txt existe dans rag/ ---
# COPY rag/requirements.txt ./requirements-rag.txt

RUN pip install --no-cache-dir -r requirements-api.txt
# RUN pip install --no-cache-dir -r requirements-rag.txt

# --- Code de l'API ---
COPY api/ ./

# --- Code du module RAG (rag_chain.py, retriever.py, generation.py) ---
COPY rag/ ./rag_module/
ENV PYTHONPATH="/app/rag_module:${PYTHONPATH}"

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
