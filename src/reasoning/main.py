from src.Retrieval.query import retrieve_documents
from src.Retrieval.context import build_context
from src.reasoning.prompt import build_prompt, STANDARD_REFUSAL_MESSAGE
from src.reasoning.llm import generate_response
from src.reasoning.safety import evaluate_retrieval_safety, CONFIDENCE_THRESHOLD
from src.logging.query_logger import log_query


def answer_question(
    question: str,
    history: list = None,
    n_results: int = 5,
    threshold: float = CONFIDENCE_THRESHOLD,
) -> dict:
    """
    Retrieve clinical evidence, apply pre-generation safety threshold,
    generate a citation-grounded answer, and log the full query end-to-end.
    """
    # 0. Normalize query typos (mitigate repeated characters, casual spelling, keyboard slips)
    from src.reasoning.normalizer import normalize_query
    normalized_q = normalize_query(question)

    # 1. Check for conversational greetings, courtesy, or meta-assistant questions
    from src.reasoning.conversational import detect_conversational_query
    conv = detect_conversational_query(normalized_q, history=history)
    if conv:
        log_query(
            question=question,
            retrieved_chunks=[],
            confidence_met=True,
            top_score=1.0,
            final_answer=conv["response"],
            refused=False,
            extra_metadata={"query_type": "conversational", "intent": conv["intent"], "normalized_query": normalized_q},
        )
        return {
            "question": question,
            "answer": conv["response"],
            "refused": False,
            "confidence_met": True,
            "top_score": 1.0,
            "retrieved_chunks": [],
            "query_type": "conversational",
        }

    # 2. Contextual follow-up resolution (enrich short follow-ups with prior turn anchor)
    from src.reasoning.contextual import resolve_contextual_query
    resolved_q = resolve_contextual_query(normalized_q, history=history) if history else normalized_q

    # 3. Retrieve clinical evidence chunks
    results = retrieve_documents(
        resolved_q,
        n_results=n_results,
    )

    # 2. Evaluate retrieval safety & confidence threshold
    is_confident, top_score, chunk_records = evaluate_retrieval_safety(
        results,
        threshold=threshold,
    )

    # 3. Pre-generation refusal if evidence similarity is below threshold
    if not is_confident:
        final_answer = STANDARD_REFUSAL_MESSAGE
        refused = True

        log_query(
            question=question,
            retrieved_chunks=chunk_records,
            confidence_met=False,
            top_score=top_score,
            final_answer=final_answer,
            refused=refused,
        )

        return {
            "question": question,
            "answer": final_answer,
            "refused": refused,
            "confidence_met": False,
            "top_score": top_score,
            "retrieved_chunks": chunk_records,
        }

    # 4. Build evidence context with citation metadata
    context = build_context(results)

    # 5. Build prompt with hard citation enforcement
    prompt = build_prompt(
        question=question,
        context=context,
    )

    # 6. Generate answer via LLM (returns tuple: answer_text, generation_mode)
    final_answer, generation_mode = generate_response(prompt)

    # 7. Check if model produced a refusal
    refused = STANDARD_REFUSAL_MESSAGE.lower() in final_answer.lower()

    # 8. Post-generation citation verification step
    from src.reasoning.safety import verify_citations
    cit_verification = verify_citations(final_answer, chunk_records)

    # 9. Log the complete query execution with verification telemetry
    fallback_triggered = generation_mode in ["fallback_synthesis", "offline_synthesis"]
    log_query(
        question=question,
        retrieved_chunks=chunk_records,
        confidence_met=True,
        top_score=top_score,
        final_answer=final_answer,
        refused=refused,
        extra_metadata={
            "citation_verification": cit_verification,
            "flagged_for_review": cit_verification.get("flagged_for_review", False),
            "generation_mode": generation_mode,
            "fallback_triggered": fallback_triggered,
        }
    )

    return {
        "question": question,
        "answer": final_answer,
        "refused": refused,
        "confidence_met": True,
        "top_score": top_score,
        "retrieved_chunks": chunk_records,
        "citation_verification": cit_verification,
        "generation_mode": generation_mode,
        "fallback_triggered": fallback_triggered,
    }


def main():
    question = input("Ask a clinical question: ")
    result = answer_question(question)
    print("\n" + "=" * 60)
    print("Answer:")
    print("=" * 60)
    print(result["answer"])
    print(f"\n[Status] Confidence Met: {result['confidence_met']} | Refused: {result['refused']} | Top Score: {result['top_score']}")


if __name__ == "__main__":
    main()