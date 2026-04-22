import json

from pathlib import Path
from base_tool import BaseTool

class ErrorLogs(BaseTool):

    @property
    def schema(self):
        return {
            "name": "get_error_logs",
            "description": "Get the error logs for the Kuberentes pod.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pod_name": {
                        "type": "string",
                        "description": "K8s pod name"
                    }
                },
                "required": ["pod_name"]
            }
        }

    def execute(self, input):

        try:
            base_path = Path(__file__).cwd()
            file_path = base_path / "mock_data" / "error_logs.json"
            
            pod_name = input.get("pod_name","default")

            with open(file_path, "r") as f:
                data = json.load(f)
                return json.dumps(pod_name)
        except KeyError:
            return json.dumps({
                "error": "App name seems to not exist in the recent deploy",
                "suggestion": "Check if the right app name is used or if we don't have access to it"
            })
        except FileNotFoundError:
            return json.dumps({
                "error": "file does not exist",
                "suggestion": "The user must have configure the incorrect file path"
            })
        
