# Sprint 6 AI Copilot Foundation Report

## 1. Overview
This report documents the Sprint 6 backend foundation architecture for SustainOCPM, preparing the codebase for AI Insights, Emission Forecasting, Scenario Simulation, AI Recommendations, and Explainability & Lineage, while preserving existing multi-tenant and isolation constraints.

---

## 2. Database Models & Schema Migration

### Tables Created
1. **`ai_insights`**: Represents AI-generated sustainability observations.
2. **`carbon_forecasts`**: Stores emission projection outputs and confidence ranges.
3. **`scenario_simulations`**: Stores input parameters and emission reduction metrics for what-if scenarios.
4. **`ai_recommendations`**: Stores optimization suggestions with cost/emission estimates.
5. **`recommendation_evidence`**: Lineage table utilizing a generic polymorphic design (no FK columns to specific models, using `entity_type` + `entity_id`).

### Indexes Created
- **`ai_insights`**: `tenant_id`, `workspace_id`, `project_id`, `analysis_id`, `status`, `created_at`
- **`carbon_forecasts`**: `tenant_id`, `workspace_id`, `project_id`, `analysis_id`, `created_at`
- **`scenario_simulations`**: `tenant_id`, `workspace_id`, `project_id`, `analysis_id`, `created_at`
- **`ai_recommendations`**: `tenant_id`, `workspace_id`, `project_id`, `analysis_id`, `status`, `created_at`
- **`recommendation_evidence`**: `recommendation_id`, `entity_type`, `created_at`

### Foreign Keys Created
- `tenant_id` $\rightarrow$ `organizations.id` (on delete CASCADE)
- `workspace_id` $\rightarrow$ `workspaces.id` (on delete CASCADE)
- `project_id` $\rightarrow$ `projects.id` (on delete CASCADE)
- `analysis_id` $\rightarrow$ `process_analyses.id` (on delete CASCADE)
- `recommendation_id` $\rightarrow$ `ai_recommendations.id` (on delete CASCADE)

---

## 3. Schemas Added
All new schemas adhere to the versioned envelope response design under [schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py):
- **Insights**: `AiInsightResponse`, `AiInsightListResponse`
- **Forecasts**: `CarbonForecastResponse`, `CarbonForecastListResponse`
- **Simulations**: `ScenarioSimulationCreate`, `ScenarioSimulationResponse`, `ScenarioSimulationListResponse`
- **Recommendations**: `AiRecommendationResponse`, `AiRecommendationListResponse`
- **Explainability**: `RecommendationEvidenceResponse`, `RecommendationEvidenceListResponse`

---

## 4. Repositories Created
Created under `backend/app/repositories/`:
1. [ai_insight_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/ai_insight_repository.py) (`create`, `get_by_id`, `list_by_analysis`)
2. [carbon_forecast_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/carbon_forecast_repository.py) (`create`, `get_by_id`, `list_by_analysis`)
3. [scenario_simulation_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/scenario_simulation_repository.py) (`create`, `get_by_id`, `list_by_analysis`)
4. [ai_recommendation_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/ai_recommendation_repository.py) (`create`, `get_by_id`, `list_by_analysis`)
5. [recommendation_evidence_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/recommendation_evidence_repository.py) (`create`, `get_by_recommendation` joined with `AiRecommendation` for tenant isolation)

---

## 5. Services Created
Created service skeleton classes under `backend/app/services/` that return placeholder results and record audit logging activities:
1. [ai_insight_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/ai_insight_service.py) (`generate_insights`, `retrieve_insights`)
2. [carbon_forecast_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_forecast_service.py) (`generate_forecast`, `retrieve_forecasts`)
3. [scenario_simulation_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/scenario_simulation_service.py) (`run_simulation`, `retrieve_simulation`)
4. [ai_recommendation_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/ai_recommendation_service.py) (`generate_recommendations`, `retrieve_recommendations`)
5. [explainability_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/explainability_service.py) (`build_lineage`, `retrieve_evidence`)

---

## 6. Routes Registered
Created router [copilot.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/copilot.py) and registered it under `/api/v1/copilot` in [main.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/main.py):
- `GET /insights` (placeholder response)
- `GET /forecasts` (placeholder response)
- `POST /simulations` (placeholder response)
- `GET /simulations` (placeholder response)
- `GET /recommendations` (placeholder response)
- `GET /recommendations/{id}/evidence` (placeholder response)

---

## 7. Audit Logging Preparation
Services call `log_activity` to register placeholder events representing execution triggers:
- `insight_generated`
- `forecast_generated`
- `simulation_executed`
- `recommendation_generated`
- `lineage_retrieved`

---

## 8. Validation Results
- **Backend Pytest**: Completed successfully (12 passed). All models, schemas, repositories, services, and routers compiled, imported, and initialized without syntax or signature errors.
- **Database Migration**: Alembic migration script `9d83949ac0d3_sprint6_ai_copilot_foundation.py` successfully registered, executed, and stamped the database.
- **Frontend Build**: `npm run build` executed successfully without compilation issues.

---

## 9. Open Items for Prompt 2
- Implement forecasting algorithms and mathematical model solvers.
- Connect AI Copilot to LLM APIs (Gemini/Vertex AI) for reasoning tasks.
- Implement simulation calculator engines using process parameters.
- Build UI elements for Scenario Simulation and Recommendations.
