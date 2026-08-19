"""
Query Enhancer / Medical Autocorrect

Corrects typographic errors in clinical queries before embedding and retrieval.
Sits between normalize_query() and detect_conversational_query() in the pipeline.

Strategy (layered, deterministic — no LLM call per query):
  1. Pre-normalised text received (repeated-char collapse already done)
  2. Exact extended-dictionary lookup (clinical + general terms)
  3. Fuzzy token matching (rapidfuzz WRatio) against CLINICAL_VOCABULARY
  4. Context-aware confidence boost for tokens in a medical-domain query

Constraints:
  - Never changes the semantics or intent of the query
  - Never forces an out-of-domain query toward the clinical domain
  - Only corrects tokens when confidence >= HIGH_CONFIDENCE_THRESHOLD
  - Preserves original query verbatim; returns enhanced_query separately
  - Added latency target: < 10 ms for a typical short query
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import List

try:
    from rapidfuzz import fuzz, process
    _RAPIDFUZZ_AVAILABLE = True
except ImportError:
    _RAPIDFUZZ_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Minimum WRatio score (0-100 scale) to accept a fuzzy correction
HIGH_CONFIDENCE_THRESHOLD = 87   # ~0.87 equivalent
# Confidence boost when the surrounding query context is clinical
CLINICAL_CONTEXT_BOOST = 5      # added to WRatio when domain keywords present

# Minimum token length to run fuzzy matching (avoids trivial short-word flips)
MIN_TOKEN_LEN_FOR_FUZZY = 4

# Stopwords: never try to spell-correct these
STOPWORDS = frozenset({
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "of", "or", "and",
    "for", "are", "how", "why", "who", "can", "do", "does", "was", "be",
    "with", "by", "from", "as", "its", "what", "when", "where", "which",
    "that", "this", "these", "those", "their", "them", "they", "we",
    "i", "me", "my", "you", "your", "he", "she", "his", "her",
    "not", "no", "yes", "very", "just", "also", "but", "if", "so",
    "will", "would", "should", "could", "may", "might",
    "has", "have", "had", "been", "about", "more", "some",
    "most", "than", "then", "up", "out", "per", "vs", "am",
})

# Domain keywords used to determine if the query is in the breast-cancer domain
DOMAIN_KEYWORDS = frozenset({
    "breast", "cancer", "tumor", "tumour", "mammogram", "mammography",
    "screening", "dcis", "lcis", "lobular", "ductal", "carcinoma",
    "her2", "brca", "estrogen", "hormone", "biopsy", "metastatic",
    "staging", "lumpectomy", "mastectomy", "oncology", "pathogenesis",
    "symptoms", "symptom", "diagnosis", "treatment", "prognosis",
    "chemotherapy", "radiotherapy", "radiation", "tomosynthesis",
    "dense", "density", "biomarker", "subtype", "uspstf", "ahrq",
})

# ---------------------------------------------------------------------------
# Extended correction dictionary
# (extends normalizer.py's CLINICAL_TYPO_MAP with more patterns)
# ---------------------------------------------------------------------------

CORRECTION_DICT: dict = {
    # --- Common general typos ---
    "whta": "what",
    "waht": "what",
    "teh": "the",
    "hte": "the",
    "adn": "and",
    "nad": "and",
    "hwo": "how",
    "taht": "that",
    "tpye": "type",
    "tpyes": "types",
    "typse": "types",
    "typs": "types",
    "tyep": "type",
    "wht": "what",
    "wwhich": "which",
    "aree": "are",
    "arre": "are",
    "comon": "common",
    "comom": "common",
    "tyes": "types",
    "sings": "signs",
    "signd": "signs",

    # --- Breast ---
    "brest": "breast",
    "braest": "breast",
    "brast": "breast",
    "breaxt": "breast",
    "bresat": "breast",
    "breastt": "breast",
    "breaast": "breast",

    # --- Cancer ---
    "cancr": "cancer",
    "cancerr": "cancer",
    "cacer": "cancer",
    "canser": "cancer",
    "caner": "cancer",
    "cncer": "cancer",
    "cancerrs": "cancers",

    # --- Symptoms ---
    "syptoms": "symptoms",
    "symtoms": "symptoms",
    "symptons": "symptoms",
    "symptmos": "symptoms",
    "symtpoms": "symptoms",
    "symptomms": "symptoms",
    "symtom": "symptom",
    "syptom": "symptom",
    "sympton": "symptom",

    # --- Pathogenesis ---
    "pathogensis": "pathogenesis",
    "pathogeneis": "pathogenesis",
    "pathogenisis": "pathogenesis",
    "pathogesis": "pathogenesis",
    "pathogneiss": "pathogenesis",
    "pathognesis": "pathogenesis",
    "pathogenesiss": "pathogenesis",

    # --- Diagnosis ---
    "diagnosiss": "diagnosis",
    "diagnossis": "diagnosis",
    "diagonsis": "diagnosis",
    "diagnisis": "diagnosis",
    "diagosis": "diagnosis",

    # --- Prognosis ---
    "prognossis": "prognosis",
    "prognosiss": "prognosis",
    "prognisis": "prognosis",

    # --- Treatment ---
    "treatmnt": "treatment",
    "treatement": "treatment",
    "treament": "treatment",
    "treatmet": "treatment",
    "treatemnt": "treatment",

    # --- Mammography / Mammogram ---
    "mamogram": "mammogram",
    "mamography": "mammography",
    "mammografy": "mammography",
    "mammograpy": "mammography",
    "mamograms": "mammograms",
    "mammogramm": "mammogram",
    "mammograhy": "mammography",
    "mammogaphy": "mammography",

    # --- Screening ---
    "screenin": "screening",
    "screning": "screening",
    "screenning": "screening",
    "screnning": "screening",
    "screenig": "screening",

    # --- Chemotherapy ---
    "chemotherpy": "chemotherapy",
    "chemothrapy": "chemotherapy",
    "chemotheray": "chemotherapy",
    "chemoterapy": "chemotherapy",
    "chemoterpy": "chemotherapy",

    # --- Radiotherapy ---
    "radiothrapy": "radiotherapy",
    "radiotherpy": "radiotherapy",
    "raditherapy": "radiotherapy",

    # --- Radiation ---
    "radition": "radiation",
    "radaition": "radiation",

    # --- Lumpectomy ---
    "lumpectmy": "lumpectomy",
    "lumpecomy": "lumpectomy",

    # --- Mastectomy ---
    "mastectmy": "mastectomy",
    "mastecomy": "mastectomy",
    "mstectomy": "mastectomy",

    # --- Carcinoma ---
    "carcinmo": "carcinoma",
    "carciomna": "carcinoma",
    "carinoma": "carcinoma",
    "carcinoms": "carcinomas",

    # --- Metastasis / Metastatic ---
    "metastis": "metastasis",
    "metastasiss": "metastasis",
    "metasatis": "metastasis",
    "metasttic": "metastatic",
    "metatastic": "metastatic",

    # --- Biomarkers / Subtypes ---
    "biomarkr": "biomarker",
    "biomarkrs": "biomarkers",
    "biomarkerss": "biomarkers",
    "subtyps": "subtypes",
    "subtypess": "subtypes",

    # --- Biopsy ---
    "biopsie": "biopsy",
    "biopsys": "biopsies",
    "biopy": "biopsy",

    # --- Tomosynthesis ---
    "tomosynthsis": "tomosynthesis",
    "tomosythesis": "tomosynthesis",
    "tomosyntesis": "tomosynthesis",

    # --- Ultrasound ---
    "ultrasond": "ultrasound",
    "ultrsound": "ultrasound",
    "ulrasound": "ultrasound",

    # --- Staging ---
    "stagingg": "staging",
    "stagig": "staging",
    "stagin": "staging",

    # --- Invasive ---
    "invasve": "invasive",
    "invasivee": "invasive",
    "invaisve": "invasive",

    # --- Ductal ---
    "ducal": "ductal",
    "dductal": "ductal",
    "dutcal": "ductal",

    # --- Lobular ---
    "lobualr": "lobular",
    "lobbular": "lobular",
    "lobullar": "lobular",

    # --- Dense / Density ---
    "densse": "dense",
    "densee": "dense",
    "densitty": "density",
    "densitt": "density",

    # --- Recommendation / Evidence ---
    "recommednation": "recommendation",
    "reccomendation": "recommendation",
    "recomendation": "recommendation",
    "recommandation": "recommendation",
    "evdence": "evidence",
    "evidnece": "evidence",
    "evidece": "evidence",

    # --- Guidelines ---
    "guideliness": "guidelines",
    "guidlines": "guidelines",
    "guidelins": "guidelines",

    # --- Existing normalizer items (kept here for completeness/lookup speed) ---
    "breaast": "breast",
    "cancerr": "cancer",
    "cancr": "cancer",
    "typessg": "types",
    "typesg": "types",
    "typess": "types",
    "symtoms": "symptoms",
    "symptomms": "symptoms",
    "symtom": "symptom",
    "pathogeneis": "pathogenesis",
    "treatmnt": "treatment",
    "treatement": "treatment",
    "biomarkr": "biomarker",
    "biomarkrs": "biomarkers",
    "subtyps": "subtypes",
    "mamogram": "mammogram",
    "mamography": "mammography",
    "mammogramm": "mammogram",
    "screenin": "screening",
    "screning": "screening",
    "screenning": "screening",
    "stagingg": "staging",
    "metastis": "metastasis",
    "metastasiss": "metastasis",
    "ultrasond": "ultrasound",
    "ultrsound": "ultrasound",
    "chemotherpy": "chemotherapy",
    "biopsie": "biopsy",
    "biopsys": "biopsies",
}

# ---------------------------------------------------------------------------
# Clinical vocabulary for fuzzy matching
# (Only tokens matched against THIS set — prevents wild domain-shift)
# ---------------------------------------------------------------------------

CLINICAL_VOCABULARY: List[str] = sorted(set([
    # Core clinical terms
    "symptoms", "symptom", "signs", "diagnosis", "prognosis", "treatment",
    "pathogenesis", "staging", "screening", "mammography", "mammogram",
    "mammograms", "biopsy", "biopsies", "ultrasound", "radiation",
    "chemotherapy", "radiotherapy", "lumpectomy", "mastectomy",
    "tomosynthesis", "carcinoma", "carcinomas", "metastasis", "metastatic",
    "invasive", "ductal", "lobular", "dense", "density",
    "biomarker", "biomarkers", "subtypes", "subtype",
    "guidelines", "guideline", "recommendation", "recommendations",
    "evidence", "benefit", "benefits", "harm", "harms", "overdiagnosis",
    "mortality", "morbidity", "incidence", "prevalence",
    "hormone", "receptor", "estrogen", "progesterone",
    "genetic", "hereditary", "mutation", "brca",
    # Breast cancer specific
    "breast", "cancer", "cancers", "tumor", "tumour", "tumors", "tumours",
    "triple", "negative", "positive", "her2", "dcis", "lcis",
    # Screening terms
    "biennial", "annual", "interval", "supplemental", "digital",
    "sensitivity", "specificity", "recall",
    # Common query words (important in medical context)
    "types", "type", "causes", "cause", "risk", "risks", "factors",
    "common", "clinical", "average", "standard",
    "women", "woman", "female", "age", "older", "younger",
    "years", "routine", "regular", "early", "late",
    "what", "how", "why", "when", "which", "diagnosis",
]))


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CorrectionRecord:
    original: str
    corrected: str
    confidence: float
    method: str   # "dictionary" | "fuzzy"


@dataclass
class EnhancementResult:
    original_query: str
    enhanced_query: str
    query_changed: bool
    enhancement_confidence: float   # mean confidence (1.0 if no changes)
    corrections: List[CorrectionRecord] = field(default_factory=list)
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ALPHANUM_RE = re.compile(r"[^\w]")
# Matches known proper nouns / initialisms / numbers: DCIS, HER2, BRCA1, 75, etc.
_PROPER_NOUN_RE = re.compile(r"^[A-Z]{2,}$|^\d+$|^[A-Z]\w*\d+$")


def _is_correction_candidate(core: str) -> bool:
    """
    Returns True if this token should be considered for spell-correction.
    Skips: stopwords, proper-noun-looking tokens, very short tokens, pure digits.
    """
    clean = _ALPHANUM_RE.sub("", core).lower()
    if len(clean) < MIN_TOKEN_LEN_FOR_FUZZY:
        return False
    if clean in STOPWORDS:
        return False
    if _PROPER_NOUN_RE.match(core):
        return False
    return True


def _has_domain_context(tokens: List[str]) -> bool:
    """Return True if any token in the query is already a domain keyword."""
    lowered = {_ALPHANUM_RE.sub("", t).lower() for t in tokens}
    return bool(lowered & DOMAIN_KEYWORDS)


def _preserve_case(original: str, corrected: str) -> str:
    """Apply the same capitalisation pattern from original to corrected."""
    if original.isupper():
        return corrected.upper()
    if original.istitle():
        return corrected.title()
    return corrected


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def enhance_query(query: str) -> EnhancementResult:
    """
    Apply layered spelling correction to a (already normalised) clinical query.

    Returns an EnhancementResult with the corrected query and full correction
    metadata. The original_query field is always the unmodified input.
    """
    t_start = time.perf_counter()

    if not query or not query.strip():
        return EnhancementResult(
            original_query=query,
            enhanced_query=query,
            query_changed=False,
            enhancement_confidence=1.0,
            corrections=[],
            latency_ms=0.0,
        )

    # Split preserving punctuation positions
    tokens = query.split()
    corrected_tokens: List[str] = []
    corrections: List[CorrectionRecord] = []
    in_domain = _has_domain_context(tokens)

    for token in tokens:
        # Strip surrounding punctuation for lookup, restore after
        m_lead = re.match(r"^([^\w]*)", token)
        leading_punct = m_lead.group(1) if m_lead else ""
        m_trail = re.search(r"([^\w]*)$", token)
        trailing_punct = m_trail.group(1) if m_trail else ""
        core = token[len(leading_punct):]
        if trailing_punct:
            core = core[:-len(trailing_punct)]

        if not core:
            corrected_tokens.append(token)
            continue

        core_lower = core.lower()

        # ---- Layer 2: Exact dictionary lookup ----
        if core_lower in CORRECTION_DICT:
            target = CORRECTION_DICT[core_lower]
            # Only record as change if actually different
            if target != core_lower:
                cased = _preserve_case(core, target)
                corrected_tokens.append(leading_punct + cased + trailing_punct)
                corrections.append(CorrectionRecord(
                    original=core,
                    corrected=cased,
                    confidence=1.0,
                    method="dictionary",
                ))
                continue

        # ---- Layer 3: Fuzzy matching ----
        if _RAPIDFUZZ_AVAILABLE and _is_correction_candidate(core):
            result = process.extractOne(
                core_lower,
                CLINICAL_VOCABULARY,
                scorer=fuzz.WRatio,
                score_cutoff=max(HIGH_CONFIDENCE_THRESHOLD - CLINICAL_CONTEXT_BOOST - 1, 75),
            )
            if result is not None:
                match_word, score, _ = result
                effective_score = score + CLINICAL_CONTEXT_BOOST if in_domain else score

                # Accept only if above threshold AND the word is actually different
                if effective_score >= HIGH_CONFIDENCE_THRESHOLD and match_word != core_lower:
                    cased = _preserve_case(core, match_word)
                    corrected_tokens.append(leading_punct + cased + trailing_punct)
                    corrections.append(CorrectionRecord(
                        original=core,
                        corrected=cased,
                        confidence=round(min(effective_score / 100.0, 1.0), 3),
                        method="fuzzy",
                    ))
                    continue

        # No correction
        corrected_tokens.append(token)

    enhanced = " ".join(corrected_tokens)
    changed = enhanced != query

    conf = (
        round(sum(c.confidence for c in corrections) / len(corrections), 3)
        if corrections else 1.0
    )

    latency_ms = round((time.perf_counter() - t_start) * 1000, 2)

    return EnhancementResult(
        original_query=query,
        enhanced_query=enhanced,
        query_changed=changed,
        enhancement_confidence=conf,
        corrections=corrections,
        latency_ms=latency_ms,
    )


def enhance_query_to_dict(query: str) -> dict:
    """
    Convenience wrapper that returns a plain dict for easy JSON serialisation
    and inclusion in API responses / log entries.
    """
    result = enhance_query(query)
    return {
        "original_query": result.original_query,
        "enhanced_query": result.enhanced_query,
        "query_changed": result.query_changed,
        "enhancement_confidence": result.enhancement_confidence,
        "corrections": [
            {
                "original": c.original,
                "corrected": c.corrected,
                "confidence": c.confidence,
                "method": c.method,
            }
            for c in result.corrections
        ],
        "latency_ms": result.latency_ms,
    }
