import anthropic
import os
import json

pods_json = {}

with open("pods.json","r") as pods:
    pods_json = json.load(pods)


client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY")
)


messages = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=500,
    messages=[
        {
            "content": f"summarize this pod json {pods_json}",
            "role" : "user"
        }
    ]
)

input_cost = (3 * messages.usage.input_tokens)/1000000
output_cost = (15 * messages.usage.output_tokens)/1000000

print(f"Input cost - ${input_cost}")
print(f"Output cost - ${output_cost}")

print(f"Total cost - ${input_cost + output_cost}")