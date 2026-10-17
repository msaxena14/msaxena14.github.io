---
severity: Medium · Client staging
tags: PostgreSQL, Kubernetes, Capacity, Root cause analysis
date: 2026-10-12
featured: true
summary: Synthetic 500s on a user-management service traced to a neighbouring service autoscaling and consuming the shared database's connection slots.
---
## Symptom
Synthetic checks against a staging user-management service started returning HTTP 500. The service's logs showed Postgres refusing connections: `remaining connection slots are reserved for roles with the SUPERUSER attribute`.

## Investigation
That error means the database has run out of regular connection slots, so the question was who was holding them. A traffic spike on a separate document-processing service had scaled it to about 27 pods. Each pod keeps its own connection pool of roughly 10 connections, around 291 in total, against a server limit of 401. With about 384 connections in use, user management lost the race for the last slots. The headroom was only a few connections, so the next spike would repeat the failure.

## Fix
Recommended three options, in order of effort: cap the per-pod pool size, raise `max_connections`, and put a connection pooler such as PgBouncer between the applications and the database. The owning application team applied the fix under a separate ticket.

## Impact
The incident was closed with a documented root cause and a clear way to stop it recurring on the next traffic spike.
