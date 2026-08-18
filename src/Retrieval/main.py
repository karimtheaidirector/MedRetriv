from src.Retrieval.query import retrieve_documents
from src.Retrieval.context import build_context


def retrieve_context(query: str, n_results=3):
    results = retrieve_documents(
        query,
        n_results=n_results,
    )

    context = build_context(results)

    return context


def main():
    query = input("Ask a question: ")

    context = retrieve_context(query)

    print("\nRetrieved Context:\n")
    print(context)


if __name__ == "__main__":
    main()