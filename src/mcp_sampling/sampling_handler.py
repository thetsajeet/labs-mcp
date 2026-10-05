from fastmcp.client.sampling import SamplingMessage, SamplingParams, RequestContext
from litellm import acompletion
from dotenv import load_dotenv
import os
from fastmcp import Client
import asyncio
from pathlib import Path

load_dotenv()

async def sampling_handler(messages: list[SamplingMessage],
                           params: SamplingParams,
                           ctx: RequestContext) -> str:

    """Handle sampling requests using LiteLLM and Gemini."""

    chat_messages = []
    
    if params.systemPrompt:
        chat_messages.append({"role": "system", 
                              "content": params.systemPrompt})
                              
    for m in messages:
        if m.content.type == "text":
            chat_messages.append({"role": m.role, 
                                  "content": m.content.text})

    try:
        response = await acompletion(model="gemini/gemini-3.5-flash-lite",
                                     messages=chat_messages,
                                     api_key=os.environ.get("GEMINI_API_KEY"),
        )
        generated_text = response["choices"][0]["message"]["content"]
    
    except Exception as e:
        generated_text = f"[Error: LLM failed: {e}]"

    return generated_text

client = Client(Path(__file__).with_name("server_context.py"),
                sampling_handler=sampling_handler,
                mode="legacy")

async def main():
    async with client:
        result = await client.call_tool("summarize_document", 
                                        {"document_text": "This is Wakanda"})
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
