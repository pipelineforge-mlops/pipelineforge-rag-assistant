import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import time
import os
import torch

df = pd.read_parquet("data/validated/chunks.parquet")
texts = df.text.tolist()
chunk_ids = df.chunk_id.tolist()

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Device : {device} | Chunks à encoder : {len(texts)}")

model = SentenceTransformer("BAAI/bge-base-en-v1.5", device=device)

start = time.time()
embeddings = model.encode(
    texts,
    batch_size=32,
    show_progress_bar=True,
    normalize_embeddings=True,
)
elapsed = time.time() - start
print(f"\nEncodage terminé en {elapsed/60:.1f} minutes")
print("Shape finale :", embeddings.shape)

os.makedirs("embeddings/output", exist_ok=True)
np.save("embeddings/output/embeddings.npy", embeddings)
pd.Series(chunk_ids).to_csv("embeddings/output/chunk_ids.csv", index=False, header=["chunk_id"])
print("Sauvegardé dans embeddings/output/")
