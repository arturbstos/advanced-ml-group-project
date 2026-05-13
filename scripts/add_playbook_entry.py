"""Add a single new playbook entry to Firestore with an embedding.

Usage:
    python scripts/add_playbook_entry.py
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore
from google.cloud.firestore_v1.vector import Vector
from openai import AsyncOpenAI

load_dotenv()

cred_path = "firebase-adminsdk.json"
if not os.path.exists(cred_path):
    sys.exit("firebase-adminsdk.json not found.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_path))

db     = firestore.AsyncClient(database="contractdb")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
EMBED_MODEL = "text-embedding-3-small"

NEW_ENTRIES = [
    {
        "id": "PB-006",
        "clause_type": "penalty_clause",
        "risk_level": "high",
        "pattern_description": "Contract imposes a lump-sum contractual penalty (Vertragsstrafe) per breach that is disproportionate to any foreseeable damage.",
        "legal_reasoning": (
            "Under §343 BGB a court may reduce a disproportionate Vertragsstrafe to a reasonable amount. "
            "However, a freelancer must still pay and litigate for reduction. Flat penalties above €10,000 per "
            "breach unrelated to actual damage are routinely reduced by German courts and represent high risk "
            "because they create leverage in disputes. The risk is especially high when the penalty applies "
            "regardless of fault or actual harm (verschuldensunabhängig)."
        ),
        "recommended_redline": (
            "Bei schuldhafter Verletzung der Vertraulichkeitsvereinbarung ist eine Vertragsstrafe von maximal "
            "EUR 5.000 je Verstoß fällig, angerechnet auf einen etwaigen Schadensersatzanspruch. "
            "§343 BGB bleibt unberührt."
        ),
        "statute_ref": "§343 BGB, §339 BGB",
        "example_risky_wording": (
            "Der Auftragnehmer verpflichtet sich zur Zahlung einer Vertragsstrafe von EUR 50.000 je Verstoß, "
            "unabhängig von einem tatsächlich eingetretenen Schaden."
        ),
    },
    {
        "id": "PB-007",
        "clause_type": "governing_law",
        "risk_level": "low",
        "pattern_description": "Standard clause selecting German law and a German court as the jurisdiction.",
        "legal_reasoning": (
            "A clause that simply designates German law and a German court (e.g., München or Berlin) "
            "is standard boilerplate for domestic freelance contracts. It does not restrict the freelancer's "
            "rights and has no meaningful negotiation upside. It should be classified as low risk."
        ),
        "recommended_redline": None,
        "statute_ref": "§38 ZPO",
        "example_risky_wording": (
            "Dieser Vertrag unterliegt dem Recht der Bundesrepublik Deutschland. Gerichtsstand ist München."
        ),
    },
]


def _compose_text(row: dict) -> str:
    parts = [f"Clause type: {row['clause_type']}", f"Pattern: {row['pattern_description']}"]
    if row.get("example_risky_wording"):
        parts.append(f"Example risky wording: {row['example_risky_wording']}")
    if row.get("recommended_redline"):
        parts.append(f"Recommended redline: {row['recommended_redline']}")
    if row.get("legal_reasoning"):
        parts.append(f"Legal reasoning: {row['legal_reasoning']}")
    return "\n".join(parts)


async def main():
    for entry in NEW_ENTRIES:
        pb_id = entry.pop("id")
        blob  = _compose_text(entry)
        resp  = await client.embeddings.create(model=EMBED_MODEL, input=blob)
        entry["embedding"] = Vector(resp.data[0].embedding)
        await db.collection("playbook").document(pb_id).set(entry)
        print(f"[{pb_id}] inserted ({len(blob)} chars)")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
