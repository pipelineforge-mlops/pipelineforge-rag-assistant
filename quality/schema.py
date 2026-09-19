from pydantic import BaseModel, Field, field_validator
from typing import Optional

VOCABULAIRE_FERME = {
    "abstract", "graphical abstract", "highlights", "background", "introduction",
    "objective", "methods", "statistical analysis", "patients", "participants",
    "data collection", "study design", "results", "findings", "case presentation",
    "case report", "patient presentation", "diagnosis", "treatment", "follow-up",
    "treatment and follow-up", "outcome", "discussion", "limitations", "conclusion", "body"
}

LICENSES_AUTORISEES = {"CC BY", "CC BY-NC", "CC BY-NC-ND", "TDM"}

class ChunkSchema(BaseModel):
    chunk_id: str = Field(..., description="Identifiant unique du chunk (ex: PMC123.1_c000)")
    doc_id: str = Field(..., description="Identifiant du document source")
    pmcid: str = Field(..., description="ID PubMed Central")
    version: int | str = Field(..., description="Version de l'article")
    chunk_index: int = Field(..., ge=0, description="Position du chunk dans le document")
    n_chunks_doc: int = Field(..., gt=0, description="Nombre total de chunks du document")
    
    section: str = Field(..., description="Titre de section normalisé")
    section_raw: str = Field(..., description="Titre de section original")
    is_abstract: bool = Field(..., description="Vrai si issu du résumé")
    
    text: str = Field(..., min_length=1, description="Contenu textuel du chunk")
    char_count: int = Field(..., gt=0, description="Nombre de caractères")
    word_count: int = Field(..., gt=0, description="Nombre de mots")
    
    title: str = Field(..., description="Titre de l'article")
    doi: Optional[str] = Field(None, description="DOI de l'article")
    
    license: str = Field(..., description="Licence du texte")
    restricted_license: bool = Field(..., description="Vrai si manuscrit d'auteur NIH")
    matched_keyword: str = Field(..., description="Mot clé de collecte")
    undersized: bool = Field(..., description="Vrai si longueur inférieure au seuil")
    source: str = Field(..., description="Origine des données (ex: pmc-oa-opendata)")
    transform_version: str = Field(..., description="Version du script de transformation")

    @field_validator('section')
    def check_section_vocab(cls, v):
        if v not in VOCABULAIRE_FERME:
            raise ValueError(f"Section non reconnue: {v}")
        return v

    @field_validator('license')
    def check_license(cls, v):
        if v not in LICENSES_AUTORISEES:
            raise ValueError(f"Licence non autorisée: {v}")
        return v

    @field_validator('text')
    def check_encoding(cls, v):
        if "\ufffd" in v:
            raise ValueError("Erreur d'encodage détectée dans le texte (caractère de remplacement présent).")
        return v
