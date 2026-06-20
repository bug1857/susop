# Sprint 5 Architecture Upgrade Report

This report documents the architectural and database design upgrades for the ESG Intelligence module, specifically expanding on KPI registry versioning, framework abstraction layers, and evidence lineage graphs.

---

## 1. Schema & Entity Changes

### 1.1 KPI Registry Versioning
We extend the structure of `esg_kpi_definitions` to support temporal validity, status flags, version numbers, and parent hierarchy relationships. This preserves score reproducibility across compliance periods.

**Modified Entity (`esg_kpi_definitions`)**:
*   `version`: `Integer` (Default: 1, nullable=False)
*   `effective_from`: `DateTime` (nullable=False)
*   `effective_to`: `DateTime` (nullable=True)
*   `is_active`: `Boolean` (Default: True, nullable=False)
*   `parent_kpi_id`: `UUID` (Foreign Key -> `esg_kpi_definitions.id` for self-reference, ondelete="SET NULL", nullable=True)

*Note: Periodic ESG scores and values must refer to the immutable record ID of the specific KPI version (`kpi_definition_id`), preventing changes in KPI formulas from retroactively changing historic ESG ratings.*

### 1.2 Framework Abstraction Layer
To support global frameworks (BRSR, GRI, SASB, CDP, TCFD, CSRD) without redesigning tables, the single-framework `brsr_mappings` table is replaced with a clean many-to-many lookup structure.

**New Entity (`esg_frameworks`)**:
*   `id`: `UUID` (Primary Key, Default: uuid4)
*   `framework_name`: `String` (e.g., "BRSR", "GRI", "SASB", unique, nullable=False)
*   `framework_version`: `String` (e.g., "2024-V2", nullable=False)
*   `description`: `String` (nullable=True)
*   `created_at`: `DateTime` (Default: utcnow, nullable=False)

**New Entity (`framework_mappings`)**:
*   `id`: `UUID` (Primary Key, Default: uuid4)
*   `framework_id`: `UUID` (Foreign Key -> `esg_frameworks.id`, ondelete="CASCADE", nullable=False)
*   `kpi_definition_id`: `UUID` (Foreign Key -> `esg_kpi_definitions.id`, ondelete="CASCADE", nullable=False)
*   `framework_section`: `String` (e.g., "Section C", nullable=False)
*   `framework_principle`: `String` (e.g., "Principle 6", nullable=True)
*   `framework_question`: `String` (e.g., "Essential-Q5", nullable=False)
*   `reporting_category`: `String` (e.g., "Essential Indicators", nullable=False)
*   `created_at`: `DateTime` (Default: utcnow, nullable=False)

### 1.3 Evidence Lineage Graph
We extend the `esg_evidence` table to support granular provenance, graph explainability, and Copilot reasoning.

**Modified Entity (`esg_evidence`)**:
*   `source_entity_type`: `String` (Constraints: "dataset", "process_analysis", "process_model", "conformance_result", "carbon_attribution", "manual_upload", "external_api", nullable=False)
*   `source_entity_id`: `UUID` (Target entity reference, nullable=True)
*   `lineage_path`: `JSON` (JSON lineage structure tracking data progression)

---

## 2. Relationship Changes

```
+------------------+         +----------------------+         +-----------------------+
|  esg_frameworks  |1-------*|  framework_mappings  |*-------1|  esg_kpi_definitions  |
+------------------+         +----------------------+         +-----------------------+
                                                                          |1
                                                                          |
                                                                          *
                                                              +-----------------------+
                                                              |    esg_kpi_values     |
                                                              +-----------------------+
                                                                          |1
                                                                          |
                                                                          1
                                                              +-----------------------+
                                                              |     esg_evidence      |
                                                              +-----------------------+
```

1.  **Many-to-Many Framework Mapping**: `framework_mappings` acts as an associative entity between `esg_frameworks` and `esg_kpi_definitions`.
2.  **KPI Self-Reference**: `esg_kpi_definitions.parent_kpi_id` allows chaining KPI modifications over time (e.g., v1 -> v2).
3.  **Traceable Provenance Link**: `esg_evidence.source_entity_id` establishes a polymorphic link to the operational record driving the metric value.

---

## 3. Migration Impact

*   **Alembic Migration Plan**:
    *   Initialize `esg_frameworks` and `framework_mappings` instead of the deprecated `brsr_mappings`.
    *   Configure foreign key constraints on `parent_kpi_id` with `ondelete="SET NULL"` rules to avoid deletion failures.
    *   Add indices on composite columns `(framework_id, kpi_definition_id)` inside `framework_mappings` to speed up framework report generations.

---

## 4. Future Framework Readiness

The many-to-many relationship decoupling allows adding new frameworks (e.g., European CSRD or TCFD guidelines) dynamically by inserting standard configurations to `esg_frameworks` and referencing the existing catalog of KPIs in `framework_mappings`. No backend SQL schema migrations or code refactoring will be required to ingest and map new regulatory standards.
