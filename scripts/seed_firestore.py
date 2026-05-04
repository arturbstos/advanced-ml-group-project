"""Seed Firestore with Playbook, Statutes, and Rate Benchmarks.

This script replaces both `db/init.sql` and `scripts/seed_vectors.py` by:
1. Creating collections for `rate_benchmarks`, `statute_references`, and `playbook`.
2. Pushing the static base data into them.
3. Automatically generating OpenAI embeddings for the playbook entries
   and storing them natively in Firestore using VectorValue.
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

# Initialize Firebase
cred_path = "firebase-adminsdk.json"
if not os.path.exists(cred_path):
    sys.exit("firebase-adminsdk.json not found! Please place it in the project root.")

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

if not firebase_admin._apps:
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

db = firestore.AsyncClient(database="contractdb")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

EMBED_MODEL = "text-embedding-3-small"

# --- STATIC SEED DATA ---
RATES = [
    {"skill_category": "Software Development", "experience": "mid", "region": "Bayern", "p25": 75.0, "median": 95.0, "p75": 115.0, "source": "Freelancer-Kompass", "source_year": 2025},
    {"skill_category": "Software Development", "experience": "mid", "region": None, "p25": 70.0, "median": 90.0, "p75": 110.0, "source": "Freelancer-Kompass", "source_year": 2025},
    {"skill_category": "Other", "experience": "mid", "region": None, "p25": 60.0, "median": 80.0, "p75": 100.0, "source": "Fallback", "source_year": 2024},
]

STATUTES = [
    {"clause_type": "late_payment_interest", "paragraph": "§288 Abs. 2 BGB", "text_excerpt": "Bei Rechtsgeschäften, an denen ein Verbraucher nicht beteiligt ist, beträgt der Zinssatz für Entgeltforderungen neun Prozentpunkte über dem Basiszinssatz.", "official_url": "https://www.gesetze-im-internet.de/bgb/__288.html"},
    {"clause_type": "payment_terms", "paragraph": "§271a BGB", "text_excerpt": "Eine Vereinbarung, nach der der Gläubiger einer Entgeltforderung die Erfüllung erst nach mehr als 60 Tagen nach Empfang der Gegenleistung verlangen kann, ist nur wirksam, wenn sie ausdrücklich getroffen und im Hinblick auf die Belange des Gläubigers nicht grob unbillig ist.", "official_url": "https://www.gesetze-im-internet.de/bgb/__271a.html"},
    {"clause_type": "scheinselbstständigkeit", "paragraph": "§7 Abs. 1 SGB IV", "text_excerpt": "Beschäftigung ist die nichtselbständige Arbeit, insbesondere in einem Arbeitsverhältnis. Anhaltspunkte für eine Beschäftigung sind eine Tätigkeit nach Weisungen und eine Eingliederung in die Arbeitsorganisation des Weisungsgebers.", "official_url": "https://www.gesetze-im-internet.de/sgb_4/__7.html"},
    {"clause_type": "intellectual_property", "paragraph": "§31 UrhG", "text_excerpt": "Der Urheber kann einem anderen das Recht einräumen, das Werk auf einzelne oder alle Nutzungsarten zu nutzen (Nutzungsrecht). Das Nutzungsrecht kann als einfaches oder ausschließliches Recht sowie räumlich, zeitlich oder inhaltlich beschränkt eingeräumt werden.", "official_url": "https://www.gesetze-im-internet.de/urhg/__31.html"},
    {"clause_type": "liability", "paragraph": "§307 Abs. 1 BGB", "text_excerpt": "Bestimmungen in Allgemeinen Geschäftsbedingungen sind unwirksam, wenn sie den Vertragspartner des Verwenders entgegen den Geboten von Treu und Glauben unangemessen benachteiligen.", "official_url": "https://www.gesetze-im-internet.de/bgb/__307.html"}
]

PLAYBOOK = [
    {
        "id": "PB-001",
        "clause_type": "late_payment_interest",
        "risk_level": "medium",
        "pattern_description": "Contract specifies a late-payment interest rate below the B2B statutory default.",
        "legal_reasoning": "§288 Abs. 2 BGB sets the default statutory interest rate for B2B transactions at 9 percentage points above the base rate. Agreeing to a fixed lower rate (e.g., 4%) reduces legal entitlement.",
        "recommended_redline": "Bei Zahlungsverzug werden Verzugszinsen in gesetzlicher Höhe gemäß §288 Abs. 2 BGB berechnet.",
        "statute_ref": "§288 Abs. 2 BGB",
        "example_risky_wording": None
    },
    {
        "id": "PB-002",
        "clause_type": "payment_terms",
        "risk_level": "medium",
        "pattern_description": "Payment term exceeds 30 days without clear justification.",
        "legal_reasoning": "Standard industry norms are 14–30 days. While §271a BGB allows up to 60 days in B2B, terms longer than 30 days impact liquidity.",
        "recommended_redline": "Invoices shall be settled within 14 calendar days of receipt.",
        "statute_ref": "§271a BGB",
        "example_risky_wording": None
    },
    {
        "id": "PB-003",
        "clause_type": "scheinselbstständigkeit",
        "risk_level": "high",
        "pattern_description": "Clause requires freelancer to follow daily instructions or work at fixed times.",
        "legal_reasoning": "Subjecting a freelancer to instructions is a primary indicator of disguised employment under §7 SGB IV, posing social security risks.",
        "recommended_redline": "Der Auftragnehmer ist in der Ausgestaltung seiner Tätigkeit frei und unterliegt keinen Weisungen des Auftraggebers.",
        "statute_ref": "§7 SGB IV",
        "example_risky_wording": None
    },
    {
        "id": "PB-004",
        "clause_type": "intellectual_property",
        "risk_level": "medium",
        "pattern_description": "Contract transfers Background IP or tools developed prior to the project.",
        "legal_reasoning": "Under UrhG, transferring pre-existing background IP without specific compensation is detrimental. Rights should be limited to project-specific foreground IP.",
        "recommended_redline": "The transfer of rights is limited to results created specifically under this agreement. Pre-existing tools and background IP remain the property of the freelancer.",
        "statute_ref": "§31 UrhG",
        "example_risky_wording": None
    },
    {
        "id": "PB-005",
        "clause_type": "liability",
        "risk_level": "high",
        "pattern_description": "Contract specifies unlimited liability for simple negligence.",
        "legal_reasoning": "Under German B2B standard terms (§307 BGB), unlimited liability for simple negligence is often invalid. Liability should be capped at contract value or insurance coverage.",
        "recommended_redline": "Die Haftung für einfache Fahrlässigkeit wird auf die Deckungssumme der Berufshaftpflichtversicherung des Auftragnehmers begrenzt.",
        "statute_ref": "§307 BGB",
        "example_risky_wording": None
    }
]

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
    print("Seeding Rates...")
    batch = db.batch()
    rates_ref = db.collection("rate_benchmarks")
    for rate in RATES:
        doc_ref = rates_ref.document()
        batch.set(doc_ref, rate)
    await batch.commit()
    print(f" -> Inserted {len(RATES)} rates.")

    print("Seeding Statutes...")
    batch = db.batch()
    statutes_ref = db.collection("statute_references")
    for stat in STATUTES:
        doc_ref = statutes_ref.document()
        batch.set(doc_ref, stat)
    await batch.commit()
    print(f" -> Inserted {len(STATUTES)} statutes.")

    print(f"Seeding Playbook (with embeddings from {EMBED_MODEL})...")
    for pb in PLAYBOOK:
        pb_id = pb.pop("id")
        blob = _compose_text(pb)
        try:
            resp = await client.embeddings.create(model=EMBED_MODEL, input=blob)
            vec = resp.data[0].embedding
            pb["embedding"] = Vector(vec)
            await db.collection("playbook").document(pb_id).set(pb)
            print(f"  [{pb_id}] embedded ({len(blob)} chars)")
        except Exception as e:
            print(f"  [{pb_id}] FAILED: {e}")

    print("Firestore Seeding Complete!")

if __name__ == "__main__":
    asyncio.run(main())
