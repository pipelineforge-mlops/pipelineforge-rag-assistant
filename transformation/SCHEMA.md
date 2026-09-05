# Schema du corpus transforme — PipelineForge

**Etape 2 (Transformation) — Imane Alouani**
Consommateurs : Hanane Ayar (qualite & tests), puis El Betti Jihad (embeddings).

`transform_version` actuel : **2.4.0**

---

## Fichiers produits

| Fichier | Contenu |
|---|---|
| `data/processed/chunks.jsonl` | 1 objet JSON par ligne = 1 chunk. Format de reference. |
| `data/processed/chunks.parquet` | Meme contenu, meme schema. Pour pandas / traitement en volume. |
| `data/processed/_manifest.json` | Parametres du run, statistiques, sections inconnues rencontrees. |

Une ligne = **un chunk**, pas un document. Un document produit N lignes.

---

## Colonnes

| Colonne | Type | Description | Garanties |
|---|---|---|---|
| `chunk_id` | string | `PMC1234567.1_c0007` | Unique sur tout le corpus, non nul |
| `doc_id` | string | `PMC1234567.1` (pmcid + version) | Non nul |
| `pmcid` | string | Identifiant PMC | Non nul, present dans `metadata_index.csv` |
| `version` | string | Version de l'article | Non nul |
| `chunk_index` | int | Position du chunk dans son document | Commence a 0, contigu, sans trou |
| `n_chunks_doc` | int | Nombre total de chunks du document | >= 1 ; identique pour tous les chunks d'un meme doc |
| `section` | string | Section de premier niveau, **vocabulaire ferme** | Non nul ; `body` si non identifiee (4.5% des chunks) |
| `section_raw` | string | Titre reellement lu dans le document | Non nul ; egal a `section` si le titre etait deja canonique |
| `is_abstract` | bool | Section issue du resume structure | Voir heuristique ci-dessous |
| `text` | string | Texte nettoye du chunk | Non vide |
| `char_count` | int | `len(text)` | >= 250, **sauf si `undersized=True`** |
| `word_count` | int | Nombre de mots | >= 1 |
| `title` | string | Titre de l'article | Repris tel quel du CSV |
| `doi` | string | DOI | Peut etre vide si absent a l'ingestion |
| `license` | string | `CC BY`, `CC BY-NC`, `CC BY-NC-ND`, `TDM` | Non nul |
| `restricted_license` | bool | `True` si `license == "TDM"` | 4 documents concernes |
| `matched_keyword` | string | Mot-cle de collecte (Sprint 1) | Repris tel quel du CSV |
| `undersized` | bool | Chunk sous le seuil, conserve volontairement | Voir ci-dessous |
| `source` | string | Toujours `pmc-oa-opendata` | Constant |
| `transform_version` | string | Version du pipeline de transformation | Constant par run |

---

## Structure reelle du corpus (mesuree, pas supposee)

Mesure le 26/08/2026 sur les 700 documents via `transformation/inspect_sections.py` :

- **2 blocs `====` dans 100% des documents** : `JOURNAL INFORMATION` puis `ARTICLE INFORMATION`.
- Le contenu scientifique suit le 2e bloc, mais il est **precede de metadonnees
  d'article** (auteurs, ORCID, affiliations, dates, copyright, editeur) dans le meme bloc.
- Les titres de sections du corps sont en **Title Case sans soulignement**
  (`Introduction`, `Statistical Analysis`, `Data Collection`...).
- Section `References` detectee dans **95.6%** des documents.
- **45.4%** des documents repetent les noms de sections (resume structure + corps).

---

## Decisions de transformation (et pourquoi)

**Point de depart du contenu** — Tout ce qui precede le premier titre de section
connu est ecarte. Sans ca, les noms d'auteurs, affiliations et dates de publication
se retrouveraient dans les embeddings (l'inspection a montre `Muacevic Alexander`
dans 8% des documents et `Electronic publication date` dans 5.6%).

**Normalisation des noms de sections** — `conclusions` -> `conclusion`,
`acknowledgements` -> `acknowledgments`, `materials and methods` -> `methods`,
toutes les variantes de declaration d'interets -> `conflicts of interest`, etc.
Sans ca, le meme concept arrive en aval sous plusieurs noms.

**Sections supprimees** — `references`, `author contributions`, `funding`,
`acknowledgments`, `data availability`, `conflicts of interest`, `disclosures`,
`declarations`, `supplementary material`, `publisher's note`, `consent for
publication`, `ethics`, `abbreviations`, `notes`. Ce sont des mentions
editoriales obligatoires, sans contenu scientifique : elles degraderaient le
retrieval et sont quasi identiques d'un article a l'autre.

**Filet references** — Pour les 4.4% de documents sans titre `References`, une
queue d'au moins 5 lignes consecutives de type citation numerotee est coupee en
fin de derniere section.

**`is_abstract`** — Heuristique : toute section situee **avant** le premier titre
`Introduction` releve du resume structure. Si le document n'a pas d'`Introduction`,
`is_abstract` reste `False` partout. Ca permet de distinguer les `methods` du
resume des `methods` du corps, qui portent le meme nom dans 45.4% des documents.

**Sous-titres** — Un titre hors vocabulaire (`Dose-Response Analysis`,
`Statistical Analysis and Modeling`) est traite comme un **sous-titre** : il
herite de la section de premier niveau en cours, et son libelle exact est
conserve dans `section_raw`. Sans cet heritage, 59% des chunks se retrouvaient
sans section exploitable.

**Sections trop courtes fusionnees** — Une section de moins de 250 caracteres
est presque toujours un faux positif (ligne de tableau, entree de glossaire
d'abreviations). Elle est fusionnee avec la section precedente au lieu de
tomber sous le seuil de chunking, ou son texte serait purement supprime.

**Chunking** — Par paragraphes, cible ~1200 caracteres (~300 tokens), overlap 200
caracteres. Un chunk ne traverse **jamais** une frontiere de section. Les
paragraphes depassant 2000 caracteres sont recoupes par phrases.

**Aucun document n'est perdu.** Si apres nettoyage un article tombe entierement
sous le seuil de 250 caracteres, il est conserve comme un chunk unique marque
`undersized=True` plutot que supprime. Verifiable :
`chunks.doc_id.nunique() == len(metadata_index.csv)`.

**Les 4 articles TDM sont conserves**, pas ecartes. Identifiables via
`restricted_license = True`, donc filtrables en aval si la demo doit etre
license-clean. Les exclure ici serait une decision irreversible prise trop tot.

**Nettoyage applique** — Normalisation NFKC, suppression des caracteres de
controle (y compris `\x9f`, rencontre a l'inspection), soft hyphens, recollage
des mots coupes en fin de ligne, normalisation des espaces.

**Pas de numero de page** — La fiche de mission (Section 5 du Plan de Projet)
prevoit un champ `page` par chunk. Le format `.txt` de `pmc-oa-opendata` ne
contient aucune information de pagination : elle n'existe que dans le PDF
d'origine ou le XML JATS. Le champ est donc absent, volontairement, plutot que
rempli d'une valeur inventee. Recuperable depuis le `.xml` sur S3 si le besoin
se confirme cote embeddings.

---

## Invariants proposes pour les tests de Hanane

```python
assert df.chunk_id.is_unique
assert df.doc_id.nunique() == len(index_csv)          # aucun document perdu
assert df.text.str.strip().ne("").all()
assert (df[~df.undersized].char_count >= 250).all()
assert df.groupby("doc_id").chunk_index.apply(          # indices contigus
    lambda s: sorted(s) == list(range(len(s)))).all()
assert df.license.isin({"CC BY","CC BY-NC","CC BY-NC-ND","TDM"}).all()
assert df.restricted_license.eq(df.license.eq("TDM")).all()
assert not df.section.isin(DROP_SECTIONS).any()       # boilerplate filtre
```

---

## Stabilite du schema

Ce schema est **fige a partir de la v2.0.0**. Toute modification de colonne
(ajout, renommage, changement de type) incremente `transform_version` et est
annoncee a Hanane et Jihad avant regeneration du corpus.

Le champ `sections_inconnues` de `_manifest.json` liste les titres rencontres
hors vocabulaire : a surveiller apres chaque run pour reperer des sections
utiles non prises en compte.

## Resultats du run de reference (26/08/2026, v2.4.0)

| Indicateur | Valeur |
|---|---|
| Documents traites | 700 / 700 |
| Chunks produits | 32 146 |
| Chunks par document | min 1, max 797, moyenne 45.9 |
| Chunks sans section identifiee (`body`) | 1 436 (4.5%) |
| Chunks sous-dimensionnes | 0 |
| Documents a licence restreinte (TDM) | 4 |
| Taux de retention du texte | 1.113 |

**Taux de retention** = caracteres dans les chunks / caracteres dans les
sections conservees. Une valeur **superieure a 1** est normale : l'overlap de
200 caracteres duplique du texte entre chunks voisins. Une valeur **inferieure
a 1 signale une perte de contenu** et doit etre investiguee avant livraison.