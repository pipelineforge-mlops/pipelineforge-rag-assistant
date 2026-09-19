#!/usr/bin/env python3
"""
PipelineForge — Sonde de structure du corps d'article
Imane Alouani

inspect_sections.py n'a trouve que 2 sections (JOURNAL INFORMATION,
ARTICLE INFORMATION). Tout le corps de l'article est donc dans un seul bloc.
Ce script regarde COMMENT ce bloc est organise, pour savoir sur quoi
decouper (et comment reperer les references).

Usage:
    python transformation/probe_structure.py
    python transformation/probe_structure.py PMC13498670
"""

import csv
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAW_DIR = Path("data/raw")
INDEX_CSV = RAW_DIR / "metadata_index.csv"


def pick_median_doc() -> tuple[str, str]:
    rows = list(csv.DictReader(INDEX_CSV.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r.get("char_count") or 0))
    r = rows[len(rows) // 2]
    return r["pmcid"], r.get("version", "1")


def main() -> None:
    if len(sys.argv) > 1:
        pmcid, version = sys.argv[1], "1"
    else:
        pmcid, version = pick_median_doc()

    path = RAW_DIR / f"{pmcid}.{version}.txt"
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()

    print(f"=== {path.name} — {len(text)} caracteres, {len(lines)} lignes ===")

    print("\n########## 40 PREMIERES LIGNES ##########")
    for i, ln in enumerate(lines[:40], 1):
        print(f"{i:5d}| {ln[:110]}")

    print("\n########## 25 DERNIERES LIGNES (zone references ?) ##########")
    start = max(0, len(lines) - 25)
    for i, ln in enumerate(lines[start:], start + 1):
        print(f"{i:5d}| {ln[:110]}")

    # Lignes courtes sans ponctuation finale = candidats titres de section
    print("\n########## CANDIDATS TITRES (lignes courtes, sans point final) ##########")
    shown = 0
    for i, ln in enumerate(lines, 1):
        s = ln.strip()
        if 2 < len(s) < 70 and not s.endswith((".", ",", ";", ":")) and not s[0].isdigit():
            print(f"{i:5d}| {s}")
            shown += 1
            if shown >= 45:
                print("      ... (tronque)")
                break

    # Ou apparaissent les mots-cles de section, quel que soit leur formatage
    print("\n########## OCCURRENCES DE MOTS-CLES DE SECTION ##########")
    for kw in ["abstract", "introduction", "background", "method", "result",
               "discussion", "conclusion", "reference", "acknowledg", "funding"]:
        hits = [i for i, ln in enumerate(lines, 1)
                if re.search(rf"\b{kw}", ln, re.I) and len(ln.strip()) < 80]
        if hits:
            print(f"{kw:<14} lignes {hits[:8]}{' ...' if len(hits) > 8 else ''}")


if __name__ == "__main__":
    main()