import streamlit as st
import asyncio
from pathlib import Path
import sys
import logging

sys.path.append(str(Path(__file__).parent.parent))

from config.http_config import HTTPConfigSTClient
from core.mcp_client_http import MCPRemoteStreamlitClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# === 1. Configuration Validation ===
try:
    config = HTTPConfigSTClient()
    if not config.backend_url:
        raise ValueError("MCP_BACKEND_URL is missing")
    logger.info(f"Configuration loaded. Backend: {config.backend_url}")
except Exception as e:
    st.error(f"❌ Bootstrapping Error: {e}")
    st.stop()

# === 2. Persistent MCP Session ===
@st.cache_resource
def get_mcp_resources(url: str):
    """
    This factory creates a single event loop and client
    instance that persists across Streamlit's reruns
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    client = MCPRemoteStreamlitClient()

    try:
        # Perform initial handshake in the persistent loop
        loop.run_until_complete(client.connect_to_http_server(url))
        return client, loop
    except Exception as e:
        logger.error(f"Handshake failed: {e}")
        raise e

# Initialize connection (Streamlit handles the spinner/loading automatically via cache_resource)
chatbot, mcp_loop = get_mcp_resources(config.backend_url)


# === 3. Streamlit UI Setup ===
st.set_page_config(
    page_title="TechPaper AI",
    page_icon="🤖💼​​",
    layout="centered",
    initial_sidebar_state="expanded"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

async def run_query_async(chatbot, prompt, on_update):
    return await chatbot.process_query(
        prompt,
        on_update=on_update
    )

st.title("TechPaper AI")
st.header("Your eyes on the frontier of tech research.")
st.text("Scan, summarize, and stay ahead -> automatically")

# === 4. Display chat history ===

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# === 5. Interaction Logic ===
# Process query avec callback

# Input in chat
prompt = st.chat_input("Votre requête ici:")
if prompt:
    # Add state user message to history
    st.session_state.messages.append({"role":"user", "content":prompt})

    # Healcheck
    is_healthy = mcp_loop.run_until_complete(chatbot.check_health())

    if not is_healthy:
        with st.warning("🔄 Connection lost. Re-establishing session..."):
            st.cache_resource.clear()
            st.rerun()

    # Display message
    with st.chat_message("user"):
        st.write(prompt)

    # Process query with status updates
    with st.chat_message("assistant"):
        with st.status("Processing...") as status:

            def update_status(msg):
                status.update(label=msg)

            # Use the persistent loop to run the query
            response = mcp_loop.run_until_complete(
                chatbot.process_query(prompt, on_update=update_status)
            )

            status.update(label="✅ Complete!", state="complete")
            st.write(response)

        st.session_state.messages.append({"role": "assistant", "content": response})


st.caption("L'IA peut faire des erreurs. Veuillez vérifier les réponses")
