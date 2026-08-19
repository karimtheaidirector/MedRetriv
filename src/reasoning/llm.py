import os
import re
import logging

from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from src.reasoning.prompt import STANDARD_REFUSAL_MESSAGE

load_dotenv()

logger = logging.getLogger("medretriv.llm")

HF_TOKEN = os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b:groq",
)


def get_client() -> InferenceClient:
    token = os.getenv("HF_TOKEN")
    if not token or not token.strip():
        raise EnvironmentError(
            "HF_TOKEN is missing or empty. Please set HF_TOKEN in your .env file."
        )
    return InferenceClient(api_key=token)


def _clean_evidence_sentence(sentence: str) -> str:
    """Clean isolated sentence and remove navigation noise or table fragments."""
    s = sentence.strip()
    s = re.sub(r"^(Recommendations of Others|Summary of Results|Background|Preamble)\s+", "", s, flags=re.IGNORECASE)
    s = re.sub(r"^\d+[\.\,\s]+", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _synthesize_grounded_response(prompt: str) -> str:
    """
    Dynamically synthesize a coherent, evidence-grounded clinical answer directly
    from the retrieved evidence chunks when live LLM API is unavailable.
    """
    print("[LLM Path] Generating response via Grounded Evidence Synthesis (Offline/Fallback Mode)")

    blocks = re.split(r"---\s*Evidence Chunk", prompt)
    if len(blocks) <= 1:
        return STANDARD_REFUSAL_MESSAGE

    claims = []
    seen_concepts = set()

    for block in blocks[1:5]:
        cit_match = re.search(r"Required Citation:\s*(\[Source:[^\]]+\])", block)
        content_match = re.search(r"Content:\s*\r?\n(.*?)(?=\r?\n---|\r?\n-+$|\Z)", block, re.DOTALL)

        cit_tag = cit_match.group(1).strip() if cit_match else ""
        content = content_match.group(1).strip() if content_match else ""

        if not cit_tag or not content:
            continue

        clean_text = " ".join(content.split())

        # Extract sentences > 35 chars
        raw_sentences = [
            s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_text)
            if len(s.strip()) > 35
        ]

        # Filter out web navigation, news list headers, and table headers
        meaningful_sentences = []
        for s in raw_sentences:
            s_lower = s.lower()
            if any(noise in s_lower for noise in [
                "latest news articles", "on this page", "enlarge image",
                "credit:", "table of contents", "doi:", "http://", "https://"
            ]):
                continue
            cleaned = _clean_evidence_sentence(s)
            if len(cleaned) > 25:
                meaningful_sentences.append(cleaned)

        if meaningful_sentences:
            # Select the most substantive sentence not already stated
            selected = None
            for s in meaningful_sentences:
                key = s[:40].lower()
                if key not in seen_concepts:
                    seen_concepts.add(key)
                    selected = s
                    break

            if selected:
                claim = selected.rstrip(".;,")
                claims.append(f"{claim} {cit_tag}.")

    if not claims:
        return STANDARD_REFUSAL_MESSAGE

    claims.append("Individual screening decisions should be discussed with a qualified healthcare professional.")
    return " ".join(claims)


def generate_response(prompt: str) -> str:
    """
    Generate an answer using the live HuggingFace LLM if HF_TOKEN is present,
    or gracefully synthesize from retrieved evidence chunks.
    """
    token = os.getenv("HF_TOKEN")

    if not token or token.strip() == "":
        print("[LLM Path] HF_TOKEN not configured — executing Grounded Evidence Synthesis")
        return _synthesize_grounded_response(prompt)

    try:
        print(f"[LLM Path] Calling live Hugging Face Inference API ({MODEL_NAME})...")
        client = get_client()

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=1024,
            temperature=0.1,
        )

        content = response.choices[0].message.content

        if not content or not content.strip():
            print("[LLM Warning] Live API returned empty response — falling back to synthesis")
            return _synthesize_grounded_response(prompt)

        print("[LLM Path] Live Hugging Face API generation successful.")
        return content.strip()

    except Exception as e:
        print(f"[LLM Error] Live API call failed ({type(e).__name__}: {e}) — falling back to Grounded Evidence Synthesis")
        return _synthesize_grounded_response(prompt)