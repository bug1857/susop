# SustainOCPM: Feature Priority Matrix

This document defines the implementation phases, scope limits, release definitions, and architectural complexity dependencies for the 18 core features of the SustainOCPM platform. 

To maintain architectural alignment without content duplication, this matrix cross-references functional targets in [PRODUCT_REQUIREMENTS_DOCUMENT.md](file:///Users/rudrapratapsingh/Desktop/newpro/PRODUCT_REQUIREMENTS_DOCUMENT.md) and milestones in [ENTERPRISE_ROADMAP.md](file:///Users/rudrapratapsingh/Desktop/newpro/ENTERPRISE_ROADMAP.md).

---

## 1. Core Feature Prioritization Matrix

| Feature | MVP | V1 | V2 | Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **CSV Upload** | **Scope:** Flat CSV files only.<br>**Limits:** Max 50MB, single object type.<br>**Release:** Manual column header mapping.<br>**Dependencies:** Ingestion Engine. | **Scope:** Multi-CSV mapping.<br>**Limits:** Max 500MB.<br>**Release:** Dynamic event-object association.<br>**Dependencies:** Relational database. | **Scope:** Auto-schema detection.<br>**Limits:** Max 2GB.<br>**Release:** Anomaly & type mismatch flagging.<br>**Dependencies:** Validation API. | **Scope:** Parallel batch upload.<br>**Limits:** Unlimited, direct S3/Blob.<br>**Release:** Streamed schema mapping.<br>**Dependencies:** Kafka pipeline. |
| **Process Discovery** | **Scope:** Single-case process maps.<br>**Limits:** Heuristics Miner only.<br>**Release:** Interactive static diagram.<br>**Dependencies:** pm4py engine, Postgres. | **Scope:** Object-Centric Process Mining.<br>**Limits:** OCEL 2.0 standard.<br>**Release:** Many-to-many relationship graphs.<br>**Dependencies:** Neo4j, OCEAn. | **Scope:** Carbon-attributed paths.<br>**Limits:** Dynamic variant visualization.<br>**Release:** Node/edge emission overlays.<br>**Dependencies:** Carbon Service. | **Scope:** Real-time process graphs.<br>**Limits:** Petabyte scale.<br>**Release:** Auto-pruned massive graphs.<br>**Dependencies:** Spark GraphX, Neo4j. |
| **Conformance** | **Scope:** Token replay checking.<br>**Limits:** Single-case BPMN models.<br>**Release:** Diagnostic logs.<br>**Dependencies:** Process Mining Agent. | **Scope:** Object-Centric Conformance.<br>**Limits:** OCEL 2.0 alignment.<br>**Release:** Multi-object deviation maps.<br>**Dependencies:** Neo4j Graph DB. | **Scope:** Carbon-boundary checks.<br>**Limits:** Regulatory threshold rules.<br>**Release:** Real-time deviation alerts.<br>**Dependencies:** Carbon Service. | **Scope:** Automated self-healing conformance.<br>**Limits:** Continuous online audit.<br>**Release:** Deviation cost projections.<br>**Dependencies:** Kafka, Alert Engine. |
| **Carbon Intelligence** | **Scope:** Scope 1 & 2 estimation.<br>**Limits:** Static emission factors.<br>**Release:** Basic KPI scorecards.<br>**Dependencies:** Relational DB. | **Scope:** Scope 3 attribution.<br>**Limits:** Upstream logistics focus.<br>**Release:** Many-to-many carbon allocation.<br>**Dependencies:** Carbon Algebra engine. | **Scope:** Real-time telemetry carbon.<br>**Limits:** Machine-level sensors.<br>**Release:** Time-series emissions maps.<br>**Dependencies:** TimescaleDB. | **Scope:** End-to-end supply chain carbon.<br>**Limits:** Audit-ready verification.<br>**Release:** QR-code verifiable certificates.<br>**Dependencies:** Data Clean Room. |
| **ESG Intelligence** | **Scope:** Manual ESG KPI entry.<br>**Limits:** Static dashboards.<br>**Release:** Basic charts (water, waste).<br>**Dependencies:** Relational DB. | **Scope:** Process-driven ESG metrics.<br>**Limits:** GRI/SASB alignments.<br>**Release:** Dynamic reports.<br>**Dependencies:** Carbon Service, ESG Service. | **Scope:** Supply chain ESG scoring.<br>**Limits:** External API inputs.<br>**Release:** Supplier ESG scorecards.<br>**Dependencies:** Supplier Service. | **Scope:** Global double-materiality.<br>**Limits:** Multi-region compliance.<br>**Release:** CSRD disclosure portal.<br>**Dependencies:** Compliance Engine. |
| **Supplier Intelligence** | **Scope:** Supplier registry.<br>**Limits:** Static contact & category profiles.<br>**Release:** Dynamic supplier tables.<br>**Dependencies:** Relational DB. | **Scope:** Supplier carbon ingestion.<br>**Limits:** Direct CSV entry.<br>**Release:** Upstream Scope 3 dashboard.<br>**Dependencies:** Ingestion Portal API. | **Scope:** Supplier risk profiling.<br>**Limits:** Automated risk scoring.<br>**Release:** Supplier ESG audit trails.<br>**Dependencies:** ESG Service. | **Scope:** Collaborative supplier networks.<br>**Limits:** Cross-tenant secure sharing.<br>**Release:** Anonymized benchmarking views.<br>**Dependencies:** Data Clean Room. |
| **AI Copilot** | **Scope:** Static QA on dashboards.<br>**Limits:** Pre-defined prompt selections.<br>**Release:** Simple RAG chat.<br>**Dependencies:** OpenAI API, pgvector. | **Scope:** Conversational OCPM.<br>**Limits:** Natural Language to Cypher.<br>**Release:** Dynamic process querying.<br>**Dependencies:** Neo4j, LLM Agent. | **Scope:** Prescriptive actions.<br>**Limits:** Decarbonization tips.<br>**Release:** Optimization recommendations.<br>**Dependencies:** Recommendation Service. | **Scope:** Autonomous multi-agent loops.<br>**Limits:** Private LLM host.<br>**Release:** Self-correcting audit loops.<br>**Dependencies:** Private GPU clusters. |
| **BRSR Reporting** | **Scope:** Manual PDF export.<br>**Limits:** BRSR Section A (General).<br>**Release:** Static form fields.<br>**Dependencies:** Reporting Service. | **Scope:** Semi-automated export.<br>**Limits:** BRSR Section B & C.<br>**Release:** Automated ESG data pull.<br>**Dependencies:** Carbon & ESG Services. | **Scope:** Fully automated reports.<br>**Limits:** Entire SEBI framework.<br>**Release:** PDF/JSON compliant files.<br>**Dependencies:** BRSR Agent, Reporting DB. | **Scope:** Digital audit-ready BRSR.<br>**Limits:** XBRL schema compliance.<br>**Release:** Direct regulatory submission.<br>**Dependencies:** Cryptographic Audit. |
| **Benchmarking** | **Scope:** Simple process benchmarking.<br>**Limits:** Compare cycle times.<br>**Release:** Dashboard comparisons.<br>**Dependencies:** Relational DB. | **Scope:** Variant-level comparisons.<br>**Limits:** Plant/facility variants.<br>**Release:** Multi-variable analytics.<br>**Dependencies:** Core Analytics Service. | **Scope:** Peer-group benchmarking.<br>**Limits:** Anonymous industrial metrics.<br>**Release:** Industry baseline comparison.<br>**Dependencies:** Data Clean Room. | **Scope:** Automated optimization maps.<br>**Limits:** Dynamic best-practice path.<br>**Release:** AI-driven optimization inputs.<br>**Dependencies:** Recommendation Service. |
| **Knowledge Base** | **Scope:** Static regulatory PDF list.<br>**Limits:** User-uploaded files only.<br>**Release:** Document list UI.<br>**Dependencies:** Relational DB. | **Scope:** Vectorized regulations.<br>**Limits:** GRI/SASB/BRSR docs.<br>**Release:** Document-grounded RAG QA.<br>**Dependencies:** pgvector, Parser API. | **Scope:** Operational wiki.<br>**Limits:** Past process resolutions.<br>**Release:** User annotation integration.<br>**Dependencies:** LLM summarizer. | **Scope:** Federated knowledge search.<br>**Limits:** External enterprise data.<br>**Release:** SharePoint/Confluence APIs.<br>**Dependencies:** OAuth gateways. |
| **Digital Twin** | **Scope:** Static plant layout.<br>**Limits:** Non-interactive image overlay.<br>**Release:** Dashboard layout page.<br>**Dependencies:** Static assets. | **Scope:** Dynamic Process Twin.<br>**Limits:** Visualizes current OCEL logs.<br>**Release:** Real-time state-graph UI.<br>**Dependencies:** Neo4j Graph DB. | **Scope:** IoT-enabled Digital Twin.<br>**Limits:** Real-time sensor telemetry.<br>**Release:** Dynamic overlay dashboard.<br>**Dependencies:** TimescaleDB, Kafka. | **Scope:** Bidirectional Digital Twin.<br>**Limits:** Active workflow execution.<br>**Release:** Automated system controls.<br>**Dependencies:** ERP API writeback. |
| **Scenario Simulator** | **Scope:** Static what-if calculator.<br>**Limits:** Manual input parameters.<br>**Release:** Formula-based slider page.<br>**Dependencies:** Carbon Service. | **Scope:** Process simulation.<br>**Limits:** Cycle time simulation.<br>**Release:** Variant time-delta projections.<br>**Dependencies:** Simulation Engine. | **Scope:** Graph-based simulation.<br>**Limits:** Carbon, cost, time loops.<br>**Release:** Dynamic variant simulator.<br>**Dependencies:** Neo4j, Digital Twin. | **Scope:** Prescriptive AI simulation.<br>**Limits:** Multi-variable optimizations.<br>**Release:** Automated ROI scenario reports.<br>**Dependencies:** Simulation Agent. |
| **Workflow Automation** | **Scope:** Static email notifications.<br>**Limits:** System admin updates.<br>**Release:** SMTP server setup.<br>**Dependencies:** Relational DB. | **Scope:** Webhook triggers.<br>**Limits:** Basic operational triggers.<br>**Release:** Jira/Slack API integrations.<br>**Dependencies:** Alert Engine. | **Scope:** Multi-step orchestration.<br>**Limits:** Cross-system workflows.<br>**Release:** Interactive workflow designer.<br>**Dependencies:** Workflow Service. | **Scope:** Autonomous self-healing.<br>**Limits:** ERP feedback loop API.<br>**Release:** Automated process correction.<br>**Dependencies:** Bidirectional twin. |
| **Collaboration** | **Scope:** Link sharing.<br>**Limits:** Raw URL copying.<br>**Release:** Static share button.<br>**Dependencies:** Frontend router. | **Scope:** Dashboard annotations.<br>**Limits:** Inline text comments.<br>**Release:** Mention capabilities (@user).<br>**Dependencies:** Relational DB. | **Scope:** Live workspaces.<br>**Limits:** Real-time dashboard co-edit.<br>**Release:** Shared collaborative room.<br>**Dependencies:** WebSockets. | **Scope:** Inter-tenant portals.<br>**Limits:** Secure supplier share.<br>**Release:** Data Clean Room sharing.<br>**Dependencies:** Encryption Gateway. |
| **Alerts** | **Scope:** Basic system failures.<br>**Limits:** Relational database flags.<br>**Release:** Log monitoring dashboard.<br>**Dependencies:** Relational DB. | **Scope:** Operational alerts.<br>**Limits:** Deviation & threshold breach.<br>**Release:** In-app notification center.<br>**Dependencies:** Alert Service. | **Scope:** Smart alert groupings.<br>**Limits:** Anomaly clustering.<br>**Release:** Reduced alert noise UI.<br>**Dependencies:** AI Copilot Service. | **Scope:** Predictive alerts.<br>**Limits:** Projected carbon violations.<br>**Release:** Proactive system interventions.<br>**Dependencies:** Scenario Simulator. |
| **Audit Trail** | **Scope:** Simple activity logs.<br>**Limits:** User auth tracking.<br>**Release:** Static table logs.<br>**Dependencies:** Relational DB. | **Scope:** Regulatory carbon audits.<br>**Limits:** Emission factor edits.<br>**Release:** Immutable audit tables.<br>**Dependencies:** Audit Service. | **Scope:** Process change logs.<br>**Limits:** Graph modification tracks.<br>**Release:** Graphical audit timeline.<br>**Dependencies:** Neo4j history engine. | **Scope:** Cryptographic verification.<br>**Limits:** Financial-grade tamper proof.<br>**Release:** Exportable blockchain/ledger.<br>**Dependencies:** Signer API. |
| **Multi-Tenant SaaS** | **Scope:** Single-tenant container.<br>**Limits:** Independent database instance.<br>**Release:** Separated VM deployment.<br>**Dependencies:** Docker, K8s. | **Scope:** Shared database schema.<br>**Limits:** Postgres RLS enforcement.<br>**Release:** Dynamic workspace routes.<br>**Dependencies:** Postgres RLS. | **Scope:** Regional cloud compliance.<br>**Limits:** Localized database storage.<br>**Release:** Cross-region user routing.<br>**Dependencies:** IAM Gateway. | **Scope:** Hybrid SaaS plane.<br>**Limits:** Dedicated edge collectors.<br>**Release:** Secure tenant isolation.<br>**Dependencies:** Private Link network. |
| **Presentation Mode** | **Scope:** Static slide export.<br>**Limits:** Standard PDF/Image downloads.<br>**Release:** Dashboard print styles.<br>**Dependencies:** Frontend export. | **Scope:** Live presentation slide.<br>**Limits:** Dashboard page projection.<br>**Release:** Fullscreen interactive mode.<br>**Dependencies:** Presentation Spec. | **Scope:** Presentation builder.<br>**Limits:** Slide compilation page.<br>**Release:** Custom chart selections.<br>**Dependencies:** Slide builder engine. | **Scope:** Shared presenting room.<br>**Limits:** Sync presenter-audience views.<br>**Release:** WebSockets live actioning.<br>**Dependencies:** WebSockets, Simulator. |

---

## 2. Key Architectural Complexity Dependencies

The rollout of features is heavily gated by three structural transitions in the database and ingestion pipeline. The diagram below illustrates how features are constrained by database migrations:

```mermaid
graph TD
    MVP[Phase 1: Relational & Vector MVP] --> V1[Phase 2: Graph Engine V1]
    V1 --> V2[Phase 3: IoT Time-Series V2]
    V2 --> ENT[Phase 4: Enterprise Cryptographic / Clean Room]

    subgraph "Phase 1: PostgreSQL & pgvector"
        CSV_M[Flat CSV Upload]
        COPI_M[AI Copilot RAG]
        CARB_M[Scope 1 & 2 Carbon]
    end

    subgraph "Phase 2: Neo4j Graph DB"
        OCPM_V1[OCPM Discovery]
        CONF_V1[Conformance Checking]
        CARB_V1[Scope 3 Carbon Algebra]
    end

    subgraph "Phase 3: TimescaleDB & Kafka"
        TWIN_V2[Digital Twin Telemetry]
        SCEN_V2[Scenario Simulation]
        ALER_V2[Predictive Alerts]
    end

    subgraph "Phase 4: Clean Rooms & Crypto Keys"
        COLL_ENT[Secure Supplier Benchmarking]
        AUDI_ENT[Verifiable Audit Ledger]
    end

    CSV_M --> OCPM_V1
    COPI_M --> OCPM_V1
    CARB_M --> CARB_V1
    OCPM_V1 --> TWIN_V2
    CARB_V1 --> SCEN_V2
    TWIN_V2 --> COLL_ENT
    CONF_V1 --> AUDI_ENT
```

### 2.1 Critical Path Dependencies
1. **Transition to Graph (MVP -> V1):** Process Discovery, Conformance, and Scope 3 Carbon calculations cannot advance beyond rudimentary, single-case tabular metrics without migrating to the Neo4j graph structure. Attempting to run many-to-many relationship mappings on standard PostgreSQL tables will lead to severe operational performance degradation.
2. **Transition to Time-Series Ingestion (V1 -> V2):** SCADA and IoT sensor integration for real-time digital twins and scenario simulation requires the addition of TimescaleDB and Kafka pipelines. Standard relational tables cannot support the write volume of high-frequency machine metrics.
3. **Transition to Secure Sharing (V2 -> Enterprise):** Collaborative benchmarking and supply chain Scope 3 calculations require a Zero-Knowledge / Data Clean Room infrastructure to avoid sharing sensitive competitive data across tenant boundaries, enforcing absolute compliance.
