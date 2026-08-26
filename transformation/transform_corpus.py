#!/usr/bin/env python3
"""
PipelineForge — Transformation (Sprint 2)
Imane Alouani

Corpus brut (data/raw/) -> corpus nettoye et chunke (data/processed/).

Calibre sur la structure REELLE des 700 documents, mesuree le 26/08/2026
avec transformation/inspect_sections.py :
  - 2 blocs '====' dans 100% des documents : JOURNAL INFORMATION, ARTICLE INFORMATION
  - le contenu scientifique suit le 2e bloc, PRECEDE de metadonnees d'article
    (auteurs, affiliations, dates, copyright) qu'il faut ecarter
  - titres de sections du corps en Title Case, sans soulignement
  - section References detectee dans 95.6% des documents
  - 45.4% des documents repetent les noms de sections (resume structure + corps)

Usage:
    python transformation/transform_corpus.py --sample 5
    python transformation/transform_corpus.py --extremes
    python transformation/transform_corpus.py
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

# --------------------------------------------------------------------------
# Parametres
# --------------------------------------------------------------------------

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
INDEX_CSV = RAW_DIR / "metadata_index.csv"

TRANSFORM_VERSION = "2.4.0"

TARGET_CHARS = 1200
OVERLAP_CHARS = 200
MIN_CHUNK_CHARS = 250
MAX_CHUNK_CHARS = 2000

RESTRICTED_LICENSES = {"TDM"}

# --------------------------------------------------------------------------
# Vocabulaire de sections (mesure sur les 700 documents)
# --------------------------------------------------------------------------

# Variantes -> nom canonique. Sans ca, Jihad recoit 'conclusion' ET 'conclusions'.
SECTION_ALIASES = {
    "conclusions": "conclusion",
    "acknowledgements": "acknowledgments",
    "conflict of interest": "conflicts of interest",
    "declaration of competing interest": "conflicts of interest",
    "declaration of interests": "conflicts of interest",
    "declaration of conflicting interests": "conflicts of interest",
    "competing interests": "conflicts of interest",
    "disclosure": "disclosures",
    "data availability statement": "data availability",
    "objectives": "objective",
    "materials and methods": "methods",
    "credit authorship contribution statement": "author contributions",
    "supplementary information": "supplementary material",
    "supporting information": "supplementary material",
    "appendix a supplementary data": "supplementary material",
    "ethics approval and consent to participate": "ethics",
    "ethics approval": "ethics",
    "ethics statement": "ethics",
    "ethical considerations": "ethics",
}

# Sections conservees : contenu scientifique reel.
KEEP_SECTIONS = {
    "abstract", "graphical abstract", "highlights", "background", "introduction",
    "objective", "methods", "statistical analysis", "patients", "participants",
    "data collection", "study design", "results", "findings", "case presentation",
    "discussion", "limitations", "conclusion", "body",
    "case report", "patient presentation", "diagnosis", "treatment",
    "follow-up", "treatment and follow-up", "outcome",
}

# Sections ecartees : boilerplate editorial, aucune valeur pour du retrieval.
DROP_SECTIONS = {
    "references", "author contributions", "funding", "acknowledgments",
    "data availability", "conflicts of interest", "disclosures", "declarations",
    "supplementary material", "publisher's note", "publisher\u2019s note",
    "consent for publication", "ethics", "abbreviations", "notes",
}

_KNOWN = set(SECTION_ALIASES) | KEEP_SECTIONS | DROP_SECTIONS
KNOWN_SECTION = re.compile(
    r"^(" + "|".join(sorted((re.escape(s) for s in _KNOWN), key=len, reverse=True)) + r")$",
    re.I,
)

SEPARATOR = re.compile(r"^=+\s*$")

# Ligne de reference numerotee : "12 Author A Author B . Titre. Journal. 2020;..."
NUMBERED_REF = re.compile(r"^\s*\d{1,3}[\.\)]?\s+[A-Z]")

# Titre numerote : "1 Patient Presentation", "2. Diagnosis". Frequent dans les
# case reports. Meme forme qu'une reference numerotee : c'est la LONGUEUR qui
# les distingue (un titre est court, une reference est une phrase entiere).
NUMBERED_HEADING = re.compile(r"^\d{1,2}[\.\)]?\s+[A-Z]")
LEADING_NUMBER = re.compile(r"^\d{1,2}[\.\)]?\s+")

# --------------------------------------------------------------------------
# Schema de sortie
# --------------------------------------------------------------------------


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    pmcid: str
    version: str
    chunk_index: int
    n_chunks_doc: int
    section: str             # vocabulaire FERME (voir KEEP_SECTIONS) ou "other"
    section_raw: str         # titre reellement lu dans le document
    is_abstract: bool        # True si la section appartient au resume structure
    text: str
    char_count: int
    word_count: int
    title: str
    doi: str
    license: str
    restricted_license: bool
    matched_keyword: str
    undersized: bool = False
    source: str = "pmc-oa-opendata"
    transform_version: str = TRANSFORM_VERSION


# --------------------------------------------------------------------------
# Nettoyage
# --------------------------------------------------------------------------

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")
_HYPHEN_BREAK = re.compile(r"(\w)-\n(\w)")
_MULTI_SPACE = re.compile(r"[ \t]+")
_MULTI_NL = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = _CTRL.sub("", text)              # inclut \x9f, vu a l'inspection
    text = text.replace("\u00ad", "")
    text = _HYPHEN_BREAK.sub(r"\1\2", text)
    text = _MULTI_SPACE.sub(" ", text)
    return _MULTI_NL.sub("\n\n", text).strip()


def normalize_section(name: str) -> str:
    """
    "2 Diagnosis: Choroidal Metastasis Secondary to..." -> "diagnosis"

    On retire le numero de tete et tout ce qui suit les deux-points : sinon
    chaque case report cree un nom de section unique, et le champ `section`
    devient inexploitable en aval.
    """
    s = LEADING_NUMBER.sub("", name.strip()).strip()
    s = s.split(":", 1)[0]
    s = re.sub(r"\s+", " ", s.lower()).strip(" :.")
    return SECTION_ALIASES.get(s, s)


# --------------------------------------------------------------------------
# Decoupage en sections
# --------------------------------------------------------------------------


def is_heading(line: str, prev_blank: bool) -> bool:
    s = line.strip().rstrip(":")
    if not (2 < len(s) < 80) or s.endswith((",", ";")):
        return False

    core = LEADING_NUMBER.sub("", s)          # "1 Patient Presentation" -> "Patient..."
    if not core or not core[0].isupper():
        return False

    if KNOWN_SECTION.match(core):
        return True

    # titre numerote : court, sinon c'est une reference bibliographique
    if NUMBERED_HEADING.match(s):
        return len(core.split()) <= 8

    if s[0].isdigit() or s.endswith("."):
        return False

    # Un titre generique ne commence pas par un article : "A Framework for
    # Action" ou "A National, Integrated Strategy" sont des bouts de phrase,
    # pas des sections (vus dans sections_inconnues au premier run complet).
    if core.split()[0].lower() in {"a", "an", "the", "this", "these", "our", "we"}:
        return False
    return prev_blank and not s.isupper() and len(s.split()) <= 7


def content_start(lines: list[str]) -> int:
    """
    Debut du contenu scientifique = la PREMIERE des trois choses suivantes :
      - un titre de section connu
      - un titre numerote court (case reports : "1 Patient Presentation")
      - une vraie phrase de prose (>= 120 caracteres, ponctuation finale)

    v2.0.0 ne cherchait que le premier titre connu : sur les case reports, elle
    sautait tout le contenu jusqu'a 'Conflict of Interest' et produisait 0 chunk.
    """
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s:
            continue
        core = LEADING_NUMBER.sub("", s.rstrip(":"))
        if core and KNOWN_SECTION.match(core):
            return i
        if NUMBERED_HEADING.match(s) and len(s) < 80 and len(core.split()) <= 8:
            return i
        if len(s) >= 120 and s.endswith((".", "?", "!")):
            return i
    return 0


def split_sections(raw: str) -> list[tuple[str, str, bool]]:
    """
    -> [(section_canonique, texte, is_abstract), ...]

    1. le contenu commence apres le DERNIER separateur '===='
    2. les metadonnees d'article (auteurs, affiliations, dates) precedent le
       contenu : on demarre au premier titre de section connu
    3. is_abstract = section situee avant le premier 'introduction'
    """
    lines = raw.splitlines()
    seps = [i for i, ln in enumerate(lines) if SEPARATOR.match(ln)]
    lines = lines[seps[-1] + 1:] if seps else lines

    # 2. sauter le bloc de metadonnees (auteurs, affiliations, dates, copyright)
    lines = lines[content_start(lines):]

    sections: list[list] = [["body", []]]
    prev_blank = True
    for ln in lines:
        if is_heading(ln, prev_blank):
            sections.append([normalize_section(ln), []])
        else:
            sections[-1][1].append(ln)
        prev_blank = not ln.strip()

    # 3. tout ce qui precede 'introduction' releve du resume structure
    names = [s[0] for s in sections]
    cut = names.index("introduction") if "introduction" in names else -1

    out: list[tuple[str, str, bool]] = []
    for i, (name, buf) in enumerate(sections):
        body = "\n".join(buf).strip()
        if not body:
            continue
        in_abs = cut > 0 and i < cut

        # Une "section" trop courte est presque toujours un faux positif :
        # ligne de tableau, entree de glossaire d'abreviations. La fusionner
        # avec la precedente au lieu de la laisser tomber sous le seuil de
        # chunking, ou son texte serait purement supprime.
        if out and len(body) < MIN_CHUNK_CHARS and out[-1][0] not in DROP_SECTIONS:
            prev_name, prev_body, prev_abs = out[-1]
            out[-1] = (prev_name, f"{prev_body}\n\n{name}\n{body}", prev_abs)
        else:
            out.append((name, body, in_abs))
    return out


def strip_trailing_refs(name: str, text: str) -> str:
    """
    Filet pour les 4.4% de documents sans titre 'References' : coupe la queue
    de lignes numerotees type citation en fin de derniere section.
    """
    if name in DROP_SECTIONS:
        return text
    lines = text.split("\n")
    i, hits = len(lines), 0
    while i > 0:
        s = lines[i - 1].strip()
        if not s:
            i -= 1
            continue
        if NUMBERED_REF.match(s):
            hits += 1
            i -= 1
            continue
        break
    return "\n".join(lines[:i]).strip() if hits >= 5 else text


# --------------------------------------------------------------------------
# Chunking
# --------------------------------------------------------------------------

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def _hard_split(block: str) -> list[str]:
    pieces, buf = [], ""
    for sent in _SENT_SPLIT.split(block):
        if len(buf) + len(sent) + 1 <= MAX_CHUNK_CHARS:
            buf = f"{buf} {sent}".strip()
        else:
            if buf:
                pieces.append(buf)
            while len(sent) > MAX_CHUNK_CHARS:
                pieces.append(sent[:MAX_CHUNK_CHARS])
                sent = sent[MAX_CHUNK_CHARS:]
            buf = sent
    if buf:
        pieces.append(buf)
    return pieces


def chunk_section(text: str) -> list[str]:
    blocks: list[str] = []
    for para in text.split("\n\n"):
        para = para.strip()
        if para:
            blocks.extend(_hard_split(para) if len(para) > MAX_CHUNK_CHARS else [para])

    chunks: list[str] = []
    buf = ""
    for block in blocks:
        if not buf:
            buf = block
        elif len(buf) + len(block) + 2 <= TARGET_CHARS:
            buf = f"{buf}\n\n{block}"
        else:
            chunks.append(buf)
            tail = buf[-OVERLAP_CHARS:]
            tail = tail[tail.find(" ") + 1:] if " " in tail else ""
            buf = f"{tail}\n\n{block}".strip() if tail else block
    if buf:
        chunks.append(buf)

    merged: list[str] = []
    for c in chunks:
        if merged and len(c) < MIN_CHUNK_CHARS:
            merged[-1] = f"{merged[-1]}\n\n{c}"
        else:
            merged.append(c)
    return [c for c in merged if len(c) >= MIN_CHUNK_CHARS]


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------


def transform_document(article: dict, raw: str) -> tuple[list[Chunk], set[str]]:
    pmcid = article["pmcid"]
    version = article.get("version", "1")
    doc_id = f"{pmcid}.{version}"
    lic = article.get("license", "")

    def new_chunk(section: str, raw_title: str, in_abs: bool, text: str, idx: int,
                  undersized: bool = False) -> Chunk:
        return Chunk(
            chunk_id="", doc_id=doc_id, pmcid=pmcid, version=str(version),
            chunk_index=idx, n_chunks_doc=0,
            section=section if section in KEEP_SECTIONS else "body",
            section_raw=raw_title, is_abstract=in_abs,
            text=text, char_count=len(text), word_count=len(text.split()),
            title=article.get("title", ""), doi=article.get("doi", ""),
            license=lic, restricted_license=lic in RESTRICTED_LICENSES,
            matched_keyword=article.get("matched_keyword", ""), undersized=undersized,
        )

    parsed = split_sections(clean_text(raw))
    seen_sections = {name for name, _, _ in parsed}

    # Un titre hors vocabulaire ("Statistical Analysis and Modeling",
    # "Dose-Response Analysis") est un SOUS-TITRE : il herite de la section de
    # premier niveau en cours. Sans ca, 59% des chunks se retrouvaient en
    # "other" et la colonne section devenait inexploitable en aval.
    chunks: list[Chunk] = []
    current = "body"
    for name, content, in_abstract in parsed:
        if name in KEEP_SECTIONS or name in DROP_SECTIONS:
            current = name
        if current in DROP_SECTIONS:
            continue
        for piece in chunk_section(strip_trailing_refs(current, content)):
            chunks.append(new_chunk(current, name, in_abstract, piece, len(chunks)))

    # Aucun document ne disparait silencieusement.
    if not chunks:
        salvage = "\n\n".join(c for n, c, _ in parsed if n not in DROP_SECTIONS).strip()
        if salvage:
            chunks.append(new_chunk("body", "body", False, salvage, 0, undersized=True))

    total = len(chunks)
    for c in chunks:
        c.n_chunks_doc = total
        c.chunk_id = f"{doc_id}_c{c.chunk_index:04d}"
    return chunks, seen_sections


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int)
    ap.add_argument("--extremes", action="store_true")
    ap.add_argument("--no-parquet", action="store_true")
    args = ap.parse_args()

    if not INDEX_CSV.exists():
        sys.exit(f"[!] {INDEX_CSV} introuvable — as-tu fait `git pull` ?")
    articles = list(csv.DictReader(INDEX_CSV.open(encoding="utf-8")))

    if args.extremes:
        articles.sort(key=lambda a: int(a.get("char_count") or 0))
        articles = [articles[0], articles[-1]]
    elif args.sample:
        articles = articles[:args.sample]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    jsonl = OUT_DIR / "chunks.jsonl"

    stats = {"docs_ok": 0, "docs_missing": 0, "chunks": 0,
             "restricted_docs": 0, "undersized_chunks": 0,
             "chunks_section_body": 0,
             "car_sections_conservees": 0, "car_chunks": 0}
    per_doc: list[int] = []
    sections_seen: set[str] = set()

    with jsonl.open("w", encoding="utf-8") as out:
        for a in articles:
            path = RAW_DIR / f"{a['pmcid']}.{a.get('version', '1')}.txt"
            if not path.exists():
                stats["docs_missing"] += 1
                print(f"[!] manquant : {path}", file=sys.stderr)
                continue

            raw = path.read_text(encoding="utf-8", errors="replace")
            chunks, seen = transform_document(a, raw)
            sections_seen |= seen
            for c in chunks:
                out.write(json.dumps(asdict(c), ensure_ascii=False) + "\n")

            stats["docs_ok"] += 1
            stats["chunks"] += len(chunks)
            if chunks:
                stats["restricted_docs"] += int(chunks[0].restricted_license)
            stats["undersized_chunks"] += sum(c.undersized for c in chunks)
            stats["chunks_section_body"] += sum(c.section == "body" for c in chunks)
            stats["car_chunks"] += sum(c.char_count for c in chunks)
            stats["car_sections_conservees"] += sum(
                len(b) for n, b, _ in split_sections(clean_text(raw))
                if n not in DROP_SECTIONS)
            per_doc.append(len(chunks))

    if not args.no_parquet and stats["chunks"]:
        try:
            import pandas as pd
            pd.read_json(jsonl, lines=True).to_parquet(OUT_DIR / "chunks.parquet",
                                                       index=False)
        except ImportError:
            print("[i] pandas/pyarrow absents — JSONL uniquement", file=sys.stderr)

    manifest = {
        "transform_version": TRANSFORM_VERSION,
        "params": {"target_chars": TARGET_CHARS, "overlap_chars": OVERLAP_CHARS,
                   "min_chunk_chars": MIN_CHUNK_CHARS, "max_chunk_chars": MAX_CHUNK_CHARS},
        "stats": stats,
        "chunks_per_doc": {"min": min(per_doc, default=0), "max": max(per_doc, default=0),
                           "moyenne": round(sum(per_doc) / len(per_doc), 1) if per_doc else 0},
        "taux_retention_texte": (
            round(stats["car_chunks"] / stats["car_sections_conservees"], 3)
            if stats["car_sections_conservees"] else 0),
        "sections_inconnues": sorted(sections_seen - _KNOWN)[:30],
    }
    (OUT_DIR / "_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()