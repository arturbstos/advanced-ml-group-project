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


def _build_brief(profile: str, findings: List[Finding]) -> str:
    priorities = [f for f in findings if f.risk in ("high", "medium")]
    acceptable = [f for f in findings if f.risk == "low"]

    lines: List[str] = [f"Profile: {profile}", f"Date: {date.today().isoformat()}", ""]

    if priorities:
        lines.append("Priority actions:")
        for i, f in enumerate(priorities, start=1):
            severity = "high" if f.risk == "high" else "medium"
            entry = f"  {i}. {f.title} ({severity} priority). {f.body}"
            if f.redline:
                entry += f"\n     Suggested redline: {f.redline}"
            if f.statute:
                entry += f"\n     Statute: {f.statute}"
            lines.append(entry)
    else:
        lines.append("Priority actions: none identified.")

    if acceptable:
        lines.append("")
        lines.append("Within standard scope:")
        for f in acceptable:
            lines.append(f"  - {f.title}")

    lines.append("")
    lines.append("For informational purposes only. This analysis does not constitute legal advice.")
    return "\n".join(lines)


def build(extraction: ContractExtraction, findings: List[Finding], rate_bench: Optional[RateBenchmark] = None) -> AnalysisReport:
    """Assemble the UI-ready report."""
    summary = {
        "high": sum(1 for f in findings if f.risk == "high"),
        "medium": sum(1 for f in findings if f.risk == "medium"),
        "low": sum(1 for f in findings if f.risk == "low"),
        "total": len(findings),
    }

    profile = (
        f"{extraction.experience_level.title()} {extraction.skill_category}"
        f" · {extraction.region or 'Germany (nationwide)'}"
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
        brief=_build_brief(profile, findings),
        rate_benchmark=bench_snapshot,
    )
