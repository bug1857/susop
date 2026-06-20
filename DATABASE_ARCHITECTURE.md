# SustainOCPM — Database Architecture

This document defines the complete database architecture for **SustainOCPM**, a Carbon-Aware Object-Centric Process Intelligence Platform. The platform combines Object-Centric Process Mining (OCPM), Carbon Attribution, Sustainability Intelligence, ESG Analytics, Conformance Checking, BRSR Reporting, AI Copilot, and Decision Intelligence.

---

## 1. Overview

SustainOCPM processes and analyzes transactional event data linked to physical and digital objects, computing carbon footprint metrics across Scope 1, 2, and 3 emissions. The database tier must support high-throughput event ingestion, complex graph traversal (OCEL 2.0 object-centric paths), low-latency analytical queries, vector search for regulatory AI compliance, and robust multi-tenancy.

### Multi-Tenancy Strategy

SustainOCPM adopts a **Shared Database, Shared Schema with Row-Level Security (RLS)** model as its primary multi-tenancy strategy. The `tenant_id` (referencing the `organizations` table) is present on every single table, and PostgreSQL Row-Level Security policies are enabled globally.

#### Architectural Trade-offs

| Strategy | Advantages | Disadvantages | Selection Rationale |
| :--- | :--- | :--- | :--- |
| **Shared Database, Shared Schema (RLS)** | - Minimal infrastructure costs.<br>- Highly efficient connection pooling.<br>- Simplified global schema updates.<br>- Enables cross-tenant de-identified benchmarking (critical for ESG sector analysis). | - Risk of "noisy neighbor" resource starvation.<br>- Risk of RLS bypass bugs.<br>- Complex point-in-time restore per tenant. | **Selected Strategy**: Crucial for cross-tenant ESG benchmarking and overall resource optimization. Mitigated using strict database connection policies and tenant-level resource limits in TimescaleDB. |
| **Schema-per-Tenant** | - Logical isolation within a single database cluster.<br>- Easier backup/restore per tenant.<br>- Customized schemas per tenant possible. | - High connection overhead.<br>- Difficult cross-tenant queries.<br>- Schema migration complexity scales linearly with the number of tenants.<br>- PostgreSQL performance degrades with thousands of schemas due to system catalog bloat. | **Rejected**: The operational overhead of applying migrations to thousands of schemas is prohibitive for a SaaS deployment, and system catalog limits would cap tenant scaling. |
| **Database-per-Tenant** | - Complete data isolation.<br>- Tailored backup/restore and PITR schemas.<br>- Hard boundaries prevent data leaks. | - Massive infrastructure cost.<br>- Idle database instances waste CPU/RAM.<br>- Impossible to run cross-tenant benchmarking without ETL pipelines.<br>- Difficult connection pooling. | **Rejected**: Too expensive for mid-market customers; breaks real-time cross-tenant ESG benchmarking which is a key product differentiator. |

#### Row-Level Security (RLS) Policy Blueprint

To enforce tenant isolation, every table containing tenant data implements the following policy:

```sql
-- Conceptual representation of Row-Level Security enforcement
ALTER TABLE tenant_table ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation_policy ON tenant_table
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
```

> [!IMPORTANT]
> The database connection pooler (e.g., PgBouncer) must be configured in transaction mode, and the application backend must explicitly set `app.current_tenant_id` within a transaction block for every request.

---

### Database Technology Choices

The architecture leverages a hybrid polyglot persistence model to handle structured data, time-series events, graph relations, vector search, and raw file storage.

```
                  ┌────────────────────────────────────────────────────────┐
                  │                 SustainOCPM Gateway                    │
                  └────────────────────────────────────────────────────────┘
                                               │
             ┌─────────────────────────────────┼──────────────────────────────┐
             ▼                                 ▼                              ▼
 ┌──────────────────────┐           ┌──────────────────────┐       ┌──────────────────────┐
 │    PostgreSQL Core   │           │     TimescaleDB      │       │     Neo4j Graph      │
 │  (Transactional Data │           │  (OCEL 2.0 Events,   │       │ (O2O, O2E Traversals,│
 │  & pgvector RAG)     │           │   Audit, Emissions)  │       │  Process Topology)   │
 └──────────────────────┘           └──────────────────────┘       └──────────────────────┘
             │                                 │                              │
             └─────────────────────────────────┼──────────────────────────────┘
                                               ▼
                                   ┌───────────────────────┐
                                   │   Amazon S3 (Files)   │
                                   │  (Raw Logs, PDF Reps) │
                                   └───────────────────────┘
```

#### 1. PostgreSQL (Transactional & Core Data)
- **Role**: Primary relational engine.
- **Data Stored**: Organizations, Users, Roles, Workspaces, Projects, Dashboards, Comments, Suppliers, Reports metadata.
- **Rationale**: Relational integrity, ACID compliance, mature ecosystem, and native support for JSONB (for dynamic configurations).

#### 2. TimescaleDB (Time-Series & Event Data)
- **Role**: High-volume, time-series engine (PostgreSQL extension).
- **Data Stored**: OCEL 2.0 `events`, `emissions` calculations, system metrics, performance logs, and mutable/immutable `audit_logs`.
- **Rationale**: Automatic partitioning by time and tenant (hypertables), field-level compression (reducing storage footprint by up to 90%), and advanced time-series analytical capabilities.

#### 3. pgvector (Vector Embeddings)
- **Role**: Vector search engine (PostgreSQL extension).
- **Data Stored**: Semantic embeddings of regulatory frameworks (BRSR, EU CSRD, GHG Protocol) in the `knowledge_base` and AI session context memory.
- **Rationale**: Keeps AI context directly in the relational engine, preventing the need for an external vector database (like Pinecone) and allowing single-transaction queries combining metadata filtering and vector search.

#### 4. Neo4j (Graph Database)
- **Role**: Relationship traversal.
- **Data Stored**: Object-to-Event (O2E) and Object-to-Object (O2O) dynamic process graphs.
- **Rationale**: OCEL 2.0 models multiple object types interacting through multiple events (e.g., one purchase order linked to five items, three shipments, and two invoices). Traversing these multi-hop relationships in relational systems requires complex, slow recursive CTEs. Neo4j handles deep graph traversals (finding cycles, tracking process paths, and identifying multi-object bottlenecks) in milliseconds.

#### 5. Redis (Cache and Pub/Sub)
- **Role**: Distributed Cache & Message Broker.
- **Data Stored**: Session states, processed API configurations, real-time alert queues, and lock management.
- **Rationale**: Sub-millisecond latency for session retrieval and real-time pub/sub capabilities for anomaly alerts.

#### 6. Amazon S3 / MinIO (Object Storage)
- **Role**: Cold storage for large unstructured files.
- **Data Stored**: Raw uploaded logs (OCEL-XML, OCEL-JSON, CSV), exported compliance reports (PDFs, XLSX), and uploaded proof-of-emission documents.
- **Rationale**: Low-cost, highly available, infinite scaling for bulk data files.

---

## 2. Core Entities

The relational database schema is structured as a single schema running on PostgreSQL with TimescaleDB and pgvector. Below are the detailed definitions of the 32 core database entities.

### 2.1 Organizations
- **Description**: The top-level administrative tenant representing a company or group. All transactional and event data is isolated by the organization identifier.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier of the organization. |
| `name` | `VARCHAR(255)` | No | None | None | Legal name of the organization. |
| `domain` | `VARCHAR(255)` | No | None | `UNIQUE` (Active) | Primary corporate email domain for self-registration. |
| `tier` | `VARCHAR(50)` | No | Default `'Enterprise'` | None | Service tier (Standard, Enterprise, Academic). |
| `settings` | `JSONB` | No | Default `'{}'::jsonb` | None | Global configs, localization, default carbon units. |
| `billing_info` | `JSONB` | Yes | None | None | Billing configuration details, subscription limits. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field: Record creation timestamp. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field: Record last update timestamp. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. Null if active. |
| `created_by` | `UUID` | Yes | None | None | User ID who created the organization. |
| `updated_by` | `UUID` | Yes | None | None | User ID who last updated the organization. |

- **JSONB Attribute Specifications**:
  - `settings`:
    - `reporting_currency` (string, ISO 4217 code, e.g., `"INR"`, `"EUR"`)
    - `carbon_unit` (string, enum: `"kg_co2e"`, `"t_co2e"`)
    - `mfa_required` (boolean, default `false`)
    - `allowed_domains` (array of strings for domain restriction)
  - `billing_info`:
    - `subscription_status` (string, enum: `"active"`, `"past_due"`, `"canceled"`)
    - `max_workspaces` (integer limit)
    - `max_users` (integer limit)
    - `max_monthly_events` (bigint limit)
- **Constraints & Indexes**:
  - `idx_org_domain`: Unique index on `domain` where `deleted_at IS NULL`.
- **Scaling & Partitioning Strategy**: Unpartitioned reference table. Standard B-Tree indexing.
- **Soft Delete Policy**: Standard soft delete using `deleted_at` filter in RLS policies.

---

### 2.2 Teams
- **Description**: Logical groupings of users within an organization to manage resource permissions and dashboard access.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier of the team. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier for data isolation (references `organizations(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Display name of the team. |
| `description` | `TEXT` | Yes | None | None | Purpose and scope of the team. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **Constraints & Indexes**:
  - `idx_team_tenant`: Composite index on `(tenant_id, id)`.
- **Scaling & Partitioning Strategy**: Managed via standard relational indexing. Row count scales linearly with users.

---

### 2.3 Workspaces
- **Description**: Isolated environments within a tenant. Workspaces isolate projects, models, and analytics dashboards (e.g., "Production Supply Chain", "Staging Logistics Simulation").
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Display name of the workspace. |
| `environment` | `VARCHAR(50)` | No | Default `'Production'` | None | Environment stage (Production, Sandbox, Archive). |
| `settings` | `JSONB` | No | Default `'{}'::jsonb` | None | Workspace-specific parameters (carbon target limits). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `settings`:
    - `target_conformance_score` (numeric, e.g., `0.95` representing 95% target fitness)
    - `carbon_target_limits` (object containing limits per scope, e.g., `{"scope_1": 100000, "scope_2": 250000, "scope_3": 1000000}`)
- **Constraints & Indexes**:
  - `idx_workspace_tenant`: Composite index on `(tenant_id, deleted_at)`.
- **Scaling & Partitioning Strategy**: Standard indexing. Isolated settings bag allows easy schema-less workspace configurations.

---

### 2.4 Users
- **Description**: Individual system users authenticated to access the platform.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | User's primary organization (references `organizations(id)`). |
| `email` | `VARCHAR(255)` | No | None | `UNIQUE` | Unique email for authentication. |
| `password_hash`| `VARCHAR(255)` | No | None | None | Secure Argon2id password hash. |
| `first_name` | `VARCHAR(100)` | No | None | None | First name. |
| `last_name` | `VARCHAR(100)` | No | None | None | Last name. |
| `status` | `VARCHAR(50)` | No | Default `'Pending'` | None | User lifecycle state (Active, Suspended, Pending). |
| `mfa_secret` | `VARCHAR(255)` | Yes | None | None | Encrypted TOTP secret key. |
| `last_login_at`| `TIMESTAMP WITH TZ` | Yes | None | None | Timestamp of last user access. |
| `settings` | `JSONB` | No | Default `'{}'::jsonb` | None | User preferences (theme, language, alerts). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `settings`:
    - `ui_theme` (string, enum: `"dark"`, `"light"`, `"system"`)
    - `language` (string, ISO 639-1 code, e.g., `"en"`, `"de"`)
    - `notification_routing` (object, e.g., `{"email": true, "slack": false, "in_app": true}`)
- **Constraints & Indexes**:
  - `idx_user_email`: Unique index on `email` where `deleted_at IS NULL`.
  - `idx_user_tenant`: Foreign key index on `tenant_id`.
- **Scaling & Partitioning Strategy**: Shared reference table. Standard B-Tree indexing.

---

### 2.5 Roles
- **Description**: RBAC templates containing sets of permissions. Roles can be global (system-defined) or tenant-specific.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | Yes | None | `FOREIGN KEY` | Tenant context. Null if global role (references `organizations(id)`). |
| `name` | `VARCHAR(100)` | No | None | None | Role name (e.g., 'ESG_Auditor', 'Workspace_Admin'). |
| `description` | `TEXT` | Yes | None | None | Purpose and definition of the role. |
| `is_system` | `BOOLEAN` | No | Default `FALSE` | None | Flag indicating if role is unmodifiable system default. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **Constraints & Indexes**:
  - `idx_role_tenant_name`: Composite unique index on `(tenant_id, name)` where `deleted_at IS NULL`.
- **Scaling & Partitioning Strategy**: Small lookup table. No partitioning.

---

### 2.6 Permissions
- **Description**: Fine-grained access control mappings linked to roles, defining allowed actions on resources.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | Yes | None | `FOREIGN KEY` | Tenant identifier. Null if global (references `organizations(id)`). |
| `role_id` | `UUID` | No | None | `FOREIGN KEY` | Target role (references `roles(id)`). |
| `resource` | `VARCHAR(100)` | No | None | None | Protected resource (e.g., 'projects', 'emissions'). |
| `action` | `VARCHAR(50)` | No | None | None | Permitted action (e.g., 'read', 'write', 'approve'). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |

- **Constraints & Indexes**:
  - `idx_permission_role`: Composite index on `(role_id, resource, action)`.
- **Scaling & Partitioning Strategy**: Small static mapping table. Cached in Redis to prevent database hits during route middleware execution.

---

### 2.7 Projects
- **Description**: An analysis scope that binds OCEL 2.0 log data (events, objects, and relationships) to carbon intelligence metrics.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `workspace_id` | `UUID` | No | None | `FOREIGN KEY` | Target workspace context (references `workspaces(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Project name. |
| `description` | `TEXT` | Yes | None | None | Scope details. |
| `ocel_version` | `VARCHAR(50)` | No | Default `'2.0'` | None | Supported OCEL version specification. |
| `status` | `VARCHAR(50)` | No | Default `'Active'` | None | Project status (Active, Archived, Processing). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **Constraints & Indexes**:
  - `idx_project_workspace`: Composite index on `(workspace_id, status)`.
  - `idx_project_tenant`: Foreign key index on `tenant_id`.
- **Scaling & Partitioning Strategy**: Metadata reference table. Ingestion status determines parser locking mechanisms.

---

### 2.8 Uploads
- **Description**: Staging tracker for ingested log files (OCEL-JSON, OCEL-XML, CSV, BPMN) before they are parsed and loaded into the main event model.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Target project (references `projects(id)`). |
| `file_name` | `VARCHAR(255)` | No | None | None | Original file name. |
| `file_size` | `BIGINT` | No | None | None | File size in bytes. |
| `file_type` | `VARCHAR(50)` | No | None | None | File format (CSV, OCEL_JSON, OCEL_XML, BPMN). |
| `storage_path` | `VARCHAR(512)` | No | None | None | S3 storage URI. |
| `status` | `VARCHAR(50)` | No | Default `'Pending'` | None | Parsing status (Pending, Processing, Success, Failed). |
| `error_message`| `TEXT` | Yes | None | None | Ingestion failure reason details. |
| `row_count` | `INTEGER` | Yes | None | None | Total raw records detected. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |

- **Constraints & Indexes**:
  - `idx_upload_project`: Index on `(project_id, status)`.
- **Scaling & Partitioning Strategy**: Small table. Heavy file binaries are stored in S3, keeping database storage footprint negligible.

---

### 2.9 Events (OCEL 2.0 Core)
- **Description**: The transactional event table adhering to the OCEL 2.0 standard. It tracks state transitions in the process. Managed as a TimescaleDB hypertable.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Link to parent project (references `projects(id)`). |
| `event_id` | `VARCHAR(255)` | No | None | `PRIMARY KEY` (Comp) | Unique event ID defined in the log. |
| `activity` | `VARCHAR(255)` | No | None | None | Name of the process step (e.g., "Create Order"). |
| `timestamp` | `TIMESTAMP WITH TZ`| No | None | `PRIMARY KEY` (Comp) | The precise occurrence time of the event. |
| `attributes` | `JSONB` | No | Default `'{}'::jsonb` | GIN Index | OCEL 2.0 dynamic event attributes. |
| `created_at` | `TIMESTAMP WITH TZ`| No | Default `CURRENT_TIMESTAMP` | None | Ingestion system audit field. |
| `created_by` | `UUID` | Yes | None | None | Ingestion actor. |

- **JSONB Attribute Specifications**:
  - `attributes`: Dynamic key-values dictated by source logs. Typical keys parsed:
    - `operator_id` (string)
    - `machine_id` (string)
    - `electricity_consumption_kwh` (numeric)
    - `temperature_c` (numeric)
    - `cost_rate` (numeric)
    - `geo_lat` (numeric), `geo_lon` (numeric)
- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, event_id, timestamp)`.
  - `idx_events_project_timestamp`: Composite index on `(project_id, timestamp DESC)`.
  - `idx_events_activity`: Index on `activity`.
  - `idx_events_attributes_gin`: GIN index on `attributes` to query nested custom attributes using containment operators.
- **Scaling & Partitioning Strategy**:
  - **Partitioning**: Range partitioned by `timestamp` (7-day intervals) and list partitioned by `tenant_id` via TimescaleDB.

---

### 2.10 Objects (OCEL 2.0 Core)
- **Description**: The entities modified or referenced by events (e.g., raw materials, delivery trucks, invoices, machinery) according to the OCEL 2.0 standard.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Target project identifier (references `projects(id)`). |
| `object_id` | `VARCHAR(255)` | No | None | `PRIMARY KEY` (Comp) | Unique identifier of the object. |
| `object_type` | `VARCHAR(255)` | No | None | None | Type of the object (e.g., "Order", "Delivery", "Vehicle"). |
| `attributes` | `JSONB` | No | Default `'{}'::jsonb` | GIN Index | Dynamic attributes (e.g., weight, supplier_id, price). |
| `created_at` | `TIMESTAMP WITH TZ`| No | Default `CURRENT_TIMESTAMP` | None | Ingestion timestamp. |
| `created_by` | `UUID` | Yes | None | None | Ingestion actor. |

- **JSONB Attribute Specifications**:
  - `attributes`: Dynamic key-values dictated by object definitions:
    - `material` (string, e.g., `"Aluminium"`, `"Recycled PET"`)
    - `weight_kg` (numeric)
    - `fuel_efficiency_km_l` (numeric)
    - `capacity_tons` (numeric)
    - `supplier_code` (string)
    - `asset_purchase_value` (numeric)
- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, object_id)`.
  - `idx_objects_project_type`: Composite index on `(project_id, object_type)`.
  - `idx_objects_attributes_gin`: GIN index on `attributes` for querying custom nested object properties.
- **Scaling & Partitioning Strategy**: Non-time-series relational table, indexed for fast ID lookups. Copied into Neo4j for fast relationship traversal.

---

### 2.11 Event-Object Relationships
- **Description**: M:N associative mapping linking events and objects. Defines the specific role an object plays during an event (e.g., a specific truck object plays the role of "transport_vehicle" in a "Ship Order" event).
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `event_id` | `VARCHAR(255)` | No | None | `PRIMARY KEY` (Comp) | Target Event ID (references `events(event_id)`). |
| `object_id` | `VARCHAR(255)` | No | None | `PRIMARY KEY` (Comp) | Target Object ID (references `objects(object_id)`). |
| `relationship_role`| `VARCHAR(255)`| No | None | `PRIMARY KEY` (Comp) | Role qualification (e.g., 'processor', 'input_material'). |
| `timestamp` | `TIMESTAMP WITH TZ`| No | None | `PRIMARY KEY` (Comp) | Copied from Event for partition key alignment. |
| `attributes` | `JSONB` | No | Default `'{}'::jsonb` | None | OCEL 2.0 attributes specific to this relationship. |

- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, event_id, object_id, relationship_role, timestamp)`.
  - `idx_e2o_object`: Composite index on `(project_id, object_id)` to find all events for a given object.
  - `idx_e2o_event`: Composite index on `(project_id, event_id)` to find all objects associated with an event.
- **Scaling & Partitioning Strategy**: Partitioned identical to the `events` table (partitioned by time `timestamp` and `tenant_id`) to allow co-located database joins.

---

### 2.12 Object-Object Relationships
- **Description**: Dynamic relationships between objects (e.g., invoice contains items, purchase order contains line items, delivery truck carries pallet). Adheres to OCEL 2.0 O2O relationship standard.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `source_object_id`| `VARCHAR(255)`| No | None | `PRIMARY KEY` (Comp) | Source Object ID (e.g., Parent Order). |
| `target_object_id`| `VARCHAR(255)`| No | None | `PRIMARY KEY` (Comp) | Target Object ID (e.g., Child Item). |
| `relationship_role`| `VARCHAR(255)`| No | None | `PRIMARY KEY` (Comp) | Type of relation (e.g., 'contains', 'pays', 'allocates'). |
| `valid_from` | `TIMESTAMP WITH TZ`| No | None | None | Temporal start of the relationship. |
| `valid_to` | `TIMESTAMP WITH TZ`| Yes | None | None | Temporal end of relation. Null if active. |
| `attributes` | `JSONB` | No | Default `'{}'::jsonb` | None | Relationship attributes. |

- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, source_object_id, target_object_id, relationship_role)`.
  - `idx_o2o_source`: Composite index on `(project_id, source_object_id)`.
  - `idx_o2o_target`: Composite index on `(project_id, target_object_id)`.
- **Scaling & Partitioning Strategy**: Structured as a standard relational table. Traversals are optimized inside the Neo4j graph mirror instance.

---

### 2.13 Suppliers
- **Description**: Profiles suppliers for ESG rating tracking and Scope 3 carbon emission attribution.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Legal name of supplier. |
| `code` | `VARCHAR(100)` | No | None | `UNIQUE` (Active) | Internal supplier ERP code. |
| `contact_email` | `VARCHAR(255)` | Yes | None | None | Contact email. |
| `tier` | `INTEGER` | No | Default `1` | None | Supplier tier (e.g., 1 = Direct Supplier, 2 = Sub-contractor). |
| `esg_score` | `NUMERIC(5,2)` | Yes | None | None | ESG score calculated out of 100. |
| `sustainability_rating`| `VARCHAR(50)`| Yes | None | None | Industry rating (EcoVadis, CDG, CDP rating). |
| `address` | `TEXT` | Yes | None | None | Headquarters address. |
| `country` | `VARCHAR(100)` | No | None | None | Country of origin (used for localization factors). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **Constraints & Indexes**:
  - `idx_supplier_tenant_code`: Composite index on `(tenant_id, code)` where `deleted_at IS NULL`.
  - `idx_supplier_country`: Index on `(tenant_id, country)` for geographic factor groupings.
- **Scaling & Partitioning Strategy**: Small reference table, queried heavily during Scope 3 calculations.

---

### 2.14 Emissions
- **Description**: Computed carbon footprints associated with process events or specific objects. This includes calculation lineages. Managed as a TimescaleDB hypertable.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Unique identifier for the transaction. |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `scope` | `INTEGER` | No | Check: `(scope IN (1, 2, 3))` | None | Carbon scope categorization. |
| `scope_category`| `VARCHAR(100)`| No | None | None | Category definition matching GHG Protocol. |
| `calculation_timestamp`| `TIMESTAMP WITH TZ`| No | None | `PRIMARY KEY` (Comp) | Time of computation / execution of event. |
| `associated_event_id`| `VARCHAR(255)`| Yes | None | `FOREIGN KEY` | Maps emission directly to an OCEL Event. |
| `associated_object_id`| `VARCHAR(255)`| Yes | None | `FOREIGN KEY` | Maps emission directly to an OCEL Object. |
| `emission_factor_id`| `UUID` | No | None | `FOREIGN KEY` | Factor resource used (references `emission_factors(id)`). |
| `activity_data_value`| `NUMERIC(20,8)`| No | None | None | Input value (e.g. 500 kWh, 100 liters fuel). |
| `activity_data_unit`| `VARCHAR(50)` | No | None | None | Metric unit (e.g., kWh, L, kg-km). |
| `co2e_kg` | `NUMERIC(20,8)`| No | None | None | Computed equivalent carbon dioxide footprint in kilograms. |
| `calculation_methodology`| `TEXT` | No | None | None | Human-readable tracking formula applied. |
| `data_quality_score`| `NUMERIC(3,2)` | No | Default `1.0` | None | Pedigree matrix quality score (0.0 to 1.0). |
| `lineage_info` | `JSONB` | No | Default `'{}'::jsonb` | None | Complete calculation lineage graph data structure. |
| `created_at` | `TIMESTAMP WITH TZ`| No | Default `CURRENT_TIMESTAMP` | None | System audit field. |
| `created_by` | `UUID` | Yes | None | None | Running system actor. |

- **JSONB Attribute Specifications**:
  - `lineage_info`:
    - `input_parameters` (object, e.g., `{"mileage_km": 1500, "cargo_weight_tonnes": 12}`)
    - `factor_source` (object, e.g., `{"name": "DEFRA", "year": 2025, "table": "Freight transport"}`)
    - `formula_applied` (string, e.g., `"co2e_kg = mileage_km * cargo_weight_tonnes * factor_unit_value"`)
    - `intermediate_results` (array of numeric values representing steps in calculations)
- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, id, calculation_timestamp)`.
  - `idx_emissions_scope`: Index on `(tenant_id, scope, calculation_timestamp DESC)`.
  - `idx_emissions_event`: Composite index on `(tenant_id, associated_event_id)` where `associated_event_id IS NOT NULL`.
- **Scaling & Partitioning Strategy**:
  - **Partitioning**: Range partitioned by `calculation_timestamp` (30-day intervals) and list partitioned by `tenant_id` using TimescaleDB.

---

### 2.15 Emission Factors
- **Description**: Reference database storing carbon intensity constants gathered from international sustainability sources. Must support versioning and validity ranges.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `source_database`| `VARCHAR(100)`| No | None | None | Database origin (e.g., DEFRA, EcoInvent, Climatiq). |
| `source_version` | `VARCHAR(50)` | No | None | None | Release version (e.g., '2025-v1.2'). |
| `activity_type` | `VARCHAR(255)` | No | None | None | Scope description (e.g., 'Electricity grid mix', 'Diesel fuel'). |
| `unit_co2e_kg` | `NUMERIC(20,8)`| No | None | None | Emission value per unit. |
| `unit` | `VARCHAR(50)` | No | None | None | Input base unit (e.g., kWh, kg, km). |
| `geography` | `VARCHAR(50)` | No | Default `'Global'` | None | Target ISO region code applicability. |
| `lifecycle_stage`| `VARCHAR(100)`| No | Default `'Cradle-to-Grave'`| None | Boundaries classification. |
| `uncertainty_percentage`| `NUMERIC(5,2)`| Yes | None | None | Statistical error variance indicator. |
| `valid_from` | `TIMESTAMP WITH TZ`| No | None | None | Factor activation time. |
| `valid_to` | `TIMESTAMP WITH TZ`| Yes | None | None | Expiration time. Null if active. |
| `status` | `VARCHAR(50)` | No | Default `'Active'` | None | Lifecycle status (e.g., Active, Deprecated). |
| `created_at` | `TIMESTAMP WITH TZ`| No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Audit author. |

- **Constraints & Indexes**:
  - `idx_ef_lookup`: Composite index on `(activity_type, geography, unit)`.
- **Scaling & Partitioning Strategy**: Relational lookup table. Cached inside application server memory for quick calculation references.

---

### 2.16 Analyses
- **Description**: Saved analytical settings, filters, and computed results of a process mining execution. Used to reproduce dashboards and conformance results.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Analysis name. |
| `description` | `TEXT` | Yes | None | None | Context details. |
| `version` | `INTEGER` | No | Default `1` | None | Incremental version tracking. |
| `configuration` | `JSONB` | No | Default `'{}'::jsonb` | None | Complete filter tree settings, target path configurations. |
| `discovered_metrics`| `JSONB` | No | Default `'{}'::jsonb` | None | Process stats (throughput times, variant distributions). |
| `carbon_metrics` | `JSONB` | No | Default `'{}'::jsonb` | None | Carbon-related aggregations (average carbon per process case). |
| `is_baseline` | `BOOLEAN` | No | Default `FALSE` | None | Flag marking if this represents the benchmark model. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `configuration`:
    - `time_bounds` (object, e.g., `{"start": "2026-01-01T00:00:00Z", "end": "2026-06-01T00:00:00Z"}`)
    - `excluded_activities` (array of strings, e.g., `["Automated Verification"]`)
    - `focus_object_types` (array of strings, e.g., `["line_item", "invoice"]`)
  - `discovered_metrics`:
    - `variant_count` (integer)
    - `total_cases` (integer)
    - `average_lead_time_sec` (numeric)
    - `bottleneck_activities` (array of objects containing activity names and queue times)
  - `carbon_metrics`:
    - `aggregate_co2e_kg` (numeric)
    - `carbon_intensity_per_case` (numeric)
    - `variant_emissions` (array of objects linking variant IDs to carbon totals)
- **Constraints & Indexes**:
  - `idx_analysis_project`: Composite index on `(project_id, is_baseline)`.
- **Scaling & Partitioning Strategy**: Row count is low. Standard relational indexing.

---

### 2.17 Process Models
- **Description**: Structural representation of normative (reference) or discovered process flows (e.g., BPMN diagrams, Petri nets, Dependency Graphs).
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `analysis_id` | `UUID` | Yes | None | `FOREIGN KEY` | Optional linking to a dynamic analysis run (references `analyses(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Display name of the model. |
| `model_type` | `VARCHAR(50)` | No | None | None | Format (e.g., 'BPMN', 'PetriNet', 'DFG'). |
| `model_definition`| `JSONB` | No | Default `'{}'::jsonb` | None | Node-link graph structure (activities, gateways, routing). |
| `bpmn_xml_path` | `VARCHAR(512)` | Yes | None | None | Storage location on S3 for standard BPMN 2.0 XML. |
| `is_normative` | `BOOLEAN` | No | Default `FALSE` | None | Marks target reference process flow design. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `model_definition`:
    - `nodes` (array of objects with `id`, `label`, `type` [Task, Gateway, Start, End], `metadata`)
    - `edges` (array of objects with `source_id`, `target_id`, `transition_probability`, `carbon_weight`)
- **Constraints & Indexes**:
  - `idx_model_project`: Composite index on `(project_id, is_normative)`.
- **Scaling & Partitioning Strategy**: Structured formats allow quick parsing. Large XML formats are stored in S3, keeping database reads light.

---

### 2.18 Conformance Results
- **Description**: Discovered process compliance outcomes generated by comparing discovered event logs against a normative `process_models` reference graph.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project scope (references `projects(id)`). |
| `process_model_id`| `UUID` | No | None | `FOREIGN KEY` | Reference normative model (references `process_models(id)`). |
| `analysis_id` | `UUID` | No | None | `FOREIGN KEY` | Target analysis settings link (references `analyses(id)`). |
| `fitness` | `NUMERIC(5,4)` | No | Check: `(fitness <= 1.0)` | None | Fitness score mapping (0.0 to 1.0). |
| `precision` | `NUMERIC(5,4)` | No | Check: `(precision <= 1.0)`| None | Precision score mapping (0.0 to 1.0). |
| `generalization` | `NUMERIC(5,4)` | No | Check: `(generalization <= 1.0)`| None | Generalization score mapping (0.0 to 1.0). |
| `deviations` | `JSONB` | No | Default `'[]'::jsonb` | None | Array of structural deviations (skips, inserts, loops). |
| `carbon_conformance_gap_co2e`| `NUMERIC(20,8)`| No | Default `0.0` | None | Estimated carbon penalty caused by non-conforming paths. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | System actor executed calculation. |

- **JSONB Attribute Specifications**:
  - `deviations`: Array of structured deviation objects:
    - `deviation_type` (string, enum: `"activity_skip"`, `"unwanted_insert"`, `"violating_loop"`)
    - `activity_name` (string)
    - `occurrence_count` (integer)
    - `average_impact_co2e` (numeric)
    - `affected_case_ids` (array of strings)
- **Constraints & Indexes**:
  - `idx_conformance_analysis`: Composite index on `(analysis_id, created_at DESC)`.
- **Scaling & Partitioning Strategy**: Small results table. Recalculated asynchronously by worker agents.

---

### 2.19 Reports
- **Description**: Official ESG performance documents (e.g. BRSR Section C, EU CSRD templates) with multi-level review workflows.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `workspace_id` | `UUID` | No | None | `FOREIGN KEY` | Context workspace (references `workspaces(id)`). |
| `title` | `VARCHAR(255)` | No | None | None | Report title. |
| `report_type` | `VARCHAR(100)` | No | None | None | Framework standard (e.g., BRSR, CSRD, GRI, TCFD). |
| `reporting_period_start`| `DATE` | No | None | None | Start date of assessment period. |
| `reporting_period_end`| `DATE` | No | None | None | End date of assessment period. |
| `content` | `JSONB` | No | Default `'{}'::jsonb` | None | Output fields, compliance statements, audited numbers. |
| `status` | `VARCHAR(50)` | No | Default `'Draft'` | None | Status state (e.g., Draft, Review, Approved, Published). |
| `approval_workflow_state`| `JSONB` | No | Default `'{}'::jsonb` | None | Chain details (reviews, approval timestamps, sign-offs). |
| `pdf_output_path`| `VARCHAR(512)`| Yes | None | None | S3 storage path for finalized signed PDF. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `content`:
    - `framework_version` (string)
    - `quantitative_disclosures` (object containing structural metric bindings, e.g., `{"electricity_grid_mwh": 12500, "scope_1_direct_t_co2e": 48.5}`)
    - `qualitative_answers` (object containing textual compliance narratives)
  - `approval_workflow_state`:
    - `current_step` (integer)
    - `workflow_template_id` (uuid)
    - `approvers` (array of objects mapping user IDs to their decision state: `"pending"`, `"approved"`, `"rejected"`)
    - `audit_trail` (array of actions with users, decisions, comments, and timestamps)
- **Constraints & Indexes**:
  - `idx_report_search`: Composite index on `(tenant_id, report_type, status)`.
- **Scaling & Partitioning Strategy**: Fully relational. Relies on JSONB structure to dynamically adapt to evolving regulatory ESG framework questionnaires.

---

### 2.20 AI Sessions
- **Description**: Tracks user conversations with the platform's AI Copilot, providing conversational memory and context retrieval bounds.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant isolation context (references `organizations(id)`). |
| `user_id` | `UUID` | No | None | `FOREIGN KEY` | User who opened session (references `users(id)`). |
| `project_id` | `UUID` | Yes | None | `FOREIGN KEY` | Optional linking constraint to scope project context (references `projects(id)`). |
| `title` | `VARCHAR(255)` | No | Default `'New Session'` | None | Display title. |
| `conversation_history`| `JSONB` | No | Default `'[]'::jsonb` | None | Chat conversation history (system, user, assistant turns). |
| `tokens_used_prompt`| `INTEGER` | No | Default `0` | None | Cumulative prompt token cost. |
| `tokens_used_completion`| `INTEGER`| No | Default `0` | None | Cumulative completion token cost. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |

- **JSONB Attribute Specifications**:
  - `conversation_history`: Array of structured message exchange blocks:
    - `role` (string, enum: `"system"`, `"user"`, `"assistant"`)
    - `content` (text of the message)
    - `timestamp` (ISO 8601 string)
    - `retrieved_chunk_ids` (array of UUIDs referencing the Knowledge Base)
    - `applied_filters` (object showing UI state at conversation step)
- **Constraints & Indexes**:
  - `idx_ai_session_user`: Index on `(user_id, updated_at DESC)`.
- **Scaling & Partitioning Strategy**: Conversational details are appended. Large sessions are pruned in application memory before saving.

---

### 2.21 Knowledge Base
- **Description**: Regulatory reference material (e.g. BRSR guidelines, SEBI regulations, IPCC metrics) chunked and indexed as vector embeddings.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `document_title`| `VARCHAR(255)`| No | None | None | Standard name of source material. |
| `document_source`| `VARCHAR(512)`| No | None | None | S3 link or URL path. |
| `section_header`| `VARCHAR(255)`| Yes | None | None | Specific section or clause header. |
| `chunk_text` | `TEXT` | No | None | GTS Index | Extracted text block (typically 1000-2000 characters). |
| `chunk_embedding`| `vector(1536)` | No | None | HNSW Index | pgvector field storing OpenAI text-embedding-3-small vector. |
| `metadata` | `JSONB` | No | Default `'{}'::jsonb` | None | Source tracking, creation date, applicability tags. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Uploading system administrator ID. |

- **JSONB Attribute Specifications**:
  - `metadata`:
    - `applicable_frameworks` (array of strings, e.g., `["BRSR", "GRI"]`)
    - `regulatory_agency` (string, e.g., `"SEBI"`)
    - `publication_year` (integer)
    - `confidence_score` (numeric validation score)
- **Constraints & Indexes**:
  - `idx_kb_vector`: HNSW vector index on `chunk_embedding` using Cosine Distance.
  - `idx_kb_fts`: GIN full-text index on `chunk_text`.
- **Scaling & Partitioning Strategy**: Flat table. Designed for pgvector query execution.

---

### 2.22 Audit Logs
- **Description**: Immutable security logs capturing security events, modifications, exports, and administration actions. Managed as a TimescaleDB hypertable.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `user_id` | `UUID` | Yes | None | None | Accessing user ID. Null for system actions. |
| `action` | `VARCHAR(100)` | No | None | None | Operation executed (e.g., 'user_login', 'report_signed', 'export_logs'). |
| `resource` | `VARCHAR(100)` | No | None | None | Impacted entity namespace. |
| `resource_id` | `VARCHAR(255)`| Yes | None | None | Primary key representation of target resource. |
| `ip_address` | `INET` | Yes | None | None | Access client IP location. |
| `user_agent` | `VARCHAR(512)`| Yes | None | None | Access browser context string. |
| `timestamp` | `TIMESTAMP WITH TZ`| No | None | `PRIMARY KEY` (Comp) | Absolute execution time. |
| `details` | `JSONB` | No | Default `'{}'::jsonb` | None | Audit payload (e.g. delta diffs, query parameters). |

- **JSONB Attribute Specifications**:
  - `details`:
    - `payload_diff` (object containing state changes, e.g., `{"old": {"tier": "Standard"}, "new": {"tier": "Enterprise"}}`)
    - `query_executed` (string parameter trace)
    - `request_parameters` (object containing API route arguments)
- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, id, timestamp)`.
  - `idx_audit_search`: Composite index on `(tenant_id, action, timestamp DESC)`.
- **Scaling & Partitioning Strategy**:
  - **Partitioning**: Range partitioned by `timestamp` (weekly intervals) and list partitioned by `tenant_id` via TimescaleDB. Writes are strictly insert-only (enforced via database trigger rules preventing updates/deletes).

---

### 2.23 Benchmarks
- **Description**: De-identified industry target baselines used to contextualize performance metrics across carbon footprints and process times.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `industry_sector`| `VARCHAR(150)`| No | None | None | Sector standard categorization (e.g., 'Automotive', 'Textiles'). |
| `region` | `VARCHAR(100)` | No | None | None | Country / Economic area (e.g., 'IN', 'EU', 'Global'). |
| `metric_name` | `VARCHAR(150)`| No | None | None | Metric name (e.g., 'co2_per_item_purchased', 'cycle_time_hours'). |
| `percentile_25` | `NUMERIC(20,8)`| No | None | None | 25th percentile value. |
| `percentile_50` | `NUMERIC(20,8)`| No | None | None | Median industry value. |
| `percentile_75` | `NUMERIC(20,8)`| No | None | None | 75th percentile value. |
| `percentile_90` | `NUMERIC(20,8)`| No | None | None | 90th percentile value. |
| `source_data_origin`| `VARCHAR(255)`| No | None | None | Data source description (e.g., 'Aggregated SustainOCPM index'). |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Last computation date. |

- **Constraints & Indexes**:
  - `idx_benchmark_lookup`: Composite index on `(industry_sector, region, metric_name)`.
- **Scaling & Partitioning Strategy**: Read-heavy, low-write table. No partitioning needed.

---

### 2.24 Alerts
- **Description**: Real-time alerts triggered by process monitoring anomalies (e.g., carbon threshold violations, conformance score drops). Managed as a TimescaleDB hypertable.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `PRIMARY KEY` (Comp) | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Target project context (references `projects(id)`). |
| `rule_name` | `VARCHAR(255)` | No | None | None | System rule name triggered. |
| `alert_type` | `VARCHAR(100)` | No | None | None | Context group (e.g., 'Carbon_Threshold', 'Conformance_Anomaly'). |
| `severity` | `VARCHAR(50)` | No | None | None | Level (e.g., 'Info', 'Warning', 'Critical'). |
| `trigger_condition`| `JSONB` | No | None | None | Metric evaluation settings that triggered the alert. |
| `trigger_value` | `NUMERIC(20,8)`| No | None | None | Calculated value at trigger time. |
| `status` | `VARCHAR(50)` | No | Default `'Active'` | None | Lifecycle state (e.g., Active, Acknowledged, Resolved, Silenced). |
| `acknowledged_at`| `TIMESTAMP WITH TZ`| Yes | None | None | Acknowledgment timestamp. |
| `acknowledged_by`| `UUID` | Yes | None | None | Acknowledging user ID. |
| `resolved_at` | `TIMESTAMP WITH TZ`| Yes | None | None | Resolution timestamp. |
| `created_at` | `TIMESTAMP WITH TZ`| No | None | `PRIMARY KEY` (Comp) | Creation time. |

- **JSONB Attribute Specifications**:
  - `trigger_condition`:
    - `operator` (string, enum: `">"`, `"<"`, `"="`)
    - `threshold_value` (numeric)
    - `evaluation_period_seconds` (integer)
    - `aggregation_function` (string, e.g., `"sum"`, `"avg"`)
- **Constraints & Indexes**:
  - Primary Key: Composite key of `(tenant_id, id, created_at)`.
  - `idx_alerts_status`: Composite index on `(tenant_id, status, created_at DESC)`.
- **Scaling & Partitioning Strategy**:
  - **Partitioning**: Range partitioned by `created_at` (14-day intervals) and list partitioned by `tenant_id` via TimescaleDB.

---

### 2.25 Recommendations
- **Description**: AI-generated optimization recommendations based on process deviations and carbon hot-spots.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Associated project context (references `projects(id)`). |
| `alert_id` | `UUID` | Yes | None | None | Triggering alert identifier (if any). |
| `title` | `VARCHAR(255)` | No | None | None | Action title (e.g., 'Swap Supplier to Eco-mix'). |
| `description` | `TEXT` | No | None | None | Detailed optimization strategy proposed. |
| `estimated_carbon_saving_kg`| `NUMERIC(20,8)`| No | None | None | Target footprint reduction forecast. |
| `estimated_cost_saving_usd`| `NUMERIC(20,8)`| No | None | None | Operational cost savings forecast. |
| `confidence_score`| `NUMERIC(5,4)` | No | None | None | Model execution certainty ranking. |
| `status` | `VARCHAR(50)` | No | Default `'Proposed'` | None | Lifecycle state (e.g., Proposed, Accepted, Rejected, Completed). |
| `feedback_score`| `INTEGER` | Yes | Check: `(feedback_score BETWEEN 1 AND 5)` | None | User feedback score on recommendations usefulness. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | System generator engine ID. |

- **Constraints & Indexes**:
  - `idx_recommendation_status`: Composite index on `(tenant_id, project_id, status)`.
- **Scaling & Partitioning Strategy**: Flat table. Scaled using standard relational indexing.

---

### 2.26 Maturity Assessments
- **Description**: Semi-structured assessments of an organization's ESG performance and process mining readiness, capturing baseline scores.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `workspace_id` | `UUID` | No | None | `FOREIGN KEY` | Context workspace (references `workspaces(id)`). |
| `assessment_type`| `VARCHAR(100)`| No | None | None | Domain (e.g., 'BRSR_Pre_Audit', 'OCPM_Readiness'). |
| `scores` | `JSONB` | No | Default `'{}'::jsonb` | None | Score breakdown (e.g., {"governance": 4.2, "carbon": 3.8}). |
| `overall_score` | `NUMERIC(5,2)` | No | None | None | Unified assessment rating. |
| `evidence_links` | `JSONB` | No | Default `'[]'::jsonb` | None | References to raw data files in S3. |
| `assessor_comments`| `TEXT` | Yes | None | None | Auditor observation notes. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Auditor user ID. |

- **JSONB Attribute Specifications**:
  - `scores`:
    - `dimension_breakdown` (object mapping capability matrices, e.g., `{"carbon_accounting_maturity": 4.0, "process_visibility_maturity": 3.5, "supplier_collaboration": 2.0}`)
    - `gap_areas` (array of strings highlighting lowest-scoring indices)
  - `evidence_links`: Array of objects:
    - `file_name` (string)
    - `s3_uri` (string)
    - `verified_at` (timestamp)
- **Constraints & Indexes**:
  - `idx_maturity_search`: Composite index on `(workspace_id, assessment_type, created_at DESC)`.
- **Scaling & Partitioning Strategy**: Audit-focused, very low update frequency. No partitioning required.

---

### 2.27 Scenario Simulations
- **Description**: "What-if" simulation settings and output results testing how carbon and cycle times change under model process modifications.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `analysis_id` | `UUID` | No | None | `FOREIGN KEY` | Reference baseline run ID (references `analyses(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Simulation run identifier name. |
| `parameters` | `JSONB` | No | Default `'{}'::jsonb` | None | Set of modified properties (e.g. alternative routing rules). |
| `results` | `JSONB` | No | Default `'{}'::jsonb` | None | Generated comparison results metrics. |
| `status` | `VARCHAR(50)` | No | Default `'Pending'` | None | Run state (e.g., Pending, Simulating, Success, Failed). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |

- **JSONB Attribute Specifications**:
  - `parameters`:
    - `process_changes` (array of objects showing task skips or sequence shifts)
    - `supplier_swaps` (array of objects mapping old supplier IDs to new ones)
    - `emission_factor_overrides` (array of objects detailing manually set conversion modifications)
  - `results`:
    - `variance_cycle_time_seconds` (numeric delta)
    - `variance_co2e_kg` (numeric delta)
    - `simulated_variants` (array of objects defining the projected process topology pathways)
- **Constraints & Indexes**:
  - `idx_simulation_project`: Index on `(project_id, status)`.
- **Scaling & Partitioning Strategy**: Result parameters can be large. Cached inside Redis during active model execution.

---

### 2.28 Digital Twins
- **Description**: Mappings of real-time transactional process tokens to process steps. This allows continuous carbon and bottleneck monitoring.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `UNIQUE`, `FOREIGN KEY` | Project context. (references `projects(id)`). |
| `name` | `VARCHAR(255)` | No | None | None | Display identifier. |
| `state_mapping` | `JSONB` | No | Default `'{}'::jsonb` | None | Active state information (token locations, path congestion). |
| `sync_frequency_seconds`| `INTEGER`| No | Default `60` | None | Stream pull frequency. |
| `last_sync_timestamp`| `TIMESTAMP WITH TZ`| Yes | None | None | Last synchronization execution. |
| `status` | `VARCHAR(50)` | No | Default `'Active'` | None | Operational state (e.g., Active, Paused, Error). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |

- **JSONB Attribute Specifications**:
  - `state_mapping`:
    - `active_tokens` (array of objects matching live tracking entities to nodes in process flow charts)
    - `congestion_points` (array of elements highlighting queues exceeding nominal latency thresholds)
    - `live_carbon_accumulation_rate` (numeric metric of footprint accumulation rate)
- **Constraints & Indexes**:
  - `idx_twin_status`: Composite index on `(status, last_sync_timestamp)`.
- **Scaling & Partitioning Strategy**: State mapping is updated in-place via high-performance upserts.

---

### 2.29 Comments (Polymorphic)
- **Description**: Threaded discussion entries attached to core entities (e.g., Reports, ProcessModels, Simulations).
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `author_id` | `UUID` | No | None | `FOREIGN KEY` | Comment author user (references `users(id)`). |
| `commentable_type`| `VARCHAR(100)`| No | None | Polymorphic | Class name of target entity (e.g. 'Reports', 'ProcessModels'). |
| `commentable_id` | `UUID` | No | None | Polymorphic | UUID of target entity. |
| `parent_id` | `UUID` | Yes | None | `FOREIGN KEY` | Self-referencing column for nesting replies (references `comments(id)`). |
| `content` | `TEXT` | No | None | None | Comment text content. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |

- **Constraints & Indexes**:
  - `idx_comment_polymorphic`: Composite index on `(commentable_type, commentable_id, created_at ASC)`.
- **Scaling & Partitioning Strategy**: Flat hierarchy. Nested responses resolved recursively in application logic.

---

### 2.30 Notifications
- **Description**: In-app notifications sent to users concerning report approvals, critical threshold alerts, or recommendation updates.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `recipient_id` | `UUID` | No | None | `FOREIGN KEY` | Target recipient (references `users(id)`). |
| `title` | `VARCHAR(255)` | No | None | None | Notification title. |
| `message` | `TEXT` | No | None | None | Body text. |
| `notification_type`| `VARCHAR(100)`| No | None | None | Category (e.g., 'Alert_Triggered', 'Report_Approved'). |
| `read_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Null if unread. |
| `delivery_channel`| `VARCHAR(50)` | No | Default `'In_App'` | None | Target channel (e.g., In_App, Email, Slack). |
| `delivery_status` | `VARCHAR(50)` | No | Default `'Pending'` | None | Delivery status (e.g., Pending, Sent, Failed). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |

- **Constraints & Indexes**:
  - `idx_notification_recipient`: Composite index on `(recipient_id, read_at)` for unread list generation.
- **Scaling & Partitioning Strategy**: Pruned periodically (e.g., deleting read notifications older than 90 days).

---

### 2.31 Tags (Polymorphic)
- **Description**: Polymorphic categorization tags attached to Events, Objects, Suppliers, or Projects.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `name` | `VARCHAR(100)` | No | None | None | Display tag name (e.g., 'Scope-3-Critical', 'Logistics'). |
| `color_hex` | `VARCHAR(7)` | No | Default `'#6B7280'` | None | Color code visualization. |
| `taggable_type` | `VARCHAR(100)` | No | None | Polymorphic | Target namespace (e.g., 'Events', 'Objects', 'Suppliers'). |
| `taggable_id` | `VARCHAR(255)`| No | None | Polymorphic | Target ID (can be UUID or event/object alphanumeric code). |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |

- **Constraints & Indexes**:
  - `idx_tags_polymorphic`: Composite unique index on `(tenant_id, taggable_type, taggable_id, name)`.
- **Scaling & Partitioning Strategy**: Small polymorphic mapping table.

---

### 2.32 Dashboards
- **Description**: Customized visualization layout configurations for process and carbon analysis dashboards.
- **Schema Table**:

| Column Name | Data Type | Nullable | Constraints / Default | Key / Index | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `UUID` | No | `gen_random_uuid()` | `PRIMARY KEY` | Unique identifier. |
| `tenant_id` | `UUID` | No | None | `FOREIGN KEY` | Tenant identifier (references `organizations(id)`). |
| `project_id` | `UUID` | No | None | `FOREIGN KEY` | Parent project (references `projects(id)`). |
| `title` | `VARCHAR(255)` | No | None | None | Dashboard title. |
| `layout` | `JSONB` | No | Default `'[]'::jsonb` | None | Array containing layout positioning coordinates. |
| `widgets` | `JSONB` | No | Default `'[]'::jsonb` | None | Widget specifications (charts type, query configurations). |
| `is_public` | `BOOLEAN` | No | Default `FALSE` | None | Shared context access config. |
| `created_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `updated_at` | `TIMESTAMP WITH TZ` | No | Default `CURRENT_TIMESTAMP` | None | Audit field. |
| `deleted_at` | `TIMESTAMP WITH TZ` | Yes | None | None | Soft delete timestamp. |
| `created_by` | `UUID` | Yes | None | None | Creator user ID. |
| `updated_by` | `UUID` | Yes | None | None | Last modifier user ID. |

- **JSONB Attribute Specifications**:
  - `layout`: Array of dashboard layout blocks:
    - `widget_id` (string)
    - `x` (integer grid position), `y` (integer grid position)
    - `w` (width in columns), `h` (height in rows)
  - `widgets`: Array of chart configurations:
    - `id` (string)
    - `type` (string, enum: `"sankey"`, `"bar"`, `"line"`, `"parallel_coordinates"`)
    - `title` (string)
    - `query_config` (object containing targeted metrics: e.g. average lead time, conformance deviations, scope emissions)
- **Constraints & Indexes**:
  - `idx_dashboard_project`: Index on `(project_id, deleted_at)`.
- **Scaling & Partitioning Strategy**: Shared config table. Content layout stored in JSONB schema to adapt to dynamic widgets.

---

## 3. Entity Relationship Diagram

*(Refer to Section 3 above for the comprehensive Mermaid ER Diagram routing path mappings.)*

---

## 4. Indexing Strategy

SustainOCPM utilizes a tailored indexing strategy to optimize transactional speeds, analytical queries, dynamic JSON queries, and high-dimensional vector search.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SustainOCPM Indexing Tier                        │
├─────────────────┬─────────────────┬──────────────────┬──────────────────┤
│   B-Tree Indexes│   GIN (JSONB)   │  HNSW (pgvector) │  Partial Indexes │
├─────────────────┼─────────────────┼──────────────────┼──────────────────┤
│ - Primary Keys  │ - Attributes    │ - Knowledge      │ - Active records │
│ - Foreign Keys  │ - Filter JSONs  │   Base vectors   │   (soft deletes) │
│ - Tenant IDs    │ - Node-Link maps│ - Session history│ - Scope 3 events │
└─────────────────┴─────────────────┴──────────────────┴──────────────────┘
```

### 1. Primary and Foreign Key Indexes
- Automatically created B-Tree indexes on all single-column primary keys.
- **Foreign Key Enforcement**: An index is explicitly created on all foreign keys (e.g. `idx_user_tenant`, `idx_project_workspace`) to prevent table-scan deadlocks during cascade deletes.

### 2. Composite Indexes for Partitioned Queries
For tables partitioned by time and tenant (e.g. `events`, `emissions`, `alerts`), composite keys must include the partitioning columns to allow the query planner to target specific partitions (partition pruning).
- **Events Index**: `(project_id, timestamp DESC)` allows queries to fetch the latest events within a project without scanning other timelines.
- **Emissions Index**: `(tenant_id, scope, calculation_timestamp DESC)` optimizes real-time aggregation dashboards filtering by emission scope.

### 3. GIN (Generalized Inverted Index) for Dynamic JSONB
To query arbitrary user-uploaded fields stored within OCEL 2.0 dynamic attribute bags:
- **DDL Template**:
  ```sql
  CREATE INDEX idx_events_attributes_gin ON events USING gin (attributes);
  CREATE INDEX idx_objects_attributes_gin ON objects USING gin (attributes);
  ```
- **Rationale**: Allows the index to speed up queries checking for nested keys (e.g. `attributes ->> 'cost'`) or using the JSONB containment operator (`@>`).

### 4. Vector Indexes (pgvector HNSW)
To power the semantic Retrieval-Augmented Generation (RAG) within the AI Copilot knowledge base:
- **DDL Template**:
  ```sql
  CREATE INDEX idx_kb_vector ON knowledge_base 
  USING hnsw (chunk_embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);
  ```
- **Rationale**: The Hierarchical Navigable Small World (HNSW) index outperforms IVFFlat in search recall and speed. Using Cosine Distance (`vector_cosine_ops`) matches the standard embedding similarity metric used by LLM embedding models.

### 5. Partial (Filtered) Indexes
To reduce index size and increase lookup speeds on tables with flag columns:
- **DDL Template**:
  ```sql
  -- Index only non-deleted active users
  CREATE UNIQUE INDEX idx_user_email_active ON users (email) 
  WHERE deleted_at IS NULL;

  -- Index only active real-time alerts
  CREATE INDEX idx_alerts_active ON alerts (tenant_id, created_at DESC) 
  WHERE status = 'Active';
  ```

---

## 5. Partitioning Strategy

Because process logs and emission calculations accumulate millions of records per day, SustainOCPM relies on database partitioning to keep tables manageable, enable fast analytical queries, and simplify data deletion.

```
                     ┌──────────────────────────────┐
                     │     Events Ingestion Pipe    │
                     └──────────────┬───────────────┘
                                    │
                                    ▼
                     ┌──────────────────────────────┐
                     │    Multi-Tenant Routing      │
                     └──────────────┬───────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌──────────────────────────────┐                  ┌──────────────────────────────┐
│     Tenant A Hypertable      │                  │     Tenant B Hypertable      │
├──────────────────────────────┤                  ├──────────────────────────────┤
│ ┌──────────────────────────┐ │                  │ ┌──────────────────────────┐ │
│ │  Partition: June 2026    │ │                  │ │  Partition: June 2026    │ │
│ └──────────────────────────┘ │                  │ └──────────────────────────┘ │
│ ┌──────────────────────────┐ │                  │ ┌──────────────────────────┐ │
│ │  Partition: July 2026    │ │                  │ │  Partition: July 2026    │ │
│ └──────────────────────────┘ │                  │ └──────────────────────────┘ │
└──────────────────────────────┘                  └──────────────────────────────┘
```

### TimescaleDB Hypertables
The platform converts three primary transactional tables into **TimescaleDB Hypertables** to take advantage of time-series scaling features:

| Table | Partition Range Column | Interval Size | Space Partition Column |
| :--- | :--- | :--- | :--- |
| `events` | `timestamp` | 7 Days | `tenant_id` |
| `emissions` | `calculation_timestamp` | 30 Days | `tenant_id` |
| `audit_logs` | `timestamp` | 7 Days | None (Global Audit) |
| `alerts` | `created_at` | 14 Days | `tenant_id` |

#### DDL Hypertable Declaration Pattern
To initialize the hypertables during initial database setup:
```sql
-- Convert events table to hypertable partitioned by timestamp (1 week range)
SELECT create_hypertable('events', 'timestamp', 
                         partitioning_column => 'tenant_id', 
                         number_partitions => 64, 
                         chunk_time_interval => INTERVAL '7 days');

-- Enable TimescaleDB internal compression on the hypertable
ALTER TABLE events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'tenant_id, project_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

-- Establish policy to compress chunks older than 14 days
SELECT add_compression_policy('events', INTERVAL '14 days');
```

### Multi-Dimensional Partitioning (Time + Space)
By partitioning by both `timestamp` (time range) and `tenant_id` (space hashing), SustainOCPM ensures:
1. **Partition Pruning**: Queries for a specific tenant looking at last week's data only touch a single slice of physical memory, bypassing billions of unrelated rows.
2. **Aggressive Compression**: TimescaleDB compression runs in the background on closed partitions (e.g., older than 14 days), converting rows to a highly compressed columnar layout.
3. **Data Retention Management**: Tenants can configure custom retention periods. Deleting expired data is as simple as dropping the database partition file, which requires zero transaction log overhead.

---

## 6. Data Migration Strategy

SustainOCPM mandates **Zero-Downtime Database Migrations** to support its enterprise-grade 99.99% availability target.

### 1. Schema Migration Pattern (Expand and Contract)

```
[ Phase 1: Expand ]
  ├─ Add nullable column 'sustainability_tier' to suppliers
  └─ Application writes to BOTH old and new fields
          │
          ▼
[ Phase 2: Backfill ]
  └─ Staggered batch migration updates default values in historical records
          │
          ▼
[ Phase 3: Transition ]
  └─ Application is redeployed to read ONLY from 'sustainability_tier'
          │
          ▼
[ Phase 4: Contract ]
  └─ DDL migration executes column drop for old field
```

- **Phase 1: Expand**: Deploy database changes in a backward-compatible manner.
  - Adding a column: Ensure the column is nullable or has a default value.
  - Renaming a column: Create a new column, deploy code that writes to both columns, and backfill existing rows.
- **Phase 2: Transition**: Deploy updated application code that reads from and writes to the new database columns.
- **Phase 3: Contract**: Deploy a final migration script that cleans up the old fields, indexes, or tables.

### 2. Safe DDL Migration Locks
To prevent schema changes from blocking the database during high-traffic periods:
- All migrations must set strict lock timeouts.
- Table locks must not queue behind long-running analytical queries.

```sql
-- Migration template for a lock-safe column addition
SET statement_timeout = '3s';
SET lock_timeout = '2s';

ALTER TABLE suppliers ADD COLUMN carbon_neutral_certified BOOLEAN DEFAULT FALSE;
```

### 3. Data Backfills
Large database updates must be broken up and run in small, staggered chunks using background worker tasks rather than running in a single transaction. This prevents locking tables and overloading the transaction log (WAL).

```sql
-- Staggered batch update template to prevent locking tables
DO $$
DECLARE
    rows_updated INT;
BEGIN
    LOOP
        UPDATE suppliers 
        SET carbon_neutral_certified = TRUE 
        WHERE id IN (
            SELECT id FROM suppliers 
            WHERE carbon_neutral_certified IS FALSE 
            AND esg_score > 80.0
            LIMIT 500
        );
        
        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        COMMIT; -- Commit chunk immediately to release row locks
        
        EXIT WHEN rows_updated = 0;
        PERFORM pg_sleep(0.5); -- Rest worker for 500ms
    END LOOP;
END $$;
```

---

## 7. Performance Optimization

To deliver fast dashboard rendering and conformance analysis, SustainOCPM implements the following performance optimizations.

```
                          ┌───────────────────────────┐
                          │     Application Tier      │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   PgBouncer Pool Manager  │
                          └─────────────┬─────────────┘
                                        │
                 ┌──────────────────────┴──────────────────────┐
                 ▼                                             ▼
     ┌───────────────────────┐                     ┌───────────────────────┐
     │   Primary DB (Reads/  │                     │   Read Replica DB     │
     │   Writes/Transactions)│                     │  (Aggregations/BPMN)  │
     └───────────┬───────────┘                     └───────────┬───────────┘
                 │                                             │
                 ▼                                             ▼
      [ Materialized Views ]                        [ Materialized Views ]
```

### 1. Query Patterns & Materialized Views
- **Materialized Views**: Aggregates for dashboards (e.g., daily total Scope 1/2/3 emissions per organization) are updated asynchronously using TimescaleDB continuous aggregates.
- **Continuous Aggregates**:
  ```sql
  -- Continuous aggregate for daily carbon totals
  CREATE MATERIALIZED VIEW mv_daily_carbon_summary
  WITH (timescaledb.continuous) AS
  SELECT tenant_id,
         time_bucket('1 day', calculation_timestamp) AS day,
         scope,
         sum(co2e_kg) AS total_co2e
  FROM emissions
  GROUP BY tenant_id, day, scope;
  
  -- Establish refresh policy for continuous aggregations
  SELECT add_continuous_aggregate_policy('mv_daily_carbon_summary',
      start_offset => INTERVAL '3 days',
      end_offset => INTERVAL '1 hour',
      schedule_interval => INTERVAL '30 minutes');
  ```

### 2. Read Replicas
- The system divides database traffic by transaction type.
- **Write Path**: Core events ingestion, user creations, and workflow status modifications run on the **Primary Database Instance**.
- **Read Path**: High-overhead analytical operations, process model discovery, and BRSR report compile jobs are directed to **Read Replicas** via connection routing.

### 3. Connection Pooling
- PostgreSQL uses a process-per-connection model that degrades in performance beyond a few hundred active connections.
- SustainOCPM places **PgBouncer** in front of PostgreSQL, configured in `Transaction Mode` with a pool size optimized to match the primary instance's CPU core count.

---

## 8. Backup and Recovery

To secure customer event data, SustainOCPM implements an automated backup and disaster recovery strategy.

```
  ┌────────────────────────────────────────────────────────┐
  │                 Primary Region (AWS ap-south-1)        │
  │    ┌────────────────┐            ┌─────────────────┐   │
  │    │  TimescaleDB   ├───────────►│ Continuous WAL  │   │
  │    │  Active DB     │            │ Archiving (S3)  │   │
  │    └───────┬────────┘            └────────┬────────┘   │
  └────────────┼──────────────────────────────┼────────────┘
               │                              │
               │ Cross-Region                 │ Cross-Region
               │ Replication                  │ Replication
               ▼                              ▼
  ┌────────────┴──────────────────────────────┴────────────┐
  │                 Secondary Region (AWS eu-central-1)    │
  │    ┌────────────────┐            ┌─────────────────┐   │
  │    │  Standby DB    │            │ Replicated WAL  │   │
  │    │  Instance      │            │ Backups (S3)    │   │
  │    └────────────────┘            └─────────────────┘   │
  └────────────────────────────────────────────────────────┘
```

### 1. Backup Schedule and Retention
- **Continuous Backups**: Streamed transaction logs (WAL) are written directly to S3 using tools like `pgBackRest`.
- **Full Backups**: Executed daily during low-traffic periods.
- **Retention**: Daily backups are kept for 30 days. Weekly backups are retained for 12 weeks, and monthly backups are archived to S3 Glacier for 7 years to meet compliance standards.

### 2. Recovery Objectives
- **Recovery Point Objective (RPO)**: **< 5 minutes**. Continuous WAL archiving ensures minimal data loss in the event of an outage.
- **Recovery Time Objective (RTO)**: **< 15 minutes**. Automated failover processes switch traffic to hot standby read replicas if the primary instance fails.

### 3. Point-in-Time Recovery (PITR)
- S3-hosted WAL records allow the platform to restore the database to any millisecond within the 30-day retention window. This is critical for recovering from accidental data deletions or security issues.

### 4. Cross-Region Replication
- S3 backups and WAL segments are replicated asynchronously to a secondary geographical region (e.g., from AWS `ap-south-1` to `eu-central-1`) to protect against regional cloud outages.

---

## 9. Data Privacy and Compliance

Because SustainOCPM processes enterprise supply chain records, user profiles, and audit trails, it must adhere to strict regulatory compliance standards (such as GDPR, DPDP Act India, and SOC 2).

> [!CAUTION]
> Failure to implement proper data isolation, masking, or deletion protocols can result in regulatory non-compliance, financial penalties, and breaches of customer trust.

### 1. PII Handling and Data Masking
- **PII Storage**: User passwords must be hashed using Argon2id. Client IP addresses in audit logs are stored using the `INET` type, and can be masked on read.
- **Dynamic Masking**: When importing event logs that contain personal data (e.g., employee names, customer credit identifiers), the system's ingestion engine applies SHA-256 hashing to mask this data before writing it to the database.

### 2. Right to Deletion (GDPR / DPDP Compliance)
- When a user requests data deletion, the platform executes a cascading soft-delete (setting the `deleted_at` timestamp).
- **Hard Deletion (Purge)**: An asynchronous background job permanently purges soft-deleted records from the database after 30 days.
  ```sql
  -- Safe background hard-delete execution pattern
  DELETE FROM users 
  WHERE deleted_at < NOW() - INTERVAL '30 days';
  ```

### 3. Data Residency and Compliance
- For tenants with strict data residency requirements (e.g. EU companies requiring data to remain in the EU, or Indian public firms requiring domestic hosting), database instances are deployed to regional cloud environments. The routing system directs tenant traffic to their designated regional database.

---

## 10. Database Topology & High Availability

To ensure continuous operation and minimize query latency, SustainOCPM implements a distributed cluster layout utilizing Patroni and Consul for coordinate consensus.

```
                   ┌────────────────────────────────────────┐
                   │            App Load Balancer           │
                   └───────────────────┬────────────────────┘
                                       │
                                       ▼
                   ┌────────────────────────────────────────┐
                   │            PgBouncer Poolers           │
                   └──────┬──────────────────────────┬──────┘
                          │                          │
                 (Writes) │                          │ (Reads)
                          ▼                          ▼
               ┌────────────────────┐      ┌────────────────────┐
               │    Patroni Leader  ├─────►│ Patroni Replica 1  │
               │    (Active Master) │      │ (Warm Standby / RO)│
               └──────────┬─────────┘      └─────────┬──────────┘
                          │                          │
                          │ (Async Replication)      │
                          ▼                          ▼
               ┌────────────────────┐      ┌────────────────────┐
               │ Patroni Replica 2  │      │   patroni DR Node  │
               │ (Warm Standby / RO)│      │  (Cross-Region RO) │
               └────────────────────┘      └────────────────────┘
```

### HA Cluster Properties
- **Patroni Coordinator**: Patroni monitors the PostgreSQL process state. It relies on a distributed consensus store (Consul or etcd) to handle failover decisions. If the primary instance goes down, Patroni automatically promotes the standby replica with the lowest replication lag.
- **Replication Mode**:
  - **Local Standby Replicas**: Configured with synchronous replication to ensure zero data loss in a local hardware failure.
  - **Disaster Recovery (DR) Replicas**: Located in secondary geographic regions, configured with asynchronous replication to prevent WAN latency from slowing down local transaction write paths.
- **PgBouncer Routing**: PgBouncer pools are separated into `pool_master` (writes, pointing to the Patroni leader) and `pool_replica` (reads, balanced across active standby instances).

---

## 11. Property Graph Mirroring (Neo4j Schema)

Object-Centric Process Mining requires tracking pathways across dynamic collections of interrelated objects (e.g. tracing an `order` object linked to multiple `item` objects, a `delivery` object, and an `invoice` object). In SustainOCPM, the database tier mirrors relational OCEL 2.0 tables into **Neo4j** to run fast path traversals.

```
       ┌─────────────────────────────────────────────────────────────────┐
       │                       Neo4j Property Graph                      │
       ├────────────────────────────────┬────────────────────────────────┤
       │          Nodes (Labels)        │      Relationships (Types)     │
       ├────────────────────────────────┼────────────────────────────────┤
       │ - :Event                       │ - (:Event)-[:RELATES_TO]->(:Obj)│
       │ - :Object                      │ - (:Obj)-[:PART_OF]->(:Obj)    │
       │ - :Activity                    │ - (:Event)-[:PRECEDES]->(:Event)│
       └────────────────────────────────┴────────────────────────────────┘
```

### Neo4j Node Definitions
1. **Event Node (`:Event`)**:
   - `id` (matches relational `event_id`)
   - `timestamp` (epoch value)
   - `activity` (matches relational `activity`)
2. **Object Node (`:Object`)**:
   - `id` (matches relational `object_id`)
   - `type` (matches relational `object_type`)
3. **Activity Node (`:Activity`)**:
   - `name` (unique identifier label)

### Neo4j Relationship Definitions
1. **Relates To (`[:RELATES_TO]`)**:
   - Direction: `(:Event)-[:RELATES_TO {role: "item_courier"}]->(:Object)`
   - Matches the relational `event_object_relationships` table.
2. **Object Relationship (`[:PART_OF]`, `[:PAYS]`)**:
   - Direction: `(:Object {type: "item"})-[:PART_OF]->(:Object {type: "order"})`
   - Matches the relational `object_object_relationships` table.
3. **Precedes (`[:PRECEDES]`)**:
   - Direction: `(:Event)-[:PRECEDES]->(:Event)`
   - Discovered dynamically by sequencing events that share common object linkages.

#### Cypher Path Traversal Example
To trace a specific delivery path and its carbon emissions:
```cypher
MATCH path = (o:Object {id: "order_9982"})<-[:PART_OF]-(i:Object)-[:RELATES_TO]-(e:Event)
RETURN path
```
This graph structure allows the system to execute multi-hop path traversals and identify bottleneck processes in milliseconds.

---

## 12. Complete Database Initialization Script (DDL)

To assist engineers in spinning up environments, this section defines the conceptual DDL blueprint for the core OCEL 2.0 schema, complete with tables, indexes, and continuous aggregates.

```sql
-- DDL Blueprint Setup
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- 1. Organizations
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(50) NOT NULL DEFAULT 'Enterprise',
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    billing_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID
);

-- 2. Projects
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    ocel_version VARCHAR(50) NOT NULL DEFAULT '2.0',
    status VARCHAR(50) NOT NULL DEFAULT 'Active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID,
    updated_by UUID
);

-- 3. Events (OCEL 2.0 Partitioned Base)
CREATE TABLE events (
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    event_id VARCHAR(255) NOT NULL,
    activity VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    PRIMARY KEY (tenant_id, event_id, timestamp)
);

-- 4. Objects (OCEL 2.0 Base)
CREATE TABLE objects (
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    object_id VARCHAR(255) NOT NULL,
    object_type VARCHAR(255) NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    PRIMARY KEY (tenant_id, object_id)
);

-- 5. Event-Object Relationships (OCEL 2.0 Partitioned Base)
CREATE TABLE event_object_relationships (
    tenant_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    event_id VARCHAR(255) NOT NULL,
    object_id VARCHAR(255) NOT NULL,
    relationship_role VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (tenant_id, event_id, object_id, relationship_role, timestamp)
);

-- Convert to TimescaleDB Hypertables
SELECT create_hypertable('events', 'timestamp', partitioning_column => 'tenant_id', number_partitions => 64);
SELECT create_hypertable('event_object_relationships', 'timestamp', partitioning_column => 'tenant_id', number_partitions => 64);

-- Indexes for Events
CREATE INDEX idx_events_proj_ts ON events(project_id, timestamp DESC);
CREATE INDEX idx_events_attrib_gin ON events USING gin(attributes);

-- Indexes for Objects
CREATE INDEX idx_objects_proj_type ON objects(project_id, object_type);
CREATE INDEX idx_objects_attrib_gin ON objects USING gin(attributes);

-- Indexes for Event-Object Relationships
CREATE INDEX idx_e2o_obj ON event_object_relationships(project_id, object_id);
CREATE INDEX idx_e2o_evt ON event_object_relationships(project_id, event_id);
```

---

## 13. Summary Checklist for Architectural Compliance

Before deploying changes to the SustainOCPM database tier, engineers must verify compliance with the following design rules:

- [ ] **Multi-Tenancy**: Every new table must include `tenant_id UUID NOT NULL` unless explicitly documented as a global reference table (e.g. `emission_factors`, `benchmarks`).
- [ ] **Row-Level Security**: Ensure `ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;` is executed, and the tenant isolation policy is active.
- [ ] **Time-Series Ingestion**: Verify high-volume tables (events, emissions, audit logs) are declared as TimescaleDB hypertables with appropriate time intervals (7 or 30 days) and dynamic compression profiles.
- [ ] **No Raw Code in DB**: Do not embed business logic within database store procedures or triggers, except for basic audit logging and immutability checks.
- [ ] **Graph Mirror Sync**: Ensure transactional writes to the relational `events` and `objects` tables trigger async messages to update the Neo4j property graph.
- [ ] **PII Protection**: Double check that employee names, customer emails, and sensitive financial fields are masked during log ingestion using SHA-256 hashes.
- [ ] **Migrations**: All DDL migration files must include a transaction block setting the lock timeout to less than 2 seconds to prevent blocking users during deployments.
