import json
import anthropic
import re

from config import Config
from models import Finding, Report


def iter_problem_pods(pods: list[dict]):
    for pod in pods:
        if pod["status"] not in ["Running","Succeeded"] or pod["restarts"] > 5 or pod["limits"] == {}:
            yield pod

def call_claude(pods: list[dict], config: Config) -> list[Finding]:

    client = anthropic.Anthropic(api_key=config.api_key)

    message = client.messages.create(
        model=config.model,
        max_tokens=config.max_token,
        messages = [
            {
                "role": "user",
                "content": f"Analyze these pods {pods} and identify any issues with them from the status or restart count or limits. Based on the analysis provide a json response of the form 'pod: str, 'issue': str, 'severity': 1|2|3, fix: str. No prose. Only retrun json, no markdown"
            }
        ],
    )

    findings = []

    for c in message.content:
        cleaned_text = re.sub(r"^```(?:json)?\s*\n?", "" , c.text)
        cleaned_text = re.sub(r"\n?```\s*$", "", cleaned_text)
        
        json_text = json.loads(cleaned_text)
        if isinstance(json_text, list):
            for j in json_text:
                finding = Finding(j["pod"],j["issue"],j["severity"],j["fix"])
                findings.append(finding)
        else:
            print(json_text)
            finding = Finding(json_text["pod"],json_text["issue"],json_text["severity"],json_text["fix"])
            findings.append(finding)

    return findings

def run_checks(snapshot:dict,config: Config) -> Report:
    
    pods = [p for p in snapshot["pods"]]
    problem_pods = list(iter_problem_pods(pods))
    if not problem_pods:
        return Report(snapshot["cluster_id"],[])
        
    findings = call_claude(problem_pods,config)
    return Report(snapshot["cluster_id"],findings)

