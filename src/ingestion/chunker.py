import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ============================================================
# Utility functions (preserved from original engine)
# ============================================================


def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences while preserving common
    clinical abbreviations and decimal numbers reasonably well.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z0-9])",
        text.strip(),
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def split_paragraphs(text: str) -> List[str]:
    """
    Split cleaned document text into paragraphs.
    """

    return [
        paragraph.strip()
        for paragraph in text.split("\n\n")
        if paragraph.strip()
    ]


def build_sentence_overlap(
    previous_chunk: str,
    overlap_size: int,
) -> str:
    """
    Build overlap using complete sentences instead of
    arbitrary character positions.
    """

    sentences = split_sentences(previous_chunk)

    if not sentences:
        return ""

    overlap_sentences = []
    current_length = 0

    for sentence in reversed(sentences):

        sentence_length = len(sentence) + 1

        if current_length + sentence_length > overlap_size:
            break

        overlap_sentences.insert(0, sentence)
        current_length += sentence_length

    return " ".join(overlap_sentences)


# ============================================================
# Per-document configuration
# ============================================================


@dataclass
class DocumentConfig:
    """
    Per-document-type configuration that controls heading
    detection, header/footer stripping, section skipping,
    and line-level stripping.
    """

    doc_type: str
    heading_patterns: List[str] = field(default_factory=list)
    header_patterns: List[str] = field(default_factory=list)
    footer_patterns: List[str] = field(default_factory=list)
    skip_sections: List[str] = field(default_factory=list)
    strip_line_patterns: List[str] = field(
        default_factory=list
    )


DOCUMENT_CONFIGS = {
    # --------------------------------------------------------
    # AHRQ systematic evidence review (244 pages)
    # Chapter/KQ/Appendix structure; heavy running headers
    # --------------------------------------------------------
    "breast-cancer-screening-final-evidence-review": DocumentConfig(
        doc_type="government_evidence_report",
        heading_patterns=[
            r"^Structured Abstract\s*$",
            r"^Chapter \d+\.\s+.+",
            r"^Appendix [A-H][\.\s].+",
            r"^Table of Contents\s*$",
            r"^References\s*$",
            r"^Key Questions? and Analytic Framework",
            r"^Summary of Results",
            r"^Limitations",
            r"^Conclusions\s*$",
        ],
        header_patterns=[
            r"Breast Cancer Screening\s+\S+\s+Kaiser Permanente",
        ],
        footer_patterns=[],
        skip_sections=[
            r"^Appendix [D-G][\.\s]",
            r"^References$",
            r"^Table of Contents$",
        ],
    ),
    # --------------------------------------------------------
    # USPSTF/JAMA recommendation statement (13 pages)
    # Sentence-case inline headings; JAMA copyright footer
    # --------------------------------------------------------
    "breast-cancer-screening-final-rec": DocumentConfig(
        doc_type="screening_guideline",
        heading_patterns=[
            r"^Summary of Recommendations\s*$",
            r"^Preamble\s*$",
            r"^Importance\s*$",
            r"^Screening Modality\s*$",
            r"^Screening Interval\s*$",
            r"^Treatment or Intervention\s*$",
            r"^Disparities in Breast Cancer",
            r"^Suggestions for Practice",
            r"^Potential Preventable Burden",
            r"^Recommendations of Others",
            r"^ARTICLE INFORMATION\s*$",
            r"^REFERENCES\s*$",
        ],
        header_patterns=[],
        footer_patterns=[
            r"2024 American Medical Association",
            r"American Medical Association\.\s*All rights reserved",
        ],
        skip_sections=[
            r"^REFERENCES$",
            r"^ARTICLE INFORMATION$",
        ],
    ),
    # --------------------------------------------------------
    # Frontiers in Oncology review (32 pages)
    # Decimal-numbered sections; journal footer on every page
    # --------------------------------------------------------
    "Frntiers Breast Cancer": DocumentConfig(
        doc_type="general_review",
        heading_patterns=[
            r"^\d+(\.\d+)*\s+[A-Z]",
            r"^Glossary\s*$",
            r"^References\s*$",
            r"^Acknowledgments?\s*$",
        ],
        header_patterns=[
            r"^OPEN ACCESS$",
            r"^EDITED BY",
            r"^REVIEWED BY",
            r"^TYPE\s",
        ],
        footer_patterns=[
            r"Pasi et al\.",
            r"Frontiers in Oncology",
            r"frontiersin\.org",
        ],
        skip_sections=[
            r"^Glossary$",
            r"^References$",
            r"^Acknowledgments?$",
        ],
    ),
    # --------------------------------------------------------
    # Nature / Signal Transduction review (33 pages)
    # ALL-CAPS major headings; journal footer on every page
    # --------------------------------------------------------
    "Nature Review Breast cancer": DocumentConfig(
        doc_type="general_review",
        heading_patterns=[
            r"^INTRODUCTION\s*$",
            r"^EPIDEMIOLOGY AND RISK FACTORS",
            r"^PATHOPHYSIOLOGY AND MOLECULAR SUBTYPES",
            r"^MECHANISMS OF BREAST CANCER PROGRESSION",
            r"^DIAGNOSIS OF BREAST CANCER",
            r"^TREATMENT OF BREAST CANCER",
            r"^QUALITY OF LIFE AND LONG-TERM MANAGEMENT",
            r"^CONCLUSIONS AND PERSPECTIVES",
            r"^ACKNOWLEDGEMENTS\s*$",
            r"^AUTHOR CONTRIBUTIONS\s*$",
            r"^ADDITIONAL INFORMATION\s*$",
            r"^REFERENCES\s*$",
        ],
        header_patterns=[
            r"^REVIEW ARTICLE OPEN$",
        ],
        footer_patterns=[
            r"Signal Transduction and Targeted Therapy",
        ],
        skip_sections=[
            r"^REFERENCES$",
            r"^ACKNOWLEDGEMENTS$",
            r"^AUTHOR CONTRIBUTIONS$",
            r"^ADDITIONAL INFORMATION$",
        ],
    ),
    # --------------------------------------------------------
    # NCI/NIH patient & professional guide (65 pages)
    # Web-to-PDF export; question-style headings; no numbering
    # --------------------------------------------------------
    "NCINIH": DocumentConfig(
        doc_type="patient_guide",
        heading_patterns=[
            r"^What Is Breast Cancer\??$",
            r"^Types of Breast Cancer\s*$",
            r"^Breast Cancer Causes and Risk Factors",
            r"^Breast Cancer Screening\s*$",
            r"^Breast Cancer Stages\s*$",
            r"^Breast Cancer Treatment\s*$",
            r"^Breast Cancer Research\s*$",
            r"^Breast Cancer Clinical Trials",
            r"^Breast Cancer Research Results",
            r"^Breast Cancer Survivorship",
            r"^Molecular subtypes",
            r"^Personal health history",
            r"^Reproductive history\s*$",
            r"^Genetics and family history",
            r"^Lifestyle factors\s*$",
        ],
        header_patterns=[],
        footer_patterns=[],
        skip_sections=[],
        strip_line_patterns=[
            r"^Credit:\s*.+$",
            r"^On This Page\s*$",
            r"^Enlarge Image\s*$",
        ],
    ),
}


def get_config(source_filename: str) -> DocumentConfig:
    """Match a source filename to its document config."""

    for key, config in DOCUMENT_CONFIGS.items():
        if key in source_filename:
            return config

    # Fallback for unknown documents
    return DocumentConfig(doc_type="clinical")


# ============================================================
# Section detection helpers
# ============================================================


def _detect_heading_line(
    line_text: str,
    config: DocumentConfig,
) -> Optional[str]:
    """
    Check a single line against heading patterns.
    Returns the heading text if matched, None otherwise.
    """

    stripped = line_text.strip()

    if not stripped or len(stripped) > 150:
        return None

    for pattern in config.heading_patterns:
        if re.match(pattern, stripped):
            return stripped

    return None


def _split_at_headings(
    paragraph: str,
    config: DocumentConfig,
) -> List[tuple]:
    """
    Scan ALL lines of a paragraph for headings.
    When a heading is found mid-paragraph, split at that
    boundary. Returns [(text, heading_or_None), ...].
    """

    lines = paragraph.split("\n")
    segments = []
    current_lines = []
    current_heading = None

    for line in lines:
        detected = _detect_heading_line(line, config)

        if detected is not None:
            # Save lines accumulated before this heading
            if current_lines:
                text = "\n".join(current_lines).strip()
                if text:
                    segments.append(
                        (text, current_heading)
                    )
                current_lines = []
            current_heading = detected
            current_lines.append(line)
        else:
            current_lines.append(line)

    # Save final segment
    if current_lines:
        text = "\n".join(current_lines).strip()
        if text:
            segments.append((text, current_heading))

    return segments if segments else [(paragraph, None)]


def should_skip_section(
    section: str,
    config: DocumentConfig,
) -> bool:
    """Check if the current section should be skipped."""

    for pattern in config.skip_sections:
        if re.search(pattern, section, re.IGNORECASE):
            return True

    return False


def strip_lines(
    text: str,
    config: DocumentConfig,
) -> str:
    """
    Strip individual lines matching strip_line_patterns
    (image credits, 'On This Page' nav blocks, etc.).
    """

    if not config.strip_line_patterns:
        return text

    lines = text.split("\n")
    filtered = []

    for line in lines:
        stripped = line.strip()
        should_strip = False

        for pattern in config.strip_line_patterns:
            if re.match(pattern, stripped, re.IGNORECASE):
                should_strip = True
                break

        if not should_strip:
            filtered.append(line)

    return "\n".join(filtered)


# ============================================================
# Core chunking engine
# ============================================================

# Chunks shorter than this are discarded
MIN_CHUNK_LENGTH = 50


def chunk_document(
    pages: List[Dict],
    config: DocumentConfig,
    source: str,
    chunk_size: int = 1800,
    chunk_overlap: int = 250,
) -> List[Dict]:
    """
    Chunk a document into metadata-enriched chunks.

    Phases:
      1. Annotate paragraphs with section + page metadata
      2. Accumulate paragraphs into chunks, splitting on
         section boundaries and chunk_size limits
      3. Add sentence-level overlap (within same section)
      4. Attach full metadata to each chunk
    """

    # ---- Phase 1: Annotate paragraphs ----
    annotated = _annotate_paragraphs(pages, config)

    # ---- Phase 2: Build raw chunks ----
    raw_chunks = _build_raw_chunks(
        annotated, config, chunk_size
    )

    # ---- Phase 3: Add overlap (same-section only) ----
    overlapped = _add_overlap(raw_chunks, chunk_overlap)

    # ---- Phase 4: Build final output ----
    result = []
    chunk_idx = 0

    for chunk in overlapped:
        text = chunk["text"].strip()
        if len(text) < MIN_CHUNK_LENGTH:
            continue

        result.append(
            {
                "chunk_id": f"{source}_{chunk_idx}",
                "source": source,
                "doc_type": config.doc_type,
                "document_type": config.doc_type,
                "section": chunk["section"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "text": text,
            }
        )
        chunk_idx += 1

    return result


def _annotate_paragraphs(
    pages: List[Dict],
    config: DocumentConfig,
) -> List[Dict]:
    """
    Walk through pages, split into paragraphs, detect
    headings, skip unwanted sections, and return
    annotated paragraphs with section + page metadata.
    """

    annotated = []
    current_section = "unknown"
    skipping = False

    for page in pages:
        page_num = page["page_number"]
        text = page["text"]

        # Strip unwanted lines (credits, nav blocks)
        text = strip_lines(text, config)

        paragraphs = split_paragraphs(text)

        for para in paragraphs:
            if not para.strip():
                continue

            # Split paragraph at any heading boundaries
            segments = _split_at_headings(para, config)

            for seg_text, seg_heading in segments:
                if seg_heading:
                    current_section = seg_heading
                    skipping = should_skip_section(
                        current_section, config
                    )

                if skipping or not seg_text.strip():
                    continue

                annotated.append(
                    {
                        "text": seg_text,
                        "section": current_section,
                        "page": page_num,
                    }
                )

    return annotated


def _build_raw_chunks(
    annotated: List[Dict],
    config: DocumentConfig,
    chunk_size: int,
) -> List[Dict]:
    """
    Accumulate annotated paragraphs into chunks.
    Forces a chunk break on section boundaries.
    Falls back to sentence-aware splitting for
    paragraphs that exceed chunk_size.
    """

    raw_chunks = []
    chunk_text = ""
    chunk_section = None  # type: Optional[str]
    chunk_page_start = 0
    chunk_page_end = 0

    def _save_chunk():
        nonlocal chunk_text
        if chunk_text.strip():
            raw_chunks.append(
                {
                    "text": chunk_text.strip(),
                    "section": chunk_section,
                    "page_start": chunk_page_start,
                    "page_end": chunk_page_end,
                }
            )
        chunk_text = ""

    for ap in annotated:
        para_text = ap["text"]
        para_section = ap["section"]
        para_page = ap["page"]

        # Section boundary → finalize current chunk
        if (
            chunk_section is not None
            and para_section != chunk_section
            and chunk_text
        ):
            _save_chunk()

        # Initialize new chunk
        if not chunk_text:
            chunk_section = para_section
            chunk_page_start = para_page

        # Paragraph fits inside current chunk
        if (
            len(chunk_text) + len(para_text) + 2
            <= chunk_size
        ):
            if chunk_text:
                chunk_text += "\n\n" + para_text
            else:
                chunk_text = para_text
            chunk_page_end = para_page
            continue

        # Current chunk is full → save it
        _save_chunk()

        # Paragraph fits inside a new chunk
        if len(para_text) <= chunk_size:
            chunk_text = para_text
            chunk_section = para_section
            chunk_page_start = para_page
            chunk_page_end = para_page
            continue

        # Large paragraph → split into sentences
        sentences = split_sentences(para_text)
        chunk_text = ""
        chunk_section = para_section
        chunk_page_start = para_page

        for sentence in sentences:
            if (
                len(chunk_text) + len(sentence) + 1
                <= chunk_size
            ):
                if chunk_text:
                    chunk_text += " " + sentence
                else:
                    chunk_text = sentence
                chunk_page_end = para_page
            else:
                _save_chunk()
                chunk_text = sentence
                chunk_section = para_section
                chunk_page_start = para_page
                chunk_page_end = para_page

    # Save final chunk
    _save_chunk()

    return raw_chunks


def _add_overlap(
    raw_chunks: List[Dict],
    chunk_overlap: int,
) -> List[Dict]:
    """
    Add sentence-level overlap between consecutive chunks
    that belong to the same section. No overlap is added
    at section boundaries.
    """

    final = []

    for idx, chunk in enumerate(raw_chunks):
        if idx == 0:
            final.append(chunk)
            continue

        prev = raw_chunks[idx - 1]

        # Only add overlap within the same section
        if prev["section"] == chunk["section"]:
            overlap = build_sentence_overlap(
                prev["text"], chunk_overlap
            )
            if overlap:
                chunk_copy = dict(chunk)
                chunk_copy["text"] = (
                    overlap + "\n\n" + chunk["text"]
                )
                final.append(chunk_copy)
                continue

        final.append(chunk)

    return final


# ============================================================
# Public entry point
# ============================================================


def build_chunks(
    documents: List[Dict],
) -> List[Dict]:
    """
    Build chunks for all documents using per-document configs.

    documents: list of {source, pages: [{page_number, text}]}
    """

    all_chunks = []

    for document in documents:
        source = document["source"]
        pages = document["pages"]

        config = get_config(source)

        print(
            f"  Chunking: {source} "
            f"({len(pages)} pages, "
            f"type={config.doc_type})"
        )

        chunks = chunk_document(pages, config, source)

        all_chunks.extend(chunks)

        print(f"    -> {len(chunks)} chunks")

    return all_chunks