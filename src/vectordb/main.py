from src.vectordb.indexer import index_documents
from src.vectordb.database import get_collection


def main():

    print("Starting ChromaDB indexing...")

    collection = index_documents()

    print(
        f"Total documents in ChromaDB: "
        f"{collection.count()}"
    )

    print("Vector database indexing completed.")


if __name__ == "__main__":
    main()