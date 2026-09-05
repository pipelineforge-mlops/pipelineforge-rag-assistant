"""
retriever.py — PipelineForge RAG (Hafsa Elhilali, Sprint 3)

Charge le Vector Store construit par El Betti Jihad (embeddings/output/chroma_db/)
et fournit une fonction de retrieval réutilisable par le reste de la chaîne RAG.
"""

import chromadb
from sentence_transformers import SentenceTransformer

# Doit être le MÊME modèle que celui utilisé pour indexer (El Betti Jihad)
EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"
VECTORSTORE_PATH = "embeddings/output/chroma_db"
COLLECTION_NAME = "pipelineforge_pmc"

# Préfixe recommandé par BGE pour les requêtes (pas pour les documents indexés)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# Chargés une seule fois au niveau du module (pas à chaque appel de retrieve())
_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
_client = chromadb.PersistentClient(path=VECTORSTORE_PATH)
_collection = _client.get_collection(COLLECTION_NAME)


def retrieve(question: str, top_k: int = 5, where: dict = None) -> list[dict]:
    """
    Recherche les chunks les plus pertinents pour une question donnée.

    Args:
        question: la question de l'utilisateur (en anglais, le corpus est en anglais)
        top_k: nombre de chunks à retourner
        where: filtre optionnel sur les métadonnées, ex. {"restricted_license": False}

    Returns:
        Liste de dicts : [{"text": ..., "metadata": {...}, "distance": ...}, ...]
    """
    query_embedding = _model.encode(
        QUERY_PREFIX + question,
        normalize_embeddings=True,
    )

    results = _collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=top_k,
        where=where,
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "metadata": meta,
            "distance": dist,
        })

    return chunks


if __name__ == "__main__":
    # Petit test manuel rapide
    question = "What are the side effects of chemotherapy in cancer patients?"
    results = retrieve(question, top_k=3)
    for i, r in enumerate(results):
        print(f"\n--- Résultat {i+1} (distance={r['distance']:.4f}) ---")
        print(f"Titre : {r['metadata']['title'][:80]}...")
        print(f"Extrait : {r['text'][:200]}...")