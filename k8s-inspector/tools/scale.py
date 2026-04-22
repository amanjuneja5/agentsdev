import json

from pathlib import Path
from base_tool import BaseTool

class ScaleReplicas(BaseTool):

    @property
    def schema(self):
        return {
            "name": "scale_replicas",
            "description": "Scale the number of replicas for a given app name",
            "input_schema": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "K8s app name"
                    }
                },
                "required": ["app_name"]
            }
        }

    def is_write(self):
        return True

    def execute(self, input):

        try:
            base_path = Path(__file__).cwd()
            file_path = base_path / "mock_data" / "write_responses.json"
            
            app_name = input.get("app_name","default")

            with open(file_path, "r") as f:
                data = json.load(f)
                rollback_responses = data.get("scale_responses")
                return json.dumps(rollback_responses.get(app_name))
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
        
