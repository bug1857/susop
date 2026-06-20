# Sprint 4 — Prompt 3: Carbon Attribution & Carbon-Aware Conformance Completion Report

## 1. Files Modified / Created
- [models.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py): Added `total_emissions`, `average_emissions`, and `emissions_per_execution` to `ProcessVariant` model.
- [schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py): Added carbon fields to `ProcessVariantResponse` schema.
- [emission_factor_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/emission_factor_repository.py): Implemented the resolution prioritizing tenant factor -> workspace factor (falls back to tenant org) -> global default factors.
- [carbon_attribution_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_attribution_service.py): Calculates event and activity emissions, maps to variants, detects hotspots, and stores attribution metadata.
- [carbon_fitness_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_fitness_service.py): Resolves budget across Project/ReferenceModel levels, evaluates compliance, and updates the structural/carbon fitness conformance metrics.
- [process.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/process.py): Wired the `/api/process/{id}/carbon-attribution` endpoint.
- [test_process_mining.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_process_mining.py): Added the `test_carbon_attribution_lifecycle` integration test.

## 2. Formulas Used

### Activity Emissions
$$activity\_emissions = event\_value \times emission\_factor$$
If a carbon column is mapped (`"carbon_emissions"`), its value serves as `event_value`. Otherwise, `event_value` defaults to `1.0`.

### Carbon Budget Compliance Factor
$$Compliance\_Factor = \begin{cases} 
1.0 & \text{if } actual\_emissions \le budget \\
\max(0.0, 1.0 - \frac{actual\_emissions - budget}{budget}) & \text{if } actual\_emissions > budget
\end{cases}$$

### Carbon-Aware Fitness Score
$$Carbon\_Fitness = Structural\_Fitness \times Budget\_Compliance\_Factor$$

## 3. Validation Results
- SQLite migrations created new columns successfully.
- The unit test suite completes successfully (`6 passed`).
- Test results confirm:
  - Emission factor resolution prioritized correctly.
  - Variant emissions successfully computed and persisted.
  - Emission hotspots detected with contribution percentages and classified severity.
  - Carbon compliance factor correctly penalizes structural fitness.

## 4. Performance Observations & Known Issues
- **Performance**: Aggregating emissions via Pandas groupings (`groupby`) scales linearly with event count, making it highly efficient.
- **Known Issue**: Since the `EmissionFactor` database table does not carry a `workspace_id` column, workspace factors resolve directly to tenant-level factors.

## 5. Blockers Before Prompt 4
- None. The backend engine is fully integrated and tested.
