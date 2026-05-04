"""Statute reference lookup (Layer 1 — Relational Facts).

Returns the German statutory references (BGB, SGB IV, UrhG, etc.) most
relevant to a given clause_type. Used by clause_analyzer to ground LLM
reasoning in authoritative legal text.
"""
from typing import List, Optional
from pydantic import BaseModel
from google.cloud import firestore

class StatuteRef(BaseModel):
    paragraph: str
    text_excerpt: str
    official_url: Optional[str] = None

async def lookup(clause_type: str, **kwargs) -> List[StatuteRef]:
    """All statute references matching `clause_type` (e.g. 'late_payment_interest')."""
    if not clause_type:
        return []

    db = firestore.AsyncClient(database="contractdb")
    
    # query collection statute_references
    query = db.collection("statute_references").where(
        filter=firestore.FieldFilter("clause_type", "==", clause_type)
    )
    
    results = []
    async for doc in query.stream():
        d = doc.to_dict()
        results.append(StatuteRef(
            paragraph=d.get("paragraph", ""),
            text_excerpt=d.get("text_excerpt", ""),
            official_url=d.get("official_url")
        ))
    return results
