# Network and connectivity troubleshooting

**Owner:** Platform Engineering  
**Last updated:** 2026-02-28  
**Severity:** P1 if cross-service communication broken, P3 for degraded  
**Tags:** network, dns, service, ingress, networkpolicy, connectivity, kubernetes

## 1. Service discovery and DNS

All service-to-service communication in Kubernetes uses DNS. A pod reaches another service via `<service-name>.<namespace>.svc.cluster.local`.

**When DNS resolution fails:**

```bash
# Test DNS from inside a pod
kubectl exec -it <pod-name> -n <namespace> -- nslookup <service-name>.<namespace>.svc.cluster.local

# If nslookup is not available
kubectl exec -it <pod-name> -n <namespace> -- cat /etc/resolv.conf

# Check if CoreDNS is healthy
kubectl get pods -n kube-system -l k8s-app=kube-dns
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=20
```

**Common DNS issues:**
- CoreDNS pods are crashing or overloaded → check CPU/memory on CoreDNS pods
- DNS policy set to `None` on the pod → pod has no DNS configuration
- Search domain misconfiguration → short names don't resolve, FQDN works
- DNS cache serving stale entries → restart CoreDNS or wait for TTL expiry

## 2. Service connectivity

When a service exists but connections fail:

```bash
# Verify the service has endpoints
kubectl get endpoints <service-name> -n <namespace>
# If ENDPOINTS shows <none>, no pods match the service selector

# Check if the service selector matches pod labels
kubectl get svc <service-name> -n <namespace> -o jsonpath='{.spec.selector}'
kubectl get pods -n <namespace> -l <selector-key>=<selector-value>

# Test connectivity from another pod
kubectl exec -it <test-pod> -n <namespace> -- curl -v http://<service-name>:8080/healthz
```

**Service with no endpoints (most common issue):**
1. Selector mismatch: service selects `app: payment-api` but pods are labeled `app: payments-api` (plural)
2. All pods are not Ready: readiness probes failing → pods removed from endpoints
3. Pods exist in a different namespace than the service
4. All pods are in CrashLoopBackOff → no Ready pods to serve traffic

## 3. Ingress troubleshooting

When external traffic can't reach the service:

```bash
# Check ingress status
kubectl get ingress -n <namespace>

# Check the ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=50

# Verify the backend service is reachable from the ingress controller
kubectl exec -it -n ingress-nginx <ingress-pod> -- curl http://<service-name>.<namespace>:8080/healthz
```

**Common ingress issues:**
- TLS certificate expired or misconfigured → check `kubectl describe ingress` for TLS secret status
- Backend service port doesn't match ingress spec → verify port numbers in both resources
- Ingress class mismatch → pod spec says `kubernetes.io/ingress.class: nginx` but controller uses `nginx-internal`
- Rate limiting or WAF rules blocking requests → check ingress controller annotations

## 4. Network policies

Network policies restrict pod-to-pod communication. If a pod can't reach another pod but DNS works and the service has endpoints, a NetworkPolicy is likely blocking traffic.

```bash
# Check if any network policies exist in the namespace
kubectl get networkpolicy -n <namespace>

# Describe a specific policy
kubectl describe networkpolicy <policy-name> -n <namespace>
```

**Default deny:** If a namespace has any NetworkPolicy selecting a pod, all traffic not explicitly allowed is denied. This is the most common surprise — adding a single ingress policy implicitly blocks all other ingress.

**Debugging network policy blocks:**
1. Check if the source pod's labels match the `from` selector in the target's NetworkPolicy
2. Check if the port matches the policy's allowed ports
3. Check if the source is in a namespace allowed by `namespaceSelector`
4. Temporarily remove the NetworkPolicy to confirm it's the cause (in staging only!)

## 5. Connection timeouts and retries

When connections succeed sometimes but fail intermittently:

**Causes of intermittent connectivity:**
- Pod is restarting and not yet Ready → brief window of failed connections between readiness probe passing and new pod starting
- Connection pool exhaustion → too many concurrent connections, new requests queue or fail
- DNS TTL caching → client caches an old pod IP after a reschedule
- Load balancer health check flapping → service endpoint oscillates between available/unavailable

**Recommended timeout settings for internal services:**
- Connection timeout: 3 seconds (fail fast if the backend is down)
- Read timeout: 30 seconds (allow for slow responses under load)
- Retry count: 3 with exponential backoff (1s, 2s, 4s)
- Circuit breaker: open after 5 consecutive failures, half-open after 30 seconds

**Istio-specific:** If using Istio service mesh, check VirtualService timeout and retry configuration:
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: <service>
spec:
  hosts:
  - <service>
  http:
  - timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
      retryOn: 5xx,connect-failure,reset
```