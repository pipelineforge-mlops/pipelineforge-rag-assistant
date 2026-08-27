import os
import shutil
import pandas as pd
from pydantic import ValidationError
from schema import ChunkSchema

INPUT_PATH = "data/processed/chunks.parquet"
OUTPUT_DIR = "data/validated"
OUTPUT_PATH = f"{OUTPUT_DIR}/chunks.parquet"
REPORT_PATH = "quality/Rapport_Qualite_Donnees.md"

def generate_report(total_chunks, duplicate_ids, duplicate_texts, pydantic_errors, char_counts):
    """Génère le rapport Markdown final de qualité des données."""
    report = f"""# Rapport de Qualité des Données (Sprint 2)

## 1. Volumétrie
- **Nombre total de chunks évalués :** {total_chunks}

## 2. Détection de doublons
- **Doublons stricts d'identifiants (chunk_id) :** {duplicate_ids}
- **Doublons de textes parfaits :** {duplicate_texts} (soit {duplicate_texts/total_chunks:.2%} du corpus)
  *Seuil d'alerte métier : < 1% toléré (phrases types répétées).*

## 3. Validation du Schéma et Encodage (Pydantic)
- **Erreurs de structure / encodage détectées :** {pydantic_errors}

## 4. Statistiques de longueurs (caractères)
- **Minimum :** {char_counts.min():.0f}
- **Médiane :** {char_counts.median():.0f}
- **Moyenne :** {char_counts.mean():.0f}
- **Maximum :** {char_counts.max():.0f}

## 5. Conclusion
"""
    if duplicate_ids == 0 and pydantic_errors == 0 and duplicate_texts / total_chunks < 0.01:
        report += "\n**RÉSULTAT : SUCCÈS ✅**\nLes données sont intègres, correctement formatées et validées. Elles sont prêtes pour les embeddings."
    else:
        report += "\n**RÉSULTAT : ÉCHEC ❌**\nDes anomalies ont été détectées. Veuillez corriger le script de transformation."
        
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"Rapport généré : {REPORT_PATH}")


def validate_corpus():
    print(f"Chargement de {INPUT_PATH}...")
    df = pd.read_parquet(INPUT_PATH)
    total_chunks = len(df)
    
    print("Vérification des doublons (Pandas)...")
    duplicate_ids = int(df['chunk_id'].duplicated().sum())
    duplicate_texts = int(df['text'].duplicated().sum())
    
    print("Validation ligne par ligne (Pydantic)...")
    pydantic_errors = 0
    records = df.to_dict(orient="records")
    for record in records:
        try:
            ChunkSchema(**record)
        except ValidationError as e:
            pydantic_errors += 1
            # print(f"Erreur sur {record['chunk_id']}: {e}") # Décommenter pour débug

    print("Génération du rapport...")
    generate_report(total_chunks, duplicate_ids, duplicate_texts, pydantic_errors, df['char_count'])
    
    if duplicate_ids == 0 and pydantic_errors == 0 and (duplicate_texts / total_chunks) < 0.01:
        print("Validation réussie. Déplacement des données vers le dossier validated...")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        # On copie Parquet
        shutil.copy2(INPUT_PATH, OUTPUT_PATH)
        # On copie le JSONL si présent
        jsonl_path = INPUT_PATH.replace(".parquet", ".jsonl")
        if os.path.exists(jsonl_path):
            shutil.copy2(jsonl_path, f"{OUTPUT_DIR}/chunks.jsonl")
        print(f"Corpus validé copié dans {OUTPUT_DIR}/")
    else:
        print("La validation a échoué. Les données ne seront pas copiées dans validated/.")

if __name__ == "__main__":
    validate_corpus()
