import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage

async def main():

    async for message in query(
        prompt="Write unit tests for utils.py, run them, and fix any failures",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Edit", "Glob", "WebSearch"],
            permission_mode="acceptEdits",
            system_prompt="You are a senior python developer. Always use the PEP 8 style guidelines"
        ),
    ):

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if hasattr(block, "text"):
                    print(block.text)
                elif hasattr(block, "name"):
                    print (f"Tool: {block.name}")
        elif isinstance(message,ResultMessage):
            print(f"Done: {message.subtype}")


asyncio.run(main())