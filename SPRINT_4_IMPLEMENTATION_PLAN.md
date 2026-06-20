# Sprint 4 Implementation Plan — Conformance Checking & Carbon Attribution

This plan outlines the system design, modifications, and algorithms for Sprint 4.

---

## 1. Required Database Changes

We will introduce three new tables:

*   `reference_models`
    *   `id`: UUID (PK)
    *   `project_id`: UUID (FK to `projects.id`)
    *   `model_name`: String
    *   `bpm_xml` / `json_structure`: Text/JSON (The reference BPMN/DFG structure)
    *   `created_at`: DateTime
*   `conformance_results`
    *   `id`: UUID (PK)
    *   `analysis_id`: UUID (FK to `process_analyses.id`)
    *   `fitness_score`: Float
    *   `precision_score`: Float
    *   `deviations`: JSON (List of missing/extra transitions, wrong ordering)
    *   `violations`: JSON (Violation alerts, SLA breaches)
*   `carbon_attributions`
    *   `id`: UUID (PK)
    *   `analysis_id`: UUID (FK to `process_analyses.id`)
    *   `activity_emissions`: JSON (Mapping of activity names to co2e emissions)
    *   `variant_emissions`: JSON (Mapping of variant IDs to accumulated co2e)

---

## 2. Required API Changes

*   `POST /api/conformance/reference-models`
    *   Upload reference model XML/JSON linked to a project context.
*   `POST /api/process/{id}/conformance`
    *   Run conformance checking of a discovered model against a reference model.
*   `GET /api/process/{id}/conformance`
    *   Retrieve conformance checks (fitness, deviations, violation counts).
*   `GET /api/process/{id}/carbon-attribution`
    *   Retrieve calculated activity node and path co2e values.

---

## 3. Required UI Changes

*   **Reference Upload Panel**: Section inside dashboard to submit/visualize reference normative flows.
*   **Conformance Panel**: Displays:
    *   Fitness speedometer dial.
    *   Deviation table (e.g. Activity X skipped, path Y->Z not allowed).
    *   Violation indicators (SLA alerts).
*   **Carbon Hotspot Graph**: Overlay co2e color-heatmaps (Green-to-Red) on React Flow graph nodes.

---

## 4. Required Algorithms

*   **Token Replay Conformance Checking**: Replay log traces on the reference model net to calculate:
    *   *Fitness* = $1/2 \cdot (1 - m/c) + 1/2 \cdot (1 - r/p)$ (missing, consumed, remaining, produced tokens).
*   **Carbon Attribution**: Group and sum the mapped `carbon_emissions` column of events by activity and case path.
*   **Carbon-Aware Fitness**: Combine trace structural fitness with carbon intensity threshold limits.

---

## 5. Dependencies on Sprint 3

*   `Dataset` schema mappings containing mapped `carbon_emissions` column.
*   Standardized pandas DataFrame output from `parse_dataset_to_dataframe`.
*   Active process analysis ID references generated from process discovery pipelines.
