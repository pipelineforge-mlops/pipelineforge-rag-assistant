# Transformation — PipelineForge

Nettoyage et decoupage en chunks du corpus biomedical collecte au Sprint 1.

**Etape 2 de la chaine** — Recoit de : Marouane Daouki (ingestion).
Livre a : Hanane Ayar (qualite & tests), puis El Betti Jihad (embeddings).
Responsable : Imane Alouani.

Le **schema du corpus produit** est documente separement dans
[`SCHEMA.md`](SCHEMA.md) : c'est le contrat avec l'aval, a lire en premier
si vous consommez les donnees plutot que le code.

---

## Lancer la transformation

```bash
pip install -r requirements.txt
python transformation/transform_corpus.py
```

Depuis la **racine du depot** (les chemins sont relatifs a `data/`).
Duree : environ 30 secondes pour les 700 documents.

Produit dans `data/processed/` (non versionne, regenerable) :

| Fichier | Contenu |
|---|---|
| `chunks.jsonl` | 1 chunk par ligne. Format de reference. |
| `chunks.parquet` | Meme contenu, pour pandas. |
| `_manifest.json` | Parametres du run + statistiques. |

Options utiles pendant le developpement :

```bash
python transformation/transform_corpus.py --sample 5   # 5 premiers articles
python transformation/transform_corpus.py --extremes   # doc le + court et le + long
python transformation/transform_corpus.py --no-parquet # JSONL seul
```

`--extremes` est le test a lancer **avant** tout run complet : c'est lui qui a
revele que les case reports produisaient 0 chunk (voir plus bas).

---

## Les scripts

| Script | Role |
|---|---|
| `transform_corpus.py` | **Le pipeline.** Nettoyage, decoupage en sections, chunking, ecriture. |
| `inspect_sections.py` | Inventorie les titres de sections reellement presents dans les 700 documents, avec leur frequence. A relancer si le corpus change. |
| `probe_structure.py` | Affiche la structure detaillee d'un document (lignes, separateurs, candidats titres). Pour comprendre un cas particulier. |
| `debug_split.py` | Trace le decoupage etape par etape sur un document et dit ou et pourquoi il produit 0 chunk. |

Les trois derniers sont des **outils d'exploration**, pas des dependances du
pipeline. Ils sont versionnes parce que les heuristiques de decoupage ne sont
valables que tant que la structure du corpus ne change pas : si le corpus est
regenere, il faut pouvoir remesurer plutot que supposer.

```bash
python transformation/inspect_sections.py > inspect_output.txt
python transformation/probe_structure.py PMC13498802
python transformation/debug_split.py PMC13499463
```

---

## Ce que fait le pipeline

1. **Nettoyage** — normalisation NFKC, suppression des caracteres de controle
   (dont `\x9f`, present dans le corpus), recollage des mots coupes en fin de
   ligne, normalisation des espaces.
2. **Retrait des metadonnees** — les blocs `JOURNAL INFORMATION` et
   `ARTICLE INFORMATION` (revue, DOI, auteurs, affiliations, dates, copyright)
   sont ecartes : ils polluent les embeddings et sont deja dans
   `metadata_index.csv`.
3. **Decoupage en sections** — titres de premier niveau normalises vers un
   vocabulaire ferme ; les sous-titres heritent de leur section parente et
   conservent leur libelle exact dans `section_raw`.
4. **Suppression du boilerplate** — `references`, `funding`,
   `author contributions`, `declarations`, `ethics`, etc.
5. **Chunking** — par paragraphes, cible ~1200 caracteres, overlap 200. Un
   chunk ne traverse jamais une frontiere de section.

Justification detaillee de chaque decision : voir `SCHEMA.md`.

---

## Structure du corpus source (mesuree, non supposee)

Mesure le 26/08/2026 sur les 700 documents avec `inspect_sections.py` :

- 2 blocs `====` dans 100% des documents : `JOURNAL INFORMATION`, `ARTICLE INFORMATION`
- titres du corps en Title Case **sans soulignement** (`Introduction`, `Data Collection`)
- certains articles utilisent des titres **numerotes** (`1 Patient Presentation`) :
  ce sont des case reports
- section `References` detectee dans 95.6% des documents ; pour les 4.4% restants,
  une heuristique coupe la queue de citations numerotees
- 45.4% des documents repetent les noms de sections (resume structure + corps),
  d'ou le champ `is_abstract`

---

## Pieges rencontres (a lire avant de modifier le code)

**Une heuristique calibree sur un document median peut detruire un type
d'article entier.** La v2.0.0 sautait les metadonnees "jusqu'au premier titre
de section connu". Sur les case reports, dont les sections s'appellent
`1 Patient Presentation`, elle sautait tout le contenu et atterrissait sur
`Conflict of Interest`. Resultat : 0 chunk, sans erreur ni avertissement.
Detecte par `--extremes`, corrige en v2.1.0.

**Une fausse section fait disparaitre du texte.** Les lignes de tableaux
d'abreviations etaient prises pour des titres. Chaque fausse section tombait
sous `MIN_CHUNK_CHARS` et son texte etait supprime. Les sections trop courtes
sont maintenant fusionnees avec la precedente (v2.3.0). Le
`taux_retention_texte` du manifest sert de garde-fou : **une valeur inferieure
a 1 signale une perte de contenu**.

**Un echec silencieux est pire qu'un crash.** Les deux bugs ci-dessus
produisaient un corpus incomplet sans lever la moindre exception. D'ou les
compteurs du manifest (`docs_ok`, `chunks_per_doc.min`, `taux_retention_texte`,
`sections_inconnues`) : ils sont la pour rendre visible ce qui echoue en
silence.

---

## Limites connues

- **Pas de numero de page.** La fiche de mission prevoit un champ `page` par
  chunk. Le format `.txt` de `pmc-oa-opendata` ne contient aucune information
  de pagination : elle n'existe que dans le PDF d'origine ou le XML JATS.
  Recuperable depuis le `.xml` sur S3 si le besoin se confirme.
- **`TARGET_CHARS` est calibre en caracteres, pas en tokens.** ~1200 caracteres
  correspondent grossierement a ~300 tokens, mais le vrai tokenizer du modele
  d'embedding decoupera differemment, surtout sur du vocabulaire biomedical.
  A valider avec El Betti Jihad.
- **`is_abstract` depend de la presence d'une section `Introduction`**, absente
  dans 43.6% des documents. La ou elle manque, le flag reste `False` partout.
- **4.5% des chunks ont `section = "body"`** : aucun titre de section n'a pu
  etre identifie. Le texte est intact, seul le libelle manque.
- **Chemins relatifs a la racine du depot.** Pour une integration dans un DAG,
  des options `--raw-dir` / `--out-dir` seraient a ajouter.

---

## Verifier une livraison

```bash
python transformation/transform_corpus.py
cat data/processed/_manifest.json
```

Quatre indicateurs doivent etre verts :

| Indicateur | Attendu |
|---|---|
| `transform_version` | la version attendue — sinon vous relisez un ancien run |
| `stats.docs_ok` | 700 |
| `chunks_per_doc.min` | >= 1 (un 0 signifie un document perdu) |
| `taux_retention_texte` | > 1.0 |

Si `chunks_per_doc.min` vaut 0, identifier le document fautif puis :

```bash
python transformation/debug_split.py <PMCID>
```

Surveiller aussi `sections_inconnues` : les titres qui y apparaissent
regulierement meritent peut-etre d'entrer dans `KEEP_SECTIONS`.