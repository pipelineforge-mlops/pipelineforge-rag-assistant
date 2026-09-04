# Embeddings & Vector Store — El Betti Jihad (Sprint 3)

## Ce qui a été fait
- Chargement du dataset validé : `data/validated/chunks.parquet` (32 146 chunks, 700 documents)
- Génération des embeddings avec `BAAI/bge-base-en-v1.5` (dimension 768, normalisés)
- Stockage dans un Vector Store Chroma persistant : `embeddings/output/chroma_db/`
- Collection : `pipelineforge_pmc`

## Comment régénérer
```bash
pip install sentence-transformers chromadb transformers torch
python embeddings/build_embeddings.py      # ~80-90 min sur CPU/GPU d'entrée de gamme
python embeddings/build_vectorstore.py     # ~1 min
```

## Point d'attention : troncature à 512 tokens
Le chunking (Sprint 2) est calibré en caractères (~1200 caractères, ~300 tokens estimés),
pas en tokens réels. Vérification sur un échantillon de 500 chunks :
- Longueur moyenne réelle : ~248 tokens
- Longueur max observée : 911 tokens
- **4% des chunks dépassent la fenêtre de 512 tokens de BGE-base**

Ces chunks sont automatiquement **tronqués à 512 tokens** par le modèle (comportement par
défaut de sentence-transformers). Perte d'information partielle sur ces 4% de chunks
(~1286 chunks sur 32146), non bloquante mais à connaître.

## Pour Hafsa Elhilali (RAG, Sprint 3)

### Charger le Vector Store
```python
import chromadb
client = chromadb.PersistentClient(path="embeddings/output/chroma_db")
collection = client.get_collection("pipelineforge_pmc")
```

### Encoder une question utilisateur
**Important** : BGE recommande un préfixe d'instruction pour les requêtes (pas pour les
documents déjà indexés) :
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("BAAI/bge-base-en-v1.5")

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
query_embedding = model.encode(QUERY_PREFIX + question, normalize_embeddings=True)

results = collection.query(query_embeddings=[query_embedding.tolist()], n_results=5)
```

### Métadonnées disponibles par chunk
`doc_id`, `pmcid`, `title`, `doi`, `section`, `section_raw`, `is_abstract`, `license`,
`restricted_license`, `chunk_index`, `n_chunks_doc`, `char_count`, `matched_keyword`

- Filtrer les licences restrictives : `where={"restricted_license": False}` dans `collection.query()`
- Retrieval ciblé par section : `where={"section": "methods"}`

## Limites connues
- Modèle : `BAAI/bge-base-en-v1.5`, fenêtre 512 tokens, dimension 768
- 4% des chunks tronqués (voir ci-dessus)
- Le dossier `embeddings/output/` (embeddings, chunk_ids, chroma_db) n'est pas versionné
  (trop volumineux, régénérable) — voir `.gitignore`
- Testé avec 3 questions de validation manuelle (résultats pertinents mais non
  systématiquement évalués avec une métrique formelle — à envisager côté Hafsa si besoin)
