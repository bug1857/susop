# Sprint 4 — Prompt 2: Conformance Checking Engine Completion Report

## Implementation Details

The backend foundation for the Conformance Checking Engine has been completely implemented.

### 1. Process Router Updates (`backend/app/routers/process.py`)
- Created `POST /api/process/{id}/conformance`: Accepts a `ConformanceCheckRequest` holding the `reference_model_id`. Invokes the `ConformanceService` to run token-based replay.
- Created `GET /api/process/{id}/conformance`: Fetches the calculated `ConformanceResult` from the database.

### 2. Conformance Service (`backend/app/services/conformance_service.py`)
- **Reference Model Loading**: Loads the model JSON via the repository. If the format is `pnml`, it translates the raw content into a PM4Py Petri net by writing to a temporary file and invoking `pm4py.objects.petri_net.importer.importer`.
- **Diagnostics Execution**: Uses PM4Py's token-based replay (`pm4py.conformance_diagnostics_token_based_replay`, `pm4py.fitness_token_based_replay`, `pm4py.precision_token_based_replay`) to calculate fitness and precision scores against the loaded event log dataset dataframe.
- **Normalized Deviations**: Processes token diagnostics output trace by trace. Traces where `trace_is_fit == False` trigger the extraction of missing tokens and transition problems. These are serialized explicitly as `ConformanceDeviation` records, adhering to the requirement of **NOT** storing raw JSON payloads.
- **Audit Logging**: Emits `conformance_started`, `deviation_detected`, `conformance_completed`, and `conformance_failed` events with exact tenant bounds.

### 3. Schema Definitions (`backend/app/schemas/schemas.py`)
- Declared `ConformanceCheckRequest` to define inputs.
- Validated Pydantic responses using `ConformanceResultResponse` and `ConformanceDeviationResponse`.

### 4. Constraints Satisfied
- PM4Py Token Replay integrated cleanly.
- Multi-tenant data segregation enforced at all levels.
- NO carbon logic was executed (set to 0.0 default).
- NO frontend components were built.

The system is fully prepared to execute token-based conformance comparisons across normative models and loaded data sets.
