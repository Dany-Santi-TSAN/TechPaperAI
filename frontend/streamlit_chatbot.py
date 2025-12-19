import streamlit as st
from core.mcp_client import MCP_ChatBot


st.set_page_config(
    page_title="TechPaper AI",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("TechPaper AI")
st.header("Your eyes on the frontier of tech research.")
st.subheader("Scan, summarize, and stay ahead -> automatically")

chatbot = MCP_ChatBot

# Chatbot UI
with st.chat_message("assistant"):
    st.write("Bonjour! Comment puis-je vous aider?")

with st.chat_message("user"):
    st.write("Your Query here: ")

# Input in chat
prompt = st.chat_input("Your Query here:")
if prompt:
    st.write(f"Vous avez dit: {prompt}")

st.caption("L'IA peut faire des erreurs. Veuillez vérifier les réponses")
