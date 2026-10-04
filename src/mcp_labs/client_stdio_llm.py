import asyncio
import json
import litellm
import warnings

from contextlib import AsyncExitStack
from typing import Any, Dict, List
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

session: ClientSession = None
exit_stack = AsyncExitStack()
model = "gemini/gemini-3.5-flash-lite"

async def connect_to_server(server_script_path: str = "server_stdio.py"):
    """Connect to the MCP server same as we did with the client_stdio.py script."""

    global session, exit_stack

    server_params = StdioServerParameters(
        command = "uv",
        args = [
            "--directory",
            "/Users/thetsajeet/Documents/workspace/labs/mcp_labs/src/mcp_labs",
            "run",
            server_script_path
        ]
    )

    stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))

    read_stream, write_stream = stdio_transport

    session = await exit_stack.enter_async_context(ClientSession(read_stream, write_stream))

    await session.initialize()


async def get_mcp_tools() -> List[Dict[str, Any]]:
    """Retrieve the MCP tools in Litellm/Gemini function format."""
        
    global session
    
    tools_result = await session.list_tools()

    print("Connected to server with tools:")
    for tool in tools_result.tools:
        print(f"  • {tool.name}: {tool.description}")

    formatted = []
    for tool in tools_result.tools:
        formatted.append({"type": "function", "function": {"name": tool.name, "description": tool.description,"parameters": tool.input_schema}})

    return formatted

async def process_query(query: str) -> str:
    """Process LLM query and decide if tool call is required"""

    global session, model
    tools = await get_mcp_tools()

    messages = [{'role': 'user', 'content': query}]

    print(f"Requesting response from {model}...")
    first_response = await litellm.acompletion(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice='auto'
    )

    calls = None
    assistant_message = first_response.choices[0].message
    messages.append(assistant_message)
    calls = assistant_message.function_call or assistant_message.tool_calls

    while calls:
        calls_list = calls if isinstance(calls, list) else [calls]

        for call in calls_list:

            if call.function:
                tool_name = call.function.name
                tool_args = call.function.arguments
            else:
                tool_name = call.name
                tool_args = call.arguments

            try:
                parsed_args = json.loads(tool_args)
            except Exception:
                parsed_args = tool_args

            print(f"\nAssistant requests tool: {tool_name}({parsed_args})")
            permission = input("Allow execution? (y/n): ").strip().lower()

            if permission == 'y':
                result = await session.call_tool(tool_name, arguments=parsed_args)
                tool_output = result.content[0].text
                print(f"→ {tool_name} returned: {tool_output}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id if hasattr(call, "id") else None,
                    "content": tool_output,
                })
            else:
                denied_msg = f"[Tool '{tool_name}' denied]"
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id if hasattr(call, "id") else None,
                    "content": denied_msg,
                })
                print(f"→ Skipped {tool_name}")

        next_response = await litellm.acompletion(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )

        assistant_message = next_response.choices[0].message
        if not assistant_message.function_call and not assistant_message.tool_calls:
            break

        messages.append(assistant_message)
        calls = assistant_message.tool_calls or assistant_message.function_call

    return assistant_message.content.strip() if assistant_message.content else ""

async def cleanup():
    """Close the MCP client session cleanly."""
    global exit_stack
    await exit_stack.aclose()

async def main():
    try:
        await connect_to_server("server_stdio.py")

        # not possible to do both of them in one iteration as it needs to store the result in memory.
        query = """
        1. What is the current form payload available? 
        store the result in form_payload key in memory.
        2. Use the form payload and update it's name to ajeet in the payload. 
        """

        print(f"\nQuery: {query}")

        response = await process_query(query)
        print(f"\nFinal Response: {response}")
    finally:
        await cleanup()

    print("Connection terminated successfully!")

if __name__ == "__main__":
    print("running client_stdio_llm.py...")
    asyncio.run(main())
