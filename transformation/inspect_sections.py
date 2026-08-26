#!/usr/bin/env python3
"""
PipelineForge — Inspection du corpus brut, v2
Imane Alouani

v1 ne cherchait que des titres MAJUSCULES soulignes : elle n'a trouve que
2 sections. La sonde de structure a montre que le corps utilise des titres
en Title Case, sans soulignement.

Ce script valide les heuristiques de decoupage sur les 700 documents avant
d'ecrire quoi que ce soit dans data/processed/.

Usage:
    python transformation/inspect_sections.py
    python transformation/inspect_sections.py > inspect_output.txt
"""

import collections
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

RAW_DIR = Path("data/raw")

# Separateur de bloc de haut niveau : une ligne composee uniquement de '='.
SEPARATOR = re.compile(r"^=+\s*$")

# Vocabulaire de sections scientifiques (insensible a la casse, ligne entiere).
KNOWN_SECTION = re.compile(
    r"^(abstract|background|introduction|objectives?|aims?|methods?|"
    r"materials and methods|patients?|participants?|study design|"
    r"data collection|statistical analysis.*|results?|findings?|"
    r"discussion|limitations?|conclusions?|acknowledge?ments?|funding|"
    r"author contributions?|conflicts? of interest|"
    r"declaration of conflicting interests|data availability.*|"
    r"supplementary material.*|references?|notes)$",
    re.I,
)


def is_heading(line: str, prev_blank: bool) -> bool:
    """Titre = ligne courte, sans ponctuation finale, isolee ou du vocabulaire connu."""
    s = line.strip()
    if not (2 < len(s) < 60):
        return False
    if s.endswith((".", ",", ";", ":")) or s[0].isdigit():
        return False
    if KNOWN_SECTION.match(s):
        return True
    # titre generique : Title Case, precede d'une ligne vide
    return prev_blank and s[0].isupper() and not s.isupper() and len(s.split()) <= 7


def analyse(text: str) -> dict:
    lines = text.splitlines()

    blocks = [i for i, ln in enumerate(lines) if SEPARATOR.match(ln)]
    block_titles = []
    for i in blocks:
        prev = lines[i - 1].strip() if i > 0 else ""
        block_titles.append(prev if prev else "(SANS TITRE)")

    # Le contenu scientifique commence apres le DERNIER separateur '===='.
    # Tout ce qui precede (JOURNAL INFORMATION, ARTICLE INFORMATION : revue,
    # DOI, auteurs, affiliations, copyright) est de la metadonnee.
    start = blocks[-1] + 1 if blocks else 0

    headings, prev_blank = [], True
    for ln in lines[start:]:
        if is_heading(ln, prev_blank):
            headings.append(ln.strip())
        prev_blank = not ln.strip()

    return {"block_titles": block_titles, "headings": headings}


def main() -> None:
    files = sorted(RAW_DIR.glob("PMC*.txt"))
    if not files:
        sys.exit(f"[!] aucun .txt dans {RAW_DIR} — as-tu fait `git pull` ?")

    n_blocks = collections.Counter()
    block_names = collections.Counter()
    heading_freq = collections.Counter()
    has_refs = 0
    dupes = 0

    for path in files:
        r = analyse(path.read_text(encoding="utf-8", errors="replace"))
        n_blocks[len(r["block_titles"])] += 1
        block_names.update(r["block_titles"])
        norm = [h.lower() for h in r["headings"]]
        heading_freq.update(set(norm))
        if any(h.startswith("reference") for h in norm):
            has_refs += 1
        if len(norm) != len(set(norm)):
            dupes += 1

    n = len(files)
    print(f"Documents analyses : {n}\n")

    print("--- Nombre de blocs '====' par document ---")
    for k, v in sorted(n_blocks.items()):
        print(f"  {k} blocs : {v} documents ({v/n:.1%})")

    print("\n--- Titres des blocs de haut niveau ---")
    for name, c in block_names.most_common(12):
        print(f"{c:5d}  ({c/n:5.1%})  {name}")

    print(f"\n--- Section 'References' detectee : {has_refs}/{n} ({has_refs/n:.1%}) ---")
    print(f"--- Documents avec titres dupliques (abstract + corps) : "
          f"{dupes}/{n} ({dupes/n:.1%}) ---")

    print(f"\n--- Titres de sections du corps, par frequence ---")
    for name, c in heading_freq.most_common(45):
        print(f"{c:5d}  ({c/n:5.1%})  {name}")


if __name__ == "__main__":
    main()