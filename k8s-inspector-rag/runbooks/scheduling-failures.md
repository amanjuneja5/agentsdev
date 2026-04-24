# Scheduling failures runbook

**Owner:** Platform Engineering  
**Last updated:** 2026-03-25  
**Severity:** P2 if production workload affected, P4 for non-critical  
**Tags:** scheduling, pending, unschedulable, node, affinity, taint, quota, kubernetes

## 1. Identifying scheduling failures

A pod is stuck in scheduling when its status is `Pending` and the `PodScheduled` condition is `False`. The scheduler cannot find a suitable node to place the pod.

**Quick diagnosis:**

```bash
# Find Pending pods
kubectl get pods -n <namespace> --field-selector=status.phase=Pending

# Get the scheduling failure reason
kubectl describe pod <pod-name> -n <namespace> | grep -A10 "Events:"

# Check scheduler logs for details
kubectl logs -n kube-system -l component=kube-scheduler --tail=50
```

**The event message tells you exactly why scheduling failed.** Common messages and their meanings:

| Event message | Root cause | Fix |
|---|---|---|
| `Insufficient cpu` | No node has enough free CPU to satisfy the pod's CPU request | Reduce CPU request, add nodes, or evict lower-priority workloads |
| `Insufficient memory` | No node has enough free memory | Reduce memory request, add nodes, or evict lower-priority workloads |
| `node(s) had untolerated taint` | Pod doesn't tolerate the node's taints (e.g., master nodes, GPU nodes, spot nodes) | Add the required toleration to the pod spec, or target different nodes |
| `node(s) didn't match Pod's node affinity/selector` | Pod requires specific nodes (zone, instance type) that are all full or unavailable | Relax affinity rules, add matching nodes, or remove nodeSelector |
| `persistentvolumeclaim not found` | PVC doesn't exist or is in a different namespace | Create the PVC or fix the reference |
| `No preemption victims found` | Priority-based preemption can't find lower-priority pods to evict | Add nodes or reduce resource requests |

## 2. Insufficient resources (CPU / memory)

The most common scheduling failure. The scheduler adds up all resource requests on each node and checks if the pod's request fits in the remaining space.

**Important:** The scheduler uses **requests**, not limits and not actual usage. A node might be at 20% actual CPU usage but 100% committed by requests — no new pods can be scheduled.

**Diagnostic commands:**

```bash
# Check allocatable vs requested resources on all nodes
kubectl describe nodes | grep -A6 "Allocated resources"

# More detailed: see per-node capacity and allocations
kubectl get nodes -o custom-columns=\
  NAME:.metadata.name,\
  CPU_ALLOC:.status.allocatable.cpu,\
  MEM_ALLOC:.status.allocatable.memory

# Check what's consuming resources in the namespace
kubectl top pods -n <namespace> --sort-by=cpu
kubectl top pods -n <namespace> --sort-by=memory
```

**Resolution options (in order of preference):**

1. **Right-size existing workloads:** Find pods requesting far more CPU/memory than they use. Reduce their requests to free capacity. Use `kubectl top pods` compared to `kubectl get pods -o jsonpath` for requests.

2. **Add nodes:** If the Cluster Autoscaler is configured, it should add nodes automatically for Pending pods. If it's not reacting, check the max node count and node group configuration.

3. **Use Pod Priority and Preemption:** Assign higher priority to critical workloads. The scheduler will evict lower-priority pods to make room. Use `PriorityClass` resources.

4. **Reduce replica count of non-critical workloads:** Temporarily scale down staging, batch, or analytics workloads to free production capacity.

## 3. Taints and tolerations

Taints prevent pods from scheduling on specific nodes. Tolerations allow pods to override taints.

**Common taint scenarios:**

```bash
# Master/control plane nodes have this taint by default
# (prevents application pods from running on masters)
node-role.kubernetes.io/master:NoSchedule

# GPU nodes tainted to reserve for GPU workloads only
nvidia.com/gpu:NoSchedule

# Spot/preemptible nodes tainted for cost-aware scheduling
cloud.google.com/gke-spot=true:NoSchedule

# Nodes cordoned for maintenance
node.kubernetes.io/unschedulable:NoSchedule
```

**Fixing taint issues:**

```bash
# List taints on all nodes
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Remove a taint from a node
kubectl taint nodes <node-name> <taint-key>-

# Add a toleration to a deployment
kubectl patch deployment <n> -n <namespace> -p '{"spec":{"template":{"spec":{"tolerations":[{"key":"<taint-key>","operator":"Exists","effect":"NoSchedule"}]}}}}'
```

**Best practice:** Don't tolerate taints broadly. If a pod tolerates all taints (`operator: Exists` with no key), it can land on master nodes, GPU nodes, or draining nodes — all bad. Always specify the exact taint key.

## 4. Node affinity and selectors

Node affinity constrains which nodes a pod can run on based on node labels.

**Soft vs hard affinity:**
- `requiredDuringSchedulingIgnoredDuringExecution`: hard constraint — pod WILL NOT schedule if no matching node exists. Use only when placement is correctness-critical (e.g., zone-local storage, GPU requirement).
- `preferredDuringSchedulingIgnoredDuringExecution`: soft constraint — scheduler prefers matching nodes but will schedule elsewhere if needed. Use for optimization (same-zone as database, specific instance type).

**Common mistakes:**

```yaml
# WRONG: nodeSelector with a typo in the label value
nodeSelector:
  node-type: highmem   # actual label is "high-memory"

# WRONG: requiring a zone that doesn't have capacity
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values: ["us-east-1a"]  # all nodes in this zone are full
```

**Debugging affinity issues:**

```bash
# Check what labels nodes actually have
kubectl get nodes --show-labels

# Check what the pod is selecting for
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.nodeSelector}'
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.affinity}'
```

## 5. Resource quota exhaustion

Namespaces can have resource quotas that limit total resource consumption. Even if nodes have capacity, the quota can block scheduling.

```bash
# Check quota status in the namespace
kubectl describe resourcequota -n <namespace>

# Example output:
# Name:       prod-quota
# Resource    Used    Hard
# --------    ----    ----
# cpu         8       10      ← only 2 CPU left for new pods
# memory      24Gi    32Gi    ← only 8Gi left
# pods        45      50      ← only 5 more pods allowed
```

**Resolution:**
- Request a quota increase from the platform team (requires capacity review)
- Right-size existing workloads to free quota
- Remove completed Jobs and Pods that are still consuming quota
- Check for orphaned ReplicaSets from old deployments: `kubectl get rs -n <namespace> | grep "0  "` — old ReplicaSets with 0 pods don't consume quota, but their pods might still be in Terminating state

## 6. Topology spread constraints

TopologySpreadConstraints ensure pods are distributed across failure domains (zones, nodes) for high availability.

**When pods fail to schedule due to topology constraints:**

```
Events:
  Warning  FailedScheduling  doesn't satisfy spread constraint: zone skew exceeds maxSkew(1)
```

This means the scheduler can't place the pod without violating the configured spread rule.

**Common fix:** Relax the constraint from `whenUnsatisfiable: DoNotSchedule` (hard) to `whenUnsatisfiable: ScheduleAnyway` (soft). This prefers even distribution but doesn't block scheduling when perfect balance is impossible.

```yaml
topologySpreadConstraints:
- maxSkew: 1
  topologyKey: topology.kubernetes.io/zone
  whenUnsatisfiable: ScheduleAnyway  # changed from DoNotSchedule
  labelSelector:
    matchLabels:
      app: <app>
```

**Best practice:** Use hard constraints only for truly zone-critical workloads (databases with synchronous replication). For stateless application pods, soft constraints give you good distribution without blocking deployments when a zone is temporarily unavailable.