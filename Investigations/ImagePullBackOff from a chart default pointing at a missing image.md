---
severity: Medium · Client prod
tags: Kubernetes, ECR, Helm, ArgoCD
date: 2026-10-09
summary: A pod stuck in ImagePullBackOff because the chart's default image path no longer existed in the registry.
---
## Symptom
A UI-shell service sat in `ImagePullBackOff` for the whole alert window on a client's production cluster.

## Investigation
The pull error and a look at the registry showed that the referenced image path and tag did not exist at all, so retries could never succeed. The path came from the chart's default values, not from anything specific to the client. A platform engineer confirmed the service shouldn't use that default and supplied the correct repository and tag.

## Fix
Added a per-client override for the image repository and tag, merged it, promoted it, and let the GitOps sync roll it out.

## Impact
The deployment synced and went healthy, with pods running without restarts or errors. The UI was checked after logging in to confirm it served correctly.
