from sentence_transformers import SentenceTransformer


MODEL_NAME = "all-MiniLM-L6-v2"

model = SentenceTransformer(MODEL_NAME)


def embed_query(query: str):
    embedding = model.encode(
        query,
        normalize_embeddings=True,
    )

    return embedding.tolist()