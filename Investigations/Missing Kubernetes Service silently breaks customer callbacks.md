---
severity: Critical · Client staging
tags: Kubernetes, Helm, ArgoCD, Log analysis, Incident response
date: 2026-10-16
summary: Exports reported success internally, but the customer's callbacks never fired. Traced to a Helm chart that only created the Service under one network topology.
---
## Symptom
On a client staging environment, customer callback notifications never fired, even though exports were marked successful internally. A Critical ticket was open and the customer was blocked.

## Investigation
Both services were healthy, which ruled out crashes and scheduling. The application logs showed repeated DNS failures (`Name or service not known`) when one service tried to reach another. Checking the cluster confirmed the target had no Kubernetes Service, so nothing could resolve it. The Helm chart only created that Service under a conditional intended for a different network topology, so environments outside that topology never got one.

## Fix
Drove a chart change adding an unconditional Service template, reviewed and merged it, and had it deployed through the GitOps pipeline.

## Impact
DNS resolution was restored, callbacks fired again, and the customer was unblocked.
