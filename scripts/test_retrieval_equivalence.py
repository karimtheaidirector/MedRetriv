"""
scripts/test_retrieval_equivalence.py

Clean-vs-Typo Retrieval Equivalence Benchmark Suite

Verifies that equivalent clinical user questions with different spelling quality
produce identical or substantially equivalent retrieval representations, top chunks,
document/section distributions, and generation modes.

Test Pairs:
  1. "breast cancer types" vs "breast canser typs"
  2. "breast cancer symptoms" vs "breast canser symptons"
  3. "breast cancer treatment" vs "breast cancr tretmnt"
  4. "breast cancer diagnosis" vs "breast cancr diagnosiss"
  5. "breast cancer screening" vs "brest canser screenng"
  6. "breast cancer pathogenesis" vs "brest cancr pathogensis"
  7. Multi-Turn Session A ("what is breast cancer" -> "types") vs Session B ("what is breast cancer" -> "typs")
  8. Multi-Turn Session A ("what is breast cancer" -> "pathogenesis") vs Session B ("what is breast cancer" -> "pathogensis")

Run with:
    python -X utf8 scripts/test_retrieval_equivalence.py
"""

import sys
import time
import io
from typing import List, Dict, Set

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, ".")

from src.reasoning.normalizer import normalize_query
from src.reasoning.query_enhancer import enhance_query
from src.reasoning.contextual import resolve_contextual_query
from src.Retrieval.query import retrieve_documents
from src.reasoning.safety import evaluate_retrieval_safety, CONFIDENCE_THRESHOLD

GREEN  = "\033[92m"
RED    = "\033[91m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0


def jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    if not set_a and not set_b:
        return 1.0
    return len(set_a & set_b) / len(set_a | set_b)


def test_equivalence_pair(name: str, clean_query: str, typo_query: str, min_overlap: float = 0.80):
    global passed, failed

    print(f"\n{BOLD}{CYAN}Evaluating Pair: {name}{RESET}")
    print(f"  Clean input : {clean_query!r}")
    print(f"  Typo input  : {typo_query!r}")

    # Process Clean
    norm_c = normalize_query(clean_query)
    enh_c = enhance_query(norm_c)
    raw_c = retrieve_documents(enh_c.enhanced_query, n_results=5)
    _, sim_c, chunks_c = evaluate_retrieval_safety(raw_c, threshold=CONFIDENCE_THRESHOLD)

    # Process Typo
    norm_t = normalize_query(typo_query)
    enh_t = enhance_query(norm_t)
    raw_t = retrieve_documents(enh_t.enhanced_query, n_results=5)
    _, sim_t, chunks_t = evaluate_retrieval_safety(raw_t, threshold=CONFIDENCE_THRESHOLD)

    # Metrics
    ids_c = [c["chunk_id"] for c in chunks_c]
    ids_t = [c["chunk_id"] for c in chunks_t]
    overlap = jaccard_similarity(set(ids_c), set(ids_t))
    sim_delta = abs(sim_t - sim_c)

    query_converged = (enh_t.enhanced_query.lower() == enh_c.enhanced_query.lower())
    overlap_ok = (overlap >= min_overlap)
    sim_ok = (sim_delta <= 0.05)

    all_ok = query_converged and overlap_ok and sim_ok

    status = f"{GREEN}PASS{RESET}" if all_ok else f"{RED}FAIL{RESET}"
    if all_ok:
        passed += 1
    else:
        failed += 1

    print(f"  [{status}] Enhanced typo   : {enh_t.enhanced_query!r}")
    print(f"         Enhanced clean  : {enh_c.enhanced_query!r}")
    print(f"         Top-1 Similarity: Clean={sim_c:.4f} | Typo={sim_t:.4f} (Delta={sim_delta:+.4f})")
    print(f"         Top-5 Jaccard   : {overlap:.1%} (Target >= {min_overlap:.0%})")
    print(f"         Clean Top Chunk : ID={chunks_c[0]['chunk_id'][:30]} | Sec={chunks_c[0]['section']}")
    print(f"         Typo Top Chunk  : ID={chunks_t[0]['chunk_id'][:30]} | Sec={chunks_t[0]['section']}")


def test_multiturn_equivalence(name: str, history_a: List[Dict], history_b: List[Dict], min_overlap: float = 0.80):
    global passed, failed

    print(f"\n{BOLD}{CYAN}Evaluating Multi-Turn Pair: {name}{RESET}")

    # Session A
    turn_a = history_a[-1]["content"]
    norm_a = normalize_query(turn_a)
    enh_a = enhance_query(norm_a)
    res_a = resolve_contextual_query(enh_a.enhanced_query, history=history_a[:-1])
    raw_a = retrieve_documents(res_a, n_results=5)
    _, sim_a, chunks_a = evaluate_retrieval_safety(raw_a, threshold=CONFIDENCE_THRESHOLD)

    # Session B
    turn_b = history_b[-1]["content"]
    norm_b = normalize_query(turn_b)
    enh_b = enhance_query(norm_b)
    res_b = resolve_contextual_query(enh_b.enhanced_query, history=history_b[:-1])
    raw_b = retrieve_documents(res_b, n_results=5)
    _, sim_b, chunks_b = evaluate_retrieval_safety(raw_b, threshold=CONFIDENCE_THRESHOLD)

    ids_a = [c["chunk_id"] for c in chunks_a]
    ids_b = [c["chunk_id"] for c in chunks_b]
    overlap = jaccard_similarity(set(ids_a), set(ids_b))
    sim_delta = abs(sim_b - sim_a)

    all_ok = (overlap >= min_overlap) and (sim_delta <= 0.05)
    status = f"{GREEN}PASS{RESET}" if all_ok else f"{RED}FAIL{RESET}"

    if all_ok:
        passed += 1
    else:
        failed += 1

    print(f"  [{status}] Resolved Turn A  : {res_a!r}")
    print(f"         Resolved Turn B  : {res_b!r}")
    print(f"         Top-1 Similarity : A={sim_a:.4f} | B={sim_b:.4f} (Delta={sim_delta:+.4f})")
    print(f"         Top-5 Jaccard    : {overlap:.1%}")


def main():
    print("=" * 65)
    print("CLEAN-VS-TYPO RETRIEVAL EQUIVALENCE BENCHMARK")
    print("=" * 65)

    test_equivalence_pair(
        "Pair 1 (Types)",
        clean_query="breast cancer types",
        typo_query="breast canser typs",
        min_overlap=0.80,
    )

    test_equivalence_pair(
        "Pair 2 (Symptoms)",
        clean_query="breast cancer symptoms",
        typo_query="breast canser symptons",
        min_overlap=0.80,
    )

    test_equivalence_pair(
        "Pair 3 (Treatment)",
        clean_query="breast cancer treatment",
        typo_query="breast cancr tretmnt",
        min_overlap=0.80,
    )

    test_equivalence_pair(
        "Pair 4 (Diagnosis)",
        clean_query="breast cancer diagnosis",
        typo_query="breast cancr diagnosiss",
        min_overlap=0.80,
    )

    test_equivalence_pair(
        "Pair 5 (Screening)",
        clean_query="breast cancer screening",
        typo_query="brest canser screenng",
        min_overlap=0.80,
    )

    test_equivalence_pair(
        "Pair 6 (Pathogenesis)",
        clean_query="breast cancer pathogenesis",
        typo_query="brest cancr pathogensis",
        min_overlap=0.80,
    )

    # Multi-turn Tests
    test_multiturn_equivalence(
        "Multi-turn (types vs typs)",
        history_a=[
            {"role": "user", "content": "what is breast cancer"},
            {"role": "assistant", "content": "Breast cancer is a malignancy of breast tissue."},
            {"role": "user", "content": "types"},
        ],
        history_b=[
            {"role": "user", "content": "what is breast cancer"},
            {"role": "assistant", "content": "Breast cancer is a malignancy of breast tissue."},
            {"role": "user", "content": "typs"},
        ],
        min_overlap=0.80,
    )

    test_multiturn_equivalence(
        "Multi-turn (pathogenesis vs pathogensis)",
        history_a=[
            {"role": "user", "content": "what is breast cancer"},
            {"role": "assistant", "content": "Breast cancer is a malignancy of breast tissue."},
            {"role": "user", "content": "pathogenesis"},
        ],
        history_b=[
            {"role": "user", "content": "what is breast cancer"},
            {"role": "assistant", "content": "Breast cancer is a malignancy of breast tissue."},
            {"role": "user", "content": "pathogensis"},
        ],
        min_overlap=0.80,
    )

    total = passed + failed
    print("\n" + "=" * 65)
    print(f"Results: {GREEN}{passed}{RESET}/{total} passed, {RED}{failed}{RESET}/{total} failed")
    print("=" * 65)


if __name__ == "__main__":
    main()
