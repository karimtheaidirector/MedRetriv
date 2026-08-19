from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.Retrieval.query import retrieve_documents
from src.Retrieval.context import build_context
from src.reasoning.prompt import build_prompt, STANDARD_REFUSAL_MESSAGE
from src.reasoning.llm import generate_response
from src.reasoning.safety import evaluate_retrieval_safety, CONFIDENCE_THRESHOLD
from src.logging.query_logger import log_query, get_logged_queries


app = FastAPI(
    title="MedRetriv API",
    description="Clinical Retrieval-Augmented Generation API with Safety Verification and Citation Enforcement",
    version="1.0.0",
)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = Field(default_factory=list)


@app.post("/chat")
def chat(request: ChatRequest):
    history_dicts = [{"role": m.role, "content": m.content} for m in request.history]

    # 0. Normalize query typos (mitigate repeated chars, casual spelling, keyboard slips)
    from src.reasoning.normalizer import normalize_query
    normalized_q = normalize_query(request.question)

    # 1. Check for conversational greetings, courtesy, or meta-assistant questions
    from src.reasoning.conversational import detect_conversational_query
    conv = detect_conversational_query(normalized_q, history=history_dicts)
    if conv:
        log_query(
            question=request.question,
            retrieved_chunks=[],
            confidence_met=True,
            top_score=1.0,
            final_answer=conv["response"],
            refused=False,
            extra_metadata={
                "source": "api_chat",
                "query_type": "conversational",
                "intent": conv["intent"],
                "normalized_query": normalized_q,
            },
        )
        return {
            "question": request.question,
            "answer": conv["response"],
            "refused": False,
            "confidence_met": True,
            "top_score": 1.0,
            "citations": [],
            "retrieved_chunks": [],
            "query_type": "conversational",
        }

    # 2. Contextual follow-up and clinical consultation resolution
    from src.reasoning.contextual import resolve_contextual_query
    resolved_q = resolve_contextual_query(normalized_q, history=history_dicts)

    # 3. Retrieve relevant clinical evidence
    results = retrieve_documents(
        resolved_q,
        n_results=8,
    )

    # 2. Evaluate retrieval safety & confidence threshold
    is_confident, top_score, chunk_records = evaluate_retrieval_safety(
        results,
        threshold=CONFIDENCE_THRESHOLD,
    )

    # 3. Pre-generation safety refusal if confidence threshold is not met
    if not is_confident:
        final_answer = STANDARD_REFUSAL_MESSAGE
        refused = True

        log_query(
            question=request.question,
            retrieved_chunks=chunk_records,
            confidence_met=False,
            top_score=top_score,
            final_answer=final_answer,
            refused=refused,
            extra_metadata={"source": "api_chat"},
        )

        return {
            "question": request.question,
            "answer": final_answer,
            "refused": refused,
            "confidence_met": False,
            "top_score": top_score,
            "citations": [],
            "retrieved_chunks": chunk_records,
        }

    # 4. Build clinical evidence context with citation tags
    context = build_context(results)

    # 5. Build conversation history if present
    conversation_history = "\n".join(
        f"{message.role}: {message.content}"
        for message in request.history
    )

    history_block = (
        f"\nCONVERSATION HISTORY (for conversational context only):\n---------------------\n{conversation_history}\n---------------------\n"
        if conversation_history.strip()
        else ""
    )

    prompt = build_prompt(
        question=f"{history_block}\n{request.question}" if history_block else request.question,
        context=context,
    )

    # 6. Generate grounded answer (returns tuple: answer_text, generation_mode)
    final_answer, generation_mode = generate_response(prompt)
    refused = STANDARD_REFUSAL_MESSAGE.lower() in final_answer.lower()

    # 7. Post-generation citation verification
    from src.reasoning.safety import verify_citations
    cit_verification = verify_citations(final_answer, chunk_records)

    # 8. Log query end-to-end with verification telemetry
    fallback_triggered = generation_mode in ["fallback_synthesis", "offline_synthesis"]
    log_query(
        question=request.question,
        retrieved_chunks=chunk_records,
        confidence_met=True,
        top_score=top_score,
        final_answer=final_answer,
        refused=refused,
        extra_metadata={
            "source": "api_chat",
            "citation_verification": cit_verification,
            "flagged_for_review": cit_verification.get("flagged_for_review", False),
            "generation_mode": generation_mode,
            "fallback_triggered": fallback_triggered,
        },
    )

    return {
        "question": request.question,
        "answer": final_answer,
        "refused": refused,
        "confidence_met": True,
        "top_score": top_score,
        "retrieved_chunks": chunk_records,
        "citation_verification": cit_verification,
        "generation_mode": generation_mode,
        "fallback_triggered": fallback_triggered,
    }


@app.get("/logs")
def get_logs(limit: int = 50):
    logs = get_logged_queries()
    return {"total": len(logs), "logs": logs[-limit:]}


@app.get("/")
def root():
    return {
        "message": "MedRetriv Clinical Decision Support API is running",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
    }