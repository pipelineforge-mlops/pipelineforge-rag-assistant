import pandas as pd
import numpy as np
import chromadb
import time

# Charger le dataset validé + les embeddings déjà calculés
df = pd.read_parquet("data/validated/chunks.parquet")
embeddings = np.load("embeddings/output/embeddings.npy")
chunk_ids_saved = pd.read_csv("embeddings/output/chunk_ids.csv")["chunk_id"].tolist()

# Sécurité : vérifier que l'ordre correspond bien entre df et embeddings
assert df.chunk_id.tolist() == chunk_ids_saved, "Ordre des chunk_id incohérent entre df et embeddings !"
assert len(df) == embeddings.shape[0], "Nombre de lignes incohérent !"

print(f"{len(df)} chunks à insérer dans le Vector Store.")

# Créer le client Chroma persistant (stocké sur disque, pas en mémoire seulement)
client = chromadb.PersistentClient(path="embeddings/output/chroma_db")

collection = client.get_or_create_collection(
    name="pipelineforge_pmc",
    metadata={"description": "Corpus PMC biomedical - PipelineForge RAG", "embedding_model": "BAAI/bge-base-en-v1.5"}
)

# Préparer les métadonnées (Chroma n'accepte que str/int/float/bool, pas de NaN)
metadatas = df[[
    "doc_id", "pmcid", "title", "doi", "section", "section_raw",
    "is_abstract", "license", "restricted_license",
    "chunk_index", "n_chunks_doc", "char_count", "matched_keyword"
]].fillna("").to_dict("records")

# Convertir les bool numpy en bool Python natif (Chroma est strict là-dessus)
for m in metadatas:
    m["is_abstract"] = bool(m["is_abstract"])
    m["restricted_license"] = bool(m["restricted_license"])
    m["chunk_index"] = int(m["chunk_index"])
    m["n_chunks_doc"] = int(m["n_chunks_doc"])
    m["char_count"] = int(m["char_count"])

# Insertion par lots (Chroma recommande des lots de ~5000 max)
BATCH_SIZE = 5000
start = time.time()
for i in range(0, len(df), BATCH_SIZE):
    end = min(i + BATCH_SIZE, len(df))
    collection.add(
        ids=df.chunk_id.tolist()[i:end],
        embeddings=embeddings[i:end].tolist(),
        documents=df.text.tolist()[i:end],
        metadatas=metadatas[i:end],
    )
    print(f"Inséré {end}/{len(df)}")

elapsed = time.time() - start
print(f"\nTerminé en {elapsed:.1f}s. Total dans la collection : {collection.count()}")
