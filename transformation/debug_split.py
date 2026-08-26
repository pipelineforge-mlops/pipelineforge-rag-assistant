#!/usr/bin/env python3
"""
PipelineForge — Diagnostic du decoupage
Imane Alouani

transform_corpus.py --extremes a produit 0 chunk sur 2 documents.
Ce script trace chaque etape du decoupage pour comprendre ou ca casse.

Usage:
    python transformation/debug_split.py            # les 2 documents extremes
    python transformation/debug_split.py PMC13498802
"""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import transform_corpus as T  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]


def diagnose(pmcid: str, version: str = "1") -> None:
    path = T.RAW_DIR / f"{pmcid}.{version}.txt"
    print("=" * 70)
    print(f"=== {path.name}")
    if not path.exists():
        print("  [!] fichier absent")
        return

    raw = path.read_text(encoding="utf-8", errors="replace")
    print(f"  brut          : {len(raw)} caracteres, {len(raw.splitlines())} lignes")

    cleaned = T.clean_text(raw)
    print(f"  apres nettoyage: {len(cleaned)} caracteres, "
          f"{len(cleaned.splitlines())} lignes")

    lines = cleaned.splitlines()
    seps = [i for i, ln in enumerate(lines) if T.SEPARATOR.match(ln)]
    print(f"  separateurs '====' aux lignes : {seps}")

    if seps:
        after = lines[seps[-1] + 1:]
        print(f"  lignes apres le dernier separateur : {len(after)}")
        print("  --- 8 premieres ---")
        for ln in after[:8]:
            print(f"      | {ln[:100]}")
    else:
        after = lines
        print("  [!] aucun separateur trouve")

    first = next((i for i, ln in enumerate(after)
                  if T.KNOWN_SECTION.match(ln.strip())), None)
    if first is None:
        print("  [!] AUCUN titre de section connu trouve apres le separateur")
    else:
        print(f"  premier titre connu : ligne +{first} -> {after[first].strip()!r}")

    parsed = T.split_sections(cleaned)
    print(f"\n  sections detectees : {len(parsed)}")
    for name, body, is_abs in parsed[:25]:
        flag = " [ABSTRACT]" if is_abs else ""
        drop = " [SUPPRIMEE]" if name in T.DROP_SECTIONS else ""
        print(f"      {name:<32} {len(body):>8} car.{flag}{drop}")
    if len(parsed) > 25:
        print(f"      ... et {len(parsed) - 25} autres")

    kept = [(n, b) for n, b, _ in parsed if n not in T.DROP_SECTIONS]
    print(f"\n  sections conservees : {len(kept)}, "
          f"total {sum(len(b) for _, b in kept)} caracteres")

    n_chunks = sum(len(T.chunk_section(T.strip_trailing_refs(n, b))) for n, b in kept)
    print(f"  chunks produits    : {n_chunks}")
    if kept and n_chunks == 0:
        n, b = max(kept, key=lambda x: len(x[1]))
        stripped = T.strip_trailing_refs(n, b)
        print(f"  [!] plus grosse section conservee : {n!r} ({len(b)} car.)")
        print(f"      apres strip_trailing_refs : {len(stripped)} car.")
        print(f"      extrait : {stripped[:200]!r}")


def main() -> None:
    if len(sys.argv) > 1:
        diagnose(sys.argv[1])
        return
    rows = list(csv.DictReader(T.INDEX_CSV.open(encoding="utf-8")))
    rows.sort(key=lambda r: int(r.get("char_count") or 0))
    for r in (rows[0], rows[-1]):
        diagnose(r["pmcid"], r.get("version", "1"))


if __name__ == "__main__":
    main()