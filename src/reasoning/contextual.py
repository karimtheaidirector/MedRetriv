import re
from typing import List, Dict, Optional

FOLLOWUP_TRIGGER_PHRASES = {
    "more details", "tell me more", "more info", "more information",
    "explain more", "details", "elaborate", "what else", "anything else",
    "can you elaborate", "more about this", "more", "expand", "tell me about it",
    "give me details", "further details"
}


def extract_persistent_topic(history: List[Dict[str, str]]) -> str:
    """
    Scans the conversation history from newest to oldest for the established
    substantive clinical question to determine the persistent topic anchor.
    """
    if not history:
        return "breast cancer"

    for msg in reversed(history):
        if msg.get("role") != "user" or not msg.get("content"):
            continue
        text = msg["content"].strip().lower()
        if "breast cancer" in text:
            return "breast cancer"
        if "mammogram" in text or "mammography" in text:
            return "breast cancer screening mammography"
        if "screening" in text:
            return "breast cancer screening"
        if "dcis" in text or "ductal" in text:
            return "ductal carcinoma in situ DCIS"
        if "dense" in text or "density" in text:
            return "dense breasts supplemental screening"
        if len(text.split()) >= 4 and ("cancer" in text or "tumor" in text or "guideline" in text):
            return " ".join([w for w in msg["content"].split() if len(w) > 3][:5])

    return "breast cancer"


AGE_CONSULTATION_PATTERN = re.compile(
    r"\b(i am|i\'m|age|aged|\d{1,2}\s*years?\s*old)\b.*?\b(suggest|recommend|advice|advise|should i|do i need|guideline|what should|what to do)\b|"
    r"\b(suggest|recommend|advice|advise|should i|do i need|what should|what to do)\b.*?\b(i am|i\'m|age|aged|\d{1,2}\s*years?\s*old)\b",
    re.IGNORECASE
)


def resolve_contextual_query(
    current_query: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    """
    Persistent context carry-over and query resolution:
    1. If the user provides an elliptical age-screening consultation query without explicit
       domain keywords (e.g. 'I am 75 years old, suggest me'), resolves it with the clinical domain.
    2. If the user provides a short follow-up or topic word with active history, enrich it with
       the persistent clinical topic anchor established in the session.
    """
    if not current_query or not current_query.strip():
        return current_query

    q_clean = current_query.strip()
    q_lower = q_clean.lower().rstrip("?!.,;:")

    # Check if clinical domain keywords are already present
    has_domain = any(k in q_lower for k in ["breast", "cancer", "mammogra", "dcis", "tumor", "tumour"])

    # Age consultation without explicit domain keywords (e.g. "I am 75 years old, suggest me")
    if not has_domain and AGE_CONSULTATION_PATTERN.search(q_clean):
        return f"{q_clean} breast cancer screening guidelines"

    if not history:
        return current_query

    words = q_clean.split()

    # If the user asks a completely new long standalone question (>= 6 words), do not force-prefix
    if len(words) >= 6:
        return current_query

    active_anchor = extract_persistent_topic(history)

    # Case A: Generic follow-up ("more details", "tell me more")
    if q_lower in FOLLOWUP_TRIGGER_PHRASES or any(q_lower.startswith(p) for p in [
        "more details", "tell me more", "explain more", "more info", "can you elaborate"
    ]):
        return f"{active_anchor} detailed clinical evidence and comprehensive guidelines"

    # Case B: Short noun/topic follow-up (<= 4 words) that doesn't explicitly mention the anchor
    if len(words) <= 4 and not has_domain:
        return f"{active_anchor} {q_clean}"

    return current_query
