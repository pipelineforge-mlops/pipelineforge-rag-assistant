import pandas as pd
from sentence_transformers import SentenceTransformer
import time
import torch

df = pd.read_parquet("data/validated/chunks.parquet")
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Device utilisé :", device)

model = SentenceTransformer("BAAI/bge-base-en-v1.5", device=device)
sample_texts = df.text.head(400).tolist()

for bs in [32, 64]:
    start = time.time()
    embeddings = model.encode(sample_texts, batch_size=bs, show_progress_bar=False)
    elapsed = time.time() - start
    print(f"batch_size={bs} : {len(sample_texts)} chunks en {elapsed:.2f}s -> estimation totale : ~{(elapsed/len(sample_texts))*32146/60:.1f} min")
