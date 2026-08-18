from src.Retrieval.embedder import embed_query
from src.vectordb.database import get_collection


def retrieve_documents(query: str, n_results=3):
    query_embedding = embed_query(query)

    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    return results