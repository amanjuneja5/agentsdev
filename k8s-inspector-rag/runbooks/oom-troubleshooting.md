# OOM troubleshooting runbook

**Owner:** Platform Engineering  
**Last updated:** 2026-03-15  
**Severity:** P1 if production, P3 if staging  
**Tags:** memory, oom, kubernetes, jvm, node.js, container

## 1. Identify the OOM-killed pod

When a pod is terminated due to memory exhaustion, Kubernetes sends SIGKILL (exit code 137). The pod enters `CrashLoopBackOff` after repeated OOM kills.

**Quick identification commands:**

```bash
# Find OOM-killed pods in a namespace
kubectl get pods -n <namespace> | grep -E 'CrashLoopBackOff|OOMKilled|Error'

# Check termination reason for a specific pod
kubectl describe pod <pod-name> -n <namespace> | grep -A5 "Last State"

# Check events for OOM kills
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp | grep OOM
```

**Key signals:** Exit code 137 always indicates SIGKILL. In a container context, this is almost always the OOM killer. Exit code 1 with memory-related errors in logs is application-level OOM (e.g., Java heap exhaustion before the kernel kills the process).

## 2. Check memory limits vs actual usage

Compare the pod's configured memory limit with its actual runtime consumption. A pod consistently using >80% of its memory limit is at risk of OOM.

**Diagnostic commands:**

```bash
# Current memory usage
kubectl top pod <pod-name> -n <namespace>

# Memory limit from the pod spec
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].resources.limits.memory}'

# Historical usage (requires Prometheus/metrics-server)
# Check if usage has been trending upward (memory leak indicator)
```

**Decision thresholds:**
- Usage < 60% of limit: healthy, no action needed
- Usage 60-80% of limit: monitor, may need increase during traffic spikes
- Usage 80-95% of limit: increase limit proactively, investigate if usage is growing over time (memory leak)
- Usage > 95% of limit: OOM imminent, increase limit immediately or rollback recent deployment

**Memory leak indicators:** If memory usage grows monotonically over hours/days without correlation to traffic, suspect a memory leak. Common causes: unclosed connections, growing caches without eviction, event listener accumulation, large object retention in closures.

## 3. Application-specific memory tuning

Different application runtimes have different memory characteristics and tuning knobs.

**JVM applications (Java, Kotlin, Scala):**
- Set `-Xmx` (max heap) to 75% of the container memory limit. The remaining 25% is for metaspace, thread stacks, native memory, and OS overhead.
- Example: container limit = 4Gi → set `-Xmx=3g`
- Enable GC logging with `-Xlog:gc*` to diagnose heap pressure
- If GC pauses exceed 2 seconds, the heap is too small or there's a leak
- Common mistake: setting `-Xmx` equal to the container limit. The JVM uses memory beyond the heap, and the OS needs memory too. This guarantees OOM.

**Node.js applications:**
- Set `--max-old-space-size` to 75% of the container limit (in MB)
- Example: container limit = 2Gi → set `--max-old-space-size=1536`
- Node.js defaults to ~1.5GB heap regardless of container limit — you must set this explicitly
- Use `process.memoryUsage()` in health endpoints to expose current heap stats

**Python applications:**
- Python has no hard heap limit — memory grows until the OS kills the process
- Use `tracemalloc` module to track allocations in development
- Common culprits: pandas DataFrames held in memory, unbounded list growth, large response caching
- Consider `resource.setrlimit(resource.RLIMIT_AS, ...)` as a soft guard

**Go applications:**
- Go's garbage collector is generally well-behaved with container limits
- Set `GOMEMLIMIT` environment variable (Go 1.19+) to 90% of container limit
- Go will trigger GC more aggressively as it approaches the limit
- If OOM still occurs, check for goroutine leaks with `pprof`

## 4. Remediation options

Choose based on urgency and root cause:

**Option A: Increase memory limit (fast, temporary)**
- When to use: production is down, need immediate relief
- Risk: may mask underlying memory leak
- Command: `kubectl patch deployment <name> -n <namespace> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"8Gi"}}}]}}}}'`
- Always also increase the memory request to at least 50% of the new limit
- Follow up with Option B or C within 48 hours

**Option B: Rollback to last known good version (fast, safe)**
- When to use: OOM started after a recent deployment
- Prerequisite: confirm the previous version was stable using deployment history
- Command: `kubectl rollout undo deployment/<name> -n <namespace>`
- Verify rollback: watch restart count, check `kubectl top pod`, confirm application logs show normal operation
- Root cause: the new version likely introduced higher memory usage (larger batch sizes, new dependencies, changed caching behavior)

**Option C: Optimize application memory (slow, permanent)**
- When to use: no recent deployment, gradual memory growth (leak)
- Steps: enable heap profiling → identify top memory consumers → fix leaks → test under load → redeploy
- JVM: use `jmap -histo` or JFR (Java Flight Recorder)
- Node.js: use `--inspect` with Chrome DevTools heap snapshots
- This is the only option that actually fixes the root cause

**Option D: Scale horizontally (fast, partial)**
- When to use: single-pod processing too much data per instance
- Increase replica count to distribute load: `kubectl scale deployment/<name> --replicas=3`
- Only works if the application can shard work across instances (e.g., Kafka consumers with multiple partitions)
- Does NOT help if the leak is per-request rather than per-volume

## 5. Post-fix verification

After applying any remediation:

1. **Watch restart count** for 15 minutes: `kubectl get pods -n <namespace> -w`
   - If restarts stop: fix is holding
   - If restarts continue: the fix is insufficient, escalate

2. **Monitor memory usage** for 1 hour: `kubectl top pod <pod-name> -n <namespace>` every 5 minutes
   - Usage should be stable (not growing)
   - Usage should be below 80% of the (new) limit

3. **Check application metrics**: verify request latency, error rates, and throughput have returned to normal

4. **Update the incident record**: document root cause, fix applied, and follow-up actions
   - If Option A was used: create a ticket to right-size the limit properly
   - If Option B was used: create a ticket to investigate why the new version uses more memory
   - If Option C was used: document the leak fix for future reference

5. **Notify stakeholders**: post in the incident Slack channel with a brief summary