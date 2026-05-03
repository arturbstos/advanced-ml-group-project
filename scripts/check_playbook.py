"""Integrity gate for the curated playbook.

This is the script that turns the "we treat the playbook as legal data,
not seed text" claim into something machine-verifiable. It runs in CI on
every push and PR, and locally before commits, asserting that every row
in db/seed_playbook.sql carries the metadata the analyzer (and any human
reviewer) needs to trust it.

It deliberately does NOT require a running database. The source of truth
for the playbook is the SQL file; if a row in the file is broken, CI must
fail before the file is ever loaded into Postgres. A separate --check-db
mode is provided for local use to verify the live DB matches the file.

Static checks (run by default, no dependencies):
  - Every PB-XXX row has exactly 10 column values.
  - statute_ref and source_url are non-empty.
  - source_type is one of {statute, case, agency, template, custom}.
  - risk_level is one of {high, medium, low}.
  - clause_type is within the locked taxonomy (CANONICAL_CLAUSE_TYPES).
  - PB-XXX ids are unique.
  - Total entry count is within the configured floor/ceiling.

Optional DB checks (--check-db, requires DATABASE_URL in env):
  - Row count in playbook table matches the file.
  - Every row that has an embedding has the expected 1536-dim vector.
  - source_url and source_type columns exist (catches schema drift).

Usage:
    python scripts/check_playbook.py             # static checks only
    python scripts/check_playbook.py --check-db  # also check live DB

Exit codes:
    0  all checks passed
    1  one or more violations
    2  unexpected error (file missing, parse failure, etc.)
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

# ---------------------------------------------------------------------------
# Configuration — the locked taxonomy.
# Editing this set is the explicit way to grow or rename categories. A typo
# in the seed file (e.g. "agb_kontrole") will fail the check rather than
# silently create a singleton orphan category that the analyzer never finds
# matches for.
# ---------------------------------------------------------------------------
CANONICAL_CLAUSE_TYPES = frozenset({
    "compensation_rate",
    "payment_terms",
    "late_payment_interest",
    "intellectual_property",
    "scheinselbstständigkeit",  # German spelling intentional — must match statute_references
    "termination",
    "liability",
    "agb_kontrolle",
    "confidentiality",
    "non_compete",
    "acceptance_werkvertrag",
    "warranty_maengel",
    "data_protection",
    "working_time",
    "dispute_resolution",
    "force_majeure",
})

VALID_RISK_LEVELS = frozenset({"high", "medium", "low"})
VALID_SOURCE_TYPES = frozenset({"statute", "case", "agency", "template", "custom"})

EXPECTED_FIELDS = 10  # id, clause_type, risk_level, pattern_description,
                     # example_risky_wording, legal_reasoning, recommended_redline,
                     # statute_ref, source_url, source_type
MIN_ENTRIES = 60     # bump these together with the corpus
MAX_ENTRIES = 200    # generous ceiling — guard against accidental data dumps

EMBEDDING_DIM = 1536  # text-embedding-3-small

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = REPO_ROOT / "db" / "seed_playbook.sql"


# ---------------------------------------------------------------------------
# Dollar-quote-aware SQL tokenizer.
# Postgres allows $$...$$ string literals that can span multiple lines and
# contain unescaped single quotes — which is exactly why we use them in
# seed_playbook.sql for the long German legal-reasoning blocks. This walker
# respects:
#   - line comments  -- ... \n   (stripped before tokenizing)
#   - single quotes  '...'        (with '' as escaped quote)
#   - dollar quotes  $$...$$
#   - paren depth    so internal commas don't split fields
# It is intentionally hand-written rather than depending on a third-party
# parser, so this script has zero pip dependencies and runs anywhere Python
# 3.9+ does.
# ---------------------------------------------------------------------------

def _strip_line_comments(src: str) -> str:
    """Remove `--` line comments. Cheap and safe for our seed file because
    every `--` outside a string is a comment (we don't construct decrement
    operators in SQL)."""
    return re.sub(r"(?m)^\s*--.*$", "", src)


def _extract_values_block(src: str) -> str:
    """Slice out everything between the INSERT ... VALUES and ON CONFLICT (id)."""
    try:
        v_start = src.index("VALUES")
        v_end = src.index("ON CONFLICT (id)")
    except ValueError as e:
        raise RuntimeError(
            "Could not locate `VALUES` and `ON CONFLICT (id)` markers in "
            f"{SEED_FILE.name} — file structure may have changed."
        ) from e
    return src[v_start + len("VALUES"):v_end]


def _tokenize_tuples(values_block: str) -> List[str]:
    """Walk the VALUES block and return one string per top-level (...) tuple."""
    tuples: List[str] = []
    buf: List[str] = []
    depth = 0
    in_squote = False
    in_dquote = False  # dollar-quoted
    i, n = 0, len(values_block)
    while i < n:
        c = values_block[i]
        # Inside $$...$$
        if in_dquote:
            if c == "$" and values_block[i:i + 2] == "$$":
                buf.append("$$")
                in_dquote = False
                i += 2
                continue
            buf.append(c)
            i += 1
            continue
        # Inside '...'
        if in_squote:
            if c == "'":
                # SQL escapes a quote by doubling it: 'it''s'
                if i + 1 < n and values_block[i + 1] == "'":
                    buf.append("''")
                    i += 2
                    continue
                in_squote = False
                buf.append(c)
                i += 1
                continue
            buf.append(c)
            i += 1
            continue
        # Not in any string: check for openers
        if c == "$" and values_block[i:i + 2] == "$$":
            buf.append("$$")
            in_dquote = True
            i += 2
            continue
        if c == "'":
            in_squote = True
            buf.append(c)
            i += 1
            continue
        if c == "(":
            if depth == 0:
                buf = ["("]
            else:
                buf.append(c)
            depth += 1
            i += 1
            continue
        if c == ")":
            depth -= 1
            buf.append(c)
            if depth == 0:
                tuples.append("".join(buf))
                buf = []
            i += 1
            continue
        if depth > 0:
            buf.append(c)
        i += 1
    return tuples


def _split_fields(tup: str) -> List[str]:
    """Split a `(...)` tuple's contents on top-level commas."""
    inner = tup[1:-1]  # drop the outer parens
    fields: List[str] = []
    cur: List[str] = []
    depth = 0
    in_s = False
    in_d = False
    j = 0
    while j < len(inner):
        c = inner[j]
        if in_d:
            if c == "$" and inner[j:j + 2] == "$$":
                cur.append("$$")
                in_d = False
                j += 2
                continue
            cur.append(c)
            j += 1
            continue
        if in_s:
            if c == "'":
                if j + 1 < len(inner) and inner[j + 1] == "'":
                    cur.append("''")
                    j += 2
                    continue
                in_s = False
                cur.append(c)
                j += 1
                continue
            cur.append(c)
            j += 1
            continue
        if c == "$" and inner[j:j + 2] == "$$":
            cur.append("$$")
            in_d = True
            j += 2
            continue
        if c == "'":
            in_s = True
            cur.append(c)
            j += 1
            continue
        if c == "(":
            depth += 1
            cur.append(c)
            j += 1
            continue
        if c == ")":
            depth -= 1
            cur.append(c)
            j += 1
            continue
        if c == "," and depth == 0:
            fields.append("".join(cur).strip())
            cur = []
            j += 1
            continue
        cur.append(c)
        j += 1
    if cur:
        fields.append("".join(cur).strip())
    return fields


# ---------------------------------------------------------------------------
# Field unwrapping
# ---------------------------------------------------------------------------

def _unwrap_literal(field: str) -> Optional[str]:
    """Return the string content of an SQL literal, or None for NULL.

    Handles 'foo', 'foo''bar' (escaped quote), and $$foo$$.
    Anything that doesn't look like one of those is returned as-is so the
    caller can decide whether it's an error.
    """
    f = field.strip()
    if f == "NULL":
        return None
    if f.startswith("$$") and f.endswith("$$"):
        return f[2:-2]
    if f.startswith("'") and f.endswith("'"):
        return f[1:-1].replace("''", "'")
    return f  # unrecognized — caller flags it


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

@dataclass
class Violation:
    pb_id: str
    rule: str
    detail: str

    def __str__(self) -> str:
        return f"  [{self.pb_id}] {self.rule}: {self.detail}"


def validate_file(path: Path) -> Tuple[List[Violation], dict]:
    """Run all static checks against `path`. Returns (violations, stats)."""
    if not path.exists():
        raise RuntimeError(f"Seed file not found: {path}")

    src = _strip_line_comments(path.read_text(encoding="utf-8"))
    values = _extract_values_block(src)
    tuples = _tokenize_tuples(values)

    violations: List[Violation] = []
    seen_ids: Counter = Counter()
    by_clause_type: Counter = Counter()
    by_risk: Counter = Counter()
    by_source_type: Counter = Counter()

    for raw_tup in tuples:
        fields = _split_fields(raw_tup)
        if not fields:
            violations.append(Violation("?", "empty_tuple", "no fields parsed"))
            continue

        # Field 0 is the id — pull it before length-checking so we can attach
        # the id to subsequent violations.
        pb_id = _unwrap_literal(fields[0]) or "?"

        if len(fields) != EXPECTED_FIELDS:
            violations.append(Violation(
                pb_id,
                "field_count",
                f"expected {EXPECTED_FIELDS} fields, got {len(fields)}",
            ))
            continue

        seen_ids[pb_id] += 1

        clause_type = _unwrap_literal(fields[1])
        risk_level = _unwrap_literal(fields[2])
        # 3 pattern_description, 4 example_risky_wording, 5 legal_reasoning,
        # 6 recommended_redline — content checks could be added here later
        # (e.g. minimum length); intentionally not enforced today.
        statute_ref = _unwrap_literal(fields[7])
        source_url = _unwrap_literal(fields[8])
        source_type = _unwrap_literal(fields[9])

        if not pb_id or not pb_id.startswith("PB-"):
            violations.append(Violation(pb_id, "bad_id", f"id must match PB-### form, got {pb_id!r}"))

        if clause_type is None or clause_type not in CANONICAL_CLAUSE_TYPES:
            violations.append(Violation(
                pb_id,
                "clause_type_taxonomy",
                f"{clause_type!r} not in CANONICAL_CLAUSE_TYPES",
            ))
        else:
            by_clause_type[clause_type] += 1

        if risk_level not in VALID_RISK_LEVELS:
            violations.append(Violation(pb_id, "risk_level", f"{risk_level!r} not in {sorted(VALID_RISK_LEVELS)}"))
        else:
            by_risk[risk_level] += 1

        if not statute_ref:
            violations.append(Violation(pb_id, "statute_ref_empty", "statute_ref is NULL or empty"))

        if not source_url:
            violations.append(Violation(pb_id, "source_url_empty", "source_url is NULL or empty"))
        elif not (source_url.startswith("http://") or source_url.startswith("https://")):
            violations.append(Violation(pb_id, "source_url_format", f"source_url should be a URL, got {source_url!r}"))

        if source_type not in VALID_SOURCE_TYPES:
            violations.append(Violation(
                pb_id,
                "source_type",
                f"{source_type!r} not in {sorted(VALID_SOURCE_TYPES)}",
            ))
        else:
            by_source_type[source_type] += 1

    # Duplicate-id check
    for pb_id, n in seen_ids.items():
        if n > 1:
            violations.append(Violation(pb_id, "duplicate_id", f"appears {n} times"))

    # Entry-count band
    total = len(tuples)
    if total < MIN_ENTRIES:
        violations.append(Violation(
            "*", "min_entries",
            f"got {total} entries, need at least {MIN_ENTRIES}",
        ))
    if total > MAX_ENTRIES:
        violations.append(Violation(
            "*", "max_entries",
            f"got {total} entries, ceiling is {MAX_ENTRIES} (raise if intentional)",
        ))

    stats = {
        "total": total,
        "by_clause_type": dict(by_clause_type),
        "by_risk_level": dict(by_risk),
        "by_source_type": dict(by_source_type),
    }
    return violations, stats


# ---------------------------------------------------------------------------
# Optional live DB checks (only run with --check-db)
# ---------------------------------------------------------------------------

def _check_db(expected_ids: List[str]) -> List[Violation]:
    """Verify the live DB matches the file. Lazy-imports SQLAlchemy so the
    static check has no third-party dependencies at all."""
    try:
        from sqlalchemy import create_engine, inspect, text
    except ImportError:
        return [Violation("*", "db_dependency", "sqlalchemy not installed; pip install sqlalchemy psycopg2-binary")]

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return [Violation("*", "db_config", "DATABASE_URL not set in environment")]

    # Convert async URL (postgresql+asyncpg://) to sync (postgresql://) so we
    # don't pull in asyncpg for a one-shot check.
    if "+asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")

    violations: List[Violation] = []
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Schema sanity: required columns exist
            cols = {c["name"] for c in inspect(engine).get_columns("playbook")}
            for required in ("source_url", "source_type", "embedding"):
                if required not in cols:
                    violations.append(Violation("*", "schema", f"playbook table missing column {required!r}"))

            # Row count matches the file
            db_count = conn.execute(text("SELECT COUNT(*) FROM playbook")).scalar_one()
            file_count = len(expected_ids)
            if db_count != file_count:
                violations.append(Violation(
                    "*", "row_count_drift",
                    f"DB has {db_count} rows, file has {file_count} — re-run seed_playbook.sql",
                ))

            # Embeddings, if present, must be the right size
            bad_dim = conn.execute(text(
                "SELECT id FROM playbook "
                "WHERE embedding IS NOT NULL "
                "  AND vector_dims(embedding) != :dim"
            ), {"dim": EMBEDDING_DIM}).all()
            for (pb_id,) in bad_dim:
                violations.append(Violation(pb_id, "embedding_dim", f"vector dim != {EMBEDDING_DIM}"))

            # IDs in DB that aren't in file (or vice versa)
            db_ids = {row[0] for row in conn.execute(text("SELECT id FROM playbook")).all()}
            file_ids = set(expected_ids)
            for pb_id in sorted(db_ids - file_ids):
                violations.append(Violation(pb_id, "ghost_in_db", "in DB but not in seed file"))
            for pb_id in sorted(file_ids - db_ids):
                violations.append(Violation(pb_id, "missing_in_db", "in seed file but not in DB"))
    except Exception as e:  # noqa: BLE001 - we want any failure surfaced
        violations.append(Violation("*", "db_error", str(e)))

    return violations


# ---------------------------------------------------------------------------
# Pretty printing
# ---------------------------------------------------------------------------

def _print_stats(stats: dict) -> None:
    print(f"Total entries:    {stats['total']}")
    print(f"By risk level:    {dict(sorted(stats['by_risk_level'].items()))}")
    print(f"By source type:   {dict(sorted(stats['by_source_type'].items()))}")
    print("By clause type:")
    for ct, n in sorted(stats["by_clause_type"].items()):
        print(f"  {n:>2}  {ct}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Integrity gate for db/seed_playbook.sql.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Returns exit 0 on pass, 1 on integrity violation, 2 on parse error.",
    )
    parser.add_argument(
        "--check-db",
        action="store_true",
        help="Also verify the live DB matches the file (needs DATABASE_URL).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print on failure (CI-friendly).",
    )
    args = parser.parse_args()

    try:
        violations, stats = validate_file(SEED_FILE)
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    if args.check_db:
        # Build the id list from the file for cross-checking
        # (re-parse cheaply rather than threading state)
        src = _strip_line_comments(SEED_FILE.read_text(encoding="utf-8"))
        tuples = _tokenize_tuples(_extract_values_block(src))
        expected_ids = []
        for t in tuples:
            f = _split_fields(t)
            if f:
                pid = _unwrap_literal(f[0])
                if pid:
                    expected_ids.append(pid)
        violations.extend(_check_db(expected_ids))

    if violations:
        print(f"\nFAIL: {len(violations)} integrity violation(s) in {SEED_FILE.name}\n")
        for v in violations:
            print(v)
        print()
        if not args.quiet:
            _print_stats(stats)
        return 1

    if not args.quiet:
        _print_stats(stats)
    print(f"\nOK: {SEED_FILE.name} passes all integrity checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
