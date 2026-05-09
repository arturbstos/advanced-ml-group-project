import pdfplumber
import os
from google.cloud import documentai
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List, Optional

from app.services.redaction import redact_text

# Define schema for extraction based on Technical Architecture Step 1
class ContractExtraction(BaseModel):
    skill_category: str
    region: Optional[str]
    experience_level: str
    hourly_rate_eur: float
    payment_terms_days: int
    clauses: List[str]

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

async def process_contract(file_path: str) -> ContractExtraction:
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

    system_prompt = """You are an expert legal AI assistant specialized in analyzing German freelancer contracts.
Your task is to extract structured data from the provided contract text according to the schema.

Strict Extraction Rules:
- clauses: Split the contract into individual clauses. Extract all clause-level provisions VERBATIM (do not paraphrase). There should be one meaningful legal provision per item in the list. This is critical for downstream vector search.
- hourly_rate_eur: Extract the hourly rate and return it as a float in EUR.
- experience_level: Normalize the freelancer's experience level to exactly one of the following: "junior", "mid", or "senior".
- region: Infer the region from city or state mentions. If no region can be inferred, leave it null.
- skill_category: Extract the primary skill category of the freelancer.
- payment_terms_days: Extract the payment terms (in days) as an integer.
"""

    # 2. Structured Extraction (using GPT-4o-mini for cost-efficiency)
    # per architecture recommendation [cite: 262]
    response = await _parse_with_retry(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please extract the contract terms from the following text. IMPORTANT: You must extract all clause-level provisions VERBATIM (not paraphrased) so that downstream vector search over the playbook works correctly.\n\n{text}"}
        ],
        response_format=ContractExtraction,
    )
    return response.choices[0].message.parsed
