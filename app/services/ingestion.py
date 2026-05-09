import os
import re

import pdfplumber
from google.cloud import documentai
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional, Tuple

from app.services.redaction import redact_text

# Metadata-only schema. Clauses are split deterministically in Python
# (see chunk_contract_text) so the LLM never has the chance to subtly
# rewrite the legal text.
class ContractExtraction(BaseModel):
    skill_category: str
    region: Optional[str]
    experience_level: str
    hourly_rate_eur: float
    payment_terms_days: int


# Split before paragraph breaks OR § markers. The lookahead on § keeps
# the §-prefix attached to its section.
_CLAUSE_SPLIT = re.compile(r"\n\s*\n+|(?=§)")
_MIN_CHUNK_LEN = 50


def chunk_contract_text(text: str) -> List[str]:
    """Split contract text into clause-sized chunks deterministically.

    No LLM is involved — output is verbatim source text grouped into
    units large enough for meaningful embedding (>= 50 chars) but small
    enough to address individually. Fragments shorter than the floor
    are merged into the preceding chunk so we never embed
    "§ 1" or "Definitions." as a standalone vector.
    """
    if not text or not text.strip():
        return []

    raw = _CLAUSE_SPLIT.split(text.strip())

    chunks: List[str] = []
    for piece in raw:
        piece = piece.strip()
        if not piece:
            continue
        if chunks and len(piece) < _MIN_CHUNK_LEN:
            chunks[-1] = chunks[-1] + " " + piece
        else:
            chunks.append(piece)
    return chunks

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@retry(wait=wait_exponential(min=1, max=4), stop=stop_after_attempt(3), reraise=True)
async def _parse_with_retry(**kwargs):
    return await client.beta.chat.completions.parse(**kwargs)


async def extract_text_with_doc_ai(file_path: str) -> str:
    """OCR fallback for scanned PDFs using a generic Google Cloud
    Document AI processor. Reads PROJECT_ID / LOCATION / PROCESSOR_ID
    from the environment.
    """
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION")
    processor_id = os.getenv("PROCESSOR_ID")
    if not (project_id and location and processor_id):
        raise RuntimeError(
            "Document AI OCR fallback is not configured. Set PROJECT_ID, "
            "LOCATION, and PROCESSOR_ID in the environment."
        )

    # Document AI requires a region-specific endpoint (e.g. eu-documentai...)
    client_options = {"api_endpoint": f"{location}-documentai.googleapis.com"}
    docai_client = documentai.DocumentProcessorServiceAsyncClient(
        client_options=client_options
    )

    name = docai_client.processor_path(project_id, location, processor_id)

    with open(file_path, "rb") as f:
        content = f.read()

    request = documentai.ProcessRequest(
        name=name,
        raw_document=documentai.RawDocument(
            content=content,
            mime_type="application/pdf",
        ),
    )
    result = await docai_client.process_document(request=request)
    return result.document.text or ""

async def process_contract(file_path: str) -> Tuple[ContractExtraction, List[str]]:
    """Return (metadata, clauses).

    `metadata` is the LLM-extracted ContractExtraction (rates, region,
    skill category, etc). `clauses` is a list of verbatim text chunks
    produced by `chunk_contract_text` — the LLM does NOT touch these
    so legal text reaches the playbook vector search byte-for-byte.
    """
    # 1. Raw Text Extraction
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    text = text.strip()
    if not text:
        # pdfplumber returned nothing — most likely a scanned PDF. Fall back
        # to Google Cloud Document AI OCR before giving up on the user.
        try:
            text = (await extract_text_with_doc_ai(file_path)).strip()
        except Exception as e:
            raise ValueError(
                "Could not extract text from this PDF. The document appears "
                f"to be scanned and the OCR fallback failed: {type(e).__name__}: {e}"
            )
        if not text:
            raise ValueError(
                "OCR returned empty text — the PDF may be unreadable. "
                "Please upload a clearer scan or a digitally-created PDF."
            )

    # GDPR: strip PII (names, orgs, locations, IBANs) on-device before any
    # OpenAI call. Applies equally to OCR-derived text.
    text = await redact_text(text)

    # 2. Deterministic clause chunking — no LLM rewriting risk.
    clauses = chunk_contract_text(text)

    # 3. Metadata-only LLM extraction (no clauses field — chunks already exist).
    system_prompt = """You are an expert legal AI assistant specialized in analyzing German freelancer contracts.
Your task is to extract structured METADATA from the provided contract text according to the schema.

Strict Extraction Rules:
- hourly_rate_eur: Extract the hourly rate and return it as a float in EUR.
- experience_level: Normalize the freelancer's experience level to exactly one of: "junior", "mid", or "senior".
- region: Infer the region from city or state mentions. If no region can be inferred, leave it null.
- skill_category: Extract the primary skill category of the freelancer.
- payment_terms_days: Extract the payment terms (in days) as an integer.
"""

    response = await _parse_with_retry(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Extract the contract metadata from the following text:\n\n{text}"},
        ],
        response_format=ContractExtraction,
    )
    metadata: ContractExtraction = response.choices[0].message.parsed
    return metadata, clauses
