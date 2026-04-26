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
                        "description": "Full pod name"
                    },
                    "level": {
                        "type": "string",
                        "enum": ["ALL", "ERROR", "WARN", "INFO"],
                        "description": "Filter by minimum log level. 'ALL' returns everything. Default: ALL"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Max log lines to return (default 20, max 50)"
                    }
                },
                "required": ["pod_name"]
            }
        }

    def execute(self, input):

        try:
            pod_name = input.get("pod_name","default")
            level_filter = input.get("level","ALL")
            max_lines = min(input.get("lines",20),50)

            base_path = Path(__file__).cwd()
            file_path = base_path / "mock_data" / "error_logs.json"
            
            with open(file_path, "r") as f:
                all_logs = json.load(f)
                
            if pod_name not in all_logs:

                prefix = pod_name.split("-")[0]
                matches = [ k for k in all_logs if k.startswith(prefix) ]
                return json.dumps({
                    "error": f"No logs found for the pod {pod_name}",
                    "similar_pods": matches if matches else list(all_logs.keys()),
                    "suggestion": "Check the exact pod name from the get_pod_status output"
                })
            
            entries = all_logs[pod_name]

            if not entries:
                return json.dumps({
                    "pod": pod_name,
                    "log_lines": [],
                    "note": "No logs available - pod may not have started"
                })
            
            level_priority = {"ERROR": 3, "WARN": 2, "INFO": 1}
            if level_filter != "ALL":
                min_priority = level_priority.get(level_filter,0)
                entries =[
                    e for e in entries
                    if level_priority.get(e.get("level","INFO"),0) >= min_priority
                ]
            
            entries = entries[:max_lines]

            return json.dumps({
                "pods": pod_name,
                "filter": level_filter,
                "returned": len(entries),
                "log_lines": entries
            })

        except KeyError:
            return json.dumps({
                "error": "Pod name seems to not exist in the recent deploy",
                "suggestion": "Check if the right app name is used or if we don't have access to it"
            })
        except FileNotFoundError:
            return json.dumps({
                "error": "file does not exist",
                "suggestion": "The user must have configure the incorrect file path"
            })
        
