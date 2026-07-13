## Nexus Autonomous Fix

**Incident:** 8d75b371-994a-42e6-87a8-6530939690d6
**Type:** reliability_degradation
**Severity:** high
**Root cause:** Reliability drop – error rate / crashloop
**Confidence:** 0.70

**Generated fix:**
```
I generated K8s Deployment patch for nexus-broken-app: correct image and resource requests
```

**Risk:** medium
**Autonomy level:** see policy gate

---
*I generated this PR automatically via Nexus control plane.*
