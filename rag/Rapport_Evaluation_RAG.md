# Rapport d'Évaluation Qualitative — Chaîne RAG
**Responsable : Hafsa Elhilali — RAG & Expérimentation MLflow (Sprint 3)**

## 1. Configuration testée

| Composant | Choix |
|-----------|-------|
| Modèle d'embedding (requêtes) | BAAI/bge-base-en-v1.5 (même que l'indexation, El Betti Jihad) |
| Base vectorielle | Chroma (embeddings/output/chroma_db/, collection pipelineforge_pmc) |
| LLM | openai/gpt-oss-20b (via Groq API) |
| top_k | 5 |
| Langue de réponse | Français (imposée explicitement dans le prompt) |
| Tracking | MLflow (expérience "pipelineforge-rag") |

## 2. Méthodologie

8 questions représentatives du domaine santé/biomédical ont été soumises à la chaîne
RAG complète (retrieval + génération), couvrant les principaux mots-clés de collecte
du Sprint 1 (cancer, diabète, cardiovasculaire, maladies infectieuses, vaccins, essais
cliniques, machine learning médical, épidémiologie). Chaque appel est tracé dans MLflow
(paramètres, métriques, réponse en artefact).

Une première exécution a révélé un mélange de langues dans les réponses (le modèle
suivait la langue dominante des sources plutôt qu'une consigne fixe). Le prompt a été
corrigé pour imposer explicitement le français, puis les 8 questions ont été
ré-exécutées. Les résultats ci-dessous correspondent à cette version corrigée.

## 3. Résultats

| # | Question | Distance retrieval (meilleure) | Qualité de la réponse |
|---|----------|-------------------------------|------------------------|
| 1 | Effets secondaires de la chimiothérapie | 0.588 | Excellente, 14 effets classés par catégorie, sourcés individuellement |
| 2 | Diagnostic du diabète | 0.580 | Très bonne, critères cliniques précis, distingue critères cliniques/administratifs/T3cDM |
| 3 | Traitements des maladies cardiovasculaires | 0.694 | Très bonne, tableau détaillé par classe thérapeutique avec contexte d'usage |
| 4 | Facteurs de risque des épidémies | 0.601 | Bonne, structuration claire par domaine (socio-éco, environnemental, gestion du bétail) |
| 5 | Efficacité des vaccins | 0.723 | Bonne, reconnaît honnêtement l'absence de données chiffrées pour certains vaccins |
| 6 | Phases d'un essai clinique | 0.624 | Très bonne, tableau complet I-IV avec exemples tirés du corpus pour chaque phase |
| 7 | Machine learning en diagnostic médical | 0.422 | Excellente — meilleur retrieval de la série, réponse claire et concise |
| 8 | Méthodes épidémiologiques en santé publique | 0.688 | Bonne, honnête sur la limite des extraits disponibles |

## 4. Points forts observés

- **Comportement anti-hallucination robuste** : sur plusieurs questions (5, 8), le
  modèle signale explicitement quand les extraits ne suffisent pas à répondre
  exhaustivement (ex. absence de chiffre d'efficacité pour certains vaccins), plutôt
  que d'inventer une information non sourcée.
- **Citations systématiques et fines** : chaque affirmation est associée à un numéro
  de source, y compris quand plusieurs effets proviennent d'une même source (question 1).
- **Cohérence retrieval/génération** : les questions correspondant à des sujets bien
  représentés dans le corpus (diabète, cancer, ML médical) obtiennent les meilleures
  distances de retrieval ET les réponses les plus complètes. La question 7 (ML en
  diagnostic médical) obtient la meilleure distance (0.422) et une réponse concise et
  bien ciblée.
- **Cohérence linguistique** : après correction, les 8 réponses sont uniformément en
  français, un comportement stable et prévisible pour l'intégration avec l'API
  (Chbab Brahim, Sprint 4).

## 5. Limites identifiées

- **Mélange de langues (identifié puis corrigé)** : la version initiale du prompt ne
  fixait aucune langue de réponse, ce qui produisait un mélange français/anglais selon
  la langue dominante des sources récupérées. Corrigé dans `generation.py` en imposant
  explicitement le français ; validé sur les 8 questions ré-exécutées (section 3).
- **Retrieval moins pertinent sur les sujets périphériques** : les questions 4 et 5
  (maladies infectieuses, vaccins) montrent des distances plus élevées (0.60-0.72),
  le corpus de 700 articles multi-thématiques n'étant pas centré sur ces sujets. Le
  retrieval dérive alors vers des articles connexes mais pas toujours parfaitement
  ciblés (ex. anthrax du bétail pour une question sur les épidémies humaines).
- **4% des chunks tronqués à 512 tokens** (limite documentée par El Betti Jihad en
  amont) — impact non mesuré spécifiquement sur la qualité du retrieval RAG, mais à
  garder en tête.
- **Évaluation manuelle uniquement** : pas de métrique formelle (ex. faithfulness,
  answer relevancy) mise en place — amélioration possible si le temps le permet.

## 6. Conclusion

La chaîne RAG répond correctement et de façon cohérente (langue, structure, sources)
à un jeu de questions représentatif du domaine biomédical, avec un comportement prudent
face aux lacunes du corpus plutôt que des réponses inventées. Le bug de cohérence
linguistique initialement identifié a été corrigé et vérifié. Le module est stable et
prêt à être intégré par Chbab Brahim via FastAPI (voir `rag/README.md`).