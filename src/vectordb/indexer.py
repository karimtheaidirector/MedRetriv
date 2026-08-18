import json
from pathlib import Path

from src.vectordb.database import get_collection, reset_collection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDED_DOCUMENTS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "embedded_documents.json"
)


def load_embedded_documents(
    path=EMBEDDED_DOCUMENTS_PATH,
):
    """
    Load embedded documents from JSON.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Embedded documents not found: {path}"
        )

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def index_documents(reset=True):
    """
    Index embedded clinical documents into ChromaDB.
    """

    documents = load_embedded_documents()

    if reset:
        collection = reset_collection()
    else:
        collection = get_collection()

    if not documents:
        print("No documents to index.")
        return collection

    ids = [
        document["chunk_id"]
        for document in documents
    ]

    texts = [
        document["text"]
        for document in documents
    ]

    embeddings = [
        document["embedding"]
        for document in documents
    ]

    metadatas = [
        {
            "source": document.get("source", ""),
            "document_type": document.get("document_type", "clinical"),
            "doc_type": document.get("doc_type", document.get("document_type", "clinical")),
            "section": document.get("section", "unknown"),
            "page_start": int(document.get("page_start", 0)),
            "page_end": int(document.get("page_end", 0)),
        }
        for document in documents
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(
        f"Indexed {len(documents)} documents "
        f"into ChromaDB."
    )

    return collection