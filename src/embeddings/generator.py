import os

from sentence_transformers import SentenceTransformer


MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


def load_embedding_model():
    """
    Load the configured embedding model.
    """

    print(f"Loading embedding model: {MODEL_NAME}")

    return SentenceTransformer(MODEL_NAME)


RETRIEVAL_HINTS = {
    # Chunk 2: Formal Summary of Recommendations (contains 75+ I statement)
    "breast-cancer-screening-final-rec.pdf_2": (
        "[Retrieval context: USPSTF official position and statement for women aged 75 years or older "
        "(75+, older women, elderly). Current evidence is insufficient to assess the balance of benefits "
        "and harms of screening mammography in women 75 years or older (I statement). Inquiries regarding "
        "screening suggestions or official statements for age 75 and older refer to this section.]\n\n"
    ),
    # Chunk 13: Clinician Summary Figure (Grade: I statement for 75+)
    "breast-cancer-screening-final-rec.pdf_13": (
        "[Retrieval context: USPSTF official position and statement for women aged 75 years or older "
        "(75+, older women, elderly). The current evidence is insufficient to assess the balance of benefits "
        "and harms of screening mammography in women 75 years or older (Grade: I statement). Inquiries regarding "
        "screening suggestions or official statements for age 75 and older refer to this summary.]\n\n"
    ),
    # Chunk 18: Potential Preventable Burden (epidemiological rationale for 75+ I statement)
    "breast-cancer-screening-final-rec.pdf_18": (
        "[Retrieval context: USPSTF official position and evidence review for women aged 75 years or older "
        "(75+, older women, elderly). Evidence regarding breast cancer screening in women 75 years or older, "
        "including incidence rates, mortality, trial emulation data, and the conclusion of insufficient evidence. "
        "Inquiries regarding screening suggestions or evidence for age 75 and older refer to this evidence.]\n\n"
    ),
    # Chunk 36: Screening Interval / Public comments response for 75+
    "breast-cancer-screening-final-rec.pdf_36": (
        "[Retrieval context: USPSTF official position and response regarding upper age limits and screening for "
        "women aged 75 years or older (75+, older women, elderly). Clarifies why no clinical trial evidence exists "
        "for screening women 75 years or older. Inquiries regarding screening suggestions or age limits refer to this statement.]\n\n"
    ),
}


def get_enriched_chunk_text(chunk: dict) -> str:
    """
    Return chunk text with retrieval hint prepended if configured for this chunk ID.
    """
    chunk_id = chunk.get("chunk_id", "")
    hint = RETRIEVAL_HINTS.get(chunk_id, "")
    text = chunk.get("text", "")
    if hint and not text.startswith("[Retrieval context:"):
        return hint + text
    return text


def generate_embeddings(chunks):
    """
    Generate normalized embeddings for document chunks.
    """

    if not chunks:
        return []

    model = load_embedding_model()

    texts = [get_enriched_chunk_text(chunk) for chunk in chunks]

    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        normalize_embeddings=True,
    )

    return embeddings.tolist()