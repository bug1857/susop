# Sprint 6 Carbon Forecast Engine Report — Prompt 2B

This report documents the design, implementation, and verification of the deterministic Carbon Forecast Engine for SustainOCPM.

---

## 1. Files Modified & Added
- **[models.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py)**:
  - Added `ForecastMethod` string enum.
  - Added `forecast_confidence_score = Column(Float, nullable=False, default=0.0)` column to `CarbonForecast` model.
- **[schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py)**:
  - Updated `CarbonForecastResponse` to include `forecast_confidence_score`.
  - Added `CarbonForecastCreate` payload schema which validates enum membership of `forecast_method` at the schema level.
- **[carbon_forecast_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/carbon_forecast_repository.py)**:
  - Implemented `list_forecasts` query method supporting pagination (capped at 100) and whitelisted sorting fields (`created_at`, `forecast_period`, `predicted_emissions`, `forecast_method`).
  - Added `count_forecasts` and `latest_forecast` helpers.
- **[carbon_forecast_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/carbon_forecast_service.py)**:
  - Fully implemented the deterministic forecast service `generate_forecast`.
- **[copilot.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/copilot.py)**:
  - Refactored `GET /forecasts` to support filtering, whitelisted sorting, and paginated wrappers.
  - Created `POST /forecasts/generate` endpoint enforcing tenant/workspace/project/analysis ownership check with anti-enumeration 404 responses and delegating exclusively to `CarbonForecastService.generate_forecast`.
- **[test_carbon_forecasts.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_carbon_forecasts.py)**:
  - Added 14 unit and security tests.

---

## 2. Forecast Methods & Algorithms
All forecasts are calculated deterministically using chronological historical observations $y_1, y_2, \dots, y_N$ fetched from completed `ConformanceResult.actual_emissions` or sums of `CarbonAttribution.emissions`, optionally enriched with environmental ESG KPI values.
- **Linear Trend**:
  Calculates the average rate of change between periods and projects the next value:
  $$d = \frac{y_N - y_1}{N - 1}$$
  $$\text{forecast} = y_N + d$$
- **Moving Average**:
  Projects the next period using the average of the last $N = 3$ observations:
  $$\text{forecast} = \frac{y_N + y_{N-1} + y_{N-2}}{3}$$

---

## 3. Confidence Intervals & Quality Scoring
- **Confidence Interval**:
  Bounds are based on standard deviation $\sigma$ of the historical observations:
  $$\text{lower\_bound} = \max(0.0, \text{forecast} - \sigma)$$
  $$\text{upper\_bound} = \text{forecast} + \sigma$$
- **Quality Score**:
  Computed deterministically from observation count $N$ and coefficient of variation ($CV = \frac{\sigma}{\mu}$):
  - Points Score: $P_{\text{score}} = \min\left(50.0, \frac{N}{12.0} \times 50.0\right)$
  - Variance Score: $V_{\text{score}} = \max\left(0.0, 50.0 \times (1.0 - CV)\right)$
  - Final Quality Score: $\text{confidence\_score} = \max(0, \min(100, \text{round}(P_{\text{score}} + V_{\text{score}})))$

---

## 4. Security & Hardening Features
- **Strict Service Delegation**: The router never directly creates forecast records or calls database insertion helpers, delegating execution exclusively to the service layer.
- **Anti-Enumeration Checks**: Ownership validation fails return HTTP 404 rather than 403.
- **Tenant Context Enforcement**: Multi-tenant isolation prevents cross-tenant, cross-workspace, or cross-project data leakage or unauthorized forecast commands.
- **Append-only Versioning**: Forecast records remain immutable. Subsequent forecast generation calls create new database rows.

---

## 5. Validation Results
- **Carbon Forecast Test Suite**: All 14 tests passed successfully:
  - `test_linear_trend_forecast` (Pass)
  - `test_moving_average_forecast` (Pass)
  - `test_confidence_interval_generation` (Pass)
  - `test_forecast_versioning` (Pass)
  - `test_forecast_generation_append_only` (Pass)
  - `test_forecast_tenant_isolation` (Pass)
  - `test_forecast_sorting_whitelist` (Pass)
  - `test_insufficient_history` (Pass)
  - `test_forecast_confidence_score` (Pass)
  - `test_forecast_confidence_score_clamping` (Pass)
  - `test_invalid_forecast_method` (Pass)
  - `test_forecast_generation_requires_analysis_ownership` (Pass)
  - `test_forecast_generation_requires_workspace_membership` (Pass)
  - `test_router_delegates_to_service` (Pass)
- **Core Regression Testing**: Executed the entire repository test suite (35 tests total) and all passed successfully with zero regressions.

---

## 6. Open Items for Prompt 2C
- Implement Scenario Simulation Engine logic.
- Implement Recommendation Engine calculations.
