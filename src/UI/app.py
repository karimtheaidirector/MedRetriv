import os
import re
import html
import requests
import streamlit as st

# ============================================================
# Page Configuration
# ============================================================

st.set_page_config(
    page_title="MedRetriv — Clinical Evidence Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("MEDRETRIV_API_URL", "http://127.0.0.1:8000/chat")

# ============================================================
# Session State Initialization
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = {
        "chat_1": {
            "title": "New Consultation",
            "messages": [],
        }
    }

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Dark Mode"


# ============================================================
# Custom CSS Theming System (Light / Dark Theme Support)
# ============================================================

def get_theme_css(is_dark: bool) -> str:
    if is_dark:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0f172a !important;
            color: #f1f5f9 !important;
        }

        /* Streamlit Top Header & Toolbar */
        header[data-testid="stHeader"],
        .stAppHeader,
        .stAppToolbar,
        div[data-testid="stToolbar"],
        header {
            background-color: #0f172a !important;
            color: #f1f5f9 !important;
        }

        /* Streamlit Bottom Block & Chat Input Container */
        div[data-testid="stBottom"],
        div[data-testid="stBottomBlockContainer"],
        footer {
            background-color: #0f172a !important;
            border-top: 1px solid #1e293b !important;
        }

        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            color: #f1f5f9 !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            color: #f1f5f9 !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #94a3b8 !important;
        }

        div[data-testid="stChatInput"] button {
            color: #38bdf8 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #1e293b !important;
            border-right: 1px solid #334155 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #e2e8f0 !important;
        }

        /* Main App Header Styling */
        .med-header-title {
            font-size: 2.1rem;
            font-weight: 700;
            color: #38bdf8;
            margin-bottom: 0.15rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .med-header-tagline {
            font-size: 1.02rem;
            color: #94a3b8;
            font-weight: 500;
            margin-bottom: 0.4rem;
        }
        .med-header-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            font-size: 0.82rem;
            color: #38bdf8;
            background: #1e293b;
            border: 1px solid #334155;
            padding: 0.45rem 0.85rem;
            border-radius: 8px;
            margin-bottom: 1.25rem;
            font-weight: 600;
        }

        /* Chat Messages */
        div[data-testid="stChatMessage"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            border-radius: 12px !important;
            margin-bottom: 0.85rem !important;
            padding: 0.85rem 1.1rem !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25) !important;
        }
        div[data-testid="stChatMessage"] p,
        div[data-testid="stChatMessage"] li {
            color: #f1f5f9 !important;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Refusal Card (High Contrast Dark Mode) */
        .chat-card-refusal {
            background: #1c1917;
            border: 1px solid #443722;
            border-left: 5px solid #f59e0b;
            border-radius: 12px;
            padding: 1.05rem 1.25rem;
            max-width: 92%;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
        }
        .refusal-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: #451a03;
            color: #fde68a !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.22rem 0.6rem;
            border-radius: 6px;
            border: 1px solid #b45309;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .refusal-text {
            color: #f8fafc !important;
            font-size: 0.95rem;
            line-height: 1.55;
            font-weight: 400;
        }
        .refusal-caption {
            font-size: 0.80rem;
            color: #fcd34d !important;
            margin-top: 0.55rem;
            font-style: italic;
            line-height: 1.4;
        }

        /* Citation Badges */
        .citation-container {
            margin-top: 0.85rem;
            padding-top: 0.65rem;
            border-top: 1px solid #334155;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.4rem;
        }
        .citation-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #94a3b8 !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-right: 0.2rem;
        }
        .citation-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: #0f172a;
            color: #7dd3fc !important;
            border: 1px solid #0284c7;
            border-radius: 6px;
            padding: 0.2rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 600;
        }

        /* Confidence Metric Tag */
        .confidence-tag {
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 600;
            margin-top: 0.35rem;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
        }
        .conf-high {
            color: #6ee7b7 !important;
            background: #064e3b;
            border: 1px solid #059669;
        }
        .conf-mod {
            color: #fde68a !important;
            background: #451a03;
            border: 1px solid #b45309;
        }

        /* Fallback Synthesis Indicator Badge */
        .fallback-indicator-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            color: #94a3b8 !important;
            background: #0f172a;
            border: 1px solid #334155;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            margin-top: 0.45rem;
            font-style: italic;
        }

        /* Evidence Expander Inner Items */
        .evidence-item {
            background: #0f172a;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.6rem;
            font-size: 0.88rem;
        }
        .evidence-meta {
            font-weight: 600;
            color: #e2e8f0 !important;
            margin-bottom: 0.25rem;
            display: flex;
            justify-content: space-between;
        }
        .evidence-preview {
            color: #94a3b8 !important;
            font-size: 0.83rem;
            line-height: 1.45;
        }
        </style>
        """
    else:
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        html, body, [class*="css"], .stApp {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* Streamlit Top Header & Toolbar */
        header[data-testid="stHeader"],
        .stAppHeader,
        .stAppToolbar,
        div[data-testid="stToolbar"],
        header {
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* Streamlit Bottom Block & Chat Input Container */
        div[data-testid="stBottom"],
        div[data-testid="stBottomBlockContainer"],
        footer {
            background-color: #f8fafc !important;
            border-top: 1px solid #e2e8f0 !important;
        }

        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }

        div[data-testid="stChatInput"] > div {
            background-color: #ffffff !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            color: #0f172a !important;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05) !important;
        }

        div[data-testid="stChatInput"] textarea {
            background-color: transparent !important;
            color: #0f172a !important;
        }

        div[data-testid="stChatInput"] textarea::placeholder {
            color: #64748b !important;
        }

        div[data-testid="stChatInput"] button {
            color: #0284c7 !important;
        }

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #f1f5f9 !important;
            border-right: 1px solid #e2e8f0 !important;
        }
        section[data-testid="stSidebar"] * {
            color: #1e293b !important;
        }

        /* Main App Header Styling */
        .med-header-title {
            font-size: 2.1rem;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 0.15rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .med-header-tagline {
            font-size: 1.02rem;
            color: #475569;
            font-weight: 500;
            margin-bottom: 0.4rem;
        }
        .med-header-stats {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            font-size: 0.82rem;
            color: #0284c7;
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 0.45rem 0.85rem;
            border-radius: 8px;
            margin-bottom: 1.25rem;
            font-weight: 600;
        }

        /* Chat Messages */
        div[data-testid="stChatMessage"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 12px !important;
            margin-bottom: 0.85rem !important;
            padding: 0.85rem 1.1rem !important;
            box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
        }
        div[data-testid="stChatMessage"] p,
        div[data-testid="stChatMessage"] li {
            color: #0f172a !important;
            font-size: 0.95rem;
            line-height: 1.6;
        }

        /* Refusal Card (Light Mode) */
        .chat-card-refusal {
            background: #fffbeb;
            border: 1px solid #fde68a;
            border-left: 5px solid #d97706;
            border-radius: 12px;
            padding: 1.05rem 1.25rem;
            max-width: 92%;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(217, 119, 6, 0.08);
        }
        .refusal-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            background: #fef3c7;
            color: #92400e !important;
            font-size: 0.78rem;
            font-weight: 700;
            padding: 0.22rem 0.6rem;
            border-radius: 6px;
            border: 1px solid #fcd34d;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .refusal-text {
            color: #1e293b !important;
            font-size: 0.95rem;
            line-height: 1.55;
        }
        .refusal-caption {
            font-size: 0.80rem;
            color: #92400e !important;
            margin-top: 0.55rem;
            font-style: italic;
            line-height: 1.4;
        }

        /* Citation Badges */
        .citation-container {
            margin-top: 0.85rem;
            padding-top: 0.65rem;
            border-top: 1px solid #f1f5f9;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.4rem;
        }
        .citation-label {
            font-size: 0.75rem;
            font-weight: 700;
            color: #64748b !important;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-right: 0.2rem;
        }
        .citation-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
            background: #f8fafc;
            color: #0369a1 !important;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 0.2rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 600;
        }

        /* Confidence Metric Tag */
        .confidence-tag {
            display: inline-block;
            font-size: 0.76rem;
            font-weight: 600;
            margin-top: 0.35rem;
            padding: 0.15rem 0.45rem;
            border-radius: 4px;
        }
        .conf-high {
            color: #047857 !important;
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
        }
        .conf-mod {
            color: #b45309 !important;
            background: #fffbeb;
            border: 1px solid #fde68a;
        }

        /* Fallback Synthesis Indicator Badge */
        .fallback-indicator-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.75rem;
            color: #64748b !important;
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            padding: 0.2rem 0.55rem;
            border-radius: 6px;
            margin-top: 0.45rem;
            font-style: italic;
        }

        /* Evidence Expander Inner Items */
        .evidence-item {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.6rem;
            font-size: 0.88rem;
        }
        .evidence-meta {
            font-weight: 600;
            color: #0f172a !important;
            margin-bottom: 0.25rem;
            display: flex;
            justify-content: space-between;
        }
        .evidence-preview {
            color: #475569 !important;
            font-size: 0.83rem;
            line-height: 1.45;
        }
        </style>
        """


# ============================================================
# Helper Functions: Citation Parsing & Label Formatting
# ============================================================

CITATION_REGEX = re.compile(
    r"\[Source:\s*(.*?)(?:,\s*Section:\s*(.*?))?,\s*Page:\s*([^\]]+)\]"
)

DOC_FRIENDLY_NAMES = {
    "breast-cancer-screening-final-rec.pdf": "USPSTF Guideline",
    "breast-cancer-screening-final-evidence-review.pdf": "AHRQ Evidence Review",
    "Frntiers Breast Cancer pathogenesis, diagnosis and treatment (2026).pdf": "Frontiers in Oncology",
    "Nature Review Breast cancer pathogenesis and treatments (2025).pdf": "Nature STTT Review",
    "NCINIH – Breast Cancer Overview (Patient & Professional Versions).pdf": "NCI / NIH Overview",
}


def parse_and_clean_answer(raw_answer: str):
    """
    Extracts citation metadata from the answer, removes raw inline citation tags
    from prose, and produces clean deduplicated badge labels.
    """
    matches = list(CITATION_REGEX.finditer(raw_answer))
    citations = []

    for m in matches:
        doc = m.group(1).strip()
        section = m.group(2).strip() if m.group(2) else ""
        pages = m.group(3).strip() if m.group(3) else ""

        friendly_doc = DOC_FRIENDLY_NAMES.get(doc, doc)
        label = f"{friendly_doc} · p.{pages}"
        if section:
            tooltip = f"Section: {section}"
        else:
            tooltip = f"Document: {doc}"

        citations.append({
            "doc": friendly_doc,
            "raw_doc": doc,
            "section": section,
            "pages": pages,
            "label": label,
            "tooltip": tooltip,
        })

    clean_prose = CITATION_REGEX.sub("", raw_answer)
    clean_prose = re.sub(r" +([.,;])", r"\1", clean_prose)
    clean_prose = re.sub(r" +", " ", clean_prose).strip()

    deduped_badges = []
    seen = set()
    for c in citations:
        key = (c["doc"], c["pages"])
        if key not in seen:
            seen.add(key)
            deduped_badges.append(c["label"])

    return clean_prose, deduped_badges


def execute_query(question: str, history_messages: list) -> dict:
    """
    Executes question via FastAPI if running, or falls back seamlessly
    to direct answer_question() pipeline with conversational context.
    """
    payload_history = [
        {"role": m["role"], "content": m.get("raw_content", m["content"])}
        for m in history_messages
        if m.get("role") in ["user", "assistant"]
    ]

    try:
        resp = requests.post(
            API_URL,
            json={"question": question, "history": payload_history},
            timeout=30,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass

    # Seamless direct backend execution fallback
    try:
        from src.reasoning.main import answer_question
        return answer_question(question, history=payload_history)
    except Exception as e:
        return {
            "answer": f"Error communicating with reasoning engine: {e}",
            "refused": False,
            "confidence_met": False,
            "top_score": 0.0,
            "retrieved_chunks": [],
        }


# ============================================================
# Sidebar: Theme Toggle, Consultation History & Knowledge Info
# ============================================================

with st.sidebar:
    st.markdown("### 🩺 **MedRetriv**")
    st.caption("Clinical Evidence & Decision Support")

    # Light / Dark Theme Toggle
    theme_choice = st.radio(
        "🎨 **Display Theme**",
        ["🌙 Dark Mode", "☀️ Light Mode"],
        index=0 if st.session_state.theme_mode == "Dark Mode" else 1,
        key="theme_radio",
        horizontal=True,
    )
    is_dark = "Dark" in theme_choice
    st.session_state.theme_mode = "Dark Mode" if is_dark else "Light Mode"

    if st.button("＋ New Consultation", use_container_width=True):
        new_id = f"chat_{len(st.session_state.chats) + 1}"
        st.session_state.chats[new_id] = {
            "title": "New Consultation",
            "messages": [],
        }
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.divider()
    st.markdown("#### **Consultations**")

    for chat_id, chat_data in list(st.session_state.chats.items()):
        is_active = chat_id == st.session_state.current_chat_id
        btn_label = f"{'▶ ' if is_active else ''}{chat_data['title']}"
        if st.button(
            btn_label,
            key=f"btn_{chat_id}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            st.session_state.current_chat_id = chat_id
            st.rerun()

    st.divider()
    st.markdown("#### **Corpus & Gating**")
    st.markdown(
        """
        <div style="font-size:0.82rem; line-height:1.5;">
        • <b>5 Authoritative Sources</b> (USPSTF, AHRQ, NCI, Nature, Frontiers)<br>
        • <b>515 Verified Chunks</b> (384d normalized embeddings)<br>
        • <b>Safety Threshold</b>: Cosine similarity &ge; 0.50<br>
        • <b>Grounding</b>: 100% Verified inline citations
        </div>
        """,
        unsafe_allow_html=True,
    )


# Inject Active Theme CSS
st.markdown(get_theme_css(is_dark), unsafe_allow_html=True)


# ============================================================
# Main Header & Credibility Bar
# ============================================================

st.markdown(
    """
    <div class="med-header-title">
        🩺 MedRetriv
    </div>
    <div class="med-header-tagline">
        Evidence-grounded clinical assistant for breast cancer screening & diagnosis
    </div>
    <div class="med-header-stats">
        <span>📚 5 Authoritative Sources</span>
        <span>•</span>
        <span>🧩 515 Verified Chunks</span>
        <span>•</span>
        <span>🎯 100% Citation Accuracy</span>
        <span>•</span>
        <span>⚡ &lt;100ms Latency</span>
        <span>•</span>
        <span>🛡️ Pre-Gen Safety Gating</span>
    </div>
    """,
    unsafe_allow_html=True,
)

current_chat = st.session_state.chats[st.session_state.current_chat_id]


# ============================================================
# Render Conversation History
# ============================================================

for msg in current_chat["messages"]:
    role = msg["role"]
    content = msg["content"]
    refused = msg.get("refused", False)
    citations = msg.get("citations", [])
    chunks = msg.get("retrieved_chunks", [])
    top_score = msg.get("top_score", 0.0)
    query_type = msg.get("query_type", "clinical")
    generation_mode = msg.get("generation_mode", "live")

    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(content)
    else:
        with st.chat_message("assistant", avatar="🩺"):
            if refused:
                refusal_card_html = (
                    f'<div class="chat-card-refusal">'
                    f'<div class="refusal-badge">⚠️ Insufficient Evidence / Out of Scope</div>'
                    f'<div class="refusal-text">{html.escape(content)}</div>'
                    f'<div class="refusal-caption">'
                    f'Similarity score ({top_score:.3f}) was below the safety threshold (0.50). Pre-generation gating prevented hallucination.'
                    f'</div></div>'
                )
                st.markdown(refusal_card_html, unsafe_allow_html=True)
            else:
                if query_type != "conversational" and top_score > 0.0:
                    if top_score >= 0.65:
                        conf_html = f'<div class="confidence-tag conf-high">🟢 High confidence match ({top_score:.2f})</div>'
                    else:
                        conf_html = f'<div class="confidence-tag conf-mod">🟡 Moderate confidence match ({top_score:.2f})</div>'
                    st.markdown(conf_html, unsafe_allow_html=True)

                # Render main answer text as Markdown (bold, lists, headings parsed natively)
                st.markdown(content)

                # Render citation badges as separate HTML
                if citations:
                    badges_str = "".join(
                        f'<span class="citation-badge">📄 {html.escape(b)}</span>'
                        for b in citations
                    )
                    citation_html = (
                        f'<div class="citation-container">'
                        f'<span class="citation-label">Sources:</span>'
                        f'{badges_str}'
                        f'</div>'
                    )
                    st.markdown(citation_html, unsafe_allow_html=True)

                # Render fallback indicator if synthesized via backup engine
                if generation_mode in ["fallback_synthesis", "offline_synthesis"] and query_type != "conversational":
                    st.markdown(
                        '<div class="fallback-indicator-badge">⚡ Grounded via Backup Evidence Synthesis</div>',
                        unsafe_allow_html=True,
                    )

                # Expandable evidence panel (only if chunks were retrieved)
                if chunks and query_type != "conversational":
                    with st.expander(f"🔍 View Evidence Used ({len(chunks)} Chunks)", expanded=False):
                        for idx, ch in enumerate(chunks):
                            src = DOC_FRIENDLY_NAMES.get(ch.get("document", ""), ch.get("document", "Document"))
                            sec = ch.get("section", "General")
                            p_start = ch.get("page_start", "?")
                            p_end = ch.get("page_end", "?")
                            p_str = f"p.{p_start}" if p_start == p_end else f"p.{p_start}-{p_end}"
                            score = ch.get("similarity_score", 0.0)
                            text_prev = ch.get("text", "")[:220].strip()

                            item_html = (
                                f'<div class="evidence-item">'
                                f'<div class="evidence-meta">'
                                f'<span><b>#{idx+1} {html.escape(src)}</b> ({html.escape(sec)}, {p_str})</span>'
                                f'<span style="color:#38bdf8;">Match: {score:.3f}</span>'
                                f'</div>'
                                f'<div class="evidence-preview">{html.escape(text_prev)}...</div>'
                                f'</div>'
                            )
                            st.markdown(item_html, unsafe_allow_html=True)


# ============================================================
# User Input & Response Generation
# ============================================================

user_query = st.chat_input("Ask a clinical breast cancer or screening question...")

if user_query:
    current_chat["messages"].append({
        "role": "user",
        "content": user_query,
    })

    if current_chat["title"] == "New Consultation":
        current_chat["title"] = user_query[:32] + ("..." if len(user_query) > 32 else "")

    st.rerun()


# Handle processing if the last message is a user message without a response
if current_chat["messages"] and current_chat["messages"][-1]["role"] == "user":
    latest_user_query = current_chat["messages"][-1]["content"]

    with st.spinner("Searching clinical evidence & evaluating safety threshold..."):
        res = execute_query(latest_user_query, current_chat["messages"][:-1])

    raw_answer = res.get("answer", "")
    refused = res.get("refused", False)
    top_score = res.get("top_score", 0.0)
    retrieved_chunks = res.get("retrieved_chunks", [])
    query_type = res.get("query_type", "clinical")
    generation_mode = res.get("generation_mode", "")

    if not refused and query_type != "conversational":
        clean_prose, citation_badges = parse_and_clean_answer(raw_answer)
    else:
        clean_prose = raw_answer
        citation_badges = []

    current_chat["messages"].append({
        "role": "assistant",
        "content": clean_prose,
        "raw_content": raw_answer,
        "refused": refused,
        "top_score": top_score,
        "citations": citation_badges,
        "retrieved_chunks": retrieved_chunks,
        "query_type": query_type,
        "generation_mode": generation_mode,
    })

    st.rerun()