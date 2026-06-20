# Sprint 5 Prompt 3 - ESG API Layer Implementation Report

This report documents the implementation of the versioned ESG API layer under `/api/v1/esg/` for Sprint 5. The API layer enforces authentication, role-based access control (RBAC), multi-tenant isolation, anti-enumeration, paginated/sorted listings, audit logging, and envelope-wrapped responses.

---

## 1. Endpoints Added

All ESG endpoints have been successfully registered under the `/api/v1/esg` prefix:

### 1.1 KPI Definitions APIs
- **POST** `/api/v1/esg/kpis`
  - Creates a new KPI definition.
  - Required Roles: `Admin`, `Manager`, `Analyst`
- **GET** `/api/v1/esg/kpis`
  - Lists KPI definitions. Supports category/active filters, pagination (`limit`, `offset`), and sorting (`sort_by`, `sort_order`).
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/kpis/{id}`
  - Retrieves a specific KPI definition. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/kpis/{id}/versions`
  - Retrieves the version evolution list for a KPI code. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **PUT** `/api/v1/esg/kpis/{id}`
  - Updates mutable KPI fields. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`

### 1.2 KPI Value APIs
- **POST** `/api/v1/esg/kpi-values`
  - Records a KPI value for a period, workspace, and optional project.
  - Required Roles: `Admin`, `Manager`, `Analyst`
- **GET** `/api/v1/esg/kpi-values`
  - Lists KPI values with period, workspace, and project filtering, pagination, and sorting.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`

### 1.3 ESG Score APIs
- **POST** `/api/v1/esg/calculate`
  - Triggers the ESG scoring engine for a specific workspace and period.
  - Required Roles: `Admin`, `Manager`, `Analyst`
- **GET** `/api/v1/esg/scores`
  - Retrieves ESG score history for a workspace. Supports period filtering.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/scores/{id}`
  - Retrieves details of a specific computed ESG score. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`

### 1.4 Framework APIs
- **GET** `/api/v1/esg/frameworks`
  - Lists global compliance frameworks (GRI, SASB, BRSR, etc.).
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/frameworks/{id}`
  - Retrieves a specific framework.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/frameworks/{id}/mappings`
  - Retrieves dynamic mappings for a framework, filtered to only include KPIs belonging to the user's active tenant.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`

### 1.5 Evidence APIs
- **GET** `/api/v1/esg/evidence`
  - Lists evidence metadata, optionally filtered by `kpi_value_id`.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/evidence/{id}`
  - Retrieves evidence details by evidence ID. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/evidence/{id}/lineage`
  - Retrieves the lineage path JSON by evidence ID. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`
- **GET** `/api/v1/esg/evidence/kpi-value/{kpi_value_id}/lineage`
  - Retrieves the lineage path JSON directly by `kpi_value_id`. Enforces anti-enumeration.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`

### 1.6 Scoring Profile Configuration APIs (Extra)
- **POST** `/api/v1/esg/scoring-profiles`
  - Sets categories and KPI weights.
  - Required Roles: `Admin`, `Manager`
- **GET** `/api/v1/esg/scoring-profiles`
  - Lists scoring profiles configured for the tenant.
  - Required Roles: `Admin`, `Manager`, `Analyst`, `Viewer`

---

## 2. Files Modified

1. **[main.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/main.py)**:
   - Modified `esg` router prefix registration to `/api/v1`.
2. **[schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py)**:
   - Added `EsgEvidenceListResponseEnvelope` to support standard response packaging for evidence listings.
   - Added `version` field to `EsgKpiDefinitionCreate` to allow users to specify custom version evolution codes.
3. **[esg.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/esg.py)**:
   - Replaced all skeletons with full route controllers, database sessions, and logic.

---

## 3. Tests Added

1. **[test_esg_api.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_esg_api.py)**:
   - Sets up multi-tenant organizations (Tenant A and Tenant B), authenticated headers, and mock workspaces.
   - Verifies the full KPI creation, retrieval, listing (with filtering/sorting), details fetching, updating, and versioning sequences.
   - Verifies recording KPI values.
   - Verifies configuring weights profiles and triggering score calculations.
   - Verifies listing global frameworks and retrieving dynamic section mappings.
   - Verifies registering evidence and tracing calculation lineages.
   - Verifies anti-enumeration protection (cross-tenant requests return 404 instead of 403).
   - Verifies audit log generation for all key operations.

---

## 4. Validation Results

The integration test suite was run locally inside the virtual environment:

```bash
PYTHONPATH=. venv/bin/pytest -v app/tests/test_esg_api.py -W ignore
```
- **Total Tests**: 1 (composed of 7 distinct logical verify checkpoints)
- **Status**: **PASSED**

A full regression run across all backend tests has also completed:
- **Total Tests**: 10
- **Status**: **PASSED**

---

## 5. Blockers before Prompt 4

- **Blockers**: None. The API layer is complete, fully integrated with DB/Services, and verified by tests.
