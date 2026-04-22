import json

from pathlib import Path
from base_tool import BaseTool

class PodStatus(BaseTool):

    @property
    def schema(self):
        return {
            "name": "get_pod_status",
            "description": "Get status of all pods in a Kubernetes namespace. Returns name, status, restart count, age, image, and termination details for crashed pods. Use as a starting point for investigating cluster health issues.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "namespace": {
                        "type": "string",
                        "description": "K8s namespace, e.g. 'prod', 'staging'. Defaults to 'default' if omitted."
                    }
                },
                "required": ["namespace"]
            }
        }

    def execute(self, input):

        try:
            base_path = Path(__file__).cwd()
            file_path = base_path / "mock_data" / "pod_status.json"
            
            namespace = input.get("namespace","default")

            with open(file_path, "r") as f:
                all_data = json.load(f)
                
            if namespace not in all_data:
                return json.dumps({
                    "error": f"Namespace {namespace} not found",
                    "available_namespaces": list(all_data.keys()),
                    "suggestion": f"Try one of {','.join(all_data.keys())}"
                })
            
            pods = all_data[namespace]

            summary = []
            for pod in pods:
                entry = {
                    "name": pod["name"],
                    "status": pod["status"],
                    "ready": pod["ready_containers"],
                    "age": pod["age"],
                    "restarts": pod["restarts"],
                    "app": pod["labels"].get("app","unknown"),
                    "version": pod["labels"].get("version","unknown"),
                }

                if "resources" in pod:
                    entry["resources"] = pod["resources"]
                
                is_unhealthy = (
                    pod["status"] not in ("Running","Succeeded")
                    or pod["restarts"] > 3
                    or not pod["ready"]
                )

                if is_unhealthy:
                    entry["node"] = pod["node"]
                    entry["containers"] = pod.get("containers",[])
                    conditions = pod.get("conditions",{})
                    if not conditions.get("PodScheduled", True):
                        entry["scheduling_failure"] = conditions.get("PodScheduled_message", "Unknown")
            
                summary.append(entry)

            healthy_count = sum(1 for p in summary if p["status"] == "Running" and p["restarts"] < 3)
            unhealthy_count = len(summary) - healthy_count

            return json.dumps({
                "namespace": namespace,
                "total_pods": len(summary),
                "healthy": healthy_count,
                "unhealthy": unhealthy_count,
                "pods": summary
            })


        except KeyError:
            return json.dumps({
                "error": "Pod status doesn't have namespace info",
                "suggestion": "Check if the user has access to the namespace or confirm if they had passed the right namespace"
            })
        except FileNotFoundError:
            return json.dumps({
                "error": "Pod status file does not exist",
                "suggestion": "The user must have configure the incorrect file path"
            })
        
