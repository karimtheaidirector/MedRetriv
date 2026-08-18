import chromadb
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "chroma"


def get_client():
    """
    Return a persistent ChromaDB client.
    """

    DB_PATH.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(
        path=str(DB_PATH)
    )


def get_collection(
    collection_name="clinical_documents",
):
    """
    Get or create the clinical documents collection.
    """

    client = get_client()

    return client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Clinical breast cancer screening knowledge base"
        },
    )


def reset_collection(
    collection_name="clinical_documents",
):
    """
    Delete existing collection if it exists, and create a fresh one.
    """
    client = get_client()
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    return get_collection(collection_name)