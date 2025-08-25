import os
import streamlit as st
from agents import MasterAgent

st.set_page_config(page_title="Multi-Agent Chat", page_icon="🤖", layout="centered")

# --- Load secrets safely ---
HF_TOKEN = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
TOMORROW_API_KEY = st.secrets.get("TOMORROW_API_KEY") or os.getenv("TOMORROW_API_KEY")

# --- Init agent router ---
agent = MasterAgent(weather_api_key=TOMORROW_API_KEY, hf_token=HF_TOKEN, groq_api_key=GROQ_API_KEY)

# --- UI ---
if "history" not in st.session_state:
    st.session_state.history = []

st.title("🤖 Multi-Agent Conversational Web App")

# history
for role, msg in st.session_state.history:
    if role == "user":
        st.markdown(f"🧑 **You:** {msg}")
    else:
        st.markdown(f"🤖 **Bot:** {msg}")

user_input = st.text_input("Type your query:")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Send") and user_input.strip():
        st.session_state.history.append(("user", user_input))
        response = agent.route(user_input)
        st.session_state.history.append(("bot", response))
        st.rerun()

with col2:
    if st.button("Clear Chat"):
        st.session_state.history = []
        st.rerun()

with col3:
    chat_text = "\n".join([f"{role}: {msg}" for role, msg in st.session_state.history])
    st.download_button("Export Chat", chat_text, file_name="chat.txt", use_container_width=True)

# Optional: small debug line (remove if you don’t want to show this)
st.caption(f"LLM backends → Groq:{bool(GROQ_API_KEY)} | HF:{bool(HF_TOKEN)}")
