"""
schemas.py — Schémas Pydantic de l'API FastAPI (Chbab Brahim, Sprint 4)
Alignés sur le format exact renvoyé par rag_chain.answer_question()
(Hafsa Elhilali, Sprint 3).
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Question de l'utilisateur")
    top_k: Optional[int] = Field(5, ge=1, le=50, description="Nombre de chunks à récupérer")
    where: Optional[Dict] = Field(
        None, description="Filtre optionnel sur les métadonnées, ex: {'restricted_license': False}"
    )


class Source(BaseModel):
    title: Optional[str] = None
    section: Optional[str] = None
    distance: Optional[float] = None


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    latency_ms: float


class HealthResponse(BaseModel):
    status: str
