# Deployment rollback runbook

**Owner:** Platform Engineering  
**Last updated:** 2026-03-20  
**Severity:** P1 during active incident, P4 for planned rollback  
**Tags:** deployment, rollback, kubernetes, argocd, jenkins, canary

## 1. When to rollback

Rollback is the correct action when ALL of these are true:
- A recent deployment occurred (within the last 2 hours)
- The issue started after or correlates with the deployment
- The previous version was known stable (check deployment history)
- The issue is impacting production availability or correctness

**Do NOT rollback if:**
- The issue predates the deployment (coincidental timing)
- The deployment included a database migration that cannot be reversed
- The new version fixes a critical security vulnerability (fix forward instead)
- The previous version has its own known issues that were the reason for the upgrade

**Decision timeline:**
- 0-5 minutes after detecting issue: investigate briefly, correlate with deployment
- 5-15 minutes: if correlation is strong, initiate rollback
- 15+ minutes: if still investigating without rollback, escalate to incident commander
- Our policy: **when in doubt, rollback first and investigate later**. Restoring service is more important than understanding the root cause in real-time.

## 2. Rollback procedures by deployment method

### 2.1 Kubectl direct rollback

For deployments managed directly via kubectl or CI pipelines:

```bash
# Check rollout history
kubectl rollout history deployment/<name> -n <namespace>

# Rollback to the immediately previous revision
kubectl rollout undo deployment/<name> -n <namespace>

# Rollback to a specific revision (e.g., revision 12)
kubectl rollout undo deployment/<name> -n <namespace> --to-revision=12

# Watch the rollout progress
kubectl rollout status deployment/<name> -n <namespace> --timeout=5m
```

### 2.2 ArgoCD rollback

For deployments managed by ArgoCD (GitOps):

```bash
# List application history
argocd app history <app-name>

# Rollback to a specific revision
argocd app rollback <app-name> <revision-id>

# Or: revert the Git commit and let ArgoCD auto-sync
git revert <commit-hash>
git push origin main
# ArgoCD syncs within 3 minutes (default poll interval)
```

**Important:** ArgoCD auto-sync will revert a manual `kubectl rollout undo`. If using ArgoCD, always rollback via Git revert, not kubectl.

### 2.3 Helm rollback

For Helm-managed releases:

```bash
# List release history
helm history <release-name> -n <namespace>

# Rollback to previous revision
helm rollback <release-name> <revision> -n <namespace>

# Verify
helm status <release-name> -n <namespace>
```

### 2.4 Canary deployment rollback

For canary deployments (Istio/Flagger/Argo Rollouts):

```bash
# If using Argo Rollouts — abort the canary
kubectl argo rollouts abort <rollout-name> -n <namespace>

# If using Flagger — it auto-rolls back on failed metrics, but to force:
kubectl annotate canary/<name> -n <namespace> flagger.app/rollback="true"

# If using Istio manual canary — shift all traffic back to stable
kubectl apply -f virtualservice-stable.yaml
```

## 3. Rollback verification

After initiating the rollback:

1. **Confirm the correct version is running:**
   ```bash
   kubectl get deployment <name> -n <namespace> -o jsonpath='{.spec.template.spec.containers[0].image}'
   ```
   This should show the previous stable image tag.

2. **Watch pod transition** (allow up to 5 minutes for graceful termination):
   ```bash
   kubectl get pods -n <namespace> -w
   ```
   Old pods should terminate, new pods with the previous version should reach `Running` and `Ready`.

3. **Check restart count resets to 0** on the new pods.

4. **Verify application health:**
   - Hit the health endpoint manually: `curl http://<service>.<namespace>:8080/healthz`
   - Check metrics dashboards for error rate returning to baseline
   - Verify end-to-end functionality (place a test order, send a test notification, etc.)

5. **Confirm no side effects:**
   - Check dependent services aren't erroring due to API contract changes
   - Verify no data corruption from the brief period the bad version was running
   - Check message queues for stuck/dead-letter messages

## 4. Common rollback pitfalls

**Schema migrations:** If the failed deployment included a database migration, rolling back the application doesn't roll back the database. The old application code may not work with the new schema. Always check migration status before rolling back.

**ConfigMap/Secret changes:** If the deployment updated a ConfigMap or Secret alongside the image, rolling back the deployment doesn't revert the ConfigMap. You need to manually revert those as well.

**StatefulSet rollback:** StatefulSets don't support `kubectl rollout undo`. You must manually update the StatefulSet spec to the previous image tag and apply. StatefulSet pods roll one at a time in reverse order (highest ordinal first).

**Persistent Volume data:** If the failed version wrote corrupted data to a PersistentVolume, rolling back doesn't restore the data. You may need to restore from a backup.

**Replica count changes:** `kubectl rollout undo` only reverts the pod template, not replica count or other deployment spec changes. If the failed deployment also changed replica count, manually restore: `kubectl scale deployment/<name> --replicas=<previous_count>`.

## 5. Post-rollback actions

1. **Notify the team:** Post in #incidents Slack channel: "Rolled back <app> from v<new> to v<old>. Service restored at <timestamp>. Investigating root cause."

2. **Create a follow-up ticket:** "Investigate why <app> v<new> caused <symptoms>. Do not redeploy until root cause is understood."

3. **Preserve evidence:** Before the failing pods are garbage collected, capture:
   ```bash
   kubectl logs <pod-name> -n <namespace> --previous > failed-pod-logs.txt
   kubectl describe pod <pod-name> -n <namespace> > failed-pod-describe.txt
   ```

4. **Root cause analysis within 48 hours:** Was it a code bug, config error, resource misconfiguration, or infrastructure issue? Update the deployment checklist to prevent recurrence.