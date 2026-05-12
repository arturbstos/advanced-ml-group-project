"""On-device PII redaction with Microsoft Presidio + spaCy NER.

Strips PERSON / ORGANIZATION / LOCATION / IBAN tokens from contract text
BEFORE the text leaves the server (i.e. before any OpenAI / external call).
The goal is GDPR data-minimisation: the LLM sees clause structure and
non-identifying boilerplate, but never the freelancer's name, the client's
trade name, the registered office, or the bank account.

Supports German (de_core_news_sm) and English (en_core_web_sm). Language
is auto-detected via langdetect so English contracts are not mangled by
the German NER model. Engines are loaded lazily on first call (~1-2s).
"""
import asyncio
from typing import Dict, Optional

from langdetect import detect as _langdetect_detect, LangDetectException
from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# en_core_web_sm over-triggers ORGANIZATION on capitalized contract terms
# (e.g. "VAT", "Cap", "Liability", "Client") — so for English we only
# redact personal names and IBANs. German NER is well-calibrated for ORG.
_REDACT_ENTITIES_BY_LANG = {
    "de": ["PERSON", "ORGANIZATION", "IBAN_CODE"],
    "en": ["PERSON", "IBAN_CODE"],
}

_OPERATORS = {
    "PERSON":       OperatorConfig("replace", {"new_value": "[PERSON]"}),
    "ORGANIZATION": OperatorConfig("replace", {"new_value": "[ORGANIZATION]"}),
    "IBAN_CODE":    OperatorConfig("replace", {"new_value": "[IBAN]"}),
}

_SUPPORTED_LANGS = {
    "de": "de_core_news_sm",
    "en": "en_core_web_sm",
}

_analyzers: Dict[str, AnalyzerEngine] = {}
_anonymizer: Optional[AnonymizerEngine] = None


def _get_analyzer(lang: str) -> AnalyzerEngine:
    if lang not in _analyzers:
        model_name = _SUPPORTED_LANGS[lang]
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": lang, "model_name": model_name}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
        _analyzers[lang] = AnalyzerEngine(
            nlp_engine=nlp_engine, supported_languages=[lang]
        )
    return _analyzers[lang]


def _get_anonymizer() -> AnonymizerEngine:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = AnonymizerEngine()
    return _anonymizer


def _detect_lang(text: str) -> str:
    """Return 'de' or 'en'. Falls back to 'de' on detection failure."""
    try:
        detected = _langdetect_detect(text[:2000])
        return detected if detected in _SUPPORTED_LANGS else "de"
    except LangDetectException:
        return "de"


def _redact_sync(text: str) -> str:
    lang = _detect_lang(text)
    analyzer = _get_analyzer(lang)
    anonymizer = _get_anonymizer()
    entities = _REDACT_ENTITIES_BY_LANG[lang]
    results = analyzer.analyze(text=text, language=lang, entities=entities)
    if not results:
        return text
    return anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators=_OPERATORS,
    ).text


async def redact_text(text: str) -> str:
    """Mask PII (PERSON / ORGANIZATION / LOCATION / IBAN) in `text`.

    Presidio's analyzer/anonymizer are sync and CPU-bound, so we run them
    in a worker thread to avoid blocking the FastAPI event loop.
    """
    if not text or not text.strip():
        return text
    return await asyncio.to_thread(_redact_sync, text)
