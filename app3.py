import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import time

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.utils.data_loader import CSVDataLoader
from src.vector_store.chroma_manager import ChromaDBManager
from src.chatbot.groq_chatbot import PersonalCareChatbot

# optional HF pre-cache
try:
    from huggingface_hub import hf_hub_download
except Exception:
    hf_hub_download = None

st.set_page_config(
    page_title="Personal Care Product Chatbot",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Styles ---
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.4rem;
        color: #FF6B9D;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #666;
        margin-bottom: 1rem;
    }
    .chat-container {
        background-color: #f7f8fb;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 12px;
        max-height: 520px;
        overflow-y: auto;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        padding: 10px 14px;
        border-radius: 14px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
    }
    .bot-message {
        background-color: #ffffff;
        color: #222;
        padding: 10px 14px;
        border-radius: 14px;
        margin: 8px 0;
        max-width: 80%;
        margin-right: auto;
        border: 1px solid #eee;
    }
    .control-box {
        background-color: #fff;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
        border: 1px solid #eee;
    }
    .small-muted {
        color: #888;
        font-size: 0.9rem;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- Helper: HF pre-cache ---
def ensure_hf_model_cached(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    filename="config_sentence_transformers.json",
    cache_dir="models",
    max_retries=3,
    timeout=30,
):
    if hf_hub_download is None:
        return False
    os.makedirs(cache_dir, exist_ok=True)
    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            hf_hub_download(
                repo_id=repo_id, filename=filename, cache_dir=cache_dir, repo_type="model", timeout=timeout
            )
            return True
        except Exception as e:
            last_exc = e
            time.sleep(0.8 * attempt)
    print("HF pre-cache failed:", last_exc)
    return False


class StreamlitApp:
    def __init__(self):
        # session state defaults
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "system_initialized" not in st.session_state:
            st.session_state.system_initialized = False
        if "current_user_id" not in st.session_state:
            st.session_state.current_user_id = f"user_{int(time.time())}"

        # local references restored from session_state when available
        self.data_loader = CSVDataLoader()
        self.chatbot = st.session_state.get("chatbot", None)
        self.vector_store = st.session_state.get("vector_store", None)

    def initialize_system(self, force=False):
        if st.session_state.get("system_initialized", False) and not force:
            if not self.chatbot and "chatbot" in st.session_state:
                self.chatbot = st.session_state.chatbot
            if not self.vector_store and "vector_store" in st.session_state:
                self.vector_store = st.session_state.vector_store
            return True

        try:
            try:
                ensure_hf_model_cached()
            except Exception:
                pass

            products = []
            try:
                products = self.data_loader.load_all_products() or []
            except Exception:
                products = []

            if not products:
                chatbot = PersonalCareChatbot()
                st.session_state.chatbot = chatbot
                self.chatbot = chatbot
                st.session_state.system_initialized = True
                return True

            vector_store = ChromaDBManager()
            vector_store.add_products(products)

            chatbot = PersonalCareChatbot()

            st.session_state.vector_store = vector_store
            st.session_state.chatbot = chatbot
            st.session_state.system_initialized = True

            self.vector_store = vector_store
            self.chatbot = chatbot
            return True

        except Exception as e:
            st.warning(f"Initialization warning: {e}")
            try:
                chatbot = PersonalCareChatbot()
                st.session_state.chatbot = chatbot
                self.chatbot = chatbot
                st.session_state.system_initialized = True
            except Exception:
                pass
            return False

    def display_layout(self):
        left_col, main_col, right_col = st.columns([1.2, 6, 2])

        # Left: status + about
        with left_col:
            st.markdown("### ⚙️ Status")
            with st.container():
                st.markdown('<div class="control-box">', unsafe_allow_html=True)
                if st.session_state.get("system_initialized", False):
                    st.success("✅ System Ready")
                    st.markdown('<div class="small-muted">Auto-initialized. Chat directly below.</div>', unsafe_allow_html=True)
                else:
                    st.info("Initializing... Please wait a moment on first load.")
                st.markdown("---")
                st.markdown("### ℹ️ About")
                st.markdown(
                    "Personal Care Product Chatbot — ask about product recommendations, brands, benefits, and more."
                )
                st.markdown("</div>", unsafe_allow_html=True)

        # Main: chat area
        with main_col:
            st.markdown('<div class="main-header">💄 Personal Care Chatbot</div>', unsafe_allow_html=True)
            st.markdown('<div class="sub-header">Ask about products, benefits, or recommendations</div>', unsafe_allow_html=True)

            st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'<div class="user-message">👤 {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="bot-message">🤖 {message["content"]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Chat input form (clears automatically after submit)
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_input(
                    "Type your message here...",
                    key="user_input_main",
                    placeholder="Hi, what can you recommend?",
                )
                submitted = st.form_submit_button("Send")

                if submitted and user_input:
                    # Ensure chatbot initialized
                    if not self.chatbot and "chatbot" in st.session_state:
                        self.chatbot = st.session_state.chatbot
                    if not self.vector_store and "vector_store" in st.session_state:
                        self.vector_store = st.session_state.vector_store

                    if not st.session_state.get("system_initialized", False):
                        self.initialize_system()

                    if not self.chatbot:
                        try:
                            chatbot = PersonalCareChatbot()
                            st.session_state.chatbot = chatbot
                            self.chatbot = chatbot
                        except Exception:
                            st.error("Chatbot currently unavailable.")
                            st.stop()  # stop instead of continue

                    # Append user message
                    st.session_state.messages.append({"role": "user", "content": user_input})

                    # Generate bot response
                    with st.spinner("🤖 Thinking..."):
                        try:
                            response = self.chatbot.generate_response(
                                user_input, st.session_state.current_user_id
                            )
                        except Exception as e:
                            response = f"Sorry, I couldn't generate a response: {e}"

                    # Append bot response and rerun to refresh
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    st.rerun()

        # Right: history panel
        with right_col:
            st.markdown("### 🕘 Chat History")
            msgs = list(reversed(st.session_state.messages))
            if msgs:
                for i, m in enumerate(msgs, 1):
                    role = "You" if m["role"] == "user" else "Bot"
                    short = m["content"] if len(m["content"]) < 120 else m["content"][:117] + "..."
                    with st.expander(f"{role}: {short}", expanded=False):
                        st.write(m["content"])
            else:
                st.write("_No messages yet_")

            st.markdown("---")
            if self.chatbot:
                try:
                    conv = self.chatbot.get_conversation_history(
                        st.session_state.current_user_id, limit=6
                    )
                    if conv:
                        st.markdown("#### Saved Conversations")
                        for idx, (user_msg, bot_resp, ts) in enumerate(reversed(conv), 1):
                            with st.expander(f"{ts} ({idx})", expanded=False):
                                st.markdown(f"**You:** {user_msg}")
                                st.markdown(f"**Bot:** {bot_resp}")
                except Exception:
                    pass

    def run(self):
        if not st.session_state.get("system_initialized", False):
            self.initialize_system()

        self.display_layout()

        st.markdown("---")
        st.markdown("Built with ❤️ — type your question and press Enter or click **Send**.")


def main():
    app = StreamlitApp()
    app.run()


if __name__ == "__main__":
    main()
