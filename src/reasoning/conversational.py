import re
from typing import Optional, Dict, Any

# Clinical domain keywords: if any of these appear, NEVER intercept as small talk
CLINICAL_SAFETY_KEYWORDS = {
    "cancer", "tumor", "tumour", "breast", "mammogram", "mammography", "screening",
    "dcis", "lobular", "ductal", "stage", "staging", "symptom", "pain", "biopsy",
    "risk", "dense", "density", "treatment", "chemo", "radiation", "therapy",
    "uspstf", "ahrq", "nci", "nih", "age", "ultrasound", "mri", "gene",
    "brca", "her2", "estrogen", "hormone", "node", "metastatic", "lesion",
    "calcification", "arm", "covid", "broken", "bone", "dose", "drug",
    "guideline", "evidence", "interval", "harm", "benefit", "overdiagnosis"
}

# Regex patterns for conversational intents
GREETING_PATTERNS = [
    r"^hi\b",
    r"^hello\b",
    r"^hey\b",
    r"^good\s+(morning|afternoon|evening|day)\b",
    r"^greetings\b",
    r"^howdy\b",
    r"^hi\s+there\b",
    r"^hello\s+there\b",
    r"^hey\s+there\b",
]

COURTESY_PATTERNS = [
    r"^(thank\s+you|thanks|thx|thank\s+you\s+so\s+much)\b",
    r"^(ok|okay|got\s+it|understood|great|perfect|sure|sounds\s+good)$",
    r"^(cool|awesome|nice|wonderful)$",
]

FAREWELL_PATTERNS = [
    r"^(bye|goodbye|see\s+you|see\s+ya|have\s+a\s+good\s+day|take\s+care)$",
]

META_IDENTITY_PATTERNS = [
    r"^who\s+are\s+you",
    r"^what\s+are\s+you",
    r"^what\s+is\s+medretriv",
    r"^what\s+is\s+instant",
    r"^tell\s+me\s+about\s+yourself",
]

META_CAPABILITY_PATTERNS = [
    r"^what\s+can\s+you\s+do",
    r"^what\s+is\s+this",
    r"^how\s+can\s+you\s+help",
    r"^how\s+do\s+you\s+work",
    r"^help$",
    r"^instructions$",
    r"^what\s+questions\s+can\s+i\s+ask",
]

RESPONSES = {
    "greeting": (
        "Hello! I'm MedRetriv, a Clinical Evidence Assistant specializing in breast cancer "
        "screening guidelines and clinical knowledge. Ask me a clinical question and I will "
        "answer using official medical guidelines (USPSTF, AHRQ, NCI, etc.) with verifiable inline citations."
    ),
    "courtesy": (
        "You're welcome! Please feel free to ask if you have any questions about breast cancer "
        "screening guidelines, recommendations, or clinical evidence."
    ),
    "farewell": (
        "Goodbye! Feel free to return if you need more clinical evidence or guideline assistance. "
        "Wishing you all the best."
    ),
    "meta_identity": (
        "I am MedRetriv, an AI Clinical Decision Support assistant. I assist clinicians, researchers, "
        "and users by searching authoritative breast cancer screening guidelines (USPSTF, AHRQ) and "
        "foundational medical reviews (NCI, Nature, Frontiers) to provide evidence-grounded answers with "
        "verifiable inline citations."
    ),
    "meta_capability": (
        "I can answer questions regarding breast cancer screening recommendations, starting ages, "
        "screening intervals, potential screening harms, supplemental screening for dense breasts, "
        "and breast cancer pathophysiology/staging. All clinical answers are strictly grounded in our "
        "curated clinical evidence base with exact source citations."
    ),
}


def detect_conversational_query(text: str) -> Optional[Dict[str, str]]:
    """
    Detect if a user input is purely conversational (greeting, courtesy, farewell, meta question)
    or if it should proceed to the clinical RAG pipeline.

    Returns dict with intent and response if conversational, or None if clinical/out-of-domain.
    """
    if not text:
        return None

    cleaned = text.strip().lower()
    # Remove trailing punctuation
    cleaned_no_punct = re.sub(r"[?!.,;:]+$", "", cleaned).strip()

    # Safety Guard: If any medical/clinical domain keywords appear, do NOT intercept as small talk
    words = set(re.findall(r"\b\w+\b", cleaned_no_punct))
    if any(keyword in words for keyword in CLINICAL_SAFETY_KEYWORDS):
        return None

    # Check Meta Identity
    for pattern in META_IDENTITY_PATTERNS:
        if re.search(pattern, cleaned_no_punct):
            return {"intent": "meta_identity", "response": RESPONSES["meta_identity"]}

    # Check Meta Capability
    for pattern in META_CAPABILITY_PATTERNS:
        if re.search(pattern, cleaned_no_punct):
            return {"intent": "meta_capability", "response": RESPONSES["meta_capability"]}

    # Check Greetings
    for pattern in GREETING_PATTERNS:
        if re.search(pattern, cleaned_no_punct):
            return {"intent": "greeting", "response": RESPONSES["greeting"]}

    # Check Courtesy
    for pattern in COURTESY_PATTERNS:
        if re.search(pattern, cleaned_no_punct):
            return {"intent": "courtesy", "response": RESPONSES["courtesy"]}

    # Check Farewell
    for pattern in FAREWELL_PATTERNS:
        if re.search(pattern, cleaned_no_punct):
            return {"intent": "farewell", "response": RESPONSES["farewell"]}

    return None
