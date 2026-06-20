# Sprint 4 Updated Plan — Conformance Checking & Carbon Attribution

This updated plan incorporates database normalization for deviations, an emission factor registry, and deep carbon-aware conformance checking.

---

## 1. Updated Database Changes

We will introduce five tables:

*   `reference_models`
    *   `id`: UUID (PK)
    *   `project_id`: UUID (FK to `projects.id`)
    *   `model_name`: String
    *   `bpmn_xml`: Text (normative BPMN schema)
    *   `created_at`: DateTime
*   `conformance_results`
    *   `id`: UUID (PK)
    *   `analysis_id`: UUID (FK to `process_analyses.id`)
    *   `fitness_score`: Float (structural alignment)
    *   `precision_score`: Float
    *   `created_at`: DateTime
*   `conformance_deviations`
    *   `id`: UUID (PK)
    *   `result_id`: UUID (FK to `conformance_results.id`)
    *   `analysis_id`: UUID (FK to `process_analyses.id`)
    *   `case_id`: String (trace context)
    *   `activity_name`: String
    *   `deviation_type`: String (e.g. "missing", "unexpected", "swap")
    *   `expected_transition`: String
    *   `actual_transition`: String
    *   `severity`: String (e.g. "low", "medium", "critical")
    *   `created_at`: DateTime
*   `emission_factors`
    *   `id`: UUID (PK)
    *   `activity_name`: String
    *   `factor_value`: Float
    *   `unit`: String (e.g. "kg_co2e")
    *   `source_name`: String (ecoinvent, EXIOBASE, BEE, etc.)
    *   `source_version`: String
    *   `effective_date`: DateTime
*   `carbon_attributions`
    *   `id`: UUID (PK)
    *   `analysis_id`: UUID (FK to `process_analyses.id`)
    *   `carbon_fitness_score`: Float
    *   `carbon_budget`: Float
    *   `actual_emissions`: Float
    *   `excess_emissions`: Float
    *   `budget_exceeded`: Boolean
    *   `emission_hotspots`: JSON (slowest/highest emission node list)
    *   `alternative_path_candidates`: JSON (recommended paths matching carbon thresholds)

---

## 2. Updated API Changes

*   `POST /api/conformance/reference-models`: Upload reference model.
*   `POST /api/process/{id}/conformance`: Run conformance checking (calculates structural & carbon metrics).
*   `GET /api/process/{id}/conformance`: Retrieve conformance summary metrics.
*   `GET /api/process/{id}/conformance/deviations`: Retrieve list of normalized deviations with filtering by case_id/severity.
*   `GET /api/process/{id}/carbon-attribution`: Retrieve carbon-aware fitness details, budgets, and hotspot analysis.
*   `POST /api/emission-factors`: Register or update emission database factors.

---

## 3. Updated Algorithm Changes

*   **Normalized Deviation Logger**: Parse alignments per case from PM4Py replay outputs, isolating exact differences (e.g. activity swaps or skipped nodes) and insert them as row records in `conformance_deviations`.
*   **Carbon-Aware Fitness Check**:
    *   Calculate structural replay fitness score.
    *   Attribute co2e to case paths using mapped emission factor registries.
    *   Evaluate case path emissions against the target `carbon_budget` (configured per project/reference).
    *   `carbon_fitness_score` = trace-fitness scaled by carbon emission excess factor.
    *   Calculate alternative path candidates using Dijkstra routing on DFG edges filtered by lowest accumulated emission weights.

---

## 4. Updated UI Changes

*   **Deviation Audit Log**: Paginated, filterable grid displaying individual case deviations, expected vs actual transitions, and severity indicators.
*   **Carbon-Aware Dashboard**: Display carbon fitness dials, excess emissions alerts, and budget status overlays.
*   **Alternative Pathway Advisor**: Panel displaying recommended alternative paths with comparative carbon reductions.
*   **Emission Factor Manager**: Tab in Settings to switch active carbon databases (ecoinvent, BEE) or view custom factors.
