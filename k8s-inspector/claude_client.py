import anthropic
import os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)

class LLMClient:

    def __init__(self,api_key,model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    
    def ask(self,**kwargs):

        if not "model" in kwargs:
            kwargs["model"] = self.model
        response = self.client.messages.create(**kwargs)

        return response
