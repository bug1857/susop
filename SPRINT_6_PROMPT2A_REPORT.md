# Sprint 6 Intelligence Core Report — Prompt 2A

This report documents the design, implementation, and verification of the deterministic, rule-based AI Copilot Insight Engine for SustainOCPM.

---

## 1. Files Modified & Added
- **[models.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py)**:
  - Added `InsightSeverity` (Enum: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - Added `insight_metadata` (`Column(JSON, nullable=True)`) to `AiInsight`.
- **[schemas.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/schemas/schemas.py)**:
  - Updated `AiInsightResponse` to serialize `severity` using the enum and include `insight_metadata`.
- **[config.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/core/config.py)**:
  - Added `INSIGHT_THRESHOLDS` setting mapping rules to thresholds.
- **[ai_insight_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/ai_insight_repository.py)**:
  - Added repository methods `find_existing_insight`, `list_active_insights` (with pagination + sorting whitelist check), and `count_active_insights`.
- **[ai_insight_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/ai_insight_service.py)**:
  - Fully implemented the deterministic insight generation rules (`generate_insights`), incorporating thresholds, severity evaluation, confidence scoring, deduplication criteria, and audit logging.
- **[copilot.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/routers/copilot.py)**:
  - Wired `GET /insights` endpoint with parameters supporting pagination, whitelisted sorting fields, and an envelope response with count metadata.
- **[test_ai_insights.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_ai_insights.py)**:
  - Implemented a suite of 9 backend tests asserting correctness.

---

## 2. Configurable Threshold Registry
Centralized in `app/core/config.py`:
```python
INSIGHT_THRESHOLDS = {
    "carbon_hotspot": {
        "low": 100.0,
        "medium": 500.0,
        "high": 1000.0,
        "critical": 5000.0
    },
    "bottleneck_hours": 24.0,
    "conformance_rate": 0.10,
    "esg_score": 50.0,
    "completeness_score": 80.0
}
```

---

## 3. Standardized Severity and Metadata Structure
Insights utilize a shared str enum `InsightSeverity` with values `LOW`, `MEDIUM`, `HIGH`, and `CRITICAL`.
Explainability metadata is persisted under the `insight_metadata` JSON column containing rule execution context.
Example structure for a Carbon Hotspot:
```json
{
  "rule": "carbon_hotspot",
  "metric": "emissions_kg",
  "observed": 600.0,
  "threshold": 500.0
}
```

---

## 4. Deduplication Strategy
Deduplication prevents the generation of duplicate active insights. Uniqueness is defined on:
$$\text{Uniqueness Key} = (\text{tenant\_id}, \text{analysis\_id}, \text{insight\_type}, \text{source\_reference})$$
Before persisting an insight, the repository calls `find_existing_insight`. If a record with `is_deleted == False` is found, the generation rule is skipped.

---

## 5. Audit Logging
Every successful execution of `generate_insights` that creates one or more new insights logs an audit trail event:
- **Event Name**: `insight_generated`
- **Payload**: `"Generated {count} AI Insights for analysis {analysis_id}"`

---

## 6. API Filtering, Pagination, and Sorting
The endpoint `GET /api/v1/copilot/insights` enforces:
- **Tenant Context**: Filters results strictly based on the request's active tenant and workspace context.
- **Pagination Safety**: Limits are capped at 100. Negative limits/offsets are rejected.
- **Sorting Whitelist**: Allowed sort columns are whitelisted (`created_at`, `confidence_score`, `severity`, `insight_type`, `status`). Unmatched fields fall back to `created_at`.

---

## 7. Validation Results
- **AI Insights Test Suite**: All 9 unit tests passed:
  - `test_hotspot_generation` (Pass)
  - `test_bottleneck_generation` (Pass)
  - `test_esg_risk_generation` (Pass)
  - `test_data_quality_generation` (Pass)
  - `test_deduplication` (Pass)
  - `test_tenant_isolation` (Pass)
  - `test_confidence_score_ranges` (Pass)
  - `test_insight_metadata_persistence` (Pass)
  - `test_sorting_whitelist` (Pass)
- **Core Regression Testing**: Executed the entire repository test suite (21 tests total) and all passed successfully with zero regressions.

---

## 8. Open Items for Sprint 6 Prompt 2B
- Connect Vertex AI/Gemini SDK models.
- Implement carbon forecasting algorithm model classes.
- Implement what-if scenario solvers using process configurations.
- Build recommendations generator.
- Implement frontend UI dashboard elements.
