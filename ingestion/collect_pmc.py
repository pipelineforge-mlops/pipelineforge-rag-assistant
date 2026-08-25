"""
PipelineForge - Ingestion script
Searches PubMed Central for a list of keywords, keeps only articles that are
actually retrievable (Open Access or Author Manuscript), downloads their
metadata + full text from the public pmc-oa-opendata S3 bucket, and builds
a metadata index that the Transformation step (Imane) will consume next.
"""

import os
import csv
import time
import requests
from Bio import Entrez

# ---------- Settings ----------
Entrez.email = "daoukimarouane@gmail.com"  # put your real email here

KEYWORDS = [
    "cancer treatment",
    "infectious disease",
    "clinical trial",
    "drug efficacy",
    "vaccine",
    "diabetes",
    "cardiovascular disease",
    "public health",
    "machine learning diagnosis",
    "epidemiology",
]

PER_KEYWORD_MAX = 150   # how many results to pull per keyword before dedup
TARGET_TOTAL = 700      # stop once we've saved this many articles overall
RAW_DIR = "data/raw"
INDEX_PATH = "data/raw/metadata_index.csv"


def search_keyword(keyword):
    """Return a list of numeric PMC IDs for one keyword, restricted to
    articles that are actually retrievable from the OA dataset."""
    term = f"{keyword} AND (open_access[filter] OR author_manuscript[filter])"
    handle = Entrez.esearch(db="pmc", term=term, retmax=PER_KEYWORD_MAX)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


session = requests.Session()  # reuse connections instead of opening a new one each time


def get_with_retry(url, attempts=3, timeout=20):
    """GET a URL, retrying on transient network errors (connection resets,
    timeouts) with a short backoff. Returns the response, or None if all
    attempts failed."""
    for attempt in range(1, attempts + 1):
        try:
            return session.get(url, timeout=timeout)
        except requests.exceptions.RequestException as e:
            print(f"    (network hiccup on attempt {attempt}/{attempts}: {e})")
            if attempt < attempts:
                time.sleep(2 * attempt)  # 2s, then 4s before next try
    return None  # gave up after all attempts


def fetch_article(pmc_id):
    """Try to download metadata + text for one article (version 1).
    Returns a dict of info to log in the index, or None if unavailable."""
    version = f"PMC{pmc_id}.1"
    base_url = f"https://pmc-oa-opendata.s3.amazonaws.com/{version}/{version}"

    meta_resp = get_with_retry(f"{base_url}.json")
    if meta_resp is None or meta_resp.status_code != 200:
        return None

    metadata = meta_resp.json()

    txt_resp = get_with_retry(f"{base_url}.txt")
    if txt_resp is None or txt_resp.status_code != 200:
        return None  # skip articles without usable full text for now

    os.makedirs(RAW_DIR, exist_ok=True)
    with open(f"{RAW_DIR}/{version}.json", "w", encoding="utf-8") as f:
        f.write(meta_resp.text)
    with open(f"{RAW_DIR}/{version}.txt", "w", encoding="utf-8") as f:
        f.write(txt_resp.text)

    return {
        "pmcid": metadata["pmcid"],
        "version": metadata["version"],
        "title": metadata["title"],
        "license": metadata.get("license_code"),
        "doi": metadata.get("doi"),
        "char_count": len(txt_resp.text),
    }


def main():
    os.makedirs(RAW_DIR, exist_ok=True)
    seen_ids = set()
    saved_rows = []

    for keyword in KEYWORDS:
        if len(saved_rows) >= TARGET_TOTAL:
            break

        print(f"\nSearching: {keyword}")
        ids = search_keyword(keyword)
        time.sleep(0.4)  # stay under NCBI's 3 requests/second limit

        new_ids = [i for i in ids if i not in seen_ids]
        print(f"  {len(ids)} results, {len(new_ids)} new")

        for pmc_id in new_ids:
            if len(saved_rows) >= TARGET_TOTAL:
                break
            seen_ids.add(pmc_id)

            row = fetch_article(pmc_id)
            if row is None:
                continue

            row["matched_keyword"] = keyword
            saved_rows.append(row)
            print(f"  -> saved PMC{pmc_id} ({row['char_count']} chars, {row['license']})")

    # write the metadata index for Imane's transformation step
    with open(INDEX_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "pmcid", "version", "title", "license", "doi",
            "char_count", "matched_keyword"
        ])
        writer.writeheader()
        writer.writerows(saved_rows)

    print(f"\nDone. Saved {len(saved_rows)} articles.")
    print(f"Metadata index written to {INDEX_PATH}")


if __name__ == "__main__":
    main()