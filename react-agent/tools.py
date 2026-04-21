import json

_get_pod_status_tool_schema = {
    "name": "get_pod_status",
    "description": "List the pod status in a given namespace",
    "input_schema": {
        "type": "object",
        "properties": {
            "namespace": {"type":"string"}
        },
        "required": ["namespace"]
    }
}

_get_recent_deploys_tool_schema = {
    "name": "get_recent_deploys",
    "description": "Find the deployment history with versions, changes, resource specs, etc for a given app name",
    "input_schema": {
        "type": "object",
        "properties": {
            "app_name": {"type":"string"}
        },
        "required": ["app_name"]
    }
}

_get_error_logs_tool_schema = {
    "name": "get_error_logs",
    "description": "Provide the recent log lines for a specified pod",
    "input_schema": {
        "type": "object",
        "properties": {
            "pod_name": {"type":"string"}
        },
        "required": ["pod_name"]
    }
}

incident_tools = [_get_pod_status_tool_schema,_get_error_logs_tool_schema,_get_recent_deploys_tool_schema]


def get_pod_status(namespace: str):

    with open("./mock_data/pod_status_prod.json","r") as f:
        data = json.load(f)
        return json.dumps(data)

def get_recent_deploys(app_name: str):

    with open("./mock_data/deploy_history.json","r") as recent_deploy:
        deploys = json.load(recent_deploy)
        return deploys.get(app_name)

def get_error_logs(pod_name: str):

    with open("./mock_data/error_logs.json","r") as error_logs:
        logs = json.load(error_logs)
        return logs.get(pod_name)


def main():
    print(get_recent_deploys("payments-api"))

if __name__ == "__main__":
    main()