import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDED_DOCUMENTS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "embedded_documents.json"
)


from src.embeddings.generator import get_enriched_chunk_text


def build_embedded_documents(chunks, embeddings):
    """
    Combine chunks with their generated embeddings.
    """

    if len(chunks) != len(embeddings):
        raise ValueError(
            "Number of chunks must match number of embeddings."
        )

    embedded_documents = []

    for chunk, embedding in zip(chunks, embeddings):

        embedded_documents.append(
            {
                "chunk_id": chunk["chunk_id"],
                "source": chunk["source"],
                "document_type": chunk.get("document_type", "clinical"),
                "doc_type": chunk.get("doc_type", chunk.get("document_type", "clinical")),
                "section": chunk.get("section", "unknown"),
                "page_start": chunk.get("page_start", 0),
                "page_end": chunk.get("page_end", 0),
                "text": get_enriched_chunk_text(chunk),
                "embedding": embedding,
            }
        )

    return embedded_documents


def save_embedded_documents(
    documents,
    path=EMBEDDED_DOCUMENTS_PATH,
):
    """
    Save embedded documents to JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            documents,
            f,
            ensure_ascii=False,
        )

    print(
        f"Saved {len(documents)} embedded documents "
        f"to {path}"
    )