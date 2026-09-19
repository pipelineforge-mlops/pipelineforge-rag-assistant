import pytest
import pandas as pd
import csv

VOCABULAIRE_FERME = {
    "abstract", "graphical abstract", "highlights", "background", "introduction",
    "objective", "methods", "statistical analysis", "patients", "participants",
    "data collection", "study design", "results", "findings", "case presentation",
    "case report", "patient presentation", "diagnosis", "treatment", "follow-up",
    "treatment and follow-up", "outcome", "discussion", "limitations", "conclusion", "body"
}

@pytest.fixture(scope="module")
def df_chunks():
    """Charge le corpus transformé (parquet)."""
    return pd.read_parquet("data/processed/chunks.parquet")

@pytest.fixture(scope="module")
def index_metadata():
    """Charge l'index des métadonnées brutes."""
    with open("data/raw/metadata_index.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_chunk_id_is_unique(df_chunks):
    """Vérifie que chaque identifiant de chunk est parfaitement unique dans tout le corpus."""
    assert df_chunks.chunk_id.is_unique, "Les identifiants de chunks ne sont pas uniques"

def test_aucun_document_perdu(df_chunks, index_metadata):
    """S'assure que le nombre de documents originaux correspond au nombre de documents transformés."""
    assert df_chunks.doc_id.nunique() == len(index_metadata), "Certains documents ont été perdus lors de la transformation"

def test_text_not_empty(df_chunks):
    """Vérifie qu'aucun chunk ne contient un texte vide (après suppression des espaces)."""
    assert df_chunks.text.str.strip().ne("").all(), "Certains chunks ont un texte vide"

def test_char_count_minimum(df_chunks):
    """Vérifie que les chunks standards (non 'undersized') respectent la longueur minimale de 250 caractères."""
    assert (df_chunks[~df_chunks.undersized].char_count >= 250).all(), "Certains chunks standards ont moins de 250 caractères"

def test_chunk_indices_are_contiguous(df_chunks):
    """S'assure que les indices des chunks au sein d'un même document se suivent de 0 à N sans trou."""
    is_contiguous = df_chunks.groupby("doc_id").chunk_index.apply(
        lambda s: sorted(s) == list(range(len(s)))
    ).all()
    assert is_contiguous, "Les indices de chunks ne sont pas contigus au sein d'un même document"

def test_license_is_valid(df_chunks):
    """Vérifie que toutes les licences appartiennent au vocabulaire ouvert PubMed / TDM autorisé."""
    valid_licenses = {"CC BY", "CC BY-NC", "CC BY-NC-ND", "TDM"}
    assert df_chunks.license.isin(valid_licenses).all(), "Certaines licences sont inconnues"

def test_restricted_license_flag(df_chunks):
    """S'assure que le booléen 'restricted_license' est cohérent avec la licence 'TDM'."""
    assert df_chunks.restricted_license.eq(df_chunks.license.eq("TDM")).all(), "Le flag restricted_license ne correspond pas à la licence TDM"

def test_section_vocabulary(df_chunks):
    """Vérifie que chaque chunk a une section normalisée appartenant au vocabulaire médical défini."""
    assert set(df_chunks.section) <= VOCABULAIRE_FERME, "Certaines sections sont en dehors du vocabulaire fermé"
