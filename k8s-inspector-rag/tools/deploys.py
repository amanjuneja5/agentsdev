import json

from pathlib import Path
from base_tool import BaseTool

class RecentDeploys(BaseTool):

    @property
    def schema(self):
        return {
            "name": "get_recent_deploys",
            "description": "Get recent deployment history. Returns timestamp, version, previous_version, deployed_by, list of changes, and resource_spec (CPU/memory requests and limits) for each deployment.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "app_name": {
                        "type": "string",
                        "description": "Kubernetes app name"
                    }
                },
                "required": ["app_name"]
            }
        }

    def execute(self, input):

        try:
            base_path = Path(__file__).cwd()
            file_path = base_path / "mock_data" / "deploy_history.json"
            
            app_name = input.get("app_name","default")

            with open(file_path, "r") as f:
                data = json.load(f)
                return json.dumps(data.get(app_name))
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
        
