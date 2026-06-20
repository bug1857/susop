# Sprint 4 — Prompt 4 Report: Production-Ready API Exposure

This report details the implementation of production-ready API wiring, multi-tenant validation, filtering, pagination, auditing, and standardized response enveloping for all Sprint 4 features.

## 1. Files Modified
- **`backend/app/schemas/schemas.py`**: Added standardized JSON envelope wrapper schemas, StandardMetadata, ErrorDetail, CarbonAttributionData, CarbonFitnessData, ReferenceModelUpdate, and various envelope classes.
- **`backend/app/routers/conformance.py`**: Completely rewrote the reference model router. Wired all CRUD endpoints for managing normative reference models with parent-link versioning and tenant isolation.
- **`backend/app/routers/process.py`**: Updated existing stubs and added new endpoints for triggering conformance, viewing deviations, carbon attributions, hotspots, and carbon fitness.
- **`backend/app/tests/test_process_mining.py`**: Integrated the new `test_sprint4_apis` test suite to verify Reference Model CRUD, conformance replay, paginated deviations/hotspots, carbon fitness evaluations, and cleanup.

---

## 2. Endpoints Added
All Sprint 4 endpoints wrap responses in standardized envelopes: `{"success": true/false, "data": ..., "metadata": ..., "errors": ...}`:

### Reference Model Endpoints
1. **`POST /api/conformance/reference-models`**: Creates a new reference model. Version-aware (auto-increments if `parent_model_id` is supplied). Triggers audit log `reference_model_uploaded`.
2. **`GET /api/conformance/reference-models`**: Lists reference models scoped by workspace/project with pagination, sorting, and date filters.
3. **`GET /api/conformance/reference-models/{id}`**: Retrieves a single reference model with access checks.
4. **`PUT /api/conformance/reference-models/{id}`**: Updates model definition, name, or status. Triggers audit log `reference_model_updated`.
5. **`DELETE /api/conformance/reference-models/{id}`**: Deletes a model. Triggers audit log `reference_model_deleted`.

### Conformance & Carbon Endpoints
6. **`POST /api/process/{id}/conformance`**: Runs Token-based Replay and calculates fitness/precision. Triggers audit log `conformance_started` and `conformance_completed`.
7. **`GET /api/process/{id}/conformance`**: Fetches the conformance results.
8. **`GET /api/process/{id}/deviations`**: Lists case-level sequence/token deviations with pagination, sorting, and filtering.
9. **`GET /api/process/{id}/deviations/{deviation_id}`**: Fetches a single deviation details.
10. **`GET /api/process/{id}/carbon-attribution`**: Computes/calculates activity and variant emissions and budget penalty metrics. Triggers audit log `carbon_attribution_completed`.
11. **`GET /api/process/{id}/hotspots`**: Lists ranked activity emissions and contribution percentages.
12. **`GET /api/process/{id}/carbon-fitness`**: Retrieves budget compliance factors and carbon-aware fitness details.

---

## 3. Filters & Pagination Support

### Pagination & Sorting
Pagination parameters (`limit`, `offset`, `sort_by`, `sort_order`) are implemented directly in the database query layer to avoid N+1 queries and memory bloat:
- **`reference_models`**: Sorts by `model_name`, `version`, or `created_at`.
- **`deviations`**: Sorts by `activity_name`, `deviation_type`, `severity`, or `created_at`.
- **`hotspots`**: Sorts by `activity_name`, `contribution_percentage`, `severity`, or `emissions`.

### Filtering
Support for filtering is added across query parameters:
- **`severity`**: Filters deviations or hotspots (e.g., Critical, High, Medium, Low).
- **`activity_name`**: Filters deviations or hotspots by name.
- **`reference_model`**: Filters deviations belonging to a specific reference model (by joining `conformance_results`).
- **`analysis_version`**: Filters deviations by analysis run version (by joining `conformance_results`).
- **`date_range`**: Supported via `start_date` and `end_date` date-time filters on models, deviations, and hotspots.

---

## 4. Validation & Error Handling
- **Isolation Checks**: All endpoints validate `tenant_access`, `workspace_access`, and `project_access` using `RoleChecker`. Users must belong to the same tenant organization, and roles are checked for read/write access.
- **Context Integrity**: Ensures reference models and parent models belong to the active project context (raises `400 Bad Request` on mismatches).
- **Error Wrapping**: No raw SQL exceptions or stack traces are leaked. All database/HTTP exceptions are intercepted and returned as a standard JSON envelope with `success: false` and structured `errors` lists.

---

## 5. Validation Results
- **Pytest Output**: The entire backend test suite executes successfully:
  - **Results**: `7 passed, 215 warnings in 5.06s`
  - **Verification Command**: `PYTHONPATH=. venv/bin/pytest`
- Tested and verified:
  - Tenant isolation and access validation.
  - CRUD operations and parent-based version lineage.
  - Pagination offset/limits and column sorting.
  - Standardized JSON responses for all outcomes.

---

## 6. Known Issues & Blockers
- **Known Issue**: Since `EmissionFactor` does not have a `workspace_id` column, workspace factors resolve directly to tenant-level factors.
- **Blockers before Prompt 5**: None. All API endpoints and core engines are fully implemented, validated, and ready for integration.
