import json
from pathlib import Path

from src.ingestion.loader import load_documents
from src.ingestion.cleaner import clean_pages
from src.ingestion.chunker import build_chunks, get_config


OUTPUT_PATH = Path("data/processed/chunks.json")


def save_chunks(chunks, path=OUTPUT_PATH):
    """
    Save processed chunks to JSON.
    """

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            chunks,
            f,
            ensure_ascii=False,
            indent=2,
        )

    print(
        f"Saved {len(chunks)} chunks to {path}"
    )


def main():
    print("Starting document ingestion...")

    documents = load_documents()

    print(f"Loaded {len(documents)} documents")

    # Clean each document's pages using per-document config
    for document in documents:
        config = get_config(document["source"])
        document["pages"] = clean_pages(
            document["pages"],
            header_patterns=config.header_patterns
            or None,
            footer_patterns=config.footer_patterns
            or None,
        )
        print(
            f"  Cleaned: {document['source']} "
            f"({len(document['pages'])} pages)"
        )

    chunks = build_chunks(documents)

    print(f"\nGenerated {len(chunks)} total chunks")

    save_chunks(chunks)

    print("Document ingestion completed.")


if __name__ == "__main__":
    main()