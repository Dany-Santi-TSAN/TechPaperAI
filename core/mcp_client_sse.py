from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp import SamplingMessageContentBlock, SamplingToolsCapability
from typing import List, Dict, TypedDict, Callable, Optional
from contextlib import AsyncExitStack
import asyncio
import nest_asyncio
import logging

from config.llm_config import LLMConfig
from config.sse_config import SseConfigSTClient

nest_asyncio.apply()
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

logger = logging.getLogger(__name__)


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



    async def _call_llm_sync(self, messages):
        """
        Wrap sync LLM call into async-safe executor.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.anthropic.messages.create(
                max_tokens=self.config.max_tokens,
                model=self.config.model,
                system=self.config.system_prompt,
                tools=self.available_tools,
                messages=messages,
                timeout=self.config.default_timeout,
            ),
        )

    async def process_query(
        self,
        query: str,
        on_update: Optional[Callable[[str], None]] = None,
        ) -> str:
        """
        Process query with remote server tool support
        Agentic query processing with explicit safety guardrails.
        """
        ###################################
        # Guardrail 1
        # Prevents infinite tool-call loops
        ###################################

        MAX_TOOL_CALL = self.config.max_tool_call
        tool_call_counter = {}

        logger.info(f"NEW Query: {query[:200]}...")
        logger.info(f"MAX_TOOL_CALL limit: {MAX_TOOL_CALL}")

        messages = [{"role": "user", "content": query}]

        if on_update:
            on_update(f"🤖 Calling LLM ({self.config.model})")

        # Initial LLM call
        response = await self._call_llm_sync(messages)
        logger.info(f"Initial stop_reason: {response.stop_reason}")

        iteration = 0

        # Agentic loop
        while response.stop_reason == "tool_use":
            iteration += 1
            logger.info(f"ITERATION {iteration} Start")

            assistant_content = []
            tool_results_content = []
            tool_called_this_turn = False

            for content in response.content:

                if content.type == "text":
                    assistant_content.append(content)

                elif content.type == "tool_use":
                    tool_called_this_turn = True
                    assistant_content.append(content)

                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    current_count = tool_call_counter.get(tool_name, 0) + 1
                    logger.info(f" Tool: {tool_name} called {current_count} /{MAX_TOOL_CALL}")
                    logger.info(f" Args: {tool_args}")

                    tool_call_counter[tool_name] = current_count

                    if current_count > MAX_TOOL_CALL:
                        logger.warning(f"⚠️ Tool '{tool_name} BLOKED (limited reached)")
                        if on_update:
                            on_update(f"⚠️ Tool '{tool_name}' call limit reached. Skipping")
                        continue

                    # Guardrail 1 - Count per tool

                    tool_call_counter[tool_name] = (
                    tool_call_counter.get(tool_name, 0) + 1
                    )

                    if tool_call_counter[tool_name] > MAX_TOOL_CALL:
                        if on_update:
                            on_update(
                                f"⚠️ Tool '{tool_name}' call limit reached. Skipping."
                            )
                        continue

                    if on_update:
                        on_update(f"Calling tool: {tool_name}")

                    session = self.tool_to_session.get(tool_name)
                    if not session:
                        if on_update:
                            on_update(f"❌ No session for tool '{tool_name}'")
                        continue

                    # Tool call is already async
                    logger.info(f"Calling tool via MCP session...")
                    tool_result = await session.call_tool(
                        tool_name,
                        arguments=tool_args,
                    )
                    logger.info(f"✅ Tool result received : {type(tool_result)} ")
                    logger.info(f"   Content: {tool_result.content[:200]}...")

                    tool_results_content.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": tool_result.content,
                        }
                    )
            ###################################
            # Guardrail 2 — Exit if no new tool results were produced
            # Prevents useless extra LLM calls
            ###################################
            if not tool_results_content:
                logger.warning("⚠️ No tool results - BREAKING loop")
                break

            logger.info(f"✅ Got {len(tool_results_content)} tool result(s)")

            # Append assistant + tool results
            messages.append(
                {"role": "assistant", "content": assistant_content}
            )
            messages.append(
                {"role": "user", "content": tool_results_content}
            )

            ###################################
            # Guardrail 3 — Explicit stop instruction to the LLM
            # Tell the model when to stop calling tools
            ###################################
            messages.append(
                {
                "role": "system",
                "content": (
                    "The tool results above are sufficient unless strictly necessary. "
                    "Do NOT call the same tool again with similar arguments. "
                    "If enough information is available, produce a final answer."
                    ),
                }
            )

            if on_update:
                on_update("Processing tool results...")

            # Next LLM call
            response = await self._call_llm_sync(messages)
            logger.info(f" Next stop_reason: {response.stop_reason}")

        # Final response
        final_text = "".join(
            content.text
            for content in response.content
            if content.type == "text"
        )

        logger.info(f"✅ Done - Total iterations: {iteration}")
        return final_text

    async def cleanup(self) -> None:
        """Close all MCP connections."""
        print("\n🧹 Cleaning up...")
        await self.exit_stack.aclose()
        print("\n ✅ Cleanup completed")
