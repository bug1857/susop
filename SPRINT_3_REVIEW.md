# Sprint 3 Review

## OCPM Readiness
* Standard event parser standardizes CSV headers into PM4Py compliant DataFrames.
* Object mapping supports basic `object_id` and `object_type` attributes. However, true multi-object relationships (OCEL 2.0 format natively) require schema extensions for graph traversals in Sprint 4.

## Process Discovery Quality
* Automated Miner Selection uses Heuristics or Inductive miners based on activity density.
* Metrics (Throughput time, cases, loop repetitions) are computed accurately.
* React Flow graph rendering provides interactive Zoom, Pan, and Node/Edge selection with actual backend frequency weights.

## Multi-Tenant Security
* Scope boundaries (`tenant_id`, `workspace_id`, `project_id`, `dataset_id`) are validated on every endpoint route.
* Context verification ensures a user cannot access data from cross-project or cross-tenant boundaries.
* API responses are sanitized; FastAPI exception handlers intercept and sanitize internal trace logs.

## Technical Debt
* SQLite configuration causes transaction lockouts under concurrent runs. We need a migration to PostgreSQL for integration environments.
* Dynamic object-centric metrics are computed on-the-fly from CSV parser files on retrieval, which could degrade performance on large files.

## Missing Items Before Sprint 4
* Conformance checking reference structures.
* Carbon attribution calculations per activity node.
* ESG score evaluation matrices.
