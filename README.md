# pipelineforge-rag-assistant
# Ingestion — PipelineForge

Collecte automatique d'articles scientifiques biomedicaux depuis PubMed Central,
via le jeu de donnees public `pmc-oa-opendata` (remplace l'ancien service FTP/OA
de NCBI, retire le 24 aout 2026).

## Sources

- **API de recherche** : NCBI E-utilities (`esearch`, base de donnees `pmc`)
- **Contenu** : bucket S3 public `pmc-oa-opendata` (metadonnees JSON + texte
  integral), acces en HTTPS simple, aucune cle/compte AWS necessaire
- **Filtre applique** : `(open_access[filter] OR author_manuscript[filter])`
  — ne garde que les articles reellement recuperables via ce dataset

## Mots-cles utilises (Sprint 1, atelier de cadrage)

cancer treatment, infectious disease, clinical trial, drug efficacy, vaccine,
diabetes, cardiovascular disease, public health, machine learning diagnosis,
epidemiology

## Comment relancer la collecte

​```powershell
python ingestion\collect_pmc.py
​```

Parametres ajustables en haut du script : `KEYWORDS`, `PER_KEYWORD_MAX`,
`TARGET_TOTAL`.

## Resultat de la collecte (Sprint 1)

- **700 articles** collectes, aucun doublon
- Repartition des licences : CC BY (367), CC BY-NC-ND (178), CC BY-NC (151), TDM (4)
- Longueur des textes : mediane ~53 000 caracteres, max ~1,2 million
  caracteres (quelques documents atypiques, a surveiller lors du chunking)
- Le mot-cle `epidemiology` n'a rapporte aucun article : le volume cible
  (700) a ete atteint avant d'y arriver dans l'ordre de la liste

## A savoir avant d'utiliser ce corpus (Transformation / Qualite)

- **Les 4 articles "TDM"** ne sont pas de l'Open Access classique : ce sont
  des manuscrits d'auteur finances par le NIH, avec une licence plus
  restrictive que les licences CC.
- **La longueur des documents varie fortement** — le chunking ne doit pas
  supposer une taille homogene.

## Schema des donnees

Chaque article produit 2 fichiers dans `data/raw/` (non versionnes dans Git,
reproductibles via le script) : `PMC<id>.1.json` (metadonnees) et
`PMC<id>.1.txt` (texte integral, deja sectionne).

`data/raw/metadata_index.csv` (celui-ci reste versionne) recense tous les
articles : `pmcid`, `version`, `title`, `license`, `doi`, `char_count`,
`matched_keyword`.

## Pour la suite (Transformation — Imane Alouani)

Lire `metadata_index.csv` pour la liste des articles, puis charger le `.txt`
correspondant a chaque `pmcid`.