# Sprint 4 Foundation Report: Conformance & Carbon Attribution

This report summarizes the foundation setup completed for Sprint 4, including the database models, schemas, repositories, service skeletons, router stubs, and Alembic migrations.

## 1. Database Entities Added
Six new database tables have been added with proper tenant, workspace, and project isolation fields, along with optimized database indices:

1. **`reference_models`**: Stores normative process definitions for conformance checking, with supporting fields for lineage (`parent_model_id`) and versioning.
2. **`conformance_results`**: Persists aggregate summary metrics (fitness, precision, carbon fitness, budgets, and emissions) for a process analysis version.
3. **`conformance_deviations`**: Stores detailed event/transition level difference records (e.g. missing transitions, incorrect sequences) mapped to specific cases for explainability.
4. **`emission_factors`**: Registry of mapped carbon emission factors (factor value, unit, data source, and effective date) for different process activities.
5. **`carbon_attributions`**: Mapped carbon emission volumes calculated by activity name using active factors from the registry.
6. **`emission_hotspots`**: Ranked contribution list of process activities based on emissions, enabling targeted severity assessments.

---

## 2. Code Files Created and Modified

### Database Models
*   Modified [models.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py): Appended SQLAlchemy models for `ReferenceModel`, `ConformanceResult`, `ConformanceDeviation`, `EmissionFactor`, `CarbonAttribution`, and `EmissionHotspot`.

### Pydantic Validation Schemas
*   Modified [schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py): Added schema definitions (`ReferenceModelCreate`, `ReferenceModelResponse`, `ConformanceResultResponse`, `ConformanceDeviationResponse`, `EmissionFactorCreate`, `EmissionFactorResponse`, `CarbonAttributionResponse`, `EmissionHotspotResponse`) with configuration options.

### Repositories (Skeleton files in `backend/app/repositories/`)
*   [reference_model_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/reference_model_repository.py)
*   [conformance_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/conformance_repository.py)
*   [deviation_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/deviation_repository.py)
*   [emission_factor_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/emission_factor_repository.py)
*   [carbon_attribution_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/carbon_attribution_repository.py)
*   [hotspot_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/hotspot_repository.py)

### Services (Skeleton files in `backend/app/services/`)
*   [reference_model_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/reference_model_service.py)
*   [conformance_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/conformance_service.py)
*   [carbon_attribution_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_attribution_service.py)
*   [carbon_fitness_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_fitness_service.py)

### API Routers
*   [conformance.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/conformance.py): Created with `POST /reference-models` stub to handle normative model registration.
*   [process.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/process.py): Modified to add:
    *   `POST /{id}/conformance` stub (to run conformance checking).
    *   `GET /{id}/conformance` stub (to fetch conformance analysis summary metrics).
    *   `GET /{id}/carbon-attribution` stub (to retrieve calculated carbon values).
*   [main.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/main.py): Registered the new `/api/conformance` router prefix.

### Audit Log Configuration
*   [audit.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/core/audit.py): Documented and registered the Audit trail action strings for reference model uploads, conformance starts, completion, deviations, and carbon calculation events.

---

## 3. Database Migration Details
*   Alembic migration version `2a4c95ff1c79` (`sprint4_conformance_init`) was generated and structured to create all tables and indexes.
*   Because `Base.metadata.create_all(bind=engine)` is called on application startup in local development/testing to automatically prepare database tables, the local SQLite database files (`sustainocpm.db` and `test.db`) already contain the new tables.
*   The migration state was successfully stamped as head (`2a4c95ff1c79`) to align the database versioning metadata with the schema state.

---

## 4. Verification Results & Blockers
*   **Verification Command**: `PYTHONPATH=. venv/bin/pytest`
*   **Results**: All tests (5 passed) execute and run successfully. Import verification passes without compilation errors.
*   **Blockers**: No blockers exist. The API stubs, database layers, and service structures are ready for the core algorithms in Prompt 2.
