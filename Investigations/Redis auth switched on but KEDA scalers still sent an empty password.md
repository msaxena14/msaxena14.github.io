---
severity: Critical · Client prod
tags: Kubernetes, KEDA, Redis, Helm, Azure
date: 2026-10-27
summary: After Redis authentication was enabled, every KEDA scaler still connected without a password, so nothing scaled and a shared queue backed up to about 600,000 messages.
---
## Symptom
KEDA scaling failed for every microservice of a multi-service application, across the Azure client environments. Pods stopped scaling out, and a work queue that another service depends on piled up to about 600,000 messages. A Critical ticket was open.

## Investigation
The error on the ScaledObjects was `connection to redis failed: NOAUTH Authentication required`. That means KEDA reached Redis but sent no credentials. Redis authentication had recently been switched on, but the chart's Redis triggers still had an empty password setting, so each trigger connected unauthenticated and was refused. The same blank value appeared in seven autoscaler templates across five subcharts, which made it a chart-level problem, not something to fix per client.

## Fix
One chart change across the seven templates: each Redis trigger now sets the password environment variable and references the existing secret-backed TriggerAuthentication, so KEDA authenticates with the same credentials the services already use. The change was opened and merged within minutes.

## Impact
The ScaledObjects went healthy and autoscaling resumed, about 12 minutes from the ticket being raised to the fix being confirmed. It was checked on the client where it was reported and on two others.
