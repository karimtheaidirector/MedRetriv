def format_citation(metadata: dict) -> str:
    """
    Format citation string from chunk metadata.
    Example: [Source: breast-cancer-screening-final-rec.pdf, Section: Summary of Recommendations, Page: 2]
    If section is unknown, omit Section field.
    If page_start != page_end, format as Page: page_start-page_end.
    """
    source = metadata.get("source", "unknown")
    section = metadata.get("section", "unknown")
    page_start = metadata.get("page_start", 0)
    page_end = metadata.get("page_end", 0)

    if page_start == page_end or not page_end or page_end == 0:
        page_str = f"Page: {page_start}"
    else:
        page_str = f"Page: {page_start}-{page_end}"

    if section and section.strip() and section != "unknown":
        return f"[Source: {source}, Section: {section}, {page_str}]"
    else:
        return f"[Source: {source}, {page_str}]"


import re


def strip_retrieval_hints(text: str) -> str:
    """
    Strip system retrieval context prefixes so the LLM and synthesis only receive
    the genuine clinical document text.
    """
    if not text:
        return ""
    return re.sub(r"^\[Retrieval context:[^\]]+\]\s*", "", text, flags=re.DOTALL).strip()


def build_context(results: dict) -> str:
    """
    Build structured clinical evidence context from retrieval results.
    """
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    ids = results.get("ids", [[]])[0]

    context_parts = []

    for document_id, document, metadata in zip(ids, documents, metadatas):
        citation = format_citation(metadata)
        doc_type = metadata.get("doc_type", metadata.get("document_type", "clinical"))
        cleaned_doc = strip_retrieval_hints(document)

        context_parts.append(
            f"--- Evidence Chunk ({citation}) ---\n"
            f"Chunk ID: {document_id}\n"
            f"Document Type: {doc_type}\n"
            f"Required Citation: {citation}\n"
            f"Content:\n{cleaned_doc}"
        )

    return "\n\n---\n\n".join(context_parts)