# MedRetriv — Clinical RAG for Breast Cancer Screening & Decision Support

MedRetriv is an AI Clinical Decision Support (CDS) Retrieval-Augmented Generation (RAG) system specializing in breast cancer screening guidelines, clinical evidence synthesis, and disease pathophysiology. Built for the AI Clinical Decision Support Lite hackathon, MedRetriv transforms authoritative clinical guidelines and peer-reviewed oncology literature into an evidence-grounded conversational assistant with mandatory, verifiable inline citations.

---

## Key Capabilities & Highlights

* **5-Document Authoritative Corpus**: Covers both screening policy/trials and foundational disease definitions across 387 total pages (525 section-aware chunks).
* **Hard Citation Enforcement**: Every factual claim is bound to an exact inline citation `[Source: <filename>, Section: <section>, Page: <page>]`.
* **Pre-Generation Safety Gating**: Zero-hallucination defense using a cosine similarity threshold (`CONFIDENCE_THRESHOLD = 0.50`) that intercepts out-of-domain queries before calling the LLM.
* **Post-Generation Citation Verification**: Programmatic audit step checking every generated citation against retrieved context.
* **Lightweight Conversational Filter**: Handles greetings and assistant queries directly with near-zero latency while shielding clinical queries.
* **Full Audit Telemetry**: Every interaction is logged to `logs/query_log.jsonl` with distance metrics and citation verification metadata.

---

## Verified Evaluation Benchmark Metrics (Day 4)

Evaluated across a standardized 24-question benchmark suite spanning general definitional, screening-specific, and out-of-domain queries:

| Metric Name | Result | Target / Interpretation |
|:---|:---:|:---|
| **Retrieval Precision @ 3 (Overall)** | **89.5%** | $\ge 85.0\%$ (High clinical precision) |
| **Retrieval Precision @ 5 (Overall)** | **89.5%** | $\ge 80.0\%$ (High multi-document relevance) |
| **Retrieval Precision @ 5 (Screening Guidelines)** | **96.0%** | Grounded in USPSTF & AHRQ evidence |
| **Retrieval Precision @ 5 (General Definitional)** | **82.2%** | NCI patient guide & Nature/Frontiers prioritized |
| **Citation Compliance Rate** | **100.0%** | All answered queries contain inline citations |
| **Citation Accuracy (Grounding)** | **100.0%** | 100% of citations ground to retrieved chunks (0% hallucinated citations) |
| **Refusal Recall (Out-of-Domain)** | **100.0%** | 5/5 off-topic queries intercepted before LLM |
| **Refusal Precision (No False Refusals)** | **100.0%** | 0 false refusals on valid clinical questions |
| **In-Domain Top-1 Similarity** | **0.733 ± 0.064** | Range: $[0.574, 0.818]$ (Well above $0.50$) |
| **Out-of-Domain Top-1 Similarity** | **0.258 ± 0.020** | Range: $[0.109, 0.281]$ (Well below $0.50$) |
| **Average Retrieval Latency** | **22.2 ms** | $p95 = 21.4\text{ ms}$ (Real-time ChromaDB semantic search) |
| **Average Total Query Latency** | **22.4 ms** | $p95 = 21.8\text{ ms}$ (Includes safety check & generation) |

---

## System Architecture

```text
                                 Clinical PDFs (5 Documents / 387 Pages)
                                                    │
                                                    ▼
                             Ingestion Layer (Loader ──► Cleaner ──► Chunker)
                                                    │
                                                    ▼
                                            chunks.json (525 Chunks)
                                                    │
                                                    ▼
                             Embeddings (all-MiniLM-L6-v2, 384d Normalized)
                                                    │
                                                    ▼
                                       ChromaDB (Vector Store)
                                                    │
User Query ──► [ Conversational Filter ] ──► (if greeting) ──► Instant Response
                     │
                     ▼ (if clinical / general)
            Semantic Retrieval (Top-5 Chunks)
                     │
                     ▼
            [ Safety Gating: Top Similarity >= 0.50? ]
             ├── NO  ──► Pre-Generation Refusal ("I don't have enough information...")
             │
             └── YES ──► Build Grounded Prompt (Mandatory Inline Citations)
                               │
                               ▼
                         LLM Generation (gpt-oss-20b via HF Inference API)
                               │
                               ▼
                   [ Post-Gen Citation Verification ]
                               │
                               ▼
                   Log Telemetry (query_log.jsonl) ──► FastAPI ──► Streamlit UI
```

---

## Clinical Knowledge Base (5 Documents)

1. **AHRQ Comparative Effectiveness Review** (`breast-cancer-screening-final-evidence-review.pdf`, 244 pages, `government_evidence_report`): Detailed trial evidence on mammography intervals, mortality reduction, and screening harms.
2. **USPSTF Final Recommendation Statement** (`breast-cancer-screening-final-rec.pdf`, 13 pages, `screening_guideline`): Official recommendation for biennial screening for women aged 40–74.
3. **NCI / NIH Breast Cancer Overview** (`NCINIH – Breast Cancer Overview (Patient & Professional Versions).pdf`, 65 pages, `patient_guide`): Patient and clinician guides on anatomy, staging, symptoms, and disease overview.
4. **Nature STTT Review (2025)** (`Nature Review Breast cancer pathogenesis and treatments (2025).pdf`, 33 pages, `general_review`): Comprehensive molecular mechanisms, hormone receptors, and modern oncology therapies.
5. **Frontiers Oncology Review (2026)** (`Frntiers Breast Cancer pathogenesis, diagnosis and treatment (2026).pdf`, 32 pages, `general_review`): Staging, biomarkers, machine learning therapeutics, and pathogenesis pathways.

---

## Installation & Setup

### 1. Prerequisites & Environment Setup

Python 3.11+ is recommended. Install dependencies via `pip`:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
HF_TOKEN=your_huggingface_token
LLM_MODEL=openai/gpt-oss-20b:groq
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CONFIDENCE_THRESHOLD=0.50
```

> **Note**: If `HF_TOKEN` is unset, MedRetriv operates in local demonstration/evaluation mode with dynamic evidence synthesis directly grounded in the retrieved chunks.

---

## Usage Guide

### 1. Ingest Documents & Build Vector Database

Run the pipeline steps to process PDFs, compute embeddings, and build the ChromaDB vector database:

```bash
# 1. Chunk documents into section-aware chunks
python -m src.ingestion.main

# 2. Generate normalized vector embeddings
python -m src.embeddings.main

# 3. Index embeddings into ChromaDB
python -m src.vectordb.main
```

### 2. Run the Benchmark Evaluation Suite

Execute the 24-question benchmark evaluation and generate all metrics and figures:

```bash
python scripts/run_evaluation.py
```

* Evaluation Notebook: `notebooks/evaluation_report.ipynb`
* Summary Metrics CSV: `docs/evaluation_summary.csv`
* Visualizations: `docs/figures/`

### 3. Launch Application (FastAPI Backend + Streamlit UI)

**Terminal 1 — FastAPI Backend Server:**
```bash
uvicorn src.API.main:app --reload --port 8000
```
API Documentation available at: `http://127.0.0.1:8000/docs`

**Terminal 2 — Streamlit Research UI:**
```bash
streamlit run src/UI/app.py
```
UI available at: `http://localhost:8501`

---

## Project Structure

```text
MedRetriv/
├── .env.example
├── .gitignore
├── pyproject.toml
├── requirements.txt
├── README.md
│
├── archive/                                    # Historical audit artifacts
│   ├── RAG_Evaluation_Report.pdf
│   └── retrieval_spot_check_report.md
│
├── data/
│   ├── chroma/                                 # Active ChromaDB vector store (525 chunks)
│   ├── processed/
│   │   ├── chunks.json                         # 525 structured clinical chunks
│   │   └── embedded_documents.json             # 525 precomputed vector embeddings
│   └── raw/                                    # Exact 5-document authoritative corpus
│
├── docs/
│   ├── EVALUATION_LOG.md                       # Master Evaluation & Decision Log (Sections 1–7)
│   ├── evaluation_summary.csv                  # Exported Day 4 Benchmark Metrics Table
│   └── figures/                                # 7 Presentation-ready evaluation figures
│
├── logs/
│   └── query_log.jsonl                         # Structured JSONL audit telemetry log
│
├── notebooks/
│   └── evaluation_report.ipynb                 # Day 4 Evaluation Jupyter Notebook
│
├── scripts/
│   └── run_evaluation.py                       # Automated 24-question benchmark runner
│
└── src/
    ├── API/                                    # FastAPI service (/chat, /logs)
    │   └── main.py
    ├── embeddings/                             # SentenceTransformer embedding pipeline
    │   ├── builder.py
    │   ├── generator.py
    │   ├── loader.py
    │   └── main.py
    ├── ingestion/                              # Shared multi-document ingestion engine
    │   ├── chunker.py
    │   ├── cleaner.py
    │   ├── loader.py
    │   └── main.py
    ├── logging/                                # Telemetry logging module
    │   └── query_logger.py
    ├── reasoning/                              # Safety gating, prompt grounding & LLM inference
    │   ├── conversational.py                   # Lightweight conversational & greeting handler
    │   ├── llm.py                              # Hugging Face Inference API client
    │   ├── main.py                             # answer_question orchestrator
    │   ├── prompt.py                           # Mandatory inline citation prompt
    │   └── safety.py                           # Confidence gating & citation verification
    ├── Retrieval/                              # Vector search & context assembly
    │   ├── context.py
    │   ├── embedder.py
    │   ├── main.py
    │   └── query.py
    ├── UI/                                     # Streamlit clinical research dashboard
    │   └── app.py
    └── vectordb/                               # ChromaDB persistent client & indexer
        ├── database.py
        ├── indexer.py
        └── main.py
```

---

## Disclaimer

MedRetriv is an AI clinical decision support prototype designed for research and educational retrieval of clinical guidelines and medical literature related to breast cancer. It is **not** a diagnostic device and should not be used as a substitute for professional clinical judgment. Clinical screening and diagnostic decisions must be made by qualified healthcare professionals based on individual patient circumstances.
