import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.streamable_http import streamable_http_client

async def main():

    # server params
    server_params_url = "http://localhost:8000/mcp"

    # create a server connection
    async with streamable_http_client(server_params_url) as (read_stream, write_stream):

        # create a client session 
        async with ClientSession(read_stream, write_stream) as session:

            # protocol init
            await session.initialize()

            tool_result = await session.list_tools()
            print("Available tools:")

            for tool in tool_result.tools:
                print(f"- {tool.name}: {tool.description}")

            resource_result = await session.list_resources()
            print("Available resources:")
            for resource in resource_result.resources:
                print(f"- {resource.name}: {resource.description}")

            calculator_result = await session.call_tool("calculator", arguments={"expression": "2 ** 2 + 3 * 4 + 1"})
            print(f"Calculator Result: {calculator_result}")

if __name__ == "__main__":
    print("Starting client...")
    asyncio.run(main())