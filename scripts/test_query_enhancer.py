"""
tests/test_query_enhancer.py

Comprehensive tests for the Clinical Query Enhancer / Medical Autocorrect.

Run with:
    python scripts/test_query_enhancer.py
    # or
    pytest scripts/test_query_enhancer.py -v
"""

import sys
import time
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, ".")

from src.reasoning.query_enhancer import enhance_query, EnhancementResult

# ─────────────────────────────────────────────────────────────────────────────
# ANSI colours for terminal output
# ─────────────────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

passed = 0
failed = 0
cases  = []


def check(name: str, query: str, expected_enhanced: str, expect_changed: bool,
          latency_budget_ms: float = 50.0):
    """Run one enhancement test case and record result."""
    global passed, failed

    result = enhance_query(query)
    ok_text  = result.enhanced_query == expected_enhanced
    ok_flag  = result.query_changed  == expect_changed
    ok_orig  = result.original_query == query          # must never mutate original
    ok_lat   = result.latency_ms     <= latency_budget_ms

    all_ok = ok_text and ok_flag and ok_orig and ok_lat
    status = f"{GREEN}PASS{RESET}" if all_ok else f"{RED}FAIL{RESET}"
    if all_ok:
        passed += 1
    else:
        failed += 1

    cases.append({
        "name": name,
        "ok": all_ok,
        "query": query,
        "expected": expected_enhanced,
        "got": result.enhanced_query,
        "changed": result.query_changed,
        "expect_changed": expect_changed,
        "latency_ms": result.latency_ms,
        "corrections": result.corrections,
    })

    details = []
    if not ok_text:
        details.append(f"  expected : {expected_enhanced!r}")
        details.append(f"  got      : {result.enhanced_query!r}")
    if not ok_flag:
        details.append(f"  expect_changed={expect_changed}, got {result.query_changed}")
    if not ok_orig:
        details.append(f"  original_query mutated! got {result.original_query!r}")
    if not ok_lat:
        details.append(f"  latency {result.latency_ms:.1f}ms > budget {latency_budget_ms}ms")

    print(f"[{status}] {name}")
    for d in details:
        print(f"       {d}")


def check_pipeline_refusal(name: str, query: str):
    """Verify that a query still triggers the safety refusal after enhancement."""
    global passed, failed
    from src.reasoning.safety import evaluate_retrieval_safety, CONFIDENCE_THRESHOLD
    from src.Retrieval.query import retrieve_documents
    from src.reasoning.normalizer import normalize_query

    norm = normalize_query(query)
    result = enhance_query(norm)
    raw = retrieve_documents(result.enhanced_query, n_results=8)
    is_confident, top_score, _ = evaluate_retrieval_safety(raw, threshold=CONFIDENCE_THRESHOLD)

    refused = not is_confident
    if refused:
        passed += 1
        print(f"[{GREEN}PASS{RESET}] {name} — correctly refused (top_score={top_score:.3f})")
    else:
        failed += 1
        print(f"[{RED}FAIL{RESET}] {name} — expected refusal but got top_score={top_score:.3f}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1: Clean queries — must remain unchanged
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Clean Queries (no change expected) ──{RESET}")

check("clean: what is breast cancer",
      "what is breast cancer",
      "what is breast cancer",
      expect_changed=False)

check("clean: symptoms of breast cancer",
      "what are the symptoms of breast cancer",
      "what are the symptoms of breast cancer",
      expect_changed=False)

check("clean: types of breast cancer",
      "what are the types of breast cancer",
      "what are the types of breast cancer",
      expect_changed=False)

check("clean: screening guidelines",
      "what are the screening guidelines for mammography",
      "what are the screening guidelines for mammography",
      expect_changed=False)

check("clean: DCIS proper noun",
      "what is DCIS",
      "what is DCIS",
      expect_changed=False)

check("clean: out-of-domain clean",
      "what is a broken arm",
      "what is a broken arm",
      expect_changed=False)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2: Single-token typos
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Single Typo ──{RESET}")

check("single: brest cancer",
      "brest cancer",
      "breast cancer",
      expect_changed=True)

check("single: breast cancerr",
      "breast cancerr",
      "breast cancer",
      expect_changed=True)

check("single: symptons",
      "symptons",
      "symptoms",
      expect_changed=True)

check("single: pathogensis",
      "pathogensis",
      "pathogenesis",
      expect_changed=True)

check("single: mammografy",
      "mammografy",
      "mammography",
      expect_changed=True)

check("single: chemotherpy",
      "chemotherpy",
      "chemotherapy",
      expect_changed=True)

check("single: treatmnt",
      "treatmnt",
      "treatment",
      expect_changed=True)

check("single: diagnosiss",
      "diagnosiss",
      "diagnosis",
      expect_changed=True)

check("single: prognosiss",
      "prognosiss",
      "prognosis",
      expect_changed=True)

check("single: subtyps",
      "subtyps",
      "subtypes",
      expect_changed=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Multiple typos in one query
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Multiple Typos ──{RESET}")

check("multi: symptons of brest cancer",
      "what are the symptons of brest cancerr",
      "what are the symptoms of breast cancer",
      expect_changed=True)

check("multi: two clinical typos",
      "pathogensis and diagnosiss",
      "pathogenesis and diagnosis",
      expect_changed=True)

check("multi: mammografy and treatmnt",
      "mammografy and treatmnt",
      "mammography and treatment",
      expect_changed=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Transposition typos (fuzzy layer)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Transposition Typos (fuzzy layer) ──{RESET}")

check("transposition: whta is breast cancer",
      "whta is breast cancer",
      "what is breast cancer",
      expect_changed=True)

check("transposition: typse of breast cancer",
      "what are the typse of breast cancer",
      "what are the types of breast cancer",
      expect_changed=True)

check("transposition: symptmos",
      "symptmos of breast cancer",
      "symptoms of breast cancer",
      expect_changed=True)

check("transposition: brest cancer",
      "what is brest cancer",
      "what is breast cancer",
      expect_changed=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: Repeated characters (post-normalizer; enhancer receives clean text)
# Note: normalizer already collapses these, so enhancer should see clean tokens
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Repeated Characters (via normalizer→enhancer) ──{RESET}")

from src.reasoning.normalizer import normalize_query

def check_full_pipeline(name: str, raw_query: str, expected_enhanced: str, expect_changed: bool):
    """Normalise first, then enhance, and assert final output."""
    global passed, failed
    norm = normalize_query(raw_query)
    result = enhance_query(norm)

    ok = result.enhanced_query == expected_enhanced
    if ok:
        passed += 1
        print(f"[{GREEN}PASS{RESET}] {name}")
    else:
        failed += 1
        print(f"[{RED}FAIL{RESET}] {name}")
        print(f"       raw      : {raw_query!r}")
        print(f"       normalized: {norm!r}")
        print(f"       expected : {expected_enhanced!r}")
        print(f"       got      : {result.enhanced_query!r}")

check_full_pipeline(
    "repeated: whattt areee theeee typesssg of breaast cancerr",
    "whattt areee theeee typesssg of breaast cancerr",
    "what are the types of breast cancer",
    expect_changed=True,
)

check_full_pipeline(
    "repeated: breaast cancerr symptons",
    "breaast cancerr symptons",
    "breast cancer symptoms",
    expect_changed=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Medical terminology standalone
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Medical Terminology Standalone ──{RESET}")

for term_in, term_out in [
    ("pathogensis",    "pathogenesis"),
    ("diagnosiss",     "diagnosis"),
    ("mammografy",     "mammography"),
    ("chemotherpy",    "chemotherapy"),
    ("treatmnt",       "treatment"),
    ("prognossis",     "prognosis"),
    ("subtyps",        "subtypes"),
    ("tomosynthsis",   "tomosynthesis"),
    ("metastis",       "metastasis"),
    ("lumpectmy",      "lumpectomy"),
]:
    check(f"term: {term_in}", term_in, term_out, expect_changed=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 7: Multi-turn follow-up typos
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Multi-Turn Follow-Up Typos ──{RESET}")

# These short tokens should be corrected so the contextual resolver sees clean text
for raw, corrected in [
    ("typess",       "types"),
    ("pathogensis",  "pathogenesis"),
    ("treatmnt",     "treatment"),
    ("diagnosiss",   "diagnosis"),
]:
    check(f"multi-turn: {raw!r}", raw, corrected, expect_changed=True)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: Out-of-domain queries — must not be domain-shifted
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Out-of-Domain Queries (no domain shift allowed) ──{RESET}")

check("ood: broken arm clean",
      "what is a broken arm",
      "what is a broken arm",
      expect_changed=False)

check("ood: covid clean",
      "what is covid",
      "what is covid",
      expect_changed=False)

check("ood: car repair clean",
      "how do I fix my car",
      "how do I fix my car",
      expect_changed=False)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: OOD queries still trigger safety refusal (pipeline integration)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── OOD Refusal Invariant (pipeline integration) ──{RESET}")

check_pipeline_refusal("ood-refusal: broken arm",  "what is a broken arm")
check_pipeline_refusal("ood-refusal: covid",        "what is covid")
check_pipeline_refusal("ood-refusal: car repair",   "how do I fix my car")
check_pipeline_refusal("ood-refusal: bicycle tyre", "how do you repair a punctured bicycle tire tube")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: Safety invariant — CONFIDENCE_THRESHOLD unchanged
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Safety Threshold Invariant ──{RESET}")

from src.reasoning.safety import CONFIDENCE_THRESHOLD
if CONFIDENCE_THRESHOLD == 0.50:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] CONFIDENCE_THRESHOLD is 0.50 (unchanged)")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] CONFIDENCE_THRESHOLD changed to {CONFIDENCE_THRESHOLD}!")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11: Latency benchmark
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Latency Benchmark ──{RESET}")

LATENCY_QUERIES = [
    "what are the symptoms of breast cancer",
    "what are the symptons of brest cancerr",
    "pathogensis of breast cancer",
    "what is DCIS",
    "mammografy screening guidelines",
]

latencies = []
for q in LATENCY_QUERIES:
    r = enhance_query(q)
    latencies.append(r.latency_ms)

avg_lat = sum(latencies) / len(latencies)
max_lat = max(latencies)

print(f"  Average latency : {avg_lat:.2f} ms")
print(f"  Max latency     : {max_lat:.2f} ms")
print(f"  Per-query       : {[f'{l:.1f}ms' for l in latencies]}")

if max_lat <= 50.0:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] All queries < 50 ms budget")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Max latency {max_lat:.1f} ms exceeds 50 ms budget")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12: Correction metadata fields
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Correction Metadata Fields ──{RESET}")

r = enhance_query("symptons of brest cancerr")
meta_ok = (
    isinstance(r.corrections, list)
    and len(r.corrections) >= 2
    and all(hasattr(c, "original") and hasattr(c, "corrected") and hasattr(c, "confidence") for c in r.corrections)
    and r.enhancement_confidence > 0.0
    and r.original_query == "symptons of brest cancerr"
    and r.query_changed is True
)
if meta_ok:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] Correction metadata fields correct")
    for c in r.corrections:
        print(f"         {c.original!r:20s} → {c.corrected!r:20s}  conf={c.confidence:.3f}  method={c.method}")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Correction metadata fields incomplete or incorrect")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13: Meaning preservation — no info added/removed
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Meaning Preservation ──{RESET}")

# Must fix spelling only — no extra words injected
r = enhance_query("what are symptons of brest cancer")
words_in  = set(r.original_query.lower().split())
words_out = set(r.enhanced_query.lower().split())
added = words_out - words_in - {"symptoms", "breast"}  # corrections are expected
extra_added = added - {"symptoms", "breast"}            # anything truly new?

if not extra_added:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] No extra words injected by enhancer")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Unexpected words added: {extra_added}")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*60}")
print(f"{BOLD}Results: {GREEN}{passed}{RESET}{BOLD}/{total} passed, {RED}{failed}{RESET}{BOLD}/{total} failed{RESET}")
print(f"{'='*60}\n")

if failed:
    print(f"{RED}Some tests failed — see above for details.{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}All tests passed.{RESET}")
