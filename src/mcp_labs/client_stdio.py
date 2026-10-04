import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():

    # server params
    server_params = StdioServerParameters(
        command = "uv",
        args = [
            "--directory",
            "/Users/thetsajeet/Documents/workspace/labs/mcp_labs/src/mcp_labs",
            "run",
            "server_stdio.py"
        ]
    )

    # create a server connection
    async with stdio_client(server_params) as (read_stream, write_stream):

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

            form_payload = await session.call_tool("form_payload")
            print(f"Form PayloadResult: {form_payload}")

            form_data = form_payload.structured_content
            print(f"Form data: {form_data}")
            form_updates = [
                {"name": "name", "value": "Ajeet"},
                {"name": "email", "value": "johnsmith@example.com"}
            ]

            form_filler = await session.call_tool("form_filler", arguments={"form_data": form_data, "updates": form_updates})
            print(f"Form Filler Result: {form_filler}")

if __name__ == "__main__":
    print("Starting client...")
    asyncio.run(main())