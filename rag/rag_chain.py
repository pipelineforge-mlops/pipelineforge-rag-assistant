"""
rag_chain.py — PipelineForge RAG (Hafsa Elhilali, Sprint 3)

Point d'entrée unique de la chaîne RAG, à consommer par Chbab Brahim (FastAPI, Sprint 4).
Chaque appel est tracé dans MLflow (paramètres, métriques).
"""

import time
import mlflow

from retriever import retrieve, EMBEDDING_MODEL_NAME
from generation import generate_answer, LLM_MODEL

mlflow.set_experiment("pipelineforge-rag")


def answer_question(question: str, top_k: int = 5, where: dict = None) -> dict:
    """
    Répond à une question en s'appuyant sur le corpus scientifique indexé.
    Trace l'appel dans MLflow (paramètres, métriques, temps de réponse).

    Args:
        question: la question de l'utilisateur
        top_k: nombre de chunks à récupérer pour la génération
        where: filtre optionnel sur les métadonnées (ex. {"restricted_license": False})

    Returns:
        dict avec :
            - "answer": la réponse générée par le LLM
            - "sources": liste des chunks utilisés (titre, section, distance)
    """
    with mlflow.start_run():
        start_time = time.time()

        # --- Paramètres de la run ---
        mlflow.log_param("question", question)
        mlflow.log_param("top_k", top_k)
        mlflow.log_param("embedding_model", EMBEDDING_MODEL_NAME)
        mlflow.log_param("llm_model", LLM_MODEL)
        mlflow.log_param("where_filter", str(where))

        # --- Retrieval ---
        t_retrieval_start = time.time()
        chunks = retrieve(question, top_k=top_k, where=where)
        retrieval_time = time.time() - t_retrieval_start

        # --- Génération ---
        t_generation_start = time.time()
        answer = generate_answer(question, chunks)
        generation_time = time.time() - t_generation_start

        total_time = time.time() - start_time

        # --- Métriques ---
        mlflow.log_metric("retrieval_time_sec", retrieval_time)
        mlflow.log_metric("generation_time_sec", generation_time)
        mlflow.log_metric("total_time_sec", total_time)
        mlflow.log_metric("nb_sources", len(chunks))
        if chunks:
            avg_distance = sum(c["distance"] for c in chunks) / len(chunks)
            mlflow.log_metric("avg_retrieval_distance", avg_distance)

        # Log de la réponse comme artefact texte (utile pour relire les runs)
        mlflow.log_text(answer, "answer.txt")

        sources = [
            {
                "title": c["metadata"].get("title"),
                "section": c["metadata"].get("section"),
                "distance": c["distance"],
            }
            for c in chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
        }


if __name__ == "__main__":
    result = answer_question("How is diabetes diagnosed?")
    print("RÉPONSE :\n", result["answer"])
    print("\nSOURCES :")
    for s in result["sources"]:
        print(f"- {s['title']} (section: {s['section']}, distance: {s['distance']:.4f})")