import json

from pathlib import Path
from base_tool import BaseTool

class QueryMetrics(BaseTool):

    @property
    def schema(self):
        return {
            "name": "query_metrics",
            "description": "Get the recent timeseries metrics for a given app name to understand when the issue started and correlate with other events.",
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
            file_path = base_path / "mock_data" / "metrics.json"
            
            app_name = input.get("app_name","default")

            with open(file_path, "r") as f:
                data = json.load(f)
                return json.dumps(data.get(app_name))
        except KeyError:
            return json.dumps({
                "error": "Missing metrics for the shared app name",
                "suggestion": "Not able to get the metrics for the app name"
            })
        except FileNotFoundError:
            return json.dumps({
                "error": "File does not exist",
                "suggestion": "The user must have configure the incorrect file path"
            })
        
