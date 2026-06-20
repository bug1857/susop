# Sprint 5 Foundation Report — ESG Intelligence

This report details the implementation and verification of the database foundation and skeleton structures for the ESG Intelligence module at the beginning of Sprint 5.

---

## 1. Files Created & Modified

### 1.1 Files Created
*   **Database Migration**:
    *   `backend/alembic/versions/ff870c70b120_sprint5_esg_foundation.py`
*   **Repository Skeletons**:
    *   `backend/app/repositories/esg_kpi_repository.py`
    *   `backend/app/repositories/esg_framework_repository.py`
    *   `backend/app/repositories/esg_score_repository.py`
    *   `backend/app/repositories/esg_profile_repository.py`
    *   `backend/app/repositories/esg_evidence_repository.py`
*   **Service Skeletons**:
    *   `backend/app/services/esg_kpi_service.py`
    *   `backend/app/services/esg_scoring_service.py`
    *   `backend/app/services/esg_evidence_service.py`
*   **API Router Placeholder**:
    *   `backend/app/routers/esg.py`

### 1.2 Files Modified
*   `backend/app/models/models.py` (Appended SQLAlchemy ORM models)
*   `backend/app/schemas/schemas.py` (Appended Pydantic schemas and envelopes)
*   `backend/app/main.py` (Registered ESG APIRouter)

---

## 2. Database & Schema Additions

### 2.1 Entities Added
1.  **`EsgKpiDefinition`** (`esg_kpi_definitions`): Versioned definitions of environmental, social, and governance KPIs.
2.  **`EsgKpiValue`** (`esg_kpi_values`): Periodic metric values mapping to active KPI definitions.
3.  **`EsgFramework`** (`esg_frameworks`): Framework parameters (BRSR, GRI, SASB, TCFD, etc.).
4.  **`FrameworkMapping`** (`framework_mappings`): Many-to-many lookups linking versioned KPIs to regulatory sections and question criteria.
5.  **`EsgScoringProfile`** (`esg_scoring_profiles`): Category weighting coefficients (E, S, G weights) and relative KPI weights.
6.  **`EsgScore`** (`esg_scores`): Rolled-up periodic scores, overall score, and completeness metrics.
7.  **`EsgEvidence`** (`esg_evidence`): Cryptographic data integrity verification records, intermediate calculation steps, and polymorphic operational sources linkage.

### 2.2 Explicit Indices Added
*   `idx_esg_kpi_code_version` on `esg_kpi_definitions (kpi_code, version)`
*   `idx_framework_kpi_mapping` on `framework_mappings (framework_id, kpi_definition_id)`

### 2.3 Alembic Migrations
*   **Migration applied**: Revision `ff870c70b120` (`sprint5_esg_foundation`).
*   *SQLite Alterations Cleanup*: Cleaned auto-generated schema script to bypass columns type alteration statements (`NUMERIC` to `UUID`) on existing tables, preventing SQLite migration execution noise.

---

## 3. Architecture & Code Skeletons

### 3.1 Repositories
*   `EsgKpiRepository`: Definition CRUD and periodic value queries.
*   `EsgFrameworkRepository`: Framework and framework-to-KPI mappings queries.
*   `EsgScoreRepository`: Persisting rolled-up scoring calculations.
*   `EsgProfileRepository`: Managing active profiles and category weight settings.
*   `EsgEvidenceRepository`: Verifying and retrieving calculation tracing details.

### 3.2 Services
*   `EsgKpiService`: KPI value calculations and manual data logs validation rules placeholder.
*   `EsgScoringService`: Scoring rollups and target normalization calculations placeholder.
*   `EsgEvidenceService`: Traceability graphs and file hashing checks placeholder.

### 3.3 Router
*   `GET /api/esg/kpi-definitions`
*   `POST /api/esg/kpi-definitions`
*   `GET /api/esg/kpi-values`
*   `POST /api/esg/kpi-values`
*   `GET /api/esg/scoring-profiles`
*   `POST /api/esg/scoring-profiles`
*   `GET /api/esg/scores`
*   `POST /api/esg/scores/calculate`
*   `GET /api/esg/evidence/{kpi_value_id}`
*   `POST /api/esg/evidence/{kpi_value_id}/attach`
*   `GET /api/esg/framework-mappings`

---

## 4. Verification & Validation Results

*   **Compilation Check**: SQLAlchemy models, Pydantic schemas, and API routers compiled successfully without syntax or dependency resolution errors.
*   **Database Upgrades**: Database successfully migrated to revision `ff870c70b120` under local development environment.
*   **FastAPI Integration**: App successfully started and existing test suites (8 integration/API cases) passed cleanly without regressions.

---

## 5. Blockers before Prompt 2

*   No blockers identified. Next step is implementing seed data for `esg_frameworks` and standard `framework_mappings` to support BRSR mapping rules, followed by the ESG scoring algebra.
