# INSTANT — Clinical RAG for Breast Cancer Screening

INSTANT is a Clinical Retrieval-Augmented Generation (RAG) prototype that retrieves and reasons over trusted clinical evidence related to breast cancer screening. It turns clinical PDF documents into searchable vector representations, retrieves the evidence relevant to a clinical question, and uses an LLM to generate an answer grounded in that evidence.

**Status:** Core pipeline (ingestion → retrieval → reasoning → API → UI) is complete. Evaluation, persistent chat storage, and advanced retrieval features are in progress — see [Roadmap](#roadmap).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup](#setup)
- [Usage](#usage)
  - [1. Document Ingestion](#1-document-ingestion)
  - [2. Embedding Generation](#2-embedding-generation)
  - [3. Vector Database](#3-vector-database)
  - [4. Retrieval](#4-retrieval)
  - [5. AI Reasoning](#5-ai-reasoning)
  - [6. Running the Full App (API + UI)](#6-running-the-full-app-api--ui)
- [Example](#example)
- [Project Structure](#project-structure)
- [Design Principles](#design-principles)
- [Roadmap](#roadmap)
- [Disclaimer](#disclaimer)

---

## Overview

The current prototype uses two clinical documents as its initial knowledge base:

- AHRQ Comparative Effectiveness Review for Breast Cancer Screening
- USPSTF Breast Cancer Screening Recommendation Statement

The knowledge base can be expanded with additional trusted guidelines (ACS, ACR, SBI, ACOG, NCI, etc.) without changing the core architecture.

**Design principles**

| Principle | What it means |
|---|---|
| Evidence grounding | The LLM answers from retrieved evidence, not unsupported knowledge |
| Source awareness | Every chunk keeps its source document, so answers stay traceable |
| Modular pipeline | Ingestion, embeddings, vector storage, retrieval, reasoning, API, and UI are independent modules |
| Reproducibility | Intermediate artifacts (chunks, embeddings) are persisted so any stage can be inspected or rerun |
| Expandability | New clinical documents can be added without redesigning the pipeline |

---

## Architecture

```text
Clinical PDFs
     │
     ▼
Ingestion (load → clean → chunk)  ──►  chunks.json
     │
     ▼
Embeddings (Sentence Transformers)  ──►  embedded_documents.json
     │
     ▼
ChromaDB (persistent vector store)
     │
     ▼
User question ──► Retrieval (semantic search, top-K)
     │
     ▼
Retrieved clinical context
     │
     ▼
Reasoning (LLM: GPT-OSS 20B via Hugging Face)
     │
     ▼
Grounded clinical answer
     │
     ▼
FastAPI backend  ──►  Streamlit UI
```

---

## Setup

### 1. Install dependencies

```bash
uv pip install -r requirements.txt
# or
uv sync
```

### 2. Configure environment variables

Create a `.env` file in the project root:

```env
HF_TOKEN=your_huggingface_token
LLM_MODEL=openai/gpt-oss-20b:groq
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

The Hugging Face token is required for LLM inference. **Do not commit `.env` to GitHub.**

---

## Usage

Clinical PDFs live in `data/raw/`. Run the pipeline stages in order the first time you set up the project.

### 1. Document Ingestion

Loads the PDFs, extracts and cleans text, and splits it into retrievable chunks. Chunking preserves clinical context by splitting on paragraphs, falling back to sentence-aware splitting for large paragraphs, avoiding arbitrary word-level cuts, and keeping sentence-level overlap between neighboring chunks.

```bash
uv run python -m src.ingestion.main
```

Output: `data/processed/chunks.json`

```json
{
  "chunk_id": "document_0",
  "source": "document.pdf",
  "text": "Clinical evidence...",
  "document_type": "clinical"
}
```

### 2. Embedding Generation

Converts chunks into vector embeddings using `sentence-transformers/all-MiniLM-L6-v2`.

```bash
uv run python -m src.embeddings.main
```

Output: `data/processed/embedded_documents.json` (chunk ID, source, document type, text, and embedding vector).

### 3. Vector Database

Loads the embeddings into a persistent ChromaDB collection, supporting semantic similarity search, top-K retrieval, metadata, and source tracking.

```bash
uv run python -m src.vectordb.main
```

Storage: `data/chroma/`

### 4. Retrieval

Embeds a clinical question with the same Sentence Transformer model and searches ChromaDB for the most relevant evidence.

```bash
uv run python -m src.Retrieval.main
```

```text
Ask a question:
What age should women start breast cancer screening?
```

Each result includes document type, chunk ID, source document, and clinical content:

```text
[CLINICAL]
ID: breast-cancer-screening-final-rec_35
Source: breast-cancer-screening-final-rec.pdf
Content: ...
```

### 5. AI Reasoning

Sends the question and retrieved context to the LLM (`openai/gpt-oss-20b:groq` via the Hugging Face Inference API).

```bash
uv run python -m src.reasoning.main
```

The reasoning prompt instructs the model to:

- Use only the provided clinical context for clinical facts
- Avoid inventing medical information
- Preserve important clinical qualifiers
- Distinguish recommendations from different organizations
- State when the provided evidence is insufficient
- Identify relevant source documents
- Avoid diagnosis and personalized medical advice

### 6. Running the Full App (API + UI)

**Terminal 1 — FastAPI backend**

```bash
uv run uvicorn src.API.main:app --reload
```

Runs at `http://127.0.0.1:8000` (docs at `/docs`).

| Endpoint | Description |
|---|---|
| `GET /` | Health check → `{"message": "INSTANT API is running"}` |
| `POST /chat` | Accepts a question and optional history; runs retrieval → context construction → LLM reasoning → returns the answer |

`POST /chat` request:

```json
{
  "question": "What age should women start breast cancer screening?",
  "history": []
}
```

`POST /chat` response:

```json
{
  "question": "What age should women start breast cancer screening?",
  "answer": "..."
}
```

Conversation history can be passed in so the assistant can resolve follow-up questions.

**Terminal 2 — Streamlit UI**

```bash
uv run streamlit run src/UI/app.py
```

Talks to `http://127.0.0.1:8000/chat`. Provides a chat-style interface, "New Chat", multiple sessions per Streamlit session, history passed to the API, and a loading state while evidence is retrieved.

---

## Example

**Question:** *What age should women start breast cancer screening?*

Retrieval may surface the USPSTF recommendation (ages 40–74) alongside guidance from other organizations. The LLM distinguishes between them rather than merging them into one universal answer:

```text
USPSTF:  Screen women aged 40–74 with mammography every 2 years.
ACS:     Regular mammography starting at 45, with the option to begin at 40–44.
ACOG:    Offer screening starting at 40, using shared decision-making.
ACR/SBI: Annual screening starting at 40 for average-risk women.
```

---

## Project Structure

```text
INSTANT/
├── data/
│   ├── raw/                        # clinical PDF documents
│   ├── processed/
│   │   ├── chunks.json
│   │   └── embedded_documents.json
│   └── chroma/                     # persistent ChromaDB storage
│
├── src/
│   ├── ingestion/     # loader.py, cleaner.py, chunker.py, main.py
│   ├── embeddings/    # loader.py, generator.py, builder.py, main.py
│   ├── vectordb/      # database.py, indexer.py, main.py
│   ├── Retrieval/     # embedder.py, query.py, context.py, main.py
│   ├── Reasoning/      # llm.py, prompt.py, main.py
│   ├── API/            # main.py
│   └── UI/             # app.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Roadmap

- [x] Document loading
- [x] Text cleaning
- [x] Clinical chunking
- [x] Embedding generation
- [x] ChromaDB vector database
- [x] Semantic retrieval
- [x] AI reasoning
- [x] FastAPI backend
- [x] Streamlit UI
- [ ] Evaluation & optimization
- [ ] Persistent chat storage
- [ ] Advanced RAG features:
  - Evidence-level citations linking claims to source chunks
  - Structured guideline comparison across organizations
  - Contradiction detection between clinical sources
  - Hybrid retrieval (semantic + keyword) for terminology, abbreviations, and numbers
  - Retrieval reranking over a larger candidate set
  - Query rewriting for ambiguous follow-up questions
  - Expanded trusted clinical sources

---

## Disclaimer

INSTANT is a prototype for retrieving and synthesizing clinical evidence related to breast cancer screening. It is **not** a medical diagnostic system and should not substitute for professional medical judgment. Clinical decisions should be made by qualified healthcare professionals using appropriate guidelines, patient history, risk factors, and individual circumstances.
