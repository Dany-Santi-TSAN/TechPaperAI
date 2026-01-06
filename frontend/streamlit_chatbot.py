import streamlit as st
import asyncio
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from config.sse_config import SseConfigSTClient
from core.mcp_client_sse import MCPRemoteStreamlitClient

# 1. Setup config
st.set_page_config(
    page_title="TechPaper AI",
    page_icon="🤖💼​​",
    layout="centered",
    initial_sidebar_state="expanded"
)

# 2. Iniatialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
    st.session_state.messages = []
    st.session_state.connected = False

# 3. Connect to backend
if not st.session_state.connected:
    with st.spinner("Connecting to backend..."):
        async def connect():
            chatbot = MCPRemoteStreamlitClient()
            config = SseConfigSTClient()
            await chatbot.connect_to_sse_server(config.backend_url)
            return chatbot

        st.session_state.chatbot = asyncio.run(connect())
        st.session_state.connected = True
    st.success("✅ Connected to backend!")
    st.balloons()

async def run_query_async(chatbot, prompt, on_update):
    return await chatbot.process_query(
        prompt,
        on_update=on_update
    )

st.title("TechPaper AI")
st.header("Your eyes on the frontier of tech research.")
st.text("Scan, summarize, and stay ahead -> automatically")

# 4. Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 5. Chatbot UI
# Process query avec callback

# Input in chat
prompt = st.chat_input("Votre requête ici:")
if prompt:
    # Add state user message to history
    st.session_state.messages.append({"role":"user", "content":prompt})

    # Display message
    with st.chat_message("user"):
        st.write(prompt)

    # Process query with status updates
    with st.chat_message("assistant"):
        with st.status("Processing...") as status:

            def update_status(msg):
                status.update(label=msg)

            response = asyncio.run(
                run_query_async(
                    st.session_state.chatbot,
                    prompt,
                    update_status
                )
            )

            status.update(label="✅ Complete!", state="complete")
            st.write(response)


st.caption("L'IA peut faire des erreurs. Veuillez vérifier les réponses")
