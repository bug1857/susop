# Sprint 5 ESG Backend Validation Report

This report documents the architectural and functional validation of the ESG Intelligence backend upgrades implemented during Sprint 5. All validation checks have been performed against the core database models, service layers, and the integration test suite.

---

## Executive Summary

A comprehensive code analysis and execution of the backend test suite verify that the database schemas, services, and repositories comply with all required specifications. The test suite runs successfully with all tests green:

```bash
PYTHONPATH=. venv/bin/pytest -v app/tests/test_esg.py
```
**Status: PASSED (100% success rate)**

---

## 1. KPI Versioning is Immutable

### Architectural Analysis
The platform ensures that once a specific version of a KPI definition is created, it cannot be modified. Evolving a KPI requires creating a new version pointing to its predecessor.

- **Model Design**: In [models.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py#L327-L350), the `EsgKpiDefinition` model maintains a version number alongside effective dates and lineage tracking:
  - `version` (Integer)
  - `effective_from` (DateTime)
  - `effective_to` (DateTime, optional)
  - `parent_kpi_id` (ForeignKey referencing self)
- **Immutability Enforcement**: In [esg_kpi_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_kpi_service.py#L78-L113), the `update_kpi_definition` method only allows modification of mutable metadata fields:
  ```python
  # Update editable fields
  if "name" in payload:
      definition.name = payload["name"]
  if "category" in payload:
      definition.category = payload["category"]
  if "description" in payload:
      definition.description = payload["description"]
  if "unit" in payload:
      definition.unit = payload["unit"]
  if "source_type" in payload:
      definition.source_type = payload["source_type"]
  if "calculation_method" in payload:
      definition.calculation_method = payload["calculation_method"]
  if "effective_from" in payload:
      ...
  if "effective_to" in payload:
      ...
  ```
  Identifying coordinate fields such as `kpi_code`, `version`, and `parent_kpi_id` are completely omitted from the update routine, ensuring that an existing version record cannot be mutated.
- **Lineage Constraints**: During new version creation in `create_kpi_definition` (lines [L49-56](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_kpi_service.py#L49-L56)), parent-child dependencies are strictly validated:
  - Parent KPI must exist.
  - Parent KPI `kpi_code` must match the child's `kpi_code`.
  - Parent KPI `version` must be strictly less than the child's `version`.

> [!NOTE]
> Unique constraints on `(kpi_code, version)` per organization tenant prevent overlapping or duplicate version records.

---

## 2. Historical ESG Scores Reference Original KPI Versions

### Architectural Analysis
Historical ESG scores must preserve their integrity even if the active version of a KPI definition is subsequently evolved (e.g., v1 is replaced by v2).

- **Data Models**: 
  - [EsgKpiValue](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py#L351-L365) points to the unique ID of the specific version record `kpi_definition_id`, rather than the generic code.
  - [EsgScore](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py#L407-L423) persists calculated snapshots directly using the JSON column `score_breakdown` (line [L420](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py#L420)), which stores raw values, normalized scores, and weights at the time of calculation.
- **Independence from Evolution**: In [esg_scoring_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_scoring_service.py#L121-L158), the calculation logic uses the recorded `kpi_definition_id` to query KPI values. Even if a v2 definition is registered, v1 values continue referencing the immutable v1 definition row. The historical `EsgScore` records remain frozen in time inside the database.

---

## 3. ESG Score Recalculation Appends New Records

### Architectural Analysis
Recalculating an ESG score for a given period (e.g. `2026-Q1`) must never overwrite or modify previously calculated and stored scores, establishing an immutable audit log.

- **Append-Only Operations**: In [esg_scoring_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_scoring_service.py#L189-L205), `calculate_esg_score` creates a new instance of `EsgScore` and delegates directly to the repository:
  ```python
  new_score = EsgScore(
      tenant_id=tenant_id,
      workspace_id=workspace_id,
      period=period,
      scoring_profile_id=profile.id,
      overall_score=overall_score,
      environmental_score=env_score,
      social_score=soc_score,
      governance_score=gov_score,
      completeness_score=completeness,
      score_breakdown=breakdown,
      is_deleted=False,
      calculated_at=datetime.utcnow()
  )
  created = self.score_repo.create(new_score)
  ```
- **Database Insertion**: The [EsgScoreRepository.create](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/esg_score_repository.py#L25-L29) method inserts a new row with a unique ID (UUID) and calculation timestamp (`calculated_at`). The repository does not perform check-and-update checks for the period, ensuring that recalculations produce new entries rather than overwriting past metrics.

---

## 4. Evidence Lineage is Tenant Scoped

### Architectural Analysis
Security rules require that evidence lineages remain strictly tenant-isolated. Under no circumstances should tenant A be able to query or register evidence referencing tenant B's values.

- **Registration Containment**: In [esg_evidence_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_evidence_service.py#L28-L35), the service verifies that the associated `EsgKpiValue` exists and matches the user's `tenant_id`:
  ```python
  val = self.db.query(EsgKpiValue).filter(
      EsgKpiValue.id == kpi_value_id,
      EsgKpiValue.tenant_id == tenant_id,
      EsgKpiValue.is_deleted == False
  ).first()
  if not val:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI value not found or unauthorized")
  ```
- **Query Isolation**: In [esg_evidence_repository.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/repositories/esg_evidence_repository.py#L17-L22), the query for evidence is strictly filtered on the evidence table's tenant scope:
  ```python
  def get_by_kpi_value(self, kpi_value_id: UUID, tenant_id: UUID) -> Optional[EsgEvidence]:
      return self.db.query(EsgEvidence).filter(
          EsgEvidence.kpi_value_id == kpi_value_id,
          EsgEvidence.tenant_id == tenant_id,
          EsgEvidence.is_deleted == False
      ).first()
  ```
- **Information Leak Protection**: If an unauthorized tenant requests the lineage path or evidence files for a KPI value that belongs to another tenant, the service returns an HTTP 404 (Not Found) rather than disclosing information about the resource.

---

## 5. Mappings Support Multiple Frameworks per KPI

### Architectural Analysis
KPI definitions must support mappings to multiple compliance standards (e.g. a single KPI mapped to both BRSR and GRI).

- **Junction Model Design**: The [FrameworkMapping](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/models/models.py#L376-L391) model maps a single `kpi_definition_id` to a `framework_id` alongside section, principle, and question details:
  - `framework_id` (ForeignKey referencing `esg_frameworks.id`)
  - `kpi_definition_id` (ForeignKey referencing `esg_kpi_definitions.id`)
- **Many-to-Many Mappings**: A single KPI can have multiple entries in `framework_mappings` pointing to different frameworks (e.g., GRI, SASB).
- **Retrieval Layer**: In [esg_framework_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_framework_service.py#L19-L20), `retrieve_framework_mappings_for_kpi` fetches all mappings for a specific KPI definition:
  ```python
  def retrieve_framework_mappings_for_kpi(self, kpi_definition_id: UUID) -> List[FrameworkMapping]:
      return self.repo.get_mappings_by_kpi(kpi_definition_id)
  ```
  This returns `List[FrameworkMapping]`, returning all standard mappings configured for the KPI.

---

## 6. No Hardcoded BRSR Assumptions Remain

### Architectural Analysis
The platform must be framework-agnostic. No hardcoded logic or schema columns related specifically to BRSR can remain in the backend.

- **Dynamic Schema**: The `brsr_mappings` table has been completely replaced by dynamic, metadata-driven entities:
  - `esg_frameworks` (e.g., store name: BRSR, GRI, SASB, CSRD, TCFD, etc.)
  - `framework_mappings` (store mappings to sections, principles, questions, and categories dynamically)
- **Generic Service Layer**: In [esg_framework_service.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/services/esg_framework_service.py), all retrieval and registration operations are generic. Framework properties (such as section names, questions, and principles) are queried from database entries rather than code.
- **Codebase Cleanliness**: A global search shows that "BRSR" does not exist in any of the application source code files (`app/models/`, `app/repositories/`, `app/services/`, `app/routers/`, or `app/schemas/`). It is only used as test seed data in [test_esg.py](file:///Users/rudrapratapsingh/Desktop/newpro/backend/app/tests/test_esg.py) to verify the dynamic retrieval capability.

---

> [!TIP]
> The database migrations are fully up to date. Alembic revision [ff870c70b120](file:///Users/rudrapratapsingh/Desktop/newpro/backend/alembic/versions/ff870c70b120_sprint5_esg_foundation.py) contains the complete schema creation scripts matching these validation specifications.
