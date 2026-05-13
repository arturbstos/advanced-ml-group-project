"""Clause-by-clause risk analysis — the orchestration brain.

For each extracted clause this module:
  1. Runs vector search over the playbook (Layer 2)
  2. Pulls matching statute references (Layer 1)
  3. Attaches rate-benchmark context (Layer 1) when the clause concerns
     compensation
  4. Asks an LLM to synthesize a single Finding (risk level, plain-
     language body, suggested redline, statute citation)

It also surfaces a synthetic "rate below benchmark" finding when the
offered rate falls beneath the p25 benchmark — even if the contract
text does not explicitly flag it.
"""
import asyncio
import os
import re
from typing import List, Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from app.services.ingestion import ContractExtraction
from db import playbook_lookup, rate_lookup, statute_lookup

_LLM_MODEL = "gpt-4o"
_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(wait=wait_exponential(min=1, max=4), stop=stop_after_attempt(3), reraise=True)
async def _parse_with_retry(**kwargs):
    return await _client.beta.chat.completions.parse(**kwargs)

_RATE_KEYWORDS = (
    "vergütung", "honorar", "stundensatz", "stundenhonorar", "euro",
    "€", "rate", "remunerat", "payment", "compensation",
)

# Language-keyed copy. "de"/"en" are coerced upstream so we can index safely.
_LANG_NAMES = {"de": "German", "en": "English"}
_LOW_RISK_TITLE = {"de": "Standardumfang", "en": "Within standard scope"}
_ANALYSIS_ERROR_TITLE = {"de": "Analysefehler", "en": "Analysis error"}
_ANALYSIS_ERROR_BODY = {
    "de": "Diese Klausel konnte nicht automatisch analysiert werden ({err}).",
    "en": "This clause could not be analyzed automatically ({err}).",
}

_RATE_FINDING_COPY = {
    "de": {
        "title": "Stundensatz unter dem 25 %-Perzentil-Benchmark",
        "body": (
            "Der angebotene Stundensatz von €{offered:.2f}/h liegt unter dem "
            "25 %-Perzentil-Benchmark von €{p25}/h für {skill} ({exp}, {region}). "
            "Der Marktmedian beträgt €{median}/h ({source})."
        ),
        "redline": "Der Auftragnehmer erhält ein Stundenhonorar von €{median:.0f} (netto).",
        "action": "Verhandle den Stundensatz mindestens auf das 25-%-Perzentil (€{p25}/h) hoch, idealerweise auf den Marktmedian (€{median}/h).",
    },
    "en": {
        "title": "Hourly rate below 25th-percentile benchmark",
        "body": (
            "The offered rate of €{offered:.2f}/h is below the 25th-percentile "
            "benchmark of €{p25}/h for {skill} ({exp}, {region}). Market median "
            "is €{median}/h ({source})."
        ),
        "redline": "Der Auftragnehmer erhält ein Stundenhonorar von €{median:.0f} (netto).",
        "action": "Negotiate the hourly rate up to at least the 25th-percentile benchmark (€{p25}/h), ideally to the market median (€{median}/h).",
    },
}


class Finding(BaseModel):
    risk: str = Field(description="One of 'high', 'medium', or 'low'.")
    title: str = Field(description="A short title summarising the issue, strictly in the requested target language.")
    clause: str = Field(description="The verbatim clause being analysed. Keep it in its ORIGINAL language (German or English). Do NOT translate or paraphrase the source clause.")
    body: str = Field(description="The legal reasoning, 2–3 sentences, strictly translated into the target language.")
    redline: Optional[str] = Field(default=None, description="A concrete replacement sentence, strictly in the target language, or null.")
    statute: Optional[str] = Field(default=None, description="Statute citation (e.g. '§ 7 SGB IV'). Statute references stay in their canonical German form.")
    action: Optional[str] = Field(default=None, description="A short, strategic recommendation in the target language describing WHAT to negotiate (e.g. 'Negotiate removal of fixed hours and replace with deliverables-based language'). One sentence. Distinct from the redline (which is the literal replacement text).")
    source: str = Field(description="Citation of the matched playbook entry (e.g. 'Playbook PB-001'), the benchmark, or 'Statutory default'.")


def _build_system_prompt(target_language: str) -> str:
    lang = _LANG_NAMES.get(target_language, "English")
    low_label = _LOW_RISK_TITLE.get(target_language, "Within standard scope")
    return f"""You are a contract-law expert specializing in European freelance contracts (German Freie Mitarbeit and equivalent English-law arrangements).

You will receive:
  1. A specific clause from a freelancer contract (may be in German or English).
  2. Up to 3 candidate playbook entries (patterns of known risky clauses, with legal reasoning and redlines).
  3. Optional statutory references (BGB, SGB IV, UrhG, etc.).
  4. Optional rate-benchmark context when the clause concerns compensation.

Output ONE Finding. Classify risk as follows:
  - "high"   — violates statute, causes material economic harm, or severely restricts the freelancer's rights (e.g. full IP transfer without fair compensation, unenforceable non-compete, liability cap below 3 months' fees).
  - "medium" — legally valid but suboptimal: reduces entitlements or leverage, departs from industry norms (e.g. payment terms >30 days, auto-renewal with long opt-out window, broad non-solicitation).
  - "low"    — genuinely within standard scope; no meaningful negotiation upside.

CRITICAL: You will receive legal context from our database that contains BOTH English and German text.
You MUST translate and synthesize your entire response — including the "title", "body" (legal reasoning),
and "redline" — STRICTLY into {lang}. Do NOT mix languages in the JSON output. The user has requested the
output in {lang}.

Rules:
  - Use playbook candidates as supporting context, but rely on your own legal expertise to assess risk.
  - "high" and "medium" require a SPECIFIC, ARTICULABLE legal concern that materially disadvantages the freelancer. Do not flag a clause merely because it could theoretically be improved.
  - Return risk="low", title="{low_label}" for clauses that are genuinely standard boilerplate with no meaningful negotiation upside. Examples that are almost always low: standard severability, mutual non-disparagement, symmetric waiver language, boilerplate force majeure, standard entire-agreement recitals, and symmetric notice-delivery requirements.
  - ANTI-HALLUCINATION: The "clause" field MUST be copied verbatim from the CLAUSE text provided in this message. Do NOT invent, recall from memory, translate, or paraphrase the source text. If in doubt, use the first 200 characters of the provided CLAUSE exactly as given.
  - The "body" must be 2–3 sentences in {lang}, citing the statute or benchmark source where applicable.
  - "redline" must be a concrete replacement sentence in {lang}, or null. Statute references inside it (e.g. "§ 7 SGB IV") stay in canonical German form.
  - "action" must be ONE sentence in {lang} describing the strategic move the freelancer should make in negotiation. Distinct from the redline. For risk="low" findings, return null.
  - "source" must cite either the matched playbook entry (e.g. "Playbook PB-001"), the benchmark (e.g. "Freelancer-Kompass 2025"), or "Statutory default".
"""


async def _analyze_single_clause(
    clause: str,
    playbook_matches: List[playbook_lookup.PlaybookMatch],
    statutes: List[statute_lookup.StatuteRef],
    rate_context: Optional[str],
    target_language: str,
) -> Finding:
    pb_context = "\n".join(
        f"[{m.id}] {m.clause_type} (risk={m.risk_level}, similarity={m.similarity:.2f})\n"
        f"  Pattern: {m.pattern_description}\n"
        f"  Reasoning: {m.legal_reasoning}\n"
        f"  Suggested redline: {m.recommended_redline or '—'}\n"
        f"  Statute: {m.statute_ref or '—'}"
        for m in playbook_matches
    ) or "(no playbook matches above similarity floor)"

    stat_context = "\n".join(
        f"{s.paragraph}: {s.text_excerpt}" for s in statutes
    ) or "(none)"

    user_msg = (
        f"CLAUSE:\n{clause}\n\n"
        f"PLAYBOOK CANDIDATES:\n{pb_context}\n\n"
        f"STATUTE REFERENCES:\n{stat_context}\n\n"
        f"RATE CONTEXT:\n{rate_context or '(not applicable)'}\n\n"
        f"REMINDER: synthesize the title, body and redline strictly in "
        f"{_LANG_NAMES.get(target_language, 'English')} only."
    )

    resp = await _parse_with_retry(
        model=_LLM_MODEL,
        messages=[
            {"role": "system", "content": _build_system_prompt(target_language)},
            {"role": "user", "content": user_msg},
        ],
        response_format=Finding,
    )
    return resp.choices[0].message.parsed


def _build_rate_context(
    extraction: ContractExtraction,
    bench: Optional[rate_lookup.RateBenchmark],
) -> Optional[str]:
    if bench is None:
        return None
    offered = extraction.hourly_rate_eur
    pct_vs_median = (offered / bench.median - 1) * 100 if bench.median else 0.0
    return (
        f"Offered rate: €{offered:.2f}/h. "
        f"Benchmark for {bench.skill_category} / {bench.experience} "
        f"({bench.region or 'Germany'}, {bench.source_year}): "
        f"p25=€{bench.p25}, median=€{bench.median}, p75=€{bench.p75} "
        f"({bench.source}). Offered is {pct_vs_median:+.0f}% vs median."
    )


def _clause_concerns_rate(clause: str) -> bool:
    low = clause.lower()
    return any(kw in low for kw in _RATE_KEYWORDS)


_RISK_ORDER = {"high": 0, "medium": 1, "low": 2}
_STOP_WORDS = {"the", "a", "an", "of", "for", "in", "and", "or", "to", "is", "are",
               "that", "this", "by", "on", "at", "with", "from", "as", "its", "any"}


def _section_of(f: Finding) -> Optional[str]:
    """Return the top-level section number from the clause text (e.g. '2' for '2.3 ...')."""
    m = re.match(r"^(\d{1,2})\.\d{1,2}", f.clause.strip())
    return m.group(1) if m else None


def _title_words(f: Finding) -> set:
    return {w.lower() for w in re.findall(r"[a-zA-Z]+", f.title) if w.lower() not in _STOP_WORDS}


def _are_duplicates(a: Finding, b: Finding) -> bool:
    """True if two findings address the same legal issue in the same contract section."""
    sec_a, sec_b = _section_of(a), _section_of(b)
    if sec_a is None or sec_b is None or sec_a != sec_b:
        return False
    # Same non-null statute in the same section → same issue
    if a.statute and b.statute and a.statute.strip() == b.statute.strip():
        return True
    # High title-word overlap in the same section → same issue
    wa, wb = _title_words(a), _title_words(b)
    if wa and wb and len(wa & wb) / min(len(wa), len(wb)) >= 0.55:
        return True
    return False


def _deduplicate(findings: List[Finding]) -> List[Finding]:
    """Keep only the highest-severity finding per unique legal issue per section."""
    sorted_f = sorted(findings, key=lambda f: _RISK_ORDER.get(f.risk, 2))
    kept: List[Finding] = []
    for f in sorted_f:
        if not any(_are_duplicates(f, k) for k in kept):
            kept.append(f)

    def _sort_key(f: Finding) -> tuple:
        m = re.match(r"^(\d{1,2})\.(\d{1,2})", f.clause.strip())
        return (int(m.group(1)), int(m.group(2))) if m else (999, 999)

    kept.sort(key=_sort_key)
    return kept


async def analyze(
    extraction: ContractExtraction,
    clauses: List[str],
    target_language: str = "de",
) -> tuple[List[Finding], Optional[rate_lookup.RateBenchmark]]:
    """Run the full clause analysis over an extracted contract.

    `clauses` is the list of verbatim chunks produced by
    `ingestion.chunk_contract_text` — analysis embeds and reasons over
    these exact strings, not LLM-paraphrased copies.

    `target_language` ("de" or "en") controls the synthesis language of
    every Finding's title / body / redline. Statute citations stay in
    canonical German form regardless.
    """
    findings: List[Finding] = []
    lang = "en" if target_language == "en" else "de"

    # 1. Rate benchmark — looked up once, reused across rate-related clauses.
    rate_bench = await rate_lookup.lookup(
        skill_category=extraction.skill_category,
        experience=extraction.experience_level,
        region=extraction.region,
    )

    # 2. Synthetic "rate below p25" finding — skip if rate is 0 (not stated in contract)
    if rate_bench and extraction.hourly_rate_eur > 0 and extraction.hourly_rate_eur < float(rate_bench.p25):
        copy = _RATE_FINDING_COPY[lang]
        findings.append(
            Finding(
                risk="high",
                title=copy["title"],
                clause=f"Stundenhonorar: €{extraction.hourly_rate_eur:.2f}/h",
                body=copy["body"].format(
                    offered=extraction.hourly_rate_eur,
                    p25=rate_bench.p25,
                    skill=rate_bench.skill_category,
                    exp=rate_bench.experience,
                    region=rate_bench.region or ("Deutschland" if lang == "de" else "Germany"),
                    median=rate_bench.median,
                    source=rate_bench.source,
                ),
                redline=copy["redline"].format(median=float(rate_bench.median)),
                statute=None,
                action=copy["action"].format(
                    p25=rate_bench.p25,
                    median=int(rate_bench.median),
                ),
                source=f"{rate_bench.source} {rate_bench.source_year}",
            )
        )

    rate_context = _build_rate_context(extraction, rate_bench)

    # Phase A: all playbook vector searches concurrently.
    all_matches = await asyncio.gather(
        *[playbook_lookup.lookup(clause, top_k=3) for clause in clauses]
    )

    # Phase B: statute lookups — deduplicated across clauses.
    unique_clause_types = {
        matches[0].clause_type
        for matches in all_matches
        if matches
    }
    await asyncio.gather(
        *[statute_lookup.lookup(ct) for ct in unique_clause_types]
    )
    # Results are now in statute_lookup._cache; subsequent calls are free.

    # Phase C: all LLM analyses concurrently with pre-fetched data.
    async def _llm_safe(clause: str, matches: List[playbook_lookup.PlaybookMatch]) -> Finding:
        try:
            statutes = await statute_lookup.lookup(matches[0].clause_type) if matches else []
            clause_rate_ctx = rate_context if _clause_concerns_rate(clause) else None
            return await _analyze_single_clause(
                clause=clause,
                playbook_matches=matches,
                statutes=statutes,
                rate_context=clause_rate_ctx,
                target_language=lang,
            )
        except Exception as e:
            return Finding(
                risk="low",
                title=_ANALYSIS_ERROR_TITLE[lang],
                clause=clause,
                body=_ANALYSIS_ERROR_BODY[lang].format(err=type(e).__name__),
                redline=None,
                statute=None,
                source="System",
            )

    clause_findings = await asyncio.gather(
        *[_llm_safe(clause, matches) for clause, matches in zip(clauses, all_matches)]
    )
    findings.extend(clause_findings)

    findings = _deduplicate(findings)
    return findings, rate_bench
