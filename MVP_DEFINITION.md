# SustainOCPM: MVP Definition

This document establishes the scope boundaries and implementation phases for the platform's 28 core features to prevent scope creep.

---

## 1. Feature Classification Matrix

| Feature | Phase | Scope Reason | Dependencies | Business Value | Complexity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Authentication** | **MVP** | Required to isolate tenant data sessions. | None | Critical: Core Security. | Low |
| **Organizations** | **MVP** | Essential for tenant onboarding hierarchy. | Authentication | High: Multi-tenant grouping. | Low |
| **Workspaces** | **MVP** | Contextual space for uploading data logs. | Organizations | High: Multi-project scope. | Low |
| **RBAC** | **MVP** | Basic roles (Admin, Member) required for tenant security. | Authentication | Critical: Access Control. | Low |
| **CSV Upload** | **MVP** | Primary data source ingestion mechanism. | Workspaces | Critical: Core Utility. | Low |
| **Schema Mapping** | **MVP** | Conforms flat files to OCEL 2.0 standards. | CSV Upload | High: Data formatting. | Medium |
| **Validation** | **MVP** | Ensures uploaded data matches schemas. | Schema Mapping | High: Data integrity. | Low |
| **Process Discovery** | **MVP** | Mined heuristics process maps (pm4py). | Validation | Critical: Core IP. | Medium |
| **Carbon Attribution** | **MVP** | Basic Scope 1 & 2 carbon estimation. | Process Discovery | Critical: Grant demo core. | Medium |
| **Presentation Mode** | **MVP** | Predefined interactive slides for grant demo. | Carbon Attribution | High: Grant evaluation. | Low |
| **Teams** | **V1** | Team-level access grouping. | Organizations, RBAC | Medium: Collab control. | Low |
| **Conformance Checking** | **V1** | Basic alignment check against BPMN. | Process Discovery | High: Compliance. | High |
| **Carbon Fitness** | **V1** | Carbon-aware conformance deviations. | Conformance, Carbon | High: Unique research IP. | High |
| **ESG Scoring** | **V1** | Static dashboards for GRI/SASB indicators. | Carbon Attribution | High: Standard reporting. | Medium |
| **Supplier Intelligence** | **V1** | Upstream supplier profiles & basic logs. | Workspaces | Medium: Scope 3 tracking. | Medium |
| **Reports** | **V1** | Automated PDF exporters for ESG metrics. | ESG Scoring | High: Shareability. | Low |
| **AI Copilot** | **V1** | Basic RAG query assistant over PDFs. | Workspaces | High: User onboarding. | High |
| **Knowledge Base** | **V1** | Storage for regulatory standards. | Workspaces | Medium: Information hub. | Low |
| **Audit Trail** | **V1** | Immutable user event & change log tables. | Authentication | High: Audit-readiness. | Medium |
| **BRSR Reporting** | **V2** | Automatic SEBI compliance document generator. | ESG Scoring, Reports | Critical: SEBI filing. | High |
| **Digital Twin** | **V2** | State-graph visualizations of active logs. | Process Discovery | High: Operational view. | High |
| **Scenario Simulator** | **V2** | Cost/carbon projection simulation sliders. | Carbon Attribution | High: Strategic decisions. | Medium |
| **Recommendations** | **V2** | Algorithmic decarbonization action plans. | Scenario Simulator | Medium: Optimization. | High |
| **Alert Center** | **V2** | Real-time threshold deviation popups. | Conformance Checking | High: Proactive monitoring. | Medium |
| **Benchmarking** | **Enterprise** | Data Clean Room cross-tenant sector comparisons. | Carbon Attribution, ESG | High: Platform network value. | High |
| **Workflow Automation** | **Enterprise** | Ticketing integrations (Jira, ServiceNow webhooks).| Recommendations | High: Closed-loop action. | High |
| **Collaboration** | **Enterprise** | Live shared dashboards & team chats. | Workspaces, Teams | Medium: Collaboration. | High |
| **Maturity Assessment** | **Enterprise** | Automated corporate transition roadmap scores. | ESG Scoring, KB | High: Executive value. | Medium |
