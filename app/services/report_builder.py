"""Assemble the final analysis report for the UI.

Takes a list of Findings plus the ContractExtraction and returns the
structured JSON that the Streamlit UI expects: summary counts, the
findings themselves, and a negotiation brief.
"""
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.services.clause_analyzer import Finding
from app.services.ingestion import ContractExtraction
from db.rate_lookup import RateBenchmark


class RateBenchmarkSnapshot(BaseModel):
    offered: float
    p25: float
    median: float
    p75: float
    skill_category: str
    experience: str
    source: str


class AnalysisReport(BaseModel):
    profile: str
    date: str
    summary: Dict[str, int]
    findings: List[Finding]
    brief: str
    rate_benchmark: Optional[RateBenchmarkSnapshot] = None


_REDLINE_NOISE_CHARS = " \t\n\r—–-•·.…"
_CLAUSE_SNIPPET_MAX = 220


_BRIEF_LABELS = {
    "en": {
        "disclaimer":     "For informational purposes only. This analysis does not constitute legal advice.",
        "profile":        "Profile",
        "date":           "Date",
        "priority":       "Priority actions:",
        "no_priority":    "Priority actions: none identified.",
        "severity_high":  "high",
        "severity_med":   "medium",
        "original":       "Original",
        "redline":        "Suggested redline",
        "statute":        "Statute",
        "scope_one":      "Reviewed and within standard scope: 1 clause (no action needed).",
        "scope_many":     "Reviewed and within standard scope: {n} clauses (no action needed).",
    },
    "de": {
        "disclaimer":     "Nur zu Informationszwecken. Diese Analyse stellt keine Rechtsberatung dar.",
        "profile":        "Profil",
        "date":           "Datum",
        "priority":       "Prioritäre Maßnahmen:",
        "no_priority":    "Prioritäre Maßnahmen: keine identifiziert.",
        "severity_high":  "hoch",
        "severity_med":   "mittel",
        "original":       "Original",
        "redline":        "Vorgeschlagene Redline",
        "statute":        "Gesetz",
        "scope_one":      "Überprüft und im Standardumfang: 1 Klausel (kein Handlungsbedarf).",
        "scope_many":     "Überprüft und im Standardumfang: {n} Klauseln (kein Handlungsbedarf).",
    },
}


def _is_meaningful_redline(s: Optional[str]) -> bool:
    """Reject placeholder redlines like '—', '...', or whitespace-only."""
    if not s:
        return False
    return len(s.strip(_REDLINE_NOISE_CHARS)) > 5


def _clause_snippet(clause: Optional[str]) -> Optional[str]:
    if not clause:
        return None
    s = " ".join(clause.split())  # collapse whitespace for compact quoting
    if len(s) > _CLAUSE_SNIPPET_MAX:
        s = s[:_CLAUSE_SNIPPET_MAX].rstrip() + "…"
    return s


def _build_brief(profile: str, findings: List[Finding], target_language: str = "de") -> str:
    lang = "en" if target_language == "en" else "de"
    L = _BRIEF_LABELS[lang]

    priorities = [f for f in findings if f.risk in ("high", "medium")]
    acceptable = [f for f in findings if f.risk == "low"]

    lines: List[str] = [
        L["disclaimer"],
        "",
        f"{L['profile']}: {profile}",
        f"{L['date']}:    {date.today().isoformat()}",
        "",
    ]

    if priorities:
        lines.append(L["priority"])
        for i, f in enumerate(priorities, start=1):
            severity = L["severity_high"] if f.risk == "high" else L["severity_med"]
            entry = f"  {i}. {f.title} ({severity}). {f.body}"
            snippet = _clause_snippet(f.clause)
            if snippet:
                entry += f'\n     {L["original"]}: "{snippet}"'
            if _is_meaningful_redline(f.redline):
                entry += f"\n     {L['redline']}: {f.redline}"
            if f.statute:
                entry += f"\n     {L['statute']}: {f.statute}"
            lines.append(entry)
    else:
        lines.append(L["no_priority"])

    if acceptable:
        lines.append("")
        if len(acceptable) == 1:
            lines.append(L["scope_one"])
        else:
            lines.append(L["scope_many"].format(n=len(acceptable)))

    return "\n".join(lines)


def build(
    extraction: ContractExtraction,
    findings: List[Finding],
    rate_bench: Optional[RateBenchmark] = None,
    target_language: str = "de",
) -> AnalysisReport:
    """Assemble the UI-ready report."""
    lang = "en" if target_language == "en" else "de"

    summary = {
        "high": sum(1 for f in findings if f.risk == "high"),
        "medium": sum(1 for f in findings if f.risk == "medium"),
        "low": sum(1 for f in findings if f.risk == "low"),
        "total": len(findings),
    }

    region_fallback = "Deutschland (bundesweit)" if lang == "de" else "Germany (nationwide)"
    profile = (
        f"{extraction.experience_level.title()} {extraction.skill_category}"
        f" · {extraction.region or region_fallback}"
    )

    bench_snapshot = None
    if rate_bench and extraction.hourly_rate_eur >= 0:
        bench_snapshot = RateBenchmarkSnapshot(
            offered=extraction.hourly_rate_eur,
            p25=float(rate_bench.p25),
            median=float(rate_bench.median),
            p75=float(rate_bench.p75),
            skill_category=rate_bench.skill_category,
            experience=rate_bench.experience,
            source=rate_bench.source,
        )

    return AnalysisReport(
        profile=profile,
        date=date.today().isoformat(),
        summary=summary,
        findings=findings,
        brief=_build_brief(profile, findings, lang),
        rate_benchmark=bench_snapshot,
    )
