# German Freelancer Contract Analyzer


## Setup Instructions

These instructions cover setting up the environment, PostgreSQL database, and Python services natively on your local machine (macOS/Linux).

### 1. Prerequisites & Database
The pipeline uses a local PostgreSQL database with the **pgvector** extension.

1. **Install PostgreSQL and pgvector via Homebrew** (macOS):
   ```bash
   brew install postgresql pgvector
   brew services start postgresql
   ```

2. **Provision the Database**:
   Create the database and the expected user in `psql`:
   ```sql
   CREATE USER postgres WITH PASSWORD 'password' SUPERUSER;
   CREATE DATABASE freelancer_analyzer OWNER postgres;
   ```
   *(Ensure these credentials match the `DATABASE_URL` in your `.env` file).*

3. **Load the Schema**:
   From the repository root, inject the tables and initial static data:
   ```bash
   psql -U postgres -d freelancer_analyzer -f db/init.sql
   ```

### 2. Environment & Dependencies

1. **Create Virtual Environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python Packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**:
   - Copy `.env.example` to a new `.env` file.
   - Insert your real `OPENAI_API_KEY` (must support `text-embedding-3-small` and `gpt-4o-mini`).

### 3. Seed Rate Benchmarks
The "rate below market" risk flag relies on hourly-rate percentiles in the `rate_benchmarks` table. Seed them from the Freelancer-Kompass 2025 report:

```bash
psql -U postgres -d freelancer_analyzer -f db/seed_rates.sql
```
*This inserts 24 rows (8 skill categories × 3 experience tiers). The script is idempotent — re-running it replaces only rows where `source = 'Freelancer-Kompass 2025'`. See **Methodology → Rate Benchmarks** below for how p25/p75 are derived from the report's published medians.*

### 4. Seed the Playbook Entries
The Layer 2 playbook contains the curated risky-clause patterns the analyzer matches contracts against. The current corpus is 66 entries spanning 16 clause categories (compensation, payment terms, late-payment interest, IP, Scheinselbstständigkeit, termination, liability, AGB-Kontrolle, confidentiality, non-compete, Werkvertrag-Abnahme, warranty, data protection, working time, dispute resolution, force majeure). Every entry carries a `statute_ref`, `source_url`, and `source_type` (statute / case / agency / template / custom) — the integrity gate expects all three to be non-empty.

```bash
psql -U postgres -d freelancer_analyzer -f db/seed_playbook.sql
```
*The script uses `ON CONFLICT (id) DO UPDATE`, so re-running propagates edits. The `embedding` column is reset to NULL only for rows whose semantic content actually changed, which means the next `seed_vectors.py` run re-embeds exactly the rows that need it.*

#### Integrity gate
The playbook is treated as legal data, not seed text. `scripts/check_playbook.py` is a static integrity check that runs in CI on every push and PR (`.github/workflows/playbook-integrity.yml`) and that you should run locally before committing changes to the seed file:

```bash
python scripts/check_playbook.py             # static checks (no DB required)
python scripts/check_playbook.py --check-db  # also verify the live DB matches
```

The gate asserts: every row has 10 fields, `statute_ref` and `source_url` are non-empty, `source_type` is in `{statute, case, agency, template, custom}`, `risk_level` is in `{high, medium, low}`, `clause_type` is within the locked taxonomy (any typo creates an orphan that the analyzer cannot match), `PB-XXX` ids are unique, and the entry count sits within the configured floor/ceiling. With `--check-db` it additionally verifies the `playbook` table has the expected schema, the row count matches the file, and any populated embeddings have the expected 1536 dimensions.

### 5. Seed the Playbook Vectors
The application compares contract clauses against the playbook via cosine similarity over OpenAI embeddings. You must generate the embeddings before the analyzer can match anything:

```bash
python scripts/seed_vectors.py
```
*Re-runs only embed rows where `embedding IS NULL`. Pass `--force` to re-embed every row. Cost: a few cents per full reseed.*

---

## Running the Application

The analyzer consists of a FastAPI backend and a Streamlit interactive frontend. They must be run simultaneously in **two separate terminal windows**.

### Window 1: Start the Backend server
The backend handles the PDF data extraction, LLM structuring, and vector comparison computations.
```bash
# Make sure your environment is activated
source .venv/bin/activate
uvicorn app.main:app --reload
```
*This server will run at `http://localhost:8000`.*

### Window 2: Start the Frontend UI
The Streamlit application presents the parsed data, contract risks, warnings, and suggested redlines interactively.
```bash
# Make sure your environment is activated
source .venv/bin/activate
streamlit run UX/UX.py
```
*This will open the user interface at `http://localhost:8501`.*

## Testing with Sample Data
A mock contract exists under `tests/samples/sample.pdf` that triggers simulated risk warnings for hourly rates, IP, Scheinselbstständigkeit, and payment terms. Simply drop it into the running Streamlit upload box to see the pipeline end to end!

---

## Methodology

The analyzer combines three knowledge layers (relational facts, embedded playbook, LLM synthesis). For the relational-facts layer the seed data is derived rather than copied verbatim from primary sources, so we document the derivation here.

### Rate Benchmarks (`db/seed_rates.sql`)

**Source.** *Freelancer-Kompass 2025*, freelancermap GmbH, Nuremberg — an annual survey of ~5,000 German freelancers. We use the field **"Stundensatz nach Fachgebiet"** (printed page 34), which reports a single median hourly rate per skill category in EUR/h.

**Skill-category translation.** The Kompass uses German labels; the canonical `skill_category` values stored in the database are English so the LLM extraction layer (which we prompt in English) can hit them directly:

| Kompass (DE)                          | Canonical (EN)                | Median (EUR/h) |
|---------------------------------------|-------------------------------|----------------|
| Beratung / Management                 | Consulting & Management       | 120            |
| SAP-Beratung / -Entwicklung           | SAP Consulting                | 117            |
| IT-Infrastruktur                      | IT Infrastructure             | 102            |
| Ingenieurwesen                        | Engineering                   |  95            |
| Softwareentwicklung                   | Software Development          |  94            |
| Marketing / Kommunikation             | Marketing & Communications    |  92            |
| Grafik / Content                      | Design & Content              |  82            |
| Sonstige Bereiche                     | Other                         | 100            |

**Free-text → canonical mapping.** Because GPT-4o-mini may emit any phrase ("Senior Java backend developer", "SAP ABAP-Berater", "Mechanical engineer"), `db/rate_lookup.py` ships a `_normalize_skill_category()` function that does case-insensitive substring matching against an order-sensitive keyword list (`_SKILL_KEYWORDS`). Order matters: SAP and IT-Infrastructure keywords are checked before generic engineering terms so, e.g., "DevOps engineer" lands in *IT Infrastructure* rather than *Software Development*. Unmatched inputs fall back to the `Other` bucket, which is itself seeded.

**Experience tier multiplier (±30 % on category median).**
* `junior  = median × 0.70`
* `mid     = median × 1.00`
* `senior  = median × 1.30`

This range is broadly consistent with experience-premium patterns reported by Eurostat's *Structure of Earnings* statistics for ISCO-08 occupation groups 21 (science & engineering professionals) and 25 (ICT professionals) in Germany — senior practitioners typically earn ~25–35 % above the occupational mean and juniors ~25–30 % below. We pick the round 30 % figure as a transparent compromise.

**Within-tier dispersion (±15 % around the tier point estimate).**
* `p25    = tier × 0.85`
* `median = tier × 1.00`
* `p75    = tier × 1.15`

Conservative relative to the GULP *Skills- und Stundensatzstudie* (which reports p25/p75 spreads of roughly ±20 % within a skill group). We deliberately err toward a tighter band so the "below p25" risk flag in `clause_analyzer` fires only on clearly under-priced contracts.

**Region.** All seeded rows have `region IS NULL` (nationwide). The Kompass does publish a federal-state split, but per-state sample sizes are too small to be robust. The lookup function in `db/rate_lookup.py` falls back to nationwide when no region match exists, so this is harmless.

### Playbook (`db/playbook` rows + `scripts/seed_vectors.py`)

The current 5-row seed in `db/init.sql` (PB-001 through PB-005) covers the highest-frequency clause families: late-payment interest, payment-term ceiling, IP transfer scope, working-time direction (Scheinselbstständigkeit), and termination notice. Each rule cites its German statutory anchor (BGB §§ 271a, 288, 305-310; UrhG §§ 31, 32; SGB IV § 7) and is rendered into a vector via `text-embedding-3-small` by `scripts/seed_vectors.py`. Expansion to 60–100 entries is tracked separately and not covered here.

### Deferred Enrichments

The following dimensions exist in the underlying sources but are intentionally **not** seeded — they would expand the schema without buying accuracy on the analyses we currently produce:

* Industry breakdowns (`Branche`)
* Education premium (`Bildung`)
* Service-type splits (`Leistung`)
* Year-over-year deltas (the 2024 → 2025 +5–7 % trend)
* Gender pay-gap dimension
