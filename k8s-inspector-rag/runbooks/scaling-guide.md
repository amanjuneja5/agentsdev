# Scaling guide

**Owner:** Platform Engineering  
**Last updated:** 2026-03-10  
**Severity:** P2 for scaling emergencies, P4 for planned scaling  
**Tags:** scaling, hpa, autoscaler, replicas, capacity, kubernetes

## 1. Horizontal Pod Autoscaler (HPA) configuration

HPA automatically adjusts replica count based on observed metrics. Our standard configuration for production workloads:

**Default HPA settings:**
- Target CPU utilization: 70%
- Target memory utilization: 80% (optional, use with caution)
- Minimum replicas: 2 (for redundancy — never set to 1 in production)
- Maximum replicas: 10 (adjust based on downstream capacity)
- Scale-up stabilization: 0 seconds (scale up immediately)
- Scale-down stabilization: 300 seconds (wait 5 minutes before scaling down to avoid flapping)

**Creating an HPA:**

```bash
# Basic CPU-based HPA
kubectl autoscale deployment <n> -n <namespace> \
  --min=2 --max=10 --cpu-percent=70

# Or use a YAML manifest for full control
kubectl apply -f - <<EOF
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <app>-hpa
  namespace: <namespace>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <app>
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
    scaleUp:
      stabilizationWindowSeconds: 0
EOF
```

**When NOT to use HPA:**
- Stateful workloads that cannot share state across instances (use VPA instead)
- Batch processing jobs (use Job parallelism instead)
- Pods with very long startup times (>5 minutes) — HPA will thrash
- When downstream services can't handle increased load (database connection limits, API rate limits)

## 2. Manual scaling

For immediate scaling needs outside HPA:

```bash
# Scale to specific replica count
kubectl scale deployment/<n> -n <namespace> --replicas=5

# Check current replica count and status
kubectl get deployment <n> -n <namespace>

# Watch pods come up
kubectl get pods -n <namespace> -l app=<n> -w
```

**Pre-scaling checklist:**
- Verify cluster has capacity for additional pods: `kubectl describe nodes | grep -A5 "Allocated resources"`
- Check resource quotas: `kubectl describe resourcequota -n <namespace>`
- Verify PodDisruptionBudget won't block: `kubectl get pdb -n <namespace>`
- Confirm downstream services can handle additional connections (database connection pools, Kafka consumer groups)

**Scaling to zero:**
- Permitted for non-critical workloads in staging/dev
- NEVER scale to zero in production without explicit incident commander approval
- Scaling to zero drops all in-flight requests — use with extreme caution
- To drain gracefully: set `terminationGracePeriodSeconds` appropriately (default 30s)

## 3. Cluster Autoscaler

When pods are Pending because no node has sufficient resources, the Cluster Autoscaler adds nodes.

**How it works:**
- Checks for Pending pods every 10 seconds
- If a Pending pod could be scheduled on a node from a configured node group, it requests a new node
- New nodes take 3-5 minutes to become Ready (depending on cloud provider and AMI/image)
- Nodes are removed (scale-down) after 10 minutes of underutilization (<50% of requests used)

**Common Cluster Autoscaler issues:**

**Pods stuck Pending despite autoscaler:**
- Check if the autoscaler has reached its maximum node count: `kubectl -n kube-system logs deployment/cluster-autoscaler | grep "max node group size reached"`
- Check if the pod's resource requests are too large for any available node type
- Check for nodeSelector/affinity constraints that limit which nodes are eligible
- Check for taints that the pod doesn't tolerate

**Autoscaler not scaling down:**
- Pods with local storage (emptyDir with data) block scale-down
- Pods with PodDisruptionBudgets that would be violated block scale-down
- Pods not managed by a controller (no ownerRef) block scale-down
- System pods (kube-system) on the node block scale-down by default

## 4. Capacity planning

**Resource request guidelines:**
- CPU requests: set to the p95 CPU usage observed during normal traffic (not peak)
- Memory requests: set to the steady-state memory usage (not startup spike)
- CPU limits: set to 2-4x the request, or omit for burstable workloads
- Memory limits: set to 1.5-2x the request. Unlike CPU (which throttles), exceeding memory limits kills the pod

**Right-sizing process:**
1. Deploy with generous limits initially (2x expected usage)
2. Run under production traffic for at least 1 week
3. Analyze actual usage: `kubectl top pods` snapshots, Prometheus metrics, or Kubecost
4. Right-size requests to p95 usage, limits to 1.5x requests
5. Re-evaluate after any significant code change or traffic pattern shift

**Warning signs of capacity issues:**
- Pods stuck in Pending for >2 minutes: check scheduler events
- CPU throttling alerts: pod is hitting its CPU limit frequently
- Memory usage consistently >80% of limit: OOM risk, increase limit
- Node CPU/memory utilization >85%: add nodes or right-size pod requests downward

## 5. Scaling anti-patterns

**Anti-pattern: Single replica in production**
- Risk: any pod restart means complete service outage
- Fix: minimum 2 replicas for all production workloads, 3+ for critical paths

**Anti-pattern: Scaling up without checking downstream capacity**
- Risk: 10x pods → 10x database connections → connection pool exhaustion → cascading failure
- Fix: verify database connection limits, API rate limits, and queue consumer capacity before scaling

**Anti-pattern: Using memory-based HPA for JVM applications**
- Risk: JVM allocates heap eagerly and GC doesn't return memory to the OS. HPA sees constant high memory and keeps scaling up.
- Fix: use CPU-based HPA for JVM apps, or use custom metrics (request queue depth, Kafka consumer lag)

**Anti-pattern: Setting CPU limit equal to request**
- Risk: no burst capacity. Brief CPU spikes (GC, request processing) cause throttling and latency spikes.
- Fix: set CPU limit to 2-4x request, or omit CPU limits entirely (Burstable QoS)

**Anti-pattern: Scaling without PodDisruptionBudget**
- Risk: during cluster maintenance or rolling updates, all pods could be evicted simultaneously
- Fix: always configure PDB with `minAvailable: 1` or `maxUnavailable: 1`