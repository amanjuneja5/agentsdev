import sys
import json
import os
import yaml

from claude_client import LLMClient

def load_snapshot(path):

    with open(path,"r") as snapshot:
        return list(yaml.safe_load_all(snapshot))

    


def main():
    
    if len(sys.argv) < 2:
        print("Not enough argument. Use python validator.py <pod.yaml>")
        sys.exit(1)
    
    snapshot = load_snapshot(sys.argv[1])
    
    prompt = [
        {
            "content": f"Analyze this Kubernetes manifest for any security vulnerabilities or missing best practices - {snapshot} and provide a structred result covering pod name, severity, issues found summary in 1 line, suggested fixes summary",
            "role": "user"
        }
    ]

    tools = [
        {
            "name": "k8s_yaml_validator",
            "description": "Check the kubenretes manifests for security vulnerabilities and best practices.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "manifest": {"type": "array"}
                },
                "required": ["manifest"]
            }
        }
    ]

    llm = LLMClient(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    respone = llm.ask(messages=prompt,tools=tools)

    print(respone.stop_reason)

    tool_use = next(block for block in respone.content if block.type == "tool_use")
    print(f"Tool: {tool_use.name}")
    print(f"Input: {tool_use.input}")
    

if __name__ == "__main__":
    main()