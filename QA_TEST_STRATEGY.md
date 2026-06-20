# SustainOCPM: QA Test Strategy

This document defines the testing scope, strategies, and quality gates for SustainOCPM.

---

## 1. Quality Gates & Test Scopes

| Test Scope | Target Component / Service | Testing Strategy / Tooling | Acceptance Threshold |
| :--- | :--- | :--- | :--- |
| **Unit Testing** | Backend calculations, carbon utilities, auth functions, database helpers. | PyTest for Python service modules, Jest for Node.js APIs. | > 85% code coverage. Zero critical regressions. |
| **Integration Testing** | Ingestion pipeline worker, relational-to-graph data mapper, database triggers. | Docker-compose mock environment, test DB migrations. | 100% of schema test suites pass. Integration lag under 200ms. |
| **E2E Testing** | User onboarding, upload-to-dashboard workflow, scenario simulator sliders. | Playwright, Cypress. | 100% of critical paths pass. Automated session restoration verified. |
| **Accessibility Testing**| All UI pages, metrics cards, graphs, presenting modes, navigation links. | axe-core, lighthouse audits, manual keyboard traversal tests. | WCAG 2.1 Level AA compliant. Score > 90 on Lighthouse. |
| **Performance Testing**| CSV ingestion processing, Cypher graph query performance, multi-user load. | k6, Apache JMeter. | Ingest 100k events in < 5 seconds. Graph queries complete in < 300ms at 100 concurrent users. |
| **Data Validation** | OCEL 2.0 file formatting compliance, schema mapping validations. | Scripted anomaly checkers, data type assertion suites. | Zero invalid schemas processed. Unmapped fields routed to Dead Letter Queue (DLQ). |
| **AI Response Quality** | LLM RAG queries, Natural Language to Cypher/SQL generation. | Ragas framework, prompt test runners. | > 90% accuracy in target SQL generation. Zero hallucination index in citations. |
| **Report Validation** | SEBI BRSR Section A, B, and C templates. | Automated schema checkers against SEBI compliance templates. | 100% compliance alignment with BRSR guidelines. Output matches target figures. |
