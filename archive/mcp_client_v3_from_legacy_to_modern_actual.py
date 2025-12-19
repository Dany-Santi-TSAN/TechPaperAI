from dotenv import load_dotenv
from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio
import nest_asyncio

from config.llm_config import LLMConfig

nest_asyncio.apply()
load_dotenv()


class ToolDefinition(TypedDict):
    """Type definition for tool structure."""
    name: str
    description: str
    input_schema: dict


class MCP_ChatBot:
    """Multi-server MCP ChatBot with resources and prompts support."""

    def __init__(self, config: LLMConfig = None):
        """Initialize multi-server MCP ChatBot."""
        self.config = config or LLMConfig()
        self.sessions: List[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=self.config.anthropic_key)
        self.available_tools: List[ToolDefinition] = []
        self.tool_to_session: Dict[str, ClientSession] = {}
        self.available_resources: Dict[str, ClientSession] = {}
        self.available_prompts: Dict[str, ClientSession] = {}

    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """
        Connect to a single MCP server.

        Args:
            server_name: Name of the server
            server_config: Server configuration dict
        """
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await session.initialize()
            self.sessions.append(session)

            # List and register tools
            response = await session.list_tools()
            tools = response.tools
            tool_names = [t.name for t in tools]
            print(f"✓ Connected to '{server_name}' with {len(tools)} tools: {tool_names}")

            for tool in tools:
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                })

        except Exception as e:
            print(f"❌ Failed to connect to '{server_name}': {e}")

        # Register resources in session
        try:
            resources_response = await session.list_resources()
            for resource in resources_response.resources:
                self.available_resources[resource.uri] = session

        except Exception as e:
            print(f" No resources from '{server_name}' : {e}")

        # Register prompts in session
        try :
            prompts_response = await session.list_prompts()
            for prompt in prompts_response.prompts:
                self.available_prompts[prompt.name] = session

        except Exception as e:
            print (f"No prompt available from '{server_name}' : {e}")


    async def connect_to_multiple_servers(self) -> None:
        """Connect to all configured MCP servers from server_config.json."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)

            servers = data.get("mcpServers", {})

            if not servers:
                print("⚠️  No servers configured")
                return

            print(f"\n🔌 Connecting to {len(servers)} server(s)...\n")

            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)

        except FileNotFoundError:
            print("❌ server_config.json not found!")
            raise
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            raise

    async def list_prompts(self):
        """Display all prompts"""
        print("\n Available prompts:")
        for name in self.available_prompts.keys():
            print(f"{name}")

    async def execute_prompt(self, prompt_name: str, arguments: dict):
        """Execute prompt"""
        session = self.available_prompts.get(prompt_name)
        if session:
            result = await session.get_prompt(prompt_name, arguments=arguments)
            prompt_text = result.messages[0].content.text
            await self.process_query(prompt_text)

    async def process_query(self, query: str) -> None:
        """
        Process query with multi-server tool support.

        Args:
            query: User's question
        """
        messages = [{"role": "user", "content": query}]

        # Initial LLM call
        response = self.anthropic.messages.create(
            max_tokens=self.config.max_tokens,
            model=self.config.model,
            system="""When calling tools:
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
                    print(content.text)
                    assistant_content.append(content)

                elif content.type == "tool_use":
                    # Tool request: store and prepare to execute
                    assistant_content.append(content)

                    tool_name = content.name
                    tool_args = content.input
                    tool_id = content.id

                    print(f"🔧 Calling '{tool_name}' with args: {tool_args}")

                    # Find correct session for this tool
                    session = self.tool_to_session.get(tool_name)
                    if not session:
                        print(f"❌ No session for tool '{tool_name}'")
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

            # Next LLM response
            response = self.anthropic.messages.create(
                max_tokens=self.config.max_tokens,
                model=self.config.model,
                tools=self.available_tools,
                messages=messages,
                timeout=self.config.default_timeout
            )

        # Final response
        for content in response.content:
            if content.type == "text":
                print(f"\n{content.text}")

    async def chat_loop(self) -> None:
        """Interactive chat loop."""
        print("\n" + "=" * 60)
        print("🤖 MCP Multi-Server ChatBot Ready!")
        print("=" * 60)
        print(f"📊 Total tools: {len(self.available_tools)}")
        print(f"📚 Resources: {len(self.available_resources)}")
        print(f"📝 Prompts: {len(self.available_prompts)}")
        print("\nCommands:")
        print("  @folders               - List available topics")
        print("  @{topic}               - Get papers for a topic")
        print("  /prompts               - List available prompts")
        print("  /prompt topic={name} num_papers{args}  - Execute a prompt")
        print("  example : /prompt generate_search_prompt topic=quantum num_papers=3")
        print()
        print("Type 'quit' to exit.\n")

        while True:
            try:
                query = input("Your Query: ").strip()

                if query.lower() in ["quit", "exit"]:
                    print("\n👋 See You!")
                    break

                if not query:
                    continue

                if query.startswith("@"):
                    resource_name = query[1:].strip().lower().replace(" ", "_")
                    uri = "papers://folders" if resource_name == "folders" else f"papers://{resource_name}"

                    session = self.sessions[0]  # MCP route la ressource
                    result = await session.read_resource(uri)

                    if result.contents:
                        print(result.contents[0].text)
                    else:
                        print(f"⚠️ Empty resource: {uri}")

                    continue

                elif query == "/prompts":
                    await self.list_prompts()
                    continue

                elif query.startswith("/prompt"):
                    query_parts = query.split()
                    name = query_parts[1]
                    args = dict(p.split("=") for p in query_parts[2:] if "=" in p)
                    await self.execute_prompt(name, args)
                    continue

                await self.process_query(query)
                print("\n" + "=" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\n👋 See You!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self) -> None:
        """Close all MCP connections."""
        print("\n🧹 Cleaning up...")
        await self.exit_stack.aclose()
        print("\n ✅ Cleanup completed")


async def main():
    """Main entry point."""
    chatbot = MCP_ChatBot()
    try:
        await chatbot.connect_to_multiple_servers()
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
