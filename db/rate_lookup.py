"""Rate benchmark lookup (Layer 1 — Relational Facts).

Returns hourly-rate percentiles (p25 / median / p75) for a given
skill_category + experience level, preferring region-specific data and
falling back to nationwide. Returns None if no benchmark exists.
"""
from typing import Optional
from pydantic import BaseModel
from google.cloud import firestore

_db: Optional[firestore.AsyncClient] = None

def _get_db() -> firestore.AsyncClient:
    global _db
    if _db is None:
        _db = firestore.AsyncClient(database="contractdb")
    return _db

_EXPERIENCE_LEVELS = ("junior", "mid", "senior")

CANONICAL_SKILL_CATEGORIES = (
    "Consulting & Management",
    "SAP Consulting",
    "IT Infrastructure",
    "Engineering",
    "Software Development",
    "Marketing & Communications",
    "Design & Content",
    "Other",
)

_SKILL_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("SAP Consulting", (
        "sap", "abap", "s/4hana", "s4hana", "fiori", "hana",
    )),
    ("IT Infrastructure", (
        "devops", "sre", "site reliability", "infrastructure", "infrastruktur",
        "cloud", "aws", "azure", "gcp", "kubernetes", "k8s", "docker",
        "network", "netzwerk", "system administrator", "sysadmin",
        "security", "sicherheit", "cybersecurity", "it-security",
        "datenbank", "database admin", "dba", "platform",
    )),
    ("Engineering", (  # non-software engineering — checked BEFORE Software Development
        "ingenieur", "mechanical", "maschinenbau", "elektrotechnik",
        "electrical engineer", "civil", "bauingenieur", "chemical",
        "verfahrenstechnik", "automotive", "automobil", "luft- und raumfahrt",
        "aerospace", "process engineer",
    )),
    ("Software Development", (
        "software", "developer", "entwickl", "programmier", "engineer",
        "frontend", "backend", "full stack", "fullstack", "full-stack",
        "java", "python", "javascript", "typescript", "react", "angular",
        "vue", "node", "rust", "golang", "go developer", ".net", "c#", "c++",
        "mobile", "ios", "android", "data engineer", "ml engineer",
        "machine learning", "data scientist", "ki-",
    )),
    ("Consulting & Management", (
        "consult", "berat", "manage", "projekt", "project manager", "pmo",
        "scrum", "agile coach", "product owner", "business analyst",
        "strategy", "strategie", "transformation", "change",
    )),
    ("Design & Content", (
        "design", "ux", "ui", "grafik", "graphic", "content", "redakteur",
        "redaktion", "copywriter", "texter", "video", "fotograf",
        "photograph", "illustrator",
    )),
    ("Marketing & Communications", (
        "marketing", "kommunikation", "communications", "pr ", "public relation",
        "social media", "seo", "sea", "performance", "brand", "campaign",
        "kampagne", "werbung", "advertising",
    )),
]

def _normalize_skill_category(raw: Optional[str]) -> str:
    if not raw:
        return "Other"

    for canonical in CANONICAL_SKILL_CATEGORIES:
        if raw.strip().lower() == canonical.lower():
            return canonical

    r = raw.lower()
    for canonical, keywords in _SKILL_KEYWORDS:
        if any(kw in r for kw in keywords):
            return canonical
    return "Other"

class RateBenchmark(BaseModel):
    skill_category: str
    region: Optional[str]
    experience: str
    p25: float
    median: float
    p75: float
    source: str
    source_year: int

def _normalize_experience(raw: str) -> Optional[str]:
    if not raw:
        return None
    r = raw.strip().lower()
    if r in _EXPERIENCE_LEVELS:
        return r
    if r in ("entry", "entry-level", "entry level", "beginner"):
        return "junior"
    if r in ("intermediate", "middle", "mid-level", "mid level"):
        return "mid"
    if r in ("expert", "lead", "principal", "staff"):
        return "senior"
    return None

async def lookup(
    skill_category: str,
    experience: str,
    region: Optional[str] = None,
    **kwargs
) -> Optional[RateBenchmark]:
    exp = _normalize_experience(experience)
    if exp is None:
        return None

    canonical_skill = _normalize_skill_category(skill_category)
    rates_ref = _get_db().collection("rate_benchmarks")

    if region:
        query = rates_ref.where(
            filter=firestore.FieldFilter("skill_category", "==", canonical_skill)
        ).where(
            filter=firestore.FieldFilter("experience", "==", exp)
        ).where(
            filter=firestore.FieldFilter("region", "==", region)
        ).limit(1)
        
        async for doc in query.stream():
            d = doc.to_dict()
            return RateBenchmark(**d)

    query = rates_ref.where(
        filter=firestore.FieldFilter("skill_category", "==", canonical_skill)
    ).where(
        filter=firestore.FieldFilter("experience", "==", exp)
    ).where(
        filter=firestore.FieldFilter("region", "==", None)
    ).limit(1)

    async for doc in query.stream():
        d = doc.to_dict()
        return RateBenchmark(**d)

    return None
