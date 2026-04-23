import sys
import json
import os

from claude_client import LLMClient
from tools import ALL_SCHEMAS, TOOL_MAP

def main():
    
    SYSTEM_PROMPT = """\
You are an SRE investigation agent. Your job is to diagnose issues in a \
Kubernetes-based production environment.
 
Investigation approach:
1. Start broad — check pod status to identify unhealthy workloads
2. Narrow down — look at logs and metrics for specific pods showing issues
3. Correlate — check deployment history or error logs or metrics to find what changed and when 
4. Check the query metrics to validate the resource pressure
4. Synthesize — produce a root cause analysis with evidence
 
Rules:
- Always start by understanding the current state before diving into specifics
- Follow the evidence — let what you find guide your next tool call
- Don't call tools you don't need. If pod status shows everything healthy, say so
- When you have enough evidence, stop investigating and present your findings
- Be specific: cite pod names, timestamps, error messages, and version numbers
- Suggest both immediate remediation and long-term fixes
"""

    if len(sys.argv) < 2:
        print("Not enough argument. Use python agent.py <user query>")
        sys.exit(1)
    
    query = sys.argv[1]

    prompt = [
        {
            "content": query,
            "role": "user"
        }
    ]

    llm = LLMClient(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    respone = llm.ask(
        system=SYSTEM_PROMPT,
        messages=prompt,
        tools=ALL_SCHEMAS,
        max_tokens=1024,
        tool_choice={"type": "auto", "disable_parallel_tool_use": True},
        temperature=0
    )

    print(respone.stop_reason)

    while respone.stop_reason == "tool_use":
        tool_use = next(block for block in respone.content if block.type == "tool_use")
        print(f"Tool: {tool_use.name}")
        print(f"Input: {tool_use.input}")
        

        tool_instance = TOOL_MAP[tool_use.name]

        if tool_instance.is_write:
            print(f"Agent wants to run the tool {tool_instance.name}({tool_use.input})")
            approval = input("Approve? (y/n):")
            if approval.lower() != "y":
                result =  json.dumps({
                    "error": "Action denied by operator",
                    "reason": "Human review rejected this action"
                })
            else:
                result = tool_instance.safe_execute(tool_use.input)
        else:
            result = tool_instance.safe_execute(tool_use.input)
        
        prompt.append(
            {
                "role": "assistant",
                "content": respone.content
            }
        )
        prompt.append(
            {
                "role": "user",
                "content" : [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result)
                    }
                ]
            }
        )

        respone = llm.ask(
            system = SYSTEM_PROMPT,
            messages=prompt,
            tools=ALL_SCHEMAS,
            max_tokens=1024,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            temperature=0
        )

    final_text = next(block for block in respone.content if block.type == "text")
    print(final_text.text)

    print(llm.usage.summary())


if __name__ == "__main__":
    main()