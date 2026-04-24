import anthropic
import os

PRICING = {
    "claude-sonnet-4-6": { "input": 3.00 , "output": 15.00 },
    "claude-opus-4-7": { "input": 5.00 , "output": 25.00 },
    "claude-haiku-4-5-20251001" : { "input": 1.00 , "output": 5.00 }
}

class UsageTracker:

    def __init__(self,model):
        self.model = model
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.call_count = 0
        self.pricing = PRICING.get(model, "claude-sonnet-4-6")

    def record(self, usage):

        self.total_input_tokens += usage.input_tokens
        self.total_output_tokens += usage.output_tokens
        self.call_count += 1

    @property
    def input_cost(self):
        return (self.pricing["input"] * self.total_input_tokens) / 1000000

    @property
    def output_cost(self):
        return (self.pricing["output"] * self.total_output_tokens) / 1000000
    
    @property
    def total_cost(self):
        return self.input_cost + self.output_cost

    def summary(self):

        return (
            f"API calls: {self.call_count}\n"
            f"Input tokens: {self.total_input_tokens}\n"
            f"Output tokens: {self.total_output_tokens}\n"
            f"Input cost: {self.input_cost:.6f}\n"
            f"Output cost: {self.output_cost:.6f}\n"
            f"Total cost: {self.total_cost:.6f}"
        )

class LLMClient:

    def __init__(self,api_key,model="claude-sonnet-4-6"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.usage = UsageTracker(model)

    
    def ask(self,**kwargs):

        if not "model" in kwargs:
            kwargs["model"] = self.model
        response = self.client.messages.create(**kwargs)
        self.usage.record(response.usage)

        return response
