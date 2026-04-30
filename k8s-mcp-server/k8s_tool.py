import os
import json

MOCK_DIR = os.path.join(os.path.dirname(__file__),"mock_data")

def fetch_pod_status(namespace):

    file_path = os.path.join(MOCK_DIR,"pod_status.json")

    with open(file_path,"r") as f:
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

def fetch_error_logs(pod_name,level_filter,max_lines):

    file_path = os.path.join(MOCK_DIR,"error_logs.json")

    with open(file_path,"r") as f:
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

def fetch_metrics(app_name):

    file_path = os.path.join(MOCK_DIR,"metrics.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
        
    return json.dumps(all_data.get(app_name))

def fetch_recent_deploys(app_name):

    file_path = os.path.join(MOCK_DIR,"deploy_history.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
        
    return json.dumps(all_data.get(app_name))

def execute_rollback(app_name):

    file_path = os.path.join(MOCK_DIR,"write_responses.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
        rollback_responses = all_data.get("rollback_responses")
        
    return json.dumps(rollback_responses.get(app_name))

def execute_scale(app_name, replicas):

    file_path = os.path.join(MOCK_DIR,"write_responses.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
        scale_responses = all_data.get("scale_responses")
        
    return json.dumps(scale_responses[app_name][replicas])

def cluster_topology(namespace):

    file_path = os.path.join(MOCK_DIR,"pod_status.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
    
    if namespace not in all_data:
        return json.dumps({
            "error": f"Namespace {namespace} not found",
            "available_namespaces": list(all_data.keys()),
            "suggestion": f"Try one of {','.join(all_data.keys())}"
        })
    
    pods = all_data[namespace]
    apps = {}
    for pod in pods:
        pod_name = pod["labels"].get("app")
        if pod_name not in apps:
            apps[pod_name] = {
                "app": pod_name,
                "version": pod["labels"].get("version"),
                "replicas": 0,
                "ready": 0,
                "pods": []
            }
        apps[pod_name]["replicas"] +=1
        if pod["ready"]:
            apps[pod_name]["ready"] +=1
        
        apps[pod_name]["pods"].append(
            {
                "name": pod["name"],
                "status": pod["status"],
                "node": pod.get("node")
            }
        )
    
    return json.dumps({
        "namespace": namespace,
        "applications": list(apps.values())
    })


def health_summary(namespace):
    
    file_path = os.path.join(MOCK_DIR,"pod_status.json")

    with open(file_path,"r") as f:
        all_data = json.load(f)
    
    if namespace not in all_data:
        return json.dumps({
            "error": f"Namespace {namespace} not found",
            "available_namespaces": list(all_data.keys()),
            "suggestion": f"Try one of {','.join(all_data.keys())}"
        })
    
    pods = all_data[namespace]
    summary = {
        "total_pods": 0,
        "healthy_count": 0,
        "unhealthy_count": 0,
        "unhealthy_pods": []
    }
    for pod in pods:
        
        summary["total_pods"] += 1
        
        if pod["status"] not in ["Running", "Succeeded"]:
            summary["unhealthy_count"] += 1    
        else:
            summary["healthy_count"] += 1
    
    summary["namespace"] = namespace
    return json.dumps(summary)

