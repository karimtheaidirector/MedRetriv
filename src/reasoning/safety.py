import os
from typing import Any, Dict, List, Tuple


# ============================================================
# Configurable Confidence & Safety Thresholds
# ============================================================

# Default minimum cosine similarity score required on the top retrieved chunk
# ChromaDB default squared L2 distance d relates to cosine similarity s by: s = 1 - d/2
# For in-domain queries s in [0.64, 0.80]; for out-of-domain queries s < 0.35.
DEFAULT_CONFIDENCE_THRESHOLD = 0.50

CONFIDENCE_THRESHOLD = float(
    os.getenv("CONFIDENCE_THRESHOLD", str(DEFAULT_CONFIDENCE_THRESHOLD))
)

# Standard refusal message used across both safety threshold and LLM prompt
STANDARD_REFUSAL_MESSAGE = (
    "I don't have enough information in the provided clinical "
    "evidence to answer this question."
)


def distance_to_similarity(distance: float) -> float:
    """
    Convert ChromaDB squared L2 distance to cosine similarity for normalized vectors.
    Range: [0.0, 1.0]
    """
    if distance is None:
        return 0.0
    return max(0.0, min(1.0, 1.0 - (float(distance) / 2.0)))


def extract_chunk_records(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract structured chunk records from ChromaDB query results.
    """
    if not results or not results.get("documents") or not results["documents"][0]:
        return []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if results.get("distances") else []
    ids = results.get("ids", [[]])[0]

    records = []
    for idx, (doc_id, text, metadata) in enumerate(zip(ids, documents, metadatas)):
        dist = distances[idx] if idx < len(distances) else 0.0
        sim = distance_to_similarity(dist)

        records.append(
            {
                "chunk_id": doc_id,
                "document": metadata.get("source", "unknown"),
                "source": metadata.get("source", "unknown"),
                "doc_type": metadata.get("doc_type", metadata.get("document_type", "unknown")),
                "section": metadata.get("section", "unknown"),
                "page_start": metadata.get("page_start", 0),
                "page_end": metadata.get("page_end", 0),
                "distance": round(float(dist), 4),
                "similarity_score": round(float(sim), 4),
                "text_snippet": text[:200] if text else "",
            }
        )

    return records


def check_confidence(
    results: Dict[str, Any],
    threshold: float = CONFIDENCE_THRESHOLD,
) -> bool:
    """
    Testable safety check: Verify if the top retrieved chunk meets the confidence threshold.
    Returns True if confidence threshold is met, False otherwise.
    """
    records = extract_chunk_records(results)
    if not records:
        return False

    top_similarity = records[0]["similarity_score"]
    return top_similarity >= threshold


def evaluate_retrieval_safety(
    results: Dict[str, Any],
    threshold: float = CONFIDENCE_THRESHOLD,
) -> Tuple[bool, float, List[Dict[str, Any]]]:
    """
    Evaluate retrieval results for safety threshold before generation.

    Returns:
      - is_confident (bool): True if meets threshold, False if should refuse
      - top_score (float): Similarity score of the top chunk
      - chunk_records (list): Structured chunk records for logging
    """
    records = extract_chunk_records(results)

    if not records:
        return False, 0.0, []

    top_score = records[0]["similarity_score"]
    is_confident = top_score >= threshold

    return is_confident, top_score, records


def parse_citations_from_text(text: str) -> List[Dict[str, str]]:
    """
    Extract citation tuples [Source: ..., (Section: ...,) Page: ...] from text using regex.
    """
    import re

    pattern = r'\[Source:\s*([^,\]]+)(?:,\s*Section:\s*([^,\]]+))?,\s*Page:\s*([^\]]+)\]'
    matches = re.findall(pattern, text)
    citations = []
    for m in matches:
        source = m[0].strip()
        section = m[1].strip() if m[1] else ""
        page = m[2].strip()
        citations.append({
            "raw": f"[Source: {source}{f', Section: {section}' if section else ''}, Page: {page}]",
            "source": source,
            "section": section,
            "page": page
        })
    return citations


def verify_citations(
    answer: str,
    chunk_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Post-generation verification step: Programmatically checks each citation in the generated
    answer against the actual retrieved chunk list for that query.
    
    Returns verification report dict for safety logging and auditing.
    """
    if not answer or STANDARD_REFUSAL_MESSAGE.lower() in answer.lower():
        return {
            "all_citations_valid": True,
            "citation_count": 0,
            "valid_citation_count": 0,
            "accuracy_rate": 1.0,
            "invalid_citations": [],
            "flagged_for_review": False,
        }

    citations = parse_citations_from_text(answer)
    if not citations:
        return {
            "all_citations_valid": False,
            "citation_count": 0,
            "valid_citation_count": 0,
            "accuracy_rate": 0.0,
            "invalid_citations": ["MISSING_CITATIONS"],
            "flagged_for_review": True,
        }

    valid_citations = []
    invalid_citations = []

    for cit in citations:
        matched = any(
            (cit["source"].lower() in c["document"].lower() or c["document"].lower() in cit["source"].lower())
            for c in chunk_records
        )
        if matched:
            valid_citations.append(cit)
        else:
            invalid_citations.append(cit)

    accuracy_rate = len(valid_citations) / len(citations) if citations else 1.0
    all_valid = len(invalid_citations) == 0

    return {
        "all_citations_valid": all_valid,
        "citation_count": len(citations),
        "valid_citation_count": len(valid_citations),
        "accuracy_rate": round(accuracy_rate, 4),
        "invalid_citations": invalid_citations,
        "flagged_for_review": not all_valid,
    }
