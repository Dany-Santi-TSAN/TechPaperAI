from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp import SamplingMessageContentBlock, SamplingToolsCapability
from typing import List, Dict, TypedDict, Callable, Optional
from contextlib import AsyncExitStack
import nest_asyncio

from config.llm_config import LLMConfig
from config.sse_config import SseConfigSTClient

nest_asyncio.apply()
load_dotenv()


class ToolDefinition(TypedDict):
    """Type definition for tool structure."""
    name: str
    description: str
    input_schema: dict


class MCPRemoteStreamlitClient:
    """MCP Remote server for ChatBot AI with resources and prompts support."""

    def __init__(self, config: LLMConfig = None, remote_config: SseConfigSTClient = None):
        """Initialize MCP Remote server for ChatBot AI."""
        self.config = config or LLMConfig()
        self.sessions: List[ClientSession] = []
        self.remote_config = remote_config or SseConfigSTClient()
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=self.config.anthropic_key)
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}

    async def connect_to_sse_server(self, server_url: str):
        """Connect to remote MCP server via SSE."""
        try :
            streams = await self.exit_stack.enter_async_context(
                sse_client(url= server_url)
            )
            read, write = streams
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)

            # List and register tools
            response = await session.list_tools()
            tools = response.tools
            tool_names = [t.name for t in tools]
            print(f"✓ Connected to '{server_url}' with {len(tools)} tools: {tool_names}")

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

        except Exception as e:
            print(f"❌ Failed to connect to '{server_url}': {e}")


    async def list_prompts(self):
        """Display all prompts."""
        try:
            session = self.sessions[0]
            prompts_response = await session.list_prompts()

            print("\n📝 Available prompts:")
            for prompt in prompts_response.prompts:
                print(f"  • {prompt.name}")
                if prompt.description:
                    print(f"    {prompt.description}")
        except Exception as e:
            print(f"❌ Error listing prompts: {e}")

    async def execute_prompt(self, prompt_name: str, arguments: dict):
        """Execute prompt - MCP routes automatically."""
        try:
            session = self.sessions[0]
            result = await session.get_prompt(prompt_name, arguments=arguments)

            if result.messages:
                prompt_text = result.messages[0].content.text
                await self.process_query(prompt_text)
            else:
                print(f"⚠️ Empty prompt result: {prompt_name}")

        except Exception as e:
            print(f"❌ Error executing prompt '{prompt_name}': {e}")


    async def process_query(self, query: str, on_update=None) -> str:
        """
        Process query with remote server tool support.

        Args:
            query: User's question
            on_update: Optional callback(message) for updates

        Returns:
            Final response text
        """
        messages = [{"role": "user", "content": query}]

        if on_update:
            on_update(f"🤖 Calling LLM: {self.config.model}")

        # Initial LLM call
        response = self.anthropic.messages.create(
            max_tokens=self.config.max_tokens,
            model=self.config.model,
            system="""You are TechPaperAI, specialized in academic paper research.
            When calling tools:
                - Use default parameter values unless user explicitly specifies different values
                - Don't arbitrarily increase max_results beyond the default
                - If user says 'search papers', use default max_results'""",
            tools=self.available_tools,
            messages=messages,
            timeout=self.config.default_timeout
        )

        # Agentic loop: continue while LLM requests tools
        while response.stop_reason == "tool_use":
            assistant_content = []
            tool_results_content = []

            # Process each content block in LLM's response
            for content in response.content:
                if content.type == "text":
                    # Text response: display and store
                    assistant_content.append(content)

                elif content.type == "tool_use":
                    # Tool request: store and prepare to execute
                    assistant_content.append(content)

                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    if on_update:
                        on_update(f"Calling tool : {tool_name}")

                    # Find correct session for this tool
                    session = self.tool_to_session.get(tool_name)
                    if not session:
                        if on_update:
                            on_update(f"❌ No session for tool '{tool_name}'")
                        continue

                    # Call tool via appropriate session
                    tool_result = await session.call_tool(
                        tool_name,
                        arguments=tool_args
                    )

                    # Store tool result
                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": tool_result.content
                    })

            # Add assistant response (with tool_use blocks)
            messages.append({
                "role": "assistant",
                "content": assistant_content
            })

            # Add tool results
            messages.append({
                "role": "user",
                "content": tool_results_content
            })

            if on_update:
                on_update("Processing results...")

            # Next LLM response
            response = self.anthropic.messages.create(
                max_tokens=self.config.max_tokens,
                model=self.config.model,
                tools=self.available_tools,
                messages=messages,
                timeout=self.config.default_timeout
            )

        # Final response
        final_text = ""
        for content in response.content:
            if content.type == "text":
                final_text += content.text

        return final_text

    async def cleanup(self) -> None:
        """Close all MCP connections."""
        print("\n🧹 Cleaning up...")
        await self.exit_stack.aclose()
        print("\n ✅ Cleanup completed")
