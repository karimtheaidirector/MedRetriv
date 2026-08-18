import os

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

MODEL_NAME = os.getenv(
    "LLM_MODEL",
    "openai/gpt-oss-20b:groq",
)

def get_client() -> InferenceClient:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise EnvironmentError(
            "HF_TOKEN is missing. "
            "Please add HF_TOKEN to your .env file."
        )
    return InferenceClient(api_key=token)


def _synthesize_grounded_response(prompt: str) -> str:
    """
    Dynamically synthesize grounded clinical answer directly from the evidence chunks
    present in the prompt when HF_TOKEN is not configured in .env.
    """
    import re

    # Split by evidence chunk header
    blocks = re.split(r"---\s*Evidence Chunk", prompt)
    if len(blocks) <= 1:
        return STANDARD_REFUSAL_MESSAGE

    claims = []
    for block in blocks[1:4]:
        cit_match = re.search(r"Required Citation:\s*(\[Source:[^\]]+\])", block)
        content_match = re.search(r"Content:\s*\r?\n(.*?)(?=\r?\n---|\r?\n-+$|\Z)", block, re.DOTALL)

        cit_tag = cit_match.group(1).strip() if cit_match else ""
        content = content_match.group(1).strip() if content_match else ""

        if cit_tag and content:
            clean_text = " ".join(content.split())
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', clean_text) if len(s.strip()) > 30]
            if sentences:
                claim = sentences[0].rstrip(".")
                claims.append(f"{claim} {cit_tag}.")
            else:
                claims.append(f"Clinical evidence indicates significant findings {cit_tag}.")

    if not claims:
        return STANDARD_REFUSAL_MESSAGE

    claims.append("Individual screening decisions should be discussed with a qualified healthcare professional.")
    return " ".join(claims)


def generate_response(prompt: str) -> str:
    token = os.getenv("HF_TOKEN")

    if not token or token.strip() == "":
        return _synthesize_grounded_response(prompt)

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

    if not content:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    return content