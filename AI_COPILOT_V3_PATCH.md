# SustainOCPM: AI Copilot V3 Patch Specification

This document defines the approved architectural patches applied to the AI Copilot system to support multi-tenant SaaS environments, security controls, and advanced workflow tracking.

---

## 1. Rejected Findings (Non-Critical/Medium/Low Priority)

The following items from `AI_COPILOT_V2_REVIEW.md` are rejected as out of scope for the core security and functional alignment updates:
*   *Finding 7 (Prompt Compression / Cost Optimization) - Medium Priority:* Rejected. Performance optimizations will be handled in separate optimization cycles.
*   *Finding 9 (Real-Time Trace Propagation) - Medium Priority:* Rejected. Observability enhancements are deferred to operational monitoring sprints.

---

## 2. Approved Critical & High Priority Patches

### PATCH-01: Multi-Tenant Security & Caching Isolation
*   **Change:** Inject the user's active `tenant_id` hash into all cache lookup keys for both the Semantic Cache and Prompt Cache.
*   **Rationale:** Prevents cross-tenant leaks that could occur if vector inputs generate semantic matches across tenant contexts.
*   **Affected Sections:** Section 10 (Performance - Caching Layers).
*   **Dependencies:** Database Row-Level Security (RLS) tables.
*   **Implementation Impact:** Restricts semantic cache hits to single-tenant scopes.
*   **Priority:** **Critical**

### PATCH-02: Zero-Trust RBAC at Agent Tool Level
*   **Change:** Intercept all orchestrator agent tool execution requests and validate user roles (e.g., Admin, Auditor) before executing them.
*   **Rationale:** Ensures users cannot bypass role restrictions using conversational prompts.
*   **Affected Sections:** Section 7 (Guardrails).
*   **Dependencies:** JWT Authentication Gateway API.
*   **Implementation Impact:** Blocks privilege escalation via chatbot interfaces.
*   **Priority:** **Critical**

### PATCH-03: Multi-Tenant Benchmarking Data Clean Room
*   **Change:** Configure the ESG and Carbon Agents to query anonymized sector-level metrics from a public registry table.
*   **Rationale:** Enables benchmarking calculations without exposing raw transactional records.
*   **Affected Sections:** Section 3.2 (Retrieval Layer) and Section 3.3 (Knowledge Layer).
*   **Dependencies:** Database aggregation background processes.
*   **Implementation Impact:** Guarantees data privacy during sector benchmarks.
*   **Priority:** **Critical**

### PATCH-04: Simulation Run Persistence
*   **Change:** Add database persistence tools (`save_scenario_run`) to the Simulation Agent mapping to a `scenario_runs` database model.
*   **Rationale:** Allows what-if simulation parameters and projections to be saved and compared across sessions.
*   **Affected Sections:** Section 4.9 (Simulation Agent - Tools).
*   **Dependencies:** `scenario_runs` database schema migrations.
*   **Implementation Impact:** Enables side-by-side what-if report comparisons.
*   **Priority:** **High**

### PATCH-05: Maturity Assessment Agent
*   **Change:** Introduce `4.10 Maturity Assessment Agent` equipped with tools to compare process KPIs against ESG frameworks (GRI, CMMI).
*   **Rationale:** Translates raw compliance metrics into strategic executive maturity scorecards.
*   **Affected Sections:** Section 4 (Specialized Agents).
*   **Dependencies:** pgvector Knowledge Base index.
*   **Implementation Impact:** Outlines gap checklists to guide sustainability improvements.
*   **Priority:** **High**

### PATCH-06: Workflow Automation Agent
*   **Change:** Introduce `4.11 Workflow Automation Agent` to dispatch webhooks and create external system tickets (Jira, ServiceNow).
*   **Rationale:** Translates process optimization recommendations into automatic actions.
*   **Affected Sections:** Section 4 (Specialized Agents).
*   **Dependencies:** Ticketing system API gateways.
*   **Implementation Impact:** Automates anomaly resolutions through closed-loop tracking.
*   **Priority:** **High**

### PATCH-07: Alert Monitoring Agent
*   **Change:** Introduce `4.12 Alert Monitoring Agent` that continuously checks TimescaleDB event streams against threshold limits.
*   **Rationale:** Transitions the platform from passive queries to real-time notification alerts.
*   **Affected Sections:** Section 4 (Specialized Agents).
*   **Dependencies:** TimescaleDB event database triggers.
*   **Implementation Impact:** Powers automated warning dispatches to alert center dashboards.
*   **Priority:** **High**

### PATCH-08: Hybrid Graph RAG
*   **Change:** Link vector chunks of unstructured ESG standards and internal SOPs directly to Neo4j process graph nodes.
*   **Rationale:** Connects policy guidelines to transactional shop-floor actions for context-aware QA.
*   **Affected Sections:** Section 3.2 (Retrieval Layer / RAG).
*   **Dependencies:** Neo4j semantic model registry.
*   **Implementation Impact:** Ensures document search results are contextualized with process flows.
*   **Priority:** **High**

---

## 3. Final Pre-Implementation Recommendation

### **STATUS: READY FOR IMPLEMENTATION**

*   **Justification:** The core architecture documents, UX layouts, and planning schedules are completely trace-aligned. The addition of the critical zero-trust RBAC at the agent tool level and the differential privacy benchmark data clean room ensures the platform is fully secure for multi-tenant deployments. Early sprints are scoped strictly to deliver the MVP (CSV Upload and Heuristics Miner) to meet grant evaluation deadlines, while the underlying schemas support future scalability.
