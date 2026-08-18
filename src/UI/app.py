import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000/chat"


st.set_page_config(
    page_title="INSTANT",
    page_icon="🩺",
    layout="centered",
)


# ============================================================
# Session State
# ============================================================

if "chats" not in st.session_state:
    st.session_state.chats = {
        "chat_1": {
            "title": "New Chat",
            "messages": [],
        }
    }


if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = "chat_1"


# ============================================================
# Chat Management
# ============================================================

def create_new_chat():
    chat_number = len(st.session_state.chats) + 1
    chat_id = f"chat_{chat_number}"

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
    }

    st.session_state.current_chat_id = chat_id


# ============================================================
# Current Chat
# ============================================================

current_chat = st.session_state.chats[
    st.session_state.current_chat_id
]


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:

    st.title("INSTANT")
    st.caption("Clinical Evidence Assistant")

    if st.button(
        "＋ New Chat",
        use_container_width=True,
    ):
        create_new_chat()
        st.rerun()

    st.divider()

    st.subheader("Chats")

    for chat_id, chat in st.session_state.chats.items():

        if st.button(
            chat["title"],
            key=f"chat_button_{chat_id}",
            use_container_width=True,
        ):
            st.session_state.current_chat_id = chat_id
            st.rerun()


# ============================================================
# Main UI
# ============================================================

st.title("🩺 INSTANT")
st.caption(
    "Clinical Evidence Assistant — "
    "Breast Cancer Screening"
)


# ============================================================
# Display Conversation
# ============================================================

for message in current_chat["messages"]:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ============================================================
# User Input
# ============================================================

question = st.chat_input(
    "Ask a clinical question..."
)


if question:

    messages = current_chat["messages"]

    # Save user message
    messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    with st.chat_message("user"):
        st.markdown(question)

    # Previous conversation
    history = messages[:-1]

    with st.chat_message("assistant"):

        with st.spinner(
            "Searching clinical evidence..."
        ):

            try:

                response = requests.post(
                    API_URL,
                    json={
                        "question": question,
                        "history": history,
                    },
                    timeout=120,
                )

                response.raise_for_status()

                answer = response.json()["answer"]

            except requests.exceptions.RequestException as e:

                answer = (
                    "Unable to connect to the INSTANT API.\n\n"
                    f"Error: {e}"
                )

        st.markdown(answer)

    # Save assistant response
    messages.append(
        {
            "role": "assistant",
            "content": answer,
        }
    )

    # Use first question as chat title
    if current_chat["title"] == "New Chat":
        current_chat["title"] = question[:35]