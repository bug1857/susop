# SustainOCPM: Sprint Plan

This document maps out the 12-sprint execution plan for SustainOCPM, detailing the scope, deliverables, and boundaries for each development cycle.

---

## Sprint 1: Tenant Foundation & Auth
*   **Sprint Goal:** Initialize multi-tenant database infrastructure and basic RBAC authorization.
*   **Scope:** PostgreSQL setup, Row Level Security (RLS) policies, JWT-based tenant login/registration.
*   **In-Scope Files/Modules:** Database schemas (`[DATABASE_ARCHITECTURE.md](./DATABASE_ARCHITECTURE.md)`), Auth Service APIs (`[API_ARCHITECTURE.md](./API_ARCHITECTURE.md)`).
*   **Dependencies:** None.
*   **Definition of Done:** Relational database migrations run; user login returns tenant-scoped JWT; cross-tenant DB isolation verified.
*   **Out-of-Scope:** Supplier registry interfaces, actual CSV uploads.

## Sprint 2: Data Ingestion Pipeline
*   **Sprint Goal:** Build the CSV ingestion pipeline.
*   **Scope:** Flat CSV file parsing, file validation worker, storage broker configuration.
*   **In-Scope Files/Modules:** Ingestion API routes, Upload Wizard UI pages, upload validator script.
*   **Dependencies:** Sprint 1 database infrastructure.
*   **Definition of Done:** CSV file uploaded, parsed to raw Postgres table, metadata recorded under current tenant.
*   **Out-of-Scope:** OCEL 2.0 graph generation, dynamic schema auto-detection.

## Sprint 3: OCEL 2.0 Schema Mapping
*   **Sprint Goal:** Enable custom CSV column mapping to the OCEL 2.0 specification.
*   **Scope:** UI mapper screen, column type validator, error/anomaly dashboard for mismatches.
*   **In-Scope Files/Modules:** Schema Mapping UI, Mapping Service API, validation rules.
*   **Dependencies:** Sprint 2 ingestion.
*   **Definition of Done:** Mapped schema persists; invalid data types raise alerts; valid records successfully match standard OCEL formats.
*   **Out-of-Scope:** Graph database insertions.

## Sprint 4: Graph Database & Discovery
*   **Sprint Goal:** Establish the OCPM Neo4j graph structure and discover basic process graphs.
*   **Scope:** Neo4j cluster configuration, event-to-object relation mappings, static process map rendering.
*   **In-Scope Files/Modules:** Neo4j Schema definitions, pm4py heuristics miner, Process Graph UI component.
*   **Dependencies:** Sprint 3 schema mapping.
*   **Definition of Done:** Parsed CSV events populated in Neo4j; many-to-many relationship queries run; process graph displays in UI.
*   **Out-of-Scope:** Carbon overlays on graph edges, conformance analysis.

## Sprint 5: Object-Centric Conformance
*   **Sprint Goal:** Detect process deviations against standard reference BPMN models.
*   **Scope:** BPMN model uploader, token replay algorithms, deviation mapping engine.
*   **In-Scope Files/Modules:** Conformance Service API, deviation report page, model uploader UI.
*   **Dependencies:** Sprint 4 process graph.
*   **Definition of Done:** Uploaded BPMN model compared to graph data; deviations mapped to specific process activities.
*   **Out-of-Scope:** Carbon-aware conformance checking.

## Sprint 6: Carbon Attribution Engine
*   **Sprint Goal:** Map carbon footprint calculations onto process execution steps.
*   **Scope:** Emission factor database table, carbon algebra utility, carbon node/edge overlays in UI.
*   **In-Scope Files/Modules:** Carbon Service, Emission Factor Registry API, Process Graph Carbon UI.
*   **Dependencies:** Sprint 4 and Sprint 5.
*   **Definition of Done:** Scope 1, 2, and 3 calculations run; carbon overlays show emissions intensity on the process map.
*   **Out-of-Scope:** Real-time sensor integration, supplier portal.

## Sprint 7: ESG scoring & Supplier Portal
*   **Sprint Goal:** Set up supplier registry and calculate foundational ESG metrics.
*   **Scope:** Supplier portal API, Supplier dashboard, GRI/SASB framework mapping tables.
*   **In-Scope Files/Modules:** ESG Service, Supplier Service, Supplier dashboard UI page.
*   **Dependencies:** Sprint 6 carbon data.
*   **Definition of Done:** Suppliers submit Scope 3 records; ESG scores update dynamically; supplier registry accessible by tenant.
*   **Out-of-Scope:** AI Copilot supplier recommendations.

## Sprint 8: AI Copilot RAG
*   **Sprint Goal:** Build the retrieval-augmented generation (RAG) conversational interface.
*   **Scope:** Vector store setup (pgvector), system prompt configuration, RAG document search pipeline.
*   **In-Scope Files/Modules:** AI Copilot Service (`[AI_COPILOT_ARCHITECTURE.md](./AI_COPILOT_ARCHITECTURE.md)`), AI Chat UI, Knowledge Base page.
*   **Dependencies:** Sprint 6 carbon data, Sprint 7 ESG configurations.
*   **Definition of Done:** PDFs upload to knowledge base; RAG queries return accurate answers citing stored document sources.
*   **Out-of-Scope:** NL-to-SQL or NL-to-Cypher graph queries.

## Sprint 9: BRSR Reporting & Exports
*   **Sprint Goal:** Standardize SEBI BRSR reporting templates and automated PDF/XBRL export.
*   **Scope:** BRSR template mapper, automatic ESG data collector, export worker.
*   **In-Scope Files/Modules:** Reporting Service, BRSR Reporting UI, XBRL/PDF format engines.
*   **Dependencies:** Sprint 7.
*   **Definition of Done:** System automatically compiles Section A, B, and C parameters; report exports successfully in valid formats.
*   **Out-of-Scope:** Real-time SCADA digital twins.

## Sprint 10: Scenario Simulator & Digital Twin
*   **Sprint Goal:** Run what-if simulations on carbon/cost variables and view process state-graphs.
*   **Scope:** Simulation algebra calculator, state-graph digital twin UI page.
*   **In-Scope Files/Modules:** Scenario Simulator Service, Digital Twin UI Component.
*   **Dependencies:** Sprint 6 and Sprint 9.
*   **Definition of Done:** User adjusts simulation sliders; UI displays carbon savings and cycle time delta projections.
*   **Out-of-Scope:** ERP writebacks, automated trigger execution.

## Sprint 11: Alert Center & Workflows
*   **Sprint Goal:** Implement automated webhooks and process deviation alerts.
*   **Scope:** Alert engine database schema, email/Slack webhooks, deviation alert trigger worker.
*   **In-Scope Files/Modules:** Alert Service, Workflow Designer UI, notification handlers.
*   **Dependencies:** Sprint 5 and Sprint 10.
*   **Definition of Done:** Deviation triggers fire automated webhook payload; alerts log to multi-tenant dashboard.
*   **Out-of-Scope:** Autonomously executing agent loops.

## Sprint 12: Polish & Presentation Mode
*   **Sprint Goal:** Run E2E system testing and configure the grant evaluation presentation screen.
*   **Scope:** Interactive presentation slides, WCAG AA contrast adjustments, system performance logs.
*   **In-Scope Files/Modules:** Presentation Mode UI, QA Dashboard, Master Index assets.
*   **Dependencies:** All prior sprints.
*   **Definition of Done:** Pass all end-to-end user tests; presentation mode walkthrough runs cleanly without failures.
*   **Out-of-Scope:** Adding new platform features.
