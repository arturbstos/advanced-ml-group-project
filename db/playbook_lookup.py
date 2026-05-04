"""Vector search over the playbook (Layer 2 — Curated Risky-Clause Patterns).

Given a clause snippet from an ingested contract, embeds it with OpenAI
text-embedding-3-small (1536-dim, matching the playbook.embedding column)
and runs a Firestore find_nearest cosine-distance query against the playbook collection.
"""
import os
from typing import List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PlaybookMatch(BaseModel):
    id: str
    clause_type: str
    risk_level: str
    pattern_description: str
    example_risky_wording: Optional[str] = None
    legal_reasoning: str
    recommended_redline: Optional[str] = None
    statute_ref: Optional[str] = None
    similarity: float

async def embed(text_in: str) -> List[float]:
    """Return a single embedding vector for `text_in`."""
    resp = await _client.embeddings.create(model=EMBED_MODEL, input=text_in)
    return resp.data[0].embedding

async def lookup(
    clause_text: str,
    top_k: int = 3,
    min_similarity: float = 0.25,
    **kwargs
) -> List[PlaybookMatch]:
    """Top-k playbook entries most similar to `clause_text`."""
    if not clause_text or not clause_text.strip():
        return []

    vec = await embed(clause_text)

    db = firestore.AsyncClient(database="contractdb")
    collection = db.collection("playbook")
    
    vector_query = collection.find_nearest(
        vector_field="embedding",
        query_vector=Vector(vec),
        distance_measure=DistanceMeasure.COSINE,
        limit=top_k,
        distance_result_field="vector_distance"
    )

    results = []
    async for doc in vector_query.stream():
        d = doc.to_dict()
        dist = d.get("vector_distance", 1.0)
        sim = 1.0 - dist
        if sim >= min_similarity:
            results.append(PlaybookMatch(
                id=doc.id,
                clause_type=d.get("clause_type", ""),
                risk_level=d.get("risk_level", ""),
                pattern_description=d.get("pattern_description", ""),
                example_risky_wording=d.get("example_risky_wording"),
                legal_reasoning=d.get("legal_reasoning", ""),
                recommended_redline=d.get("recommended_redline"),
                statute_ref=d.get("statute_ref"),
                similarity=sim
            ))

    results.sort(key=lambda x: x.similarity, reverse=True)
    return results
