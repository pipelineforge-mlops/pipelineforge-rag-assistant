import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="embeddings/output/chroma_db")
collection = client.get_collection("pipelineforge_pmc")

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# Note : BGE recommande un préfixe d'instruction pour les REQUÊTES (pas pour les documents déjà indexés)
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

questions = [
    "What are the side effects of chemotherapy in cancer patients?",
    "How is diabetes diagnosed?",
    "What treatments exist for cardiovascular disease?",
]

for question in questions:
    print("\n" + "="*80)
    print("QUESTION :", question)
    print("="*80)

    query_embedding = model.encode(QUERY_PREFIX + question, normalize_embeddings=True)

    results = collection.query(
        query_embeddings=[query_embedding.tolist()],
        n_results=3,
    )

    for i, (doc, meta, dist) in enumerate(zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    )):
        print(f"\n--- Résultat {i+1} (distance={dist:.4f}) ---")
        print(f"Titre : {meta['title'][:80]}...")
        print(f"Section : {meta['section']} | License : {meta['license']}")
        print(f"Extrait : {doc[:200]}...")