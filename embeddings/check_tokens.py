from transformers import AutoTokenizer

MODEL_NAME = "BAAI/bge-base-en-v1.5"
tok = AutoTokenizer.from_pretrained(MODEL_NAME)

# Échantillon de 500 chunks (comme suggéré par Imane), reproductible
sample = df.text.sample(500, random_state=42)
lengths = [len(tok.encode(t)) for t in sample]

print("Modèle :", MODEL_NAME)
print("Nombre de chunks échantillonnés :", len(lengths))
print("Longueur min :", min(lengths))
print("Longueur max :", max(lengths))
print("Longueur moyenne :", sum(lengths) / len(lengths))

# Combien dépassent la fenêtre max du modèle (512 tokens) ?
over_limit = [l for l in lengths if l > 512]
print(f"\nChunks dépassant 512 tokens : {len(over_limit)} / {len(lengths)} ({100*len(over_limit)/len(lengths):.1f}%)")