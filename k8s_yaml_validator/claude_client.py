import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

class LLMClient:

    def __init__(self,api_key,model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    
    def ask(self,messages=[],tools=[]):

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=messages,
            tools=tools
        )

        return response
