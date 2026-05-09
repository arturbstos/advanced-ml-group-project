"""On-device PII redaction with Microsoft Presidio + spaCy German NER.

Strips PERSON / ORGANIZATION / LOCATION / IBAN tokens from contract text
BEFORE the text leaves the server (i.e. before any OpenAI / external call).
The goal is GDPR data-minimisation: the LLM sees clause structure and
non-identifying boilerplate, but never the freelancer's name, the client's
trade name, the registered office, or the bank account.

Engines are loaded lazily on first call (~1-2s) so app cold-start stays
fast. Subsequent calls reuse the cached engines.
"""
import asyncio
from typing import Optional, Tuple

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Entities we care about for German freelance contracts. Presidio's spaCy
# recognizer maps the de_core_news_sm NER labels (PER/LOC/ORG) to these
# canonical entity names. IBAN_CODE is detected by Presidio's built-in
# regex+checksum recognizer.
_REDACT_ENTITIES = ["PERSON", "ORGANIZATION", "LOCATION", "IBAN_CODE"]

_OPERATORS = {
    "PERSON":       OperatorConfig("replace", {"new_value": "[PERSON]"}),
    "ORGANIZATION": OperatorConfig("replace", {"new_value": "[ORGANIZATION]"}),
    "LOCATION":     OperatorConfig("replace", {"new_value": "[LOCATION]"}),
    "IBAN_CODE":    OperatorConfig("replace", {"new_value": "[IBAN]"}),
}

_analyzer: Optional[AnalyzerEngine] = None
_anonymizer: Optional[AnonymizerEngine] = None


def _build_engines() -> Tuple[AnalyzerEngine, AnonymizerEngine]:
    """Initialise Presidio with the German spaCy model. Called once."""
    nlp_config = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "de", "model_name": "de_core_news_sm"}],
    }
    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
    return (
        AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["de"]),
        AnonymizerEngine(),
    )


def _get_engines() -> Tuple[AnalyzerEngine, AnonymizerEngine]:
    global _analyzer, _anonymizer
    if _analyzer is None or _anonymizer is None:
        _analyzer, _anonymizer = _build_engines()
    return _analyzer, _anonymizer


def _redact_sync(text: str) -> str:
    analyzer, anonymizer = _get_engines()
    results = analyzer.analyze(
        text=text,
        language="de",
        entities=_REDACT_ENTITIES,
    )
    if not results:
        return text
    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATORS,
    )
    return anonymized.text


async def redact_text(text: str) -> str:
    """Mask PII (PERSON / ORGANIZATION / LOCATION / IBAN) in `text`.

    Presidio's analyzer/anonymizer are sync and CPU-bound, so we run them
    in a worker thread to avoid blocking the FastAPI event loop.
    """
    if not text or not text.strip():
        return text
    return await asyncio.to_thread(_redact_sync, text)
