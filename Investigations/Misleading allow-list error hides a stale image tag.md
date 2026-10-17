---
severity: Medium · Client prod
tags: Kubernetes, Azure, Troubleshooting, Image versions
date: 2026-10-15
summary: A pod restarted 12,000+ times behind an "IP not whitelisted" error. The allow-list was fine; a very old image tag was the real cause.
---
## Symptom
A pod on a client's Azure cluster had restarted more than 12,000 times, a long-standing condition rather than a new regression. Its logs ended in `ConnectionError: Customer IP is not whitelisted` against an Azure OpenAI endpoint.

## Investigation
The error read like a network allow-list gap, and the first step was to ask for the client's egress IP. A teammate questioned that: the service calls the endpoint from the cluster, not from the customer's network. Checking the cluster's NAT gateway address against the endpoint's network rules showed it was already allow-listed, which disproved the hypothesis. With networking ruled out, comparing the deployed version with current releases showed the service was running a very old image tag, and together with the owning team that became the most likely cause.

## Fix
Upgraded the service to a current release through the GitOps configuration.

## Impact
The pods came up and stayed up with no restarts, ending a restart loop that had run for more than two weeks.
