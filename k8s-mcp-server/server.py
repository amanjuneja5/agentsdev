import json
from pathlib import Path

from k8s_tool import fetch_pod_status, fetch_error_logs, fetch_metrics, fetch_recent_deploys, execute_rollback, execute_scale, cluster_topology, health_summary
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("K8s MCP Server")

@mcp.tool(
    title="get_pod_status",
    description="Get status of all pods in a Kubernetes namespace. Returns name, status, restart count, age, image, and termination details for crashed pods. Use as a starting point for investigating cluster health issues."
)
def get_pod_status(namespace: str = "default"):
    return fetch_pod_status(namespace)
     
@mcp.tool(
    title="get_error_logs",
    description="Get the error logs for the Kuberentes pod."
)
def get_error_logs(pod_name: str, level: str = "ALL", lines: int = 20):
    return fetch_error_logs(pod_name,level,lines)

@mcp.tool(
    title="query_metrics",
    description="Get the recent timeseries metrics for a given app name to understand when the issue started and correlate with other events."
)
def query_metrics(app_name : str):
    return fetch_metrics(app_name)


@mcp.tool(
    title="get_recent_deploys",
    description="Get recent deployment history. Returns timestamp, version, previous_version, deployed_by, list of changes, and resource_spec (CPU/memory requests and limits) for each deployment."
)
def get_recent_deploys(app_name : str):
    return fetch_recent_deploys(app_name)

@mcp.tool(
    title="rollback_deployment",
    description="Rollbacks the deployment to the previous stable release. This is a write operation that modifies cluster state"
)
def rollback_deployment(app_name : str):
    return execute_rollback(app_name)

@mcp.tool(
    title="scale_replicas",
    description="Scale the number of replicas for a given app name. This is a write operation that modifies cluster state"
)
def scale_replicas(app_name : str, replicas: str):
    return execute_scale(app_name, replicas)

@mcp.resource(
    "cluster://{namespace}/topology",
    mime_type="application/json",
    description="Returns a compact overview of the cluster"
)
def get_cluster_topology(namespace:str):
    return cluster_topology(namespace)

@mcp.resource(
    "cluster://{namespace}/health-summary",
    description="Returns a short health report"
)
def get_health_summary(namespace:str):
    return health_summary(namespace)

@mcp.prompt(
    name="investigate_incident",
    description="Investigation prompt for a specific application incident"
)
def investigate_incident(app: str, env: str = "prod"):
    return f"""
    You are an SRE investigation agent diagnosing an issue with \
{app} in the {env} environment.
 
Investigation approach:
1. Start with get_pod_status(namespace="{env}") to identify unhealthy pods
2. For unhealthy pods, check get_error_logs for failure details
3. Check get_recent_deploys(app_name="{app}") to correlate with recent changes
4. Use query_metrics(app_name="{app}") to verify resource pressure
5. If remediation is needed, propose rollback_deployment or scale_replicas
 
Rules:
- Follow the evidence — let findings guide your next tool call
- If the issue is not related to {app}, investigate what IS unhealthy
- When proposing write operations, explain your reasoning clearly
- Present findings as: timeline, root cause, evidence, immediate fix, long-term fix
- Compare {env} with other environments if relevant (e.g. staging vs prod)
    """

if __name__ == "__main__":
    mcp.run(transport="stdio")