"""
tests/test_query_enhancer.py

Comprehensive test suite for the Clinical Query Recovery System / Medical Autocorrect.

Covers:
  - Section 1: Clean Queries (Parity Invariant)
  - Section 2: Easy Typos (Single-token slips)
  - Section 3: Medium Typos (Transpositions & inverted chars)
  - Section 4: Hard Typo Corruptions (Multi-word slips, e.g. 'brst caser', 'tybesss of breasst cancerr')
  - Section 5: Very Hard Typos (Multi-word phonetic & vowel drop, e.g. 'wht r the symptons of brst cancr')
  - Section 6: Repeated Characters & Slips
  - Section 7: Medical Terminology Standalone
  - Section 8: Multi-Turn Follow-Up Stems
  - Section 9: Out-of-Domain Queries (Zero domain-shift & 100% refusal gating)
  - Section 10: False-Correction Protection (Random & non-medical words)
  - Section 11: Safety Threshold Invariant (CONFIDENCE_THRESHOLD == 0.50)
  - Section 12: Latency Benchmark (< 50 ms budget)
  - Section 13: Metadata & Multi-Representation Fields
  - Section 14: Meaning Preservation (Zero hallucinated token injection)

Run with:
    python -X utf8 scripts/test_query_enhancer.py
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

    result = enhance_query(query, validate_retrieval=False)
    ok_text  = result.enhanced_query.lower() == expected_enhanced.lower()
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
    """Verify that an out-of-domain query still triggers the safety refusal after enhancement."""
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
# SECTION 1: Clean queries — must remain unchanged (Parity Invariant)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 1: Clean Queries (Parity Invariant) ──{RESET}")

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
# SECTION 2: Easy Typos (Single-token keyboard slips)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 2: Easy Typos (Single-token slips) ──{RESET}")

check("easy: brest cancer",
      "brest cancer",
      "breast cancer",
      expect_changed=True)

check("easy: breast cancerr",
      "breast cancerr",
      "breast cancer",
      expect_changed=True)

check("easy: symptons",
      "symptons",
      "symptoms",
      expect_changed=True)

check("easy: pathogensis",
      "pathogensis",
      "pathogenesis",
      expect_changed=True)

check("easy: mammografy",
      "mammografy",
      "mammography",
      expect_changed=True)

check("easy: chemotherpy",
      "chemotherpy",
      "chemotherapy",
      expect_changed=True)

check("easy: treatmnt",
      "treatmnt",
      "treatment",
      expect_changed=True)

check("easy: diagnosiss",
      "diagnosiss",
      "diagnosis",
      expect_changed=True)

check("easy: prognosiss",
      "prognosiss",
      "prognosis",
      expect_changed=True)

check("easy: subtyps",
      "subtyps",
      "subtypes",
      expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3: Medium Typos (Transpositions & letter inversions)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 3: Medium Typos (Transpositions & Inversions) ──{RESET}")

check("medium: whta is breast cancer",
      "whta is breast cancer",
      "what is breast cancer",
      expect_changed=True)

check("medium: breats cancer",
      "breats cancer",
      "breast cancer",
      expect_changed=True)

check("medium: breast cnacer",
      "breast cnacer",
      "breast cancer",
      expect_changed=True)

check("medium: symtoms of breast cancer",
      "symtoms of breast cancer",
      "symptoms of breast cancer",
      expect_changed=True)

check("medium: typse of breast cancer",
      "what are the typse of breast cancer",
      "what are the types of breast cancer",
      expect_changed=True)

check("medium: symptmos",
      "symptmos of breast cancer",
      "symptoms of breast cancer",
      expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4: Hard Typo Corruptions (Multi-word severe corruptions)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 4: Hard Typo Corruptions (Multi-Word Slips) ──{RESET}")

check("hard: brst caser -> breast cancer",
      "brst caser",
      "breast cancer",
      expect_changed=True)

check("hard: bast caasre -> breast cancer",
      "bast caasre",
      "breast cancer",
      expect_changed=True)

check("hard: brest cancr -> breast cancer",
      "brest cancr",
      "breast cancer",
      expect_changed=True)

check("hard: tybesss of breasst cancerr -> types of breast cancer",
      "tybesss of breasst cancerr",
      "types of breast cancer",
      expect_changed=True)

check("hard: whta are the typse of brest cancr",
      "whta are the typse of brest cancr",
      "what are the types of breast cancer",
      expect_changed=True)

check("hard: symptons of brest cancr -> symptoms of breast cancer",
      "symptons of brest cancr",
      "symptoms of breast cancer",
      expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5: Very Hard Typos (Phonetic & severe vowel drops)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 5: Very Hard Typos (Phonetic & Vowel Drops) ──{RESET}")

check("vhard: what are the symptns of brest cance",
      "what are the symptns of brest cance",
      "what are the symptoms of breast cancer",
      expect_changed=True)

check("vhard: wht r the symptons of brst cancr",
      "wht r the symptons of brst cancr",
      "what are the symptoms of breast cancer",
      expect_changed=True)

check("vhard: whattt r the typess of brest caancer",
      "whattt r the typess of brest caancer",
      "what are the types of breast cancer",
      expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6: Repeated characters & normalizer pipeline integration
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 6: Repeated Characters & Normalizer Integration ──{RESET}")

from src.reasoning.normalizer import normalize_query

def check_full_pipeline(name: str, raw_query: str, expected_enhanced: str, expect_changed: bool):
    global passed, failed
    norm = normalize_query(raw_query)
    result = enhance_query(norm, validate_retrieval=False)

    ok = result.enhanced_query.lower() == expected_enhanced.lower()
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
# SECTION 7: Medical Terminology Standalone
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 7: Medical Terminology Standalone ──{RESET}")

for term_in, term_out in [
    ("pathogensis",    "pathogenesis"),
    ("diagnosiss",     "diagnosis"),
    ("mammografy",     "mammography"),
    ("chemotherpy",    "chemotherapy"),
    ("treatmnt",       "treatment"),
    ("tretmnt",        "treatment"),
    ("prognossis",     "prognosis"),
    ("subtyps",        "subtypes"),
    ("tomosynthsis",   "tomosynthesis"),
    ("metastis",       "metastasis"),
    ("lumpectmy",      "lumpectomy"),
    ("mastectmy",      "mastectomy"),
]:
    check(f"term: {term_in}", term_in, term_out, expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 8: Multi-Turn Follow-Up Typos
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 8: Multi-Turn Follow-Up Stems ──{RESET}")

for raw, corrected in [
    ("typess",       "types"),
    ("pathogensis",  "pathogenesis"),
    ("treatmnt",     "treatment"),
    ("tretmnt",      "treatment"),
    ("diagnosiss",   "diagnosis"),
    ("symptons",     "symptoms"),
]:
    check(f"multi-turn: {raw!r}", raw, corrected, expect_changed=True)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 9: Out-of-Domain Queries (Zero domain-shift & refusal safety)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 9: Out-of-Domain Queries (Zero Domain Shift) ──{RESET}")

check("ood: broken armmm -> broken arm",
      "what is a broken armmm",
      "what is a broken arm",
      expect_changed=True)

check("ood: car engien -> car engine",
      "how do I fix my car engien",
      "how do I fix my car engine",
      expect_changed=True)

check("ood: covid symptons -> covid symptoms",
      "what are the symptons of covid",
      "what are the symptoms of covid",
      expect_changed=True)

check("ood: weather tomorow -> weather tomorrow",
      "what is the weather tomorow",
      "what is the weather tomorrow",
      expect_changed=True)

print(f"\n{BOLD}{CYAN}── Section 9b: OOD Pipeline Refusal Safety Verification ──{RESET}")
check_pipeline_refusal("ood-refusal: broken armmm",  "what is a broken armmm")
check_pipeline_refusal("ood-refusal: car engien",    "how do I fix my car engien")
check_pipeline_refusal("ood-refusal: covid symptons","what are the symptons of covid")
check_pipeline_refusal("ood-refusal: bicycle tyre",  "how do you repair a punctured bicycle tire tube")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 10: False-Correction Protection (Random & Unrelated Words)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 10: False-Correction Protection (Random Words) ──{RESET}")

check("false-corr: randomword unaltered",
      "randomword",
      "randomword",
      expect_changed=False)

check("false-corr: xyzabc unaltered",
      "xyzabc",
      "xyzabc",
      expect_changed=False)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 11: Safety Threshold Invariant
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 11: Safety Threshold Invariant ──{RESET}")

from src.reasoning.safety import CONFIDENCE_THRESHOLD
if CONFIDENCE_THRESHOLD == 0.50:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] CONFIDENCE_THRESHOLD is 0.50 (strictly unchanged)")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] CONFIDENCE_THRESHOLD changed to {CONFIDENCE_THRESHOLD}!")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 12: Latency Benchmark
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 12: Latency Benchmark ──{RESET}")

LATENCY_QUERIES = [
    "what are the symptoms of breast cancer",
    "brst caser",
    "tybesss of breasst cancerr",
    "wht r the symptons of brst cancr",
    "what is DCIS",
]

latencies = []
for q in LATENCY_QUERIES:
    r = enhance_query(q, validate_retrieval=False)
    latencies.append(r.latency_ms)

avg_lat = sum(latencies) / len(latencies)
max_lat = max(latencies)

print(f"  Average standalone latency : {avg_lat:.2f} ms")
print(f"  Max standalone latency     : {max_lat:.2f} ms")
print(f"  Per-query latencies        : {[f'{l:.2f}ms' for l in latencies]}")

if max_lat <= 50.0:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] Standalone latency < 50 ms budget")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Max latency {max_lat:.1f} ms exceeds 50 ms budget")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 13: Correction Metadata Fields & Multi-Representation
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 13: Correction Metadata Fields & Multi-Representation ──{RESET}")

r = enhance_query("brst caser", validate_retrieval=False)
meta_ok = (
    isinstance(r.corrections, list)
    and len(r.corrections) >= 1
    and all(hasattr(c, "original") and hasattr(c, "corrected") and hasattr(c, "confidence") for c in r.corrections)
    and r.enhancement_confidence > 0.0
    and r.original_query == "brst caser"
    and r.enhanced_query == "breast cancer"
    and r.query_changed is True
    and hasattr(r, "candidates")
    and hasattr(r, "candidate_scores")
)
if meta_ok:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] Multi-representation metadata fields correct")
    for c in r.corrections:
        print(f"         {c.original!r:20s} → {c.corrected!r:20s}  conf={c.confidence:.3f}  method={c.method}")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Multi-representation metadata fields incomplete or incorrect")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 14: Meaning Preservation (Zero hallucinated token injection)
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 14: Meaning Preservation ──{RESET}")

r = enhance_query("what are symptons of brest cancer", validate_retrieval=False)
words_in  = set(r.original_query.lower().split())
words_out = set(r.enhanced_query.lower().split())
added = words_out - words_in - {"symptoms", "breast"}

if not added:
    passed += 1
    print(f"[{GREEN}PASS{RESET}] No extra/hallucinated words injected by recovery engine")
else:
    failed += 1
    print(f"[{RED}FAIL{RESET}] Unexpected words added: {added}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 15: In-Place Intent Substitution & Positional Alignment
# ─────────────────────────────────────────────────────────────────────────────
print(f"\n{BOLD}{CYAN}── Section 15: In-Place Intent Substitution & Positional Alignment ──{RESET}")

check("inplace: breast canser typs",
      "breast canser typs",
      "breast cancer types",
      expect_changed=True)

check("inplace: breast cancer symptns",
      "breast cancer symptns",
      "breast cancer symptoms",
      expect_changed=True)

check("inplace: breast cancer trtmnt",
      "breast cancer trtmnt",
      "breast cancer treatment",
      expect_changed=True)

check("inplace: breast cancer diagnosiss",
      "breast cancer diagnosiss",
      "breast cancer diagnosis",
      expect_changed=True)

check("inplace: breast cancer pathogensis",
      "breast cancer pathogensis",
      "breast cancer pathogenesis",
      expect_changed=True)

check("inplace: what are the symptons of brest cancer",
      "what are the symptons of brest cancer",
      "what are the symptoms of breast cancer",
      expect_changed=True)

# Test that intent tokens are NEVER duplicated
dup_test_cases = [
    ("breast cancer typs", "breast cancer types"),
    ("breast cancer symptons", "breast cancer symptoms"),
    ("breast canser trtmnt", "breast cancer treatment"),
]

for raw_q, exp_q in dup_test_cases:
    r = enhance_query(raw_q, validate_retrieval=False)
    toks = r.enhanced_query.lower().split()
    # Check no consecutive duplicates
    has_consecutive_dup = any(toks[i] == toks[i+1] for i in range(len(toks)-1))
    if r.enhanced_query.lower() == exp_q.lower() and not has_consecutive_dup:
        passed += 1
        print(f"[{GREEN}PASS{RESET}] no-dup: {raw_q!r} -> {r.enhanced_query!r}")
    else:
        failed += 1
        print(f"[{RED}FAIL{RESET}] duplication detected: {raw_q!r} -> {r.enhanced_query!r}")

# Test intent non-invention (never inject intent terms where none was present)
check("non-invention: generic breast cancer",
      "breast cancer",
      "breast cancer",
      expect_changed=False)

check("non-invention: definitional what is breast cancer",
      "what is breast cancer",
      "what is breast cancer",
      expect_changed=False)
total = passed + failed
print(f"\n{'='*60}")
print(f"{BOLD}Results: {GREEN}{passed}{RESET}{BOLD}/{total} passed, {RED}{failed}{RESET}{BOLD}/{total} failed{RESET}")
print(f"{'='*60}\n")

if failed:
    print(f"{RED}Some tests failed — see above for details.{RESET}")
    sys.exit(1)
else:
    print(f"{GREEN}All tests passed.{RESET}")
