import asyncio
import json
import litellm
import warnings

from contextlib import AsyncExitStack
from typing import Any, Dict, List
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from dotenv import load_dotenv

warnings.filterwarnings("ignore")
load_dotenv()

session: ClientSession = None
exit_stack = AsyncExitStack()
model = "gemini/gemini-3.5-flash-lite"

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
        server_mcp_url = "http://127.0.0.1:8000/mcp"

    # 1) Open an HTTP connection, which yields (read_stream, write_stream).
    # 2) Wrap those in a ClientSession so we can talk to MCP.
        async with streamable_http_client(server_mcp_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                global session
                session = mcp_session

                # Initialize the MCP connection
                await session.initialize()

                # Example query
                query = "What is 90 multiplied by 68.6? Use MCP tools if available."
                print(f"\nQuery: {query}")
                response = await process_query(query)
                print(f"\nFinal Response: {response}")

        print("Connection terminated successfully!")
    finally:
        await cleanup()

if __name__ == "__main__":
    print("running client_sse_llm.py...")
    asyncio.run(main())
