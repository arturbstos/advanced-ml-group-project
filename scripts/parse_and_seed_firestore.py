import re
import asyncio
import os
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.vector import Vector
from openai import AsyncOpenAI

# 1. Parse seed_playbook.sql
with open("db/seed_playbook.sql", "r", encoding="utf-8") as f:
    sql = f.read()

# Extract the VALUES part
values_part = sql.split("VALUES")[1].strip()
if values_part.endswith(";"):
    values_part = values_part[:-1]

# Split into entries
# We can use a regex to match each tuple
pattern = re.compile(
    r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*\)",
    re.DOTALL
)

def unwrap(val):
    val = val.strip()
    if val == "NULL":
        return None
    if val.startswith("$$") and val.endswith("$$"):
        return val[2:-2].strip()
    if val.startswith("'") and val.endswith("'"):
        return val[1:-1].strip()
    return val

entries = []
for match in pattern.finditer(values_part):
    pb_id, clause_type, risk_level, p4, p5, p6, p7, statute_ref, source_url, source_type = match.groups()
    
    entries.append({
        "id": pb_id,
        "clause_type": clause_type,
        "risk_level": risk_level,
        "pattern_description": unwrap(p4),
        "example_risky_wording": unwrap(p5),
        "legal_reasoning": unwrap(p6),
        "recommended_redline": unwrap(p7),
        "statute_ref": statute_ref,
        "source_url": source_url,
        "source_type": source_type
    })

print(f"Parsed {len(entries)} playbook entries from SQL.")

def _compose_text(row) -> str:
    parts = [f"Clause type: {row['clause_type']}", f"Pattern: {row['pattern_description']}"]
    if row.get("example_risky_wording"):
        parts.append(f"Example risky wording: {row['example_risky_wording']}")
    if row.get("recommended_redline"):
        parts.append(f"Recommended redline: {row['recommended_redline']}")
    if row.get("legal_reasoning"):
        parts.append(f"Legal reasoning: {row['legal_reasoning']}")
    return "\n".join(parts)

async def main():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase-adminsdk.json"
    cred = credentials.Certificate("firebase-adminsdk.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.AsyncClient(database="contractdb")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    EMBED_MODEL = "text-embedding-3-small"

    print(f"Seeding {len(entries)} Playbook entries to Firestore (with embeddings)...")
    succeeded, failed = 0, 0
    for pb in entries:
        pb_id = pb.pop("id")
        blob = _compose_text(pb)
        try:
            resp = await client.embeddings.create(model=EMBED_MODEL, input=blob)
            vec = resp.data[0].embedding
            pb["embedding"] = Vector(vec)
            await db.collection("playbook").document(pb_id).set(pb)
            print(f"  [{pb_id}] embedded ({len(blob)} chars)")
            succeeded += 1
        except Exception as e:
            print(f"  [{pb_id}] FAILED: {e}")
            failed += 1
    print(f"Done. {succeeded} succeeded, {failed} failed.")

if __name__ == "__main__":
    asyncio.run(main())
