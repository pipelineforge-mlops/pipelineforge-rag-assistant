import pandas as pd
from transformers import AutoTokenizer
# Charger le dataset validé (celui produit par le pipeline, pas data/raw ni data/processed)
df = pd.read_parquet("data/validated/chunks.parquet")

print("Shape :", df.shape)
print("\nColonnes :", df.columns.tolist())

# Vérifications de sanité
assert df.chunk_id.is_unique, "chunk_id non unique !"
assert df.text.str.strip().ne("").all(), "des chunks ont un texte vide !"

print("\nNombre de chunks :", len(df))
print("Nombre de documents uniques :", df.doc_id.nunique())
print("\nRépartition licences :")
print(df.license.value_counts())

print("\nChunks TDM (restricted_license) :", df.restricted_license.sum())

# Aperçu d'un chunk
print("\n--- Exemple de chunk ---")
print(df.iloc[0][["chunk_id", "doc_id", "section", "char_count", "text"]])
# --- Vérification de la distribution en tokens (Étape 2) ---
MODEL_NAME = "BAAI/bge-base-en-v1.5"
tok = AutoTokenizer.from_pretrained(MODEL_NAME)

sample = df.text.sample(500, random_state=42)
lengths = [len(tok.encode(t)) for t in sample]

print("\n--- Vérification tokens ---")
print("Modèle :", MODEL_NAME)
print("Nombre de chunks échantillonnés :", len(lengths))
print("Longueur min :", min(lengths))
print("Longueur max :", max(lengths))
print("Longueur moyenne :", sum(lengths) / len(lengths))

over_limit = [l for l in lengths if l > 512]
print(f"Chunks dépassant 512 tokens : {len(over_limit)} / {len(lengths)} ({100*len(over_limit)/len(lengths):.1f}%)")
