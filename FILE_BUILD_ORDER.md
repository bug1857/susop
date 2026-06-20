# SustainOCPM: File Build Order

This document details the exact chronological sequence for building the platform's files, modules, and schemas. Building in this order minimizes rework by ensuring database models and API cores exist before user interfaces or AI layers are deployed.

---

## 1. Sequence Map

| Order | Module / File Group | Rationale for Sequence | Dependencies | Key Blockers |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **Database Schemas & Migrations** (`[DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md)`) | Relational database models and Row-Level Security policies must be in place before any services read or write data. | None | Unresolved schema boundaries for multi-tenant isolation. |
| **2** | **Auth & Authorization Middleware** (`[API_ARCHITECTURE.md](./API_ARCHITECTURE.md)`) | Every subsequent API route depends on tenant authentication context. | Step 1 (DB Schema) | Missing JWT signer configuration or RBAC role matrices. |
| **3** | **Ingestion & Validation Engine** (`[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)`) | Platform requires event data. Ingesting and validating CSVs is a prerequisite for process mining. | Step 2 (Auth) | Non-compliant CSV structures, lack of basic data sanitization. |
| **4** | **OCEL 2.0 Graph Mapper** (`[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)`) | Maps flat relational events into Neo4j graph nodes and many-to-many object relations. | Step 3 (Ingestion) | Improperly configured Neo4j node keys, high ingestion overhead. |
| **5** | **Core Process Discovery Service** | Translates graph nodes to heuristics-mined process charts. | Step 4 (Graph Map) | Inefficient cypher traversals over large object networks. |
| **6** | **Conformance Checking Engine** | Compares graph pathways to reference BPMN models to flag deviations. | Step 5 (Discovery) | Incorrect BPMN validation syntax. |
| **7** | **Carbon Attribution Calculator** | Applies emission factors to mined events and paths. | Step 5 (Discovery) | Incomplete or unverified carbon lookup datasets. |
| **8** | **ESG Scoring Framework** | Aggregates operational metrics into framework scores (GRI, SASB). | Step 7 (Carbon) | Out-of-boundary calculations. |
| **9** | **Supplier Portal API** | Collects upstream Scope 3 supplier carbon data. | Step 8 (ESG Scoring) | Supplier tenant cross-contamination risks. |
| **10**| **Vector Database & RAG Pipeline** (`[AI_COPILOT_ARCHITECTURE.md](./AI_COPILOT_ARCHITECTURE.md)`) | Initializes pgvector and embeds ESG regulations/corporate documents. | Step 2 (Auth) | Document parsing failures, high embedding latency. |
| **11**| **AI Copilot Orchestrator** (`[AI_COPILOT_ARCHITECTURE.md](./AI_COPILOT_ARCHITECTURE.md)`) | Chat engine that translates NL to SQL/Cypher queries. | Step 4 (Graph), Step 10 (RAG) | Unoptimized prompt contexts leading to hallucination. |
| **12**| **Digital Twin State-Graph Builder** | Visualizes current-state logs inside the process UI. | Step 4 (Graph) | Excessive Neo4j query latency during dynamic page rendering. |
| **13**| **Scenario Simulation Service** | Calculates cost/carbon slider projections. | Step 7 (Carbon), Step 12 (Twin) | Simulation loops triggering stack overflows. |
| **14**| **BRSR Report Generator** | Automatically populates SEBI compliance reports. | Step 8 (ESG Scoring) | Formatting errors in export outputs. |
| **15**| **Alert & Webhook Automation Core** | Handles automated threshold alerts and Slack/email notifications. | Step 6 (Conformance) | Missed event triggers, webhook delivery failures. |
| **16**| **Presentation Mode Engine** (`[PRESENTATION_MODE_SPEC.md](./PRESENTATION_MODE_SPEC.md)`) | Builds slides that pull live, tenant-scoped dashboard calculations. | Step 13 (Simulation) | Inconsistent telemetry calculations between presenter and audience. |
