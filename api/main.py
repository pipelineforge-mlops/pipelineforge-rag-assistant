"""
main.py — API FastAPI (Chbab Brahim, Sprint 4)
Expose le module RAG d'Hafsa Elhilali (rag_chain.answer_question) via HTTP.
"""
import time
import logging

from fastapi import FastAPI, HTTPException

from schemas import AskRequest, AskResponse, HealthResponse, Source

# Le dossier rag/ (livré par Hafsa Elhilali) est monté/installé comme package
# à côté de l'API — voir docker-compose.yml (volume) ou requirements.txt (pip install -e ../rag)
from rag_chain import answer_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pipelineforge-api")

app = FastAPI(
    title="PipelineForge — Assistant scientifique documentaire (RAG)",
    description="API exposant la chaîne RAG (retrieval + génération) sur le corpus scientifique.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health():
    """Vérifie que le service est en ligne."""
    return HealthResponse(status="ok")


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    """
    Pose une question au système RAG.

    Note : answer_question() ne lève pas d'exception en cas de panne du LLM —
    generation.py gère déjà ce cas en interne et renvoie un message de repli.
    Une exception ici signale donc un problème plus grave (retriever, vector
    store, MLflow indisponible, etc.).
    """
    start = time.time()
    try:
        result = answer_question(
            question=request.question,
            top_k=request.top_k,
            where=request.where,
        )
    except Exception as e:
        logger.exception("Échec de answer_question()")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne du pipeline RAG : {e}",
        )

    latency_ms = (time.time() - start) * 1000

    return AskResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        latency_ms=latency_ms,
    )
