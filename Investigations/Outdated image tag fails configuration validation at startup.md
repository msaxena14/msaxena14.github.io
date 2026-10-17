---
severity: Medium · Client prod
tags: Kubernetes, Azure, Configuration, Image versions
date: 2026-10-09
summary: A service stuck in a container config error was running a release too old for the environment's storage settings.
---
## Symptom
On a client's Azure cluster, a service's pod was stuck in `CreateContainerConfigError`.

## Investigation
The alert reported a container configuration problem. Reading the service's own startup logs showed the application failing validation of its settings: the storage-type value supplied by the environment was rejected by the running release, which only accepted two named values. Comparing the running image tag with current releases showed it was far behind, and the owning team confirmed which version the environment should run. The feature had already been enabled in a failing state, so the question of whether it was needed at all went back to the owning team.

## Fix
Deployed the correct, newer image tag through a merge request on the client configuration. The owning team agreed to raise a request to offboard the feature if it isn't required.

## Impact
The pods came up and stayed running with no restarts and no error logs.
