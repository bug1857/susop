from pydantic import BaseModel, EmailStr, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from app.models.models import InsightSeverity, ForecastMethod, ScenarioType, RecommendationPriority, RecommendationType, ExplainabilityType, AIProvider, AIRequestType

# User Schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

# Organization Schemas
class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class OrganizationUpdate(BaseModel):
    name: str

# Workspace Schemas
class WorkspaceCreate(BaseModel):
    organization_id: UUID
    name: str

class WorkspaceResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    created_at: datetime

    class Config:
        from_attributes = True

class WorkspaceUpdate(BaseModel):
    name: str

# Project Schemas
class ProjectCreate(BaseModel):
    workspace_id: UUID
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    description: Optional[str] = None
    is_archived: bool
    created_at: datetime

    class Config:
        from_attributes = True

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_archived: Optional[bool] = None

# User Role & Invitation Schemas
class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str  # "Admin", "Manager", "Analyst", "Viewer"

class UserRoleResponse(BaseModel):
    id: UUID
    user: UserResponse
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: UUID
    tenant_id: Optional[UUID] = None
    user_id: UUID
    action: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Dataset Schemas
class DatasetResponse(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    original_file_path: str
    processed_file_path: Optional[str] = None
    file_size: int
    status: str
    dataset_type: str
    version: int
    parent_dataset_id: Optional[UUID] = None
    is_archived: bool
    is_deleted: bool
    row_count: Optional[int] = None
    headers: Optional[List[str]] = None
    schema_confidence: Optional[dict] = None
    mappings: Optional[dict] = None
    validation_errors: Optional[List[dict]] = None
    uploaded_by: Optional[UUID] = None
    uploaded_at: datetime
    validated_by: Optional[UUID] = None
    validated_at: Optional[datetime] = None
    mapping_saved_by: Optional[UUID] = None
    mapping_saved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SaveMappingRequest(BaseModel):
    mappings: dict


# Process Mining Foundation Schemas
class ProcessAnalysisCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    dataset_id: UUID
    parent_analysis_id: Optional[UUID] = None

class ProcessAnalysisResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    dataset_id: UUID
    analysis_version: int
    parent_analysis_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    is_deleted: bool

    class Config:
        from_attributes = True

class ProcessModelResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    model_name: str
    activity_count: int
    edge_count: int
    node_count: int
    object_type_count: int
    metadata_fields: Optional[dict] = None
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ProcessVariantResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    variant_name: str
    frequency: int
    percentage: float
    activity_sequence: List[str]
    total_emissions: Optional[float] = None
    average_emissions: Optional[float] = None
    emissions_per_execution: Optional[float] = None
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ProcessBottleneckResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    activity_name: str
    average_wait_time: float
    occurrence_count: int
    metadata_fields: Optional[dict] = None
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ProcessGraphResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    graph_type: str
    node_count: int
    edge_count: int
    graph_data: dict
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ProcessAnalysisSummaryResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    dataset_id: UUID
    analysis_version: int
    parent_analysis_id: Optional[UUID] = None
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    summary_metrics: Optional[dict] = None
    model_metadata: Optional[dict] = None

    class Config:
        from_attributes = True

class ProcessGraphDataResponse(BaseModel):
    nodes: List[dict]
    edges: List[dict]
    frequencies: dict
    metadata: dict

# Sprint 4 Schemas
class ConformanceCheckRequest(BaseModel):
    reference_model_id: UUID

class ReferenceModelCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    model_name: str
    model_definition: dict
    parent_model_id: Optional[UUID] = None

class ReferenceModelResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    model_name: str
    version: int
    parent_model_id: Optional[UUID] = None
    status: str
    model_definition: dict
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConformanceResultResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    fitness_score: float
    precision_score: float
    carbon_fitness_score: float
    carbon_budget: float
    actual_emissions: float
    excess_emissions: float
    budget_exceeded: bool
    conformance_method: Optional[str] = None
    execution_time_ms: Optional[int] = None
    diagnostic_trace_count: Optional[int] = None
    non_conforming_trace_count: Optional[int] = None
    reference_model_version: Optional[int] = None
    reference_model_id: Optional[UUID] = None
    failure_reason: Optional[str] = None
    dataset_id: Optional[UUID] = None
    analysis_version: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class ConformanceDeviationResponse(BaseModel):
    id: UUID
    result_id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    case_id: str
    activity_name: str
    deviation_type: str
    expected_transition: Optional[str] = None
    actual_transition: Optional[str] = None
    severity: str
    trace_reference: Optional[str] = None
    evidence_payload: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EmissionFactorCreate(BaseModel):
    activity_name: str
    factor_value: float
    unit: str
    source_name: str
    source_version: str
    effective_date: datetime

class EmissionFactorResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    activity_name: str
    factor_value: float
    unit: str
    source_name: str
    source_version: str
    effective_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class CarbonAttributionResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    activity_name: str
    emission_factor_id: UUID
    emissions: float
    created_at: datetime

    class Config:
        from_attributes = True

class EmissionHotspotResponse(BaseModel):
    id: UUID
    analysis_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    activity_name: str
    emissions: float
    contribution_percentage: float
    severity: str
    created_at: datetime

    class Config:
        from_attributes = True


# Sprint 4 API Response Envelopes & Update Request Schemas

class ReferenceModelUpdate(BaseModel):
    model_name: Optional[str] = None
    model_definition: Optional[dict] = None
    status: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str


class StandardMetadata(BaseModel):
    limit: Optional[int] = None
    offset: Optional[int] = None
    total: Optional[int] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None


class ReferenceModelResponseEnvelope(BaseModel):
    success: bool
    data: Optional[ReferenceModelResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class ReferenceModelListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[ReferenceModelResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class ConformanceResultResponseEnvelope(BaseModel):
    success: bool
    data: Optional[ConformanceResultResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class ConformanceDeviationResponseEnvelope(BaseModel):
    success: bool
    data: Optional[ConformanceDeviationResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class ConformanceDeviationListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[ConformanceDeviationResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class CarbonAttributionData(BaseModel):
    activity_emissions: List[CarbonAttributionResponse]
    variant_emissions: List[ProcessVariantResponse]
    carbon_budget: float
    actual_emissions: float
    excess_emissions: float
    carbon_fitness_score: float


class CarbonAttributionResponseEnvelope(BaseModel):
    success: bool
    data: Optional[CarbonAttributionData] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class EmissionHotspotListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EmissionHotspotResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class CarbonFitnessData(BaseModel):
    carbon_fitness_score: float
    carbon_budget: float
    actual_emissions: float
    excess_emissions: float
    budget_exceeded: bool
    compliance_factor: Optional[float] = None
    formula: Optional[str] = None


class CarbonFitnessResponseEnvelope(BaseModel):
    success: bool
    data: Optional[CarbonFitnessData] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class StandardSuccessEnvelope(BaseModel):
    success: bool
    data: Optional[dict] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


# ESG KPI Definition Schemas
class EsgKpiDefinitionCreate(BaseModel):
    kpi_code: str
    version: Optional[int] = 1
    name: str
    category: str
    description: Optional[str] = None
    unit: str
    source_type: str
    calculation_method: Optional[dict] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
    parent_kpi_id: Optional[UUID] = None


class EsgKpiDefinitionResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    kpi_code: str
    version: int
    name: str
    category: str
    description: Optional[str] = None
    unit: str
    source_type: str
    calculation_method: Optional[dict] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
    is_active: bool
    parent_kpi_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ESG KPI Value Schemas
class EsgKpiValueCreate(BaseModel):
    kpi_definition_id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    period: str
    value: float
    is_manual: bool = False

class EsgKpiValueResponse(BaseModel):
    id: UUID
    kpi_definition_id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: Optional[UUID] = None
    period: str
    value: float
    is_manual: bool
    calculated_at: datetime
    recorded_by: Optional[UUID] = None

    class Config:
        from_attributes = True

# ESG Framework Schemas
class EsgFrameworkCreate(BaseModel):
    framework_name: str
    framework_version: str
    description: Optional[str] = None

class EsgFrameworkResponse(BaseModel):
    id: UUID
    framework_name: str
    framework_version: str
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Framework Mapping Schemas
class FrameworkMappingCreate(BaseModel):
    framework_id: UUID
    kpi_definition_id: UUID
    framework_section: str
    framework_principle: Optional[str] = None
    framework_question: str
    reporting_category: str

class FrameworkMappingResponse(BaseModel):
    id: UUID
    framework_id: UUID
    kpi_definition_id: UUID
    framework_section: str
    framework_principle: Optional[str] = None
    framework_question: str
    reporting_category: str
    created_at: datetime

    class Config:
        from_attributes = True

# ESG Scoring Profile Schemas
class EsgScoringProfileCreate(BaseModel):
    name: str
    environmental_weight: float
    social_weight: float
    governance_weight: float
    kpi_weights: dict
    is_active: bool = True

class EsgScoringProfileResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    name: str
    environmental_weight: float
    social_weight: float
    governance_weight: float
    kpi_weights: dict
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# ESG Score Schemas
class EsgScoreCreate(BaseModel):
    workspace_id: UUID
    period: str
    scoring_profile_id: UUID
    overall_score: float
    environmental_score: float
    social_score: float
    governance_score: float
    completeness_score: float
    score_breakdown: Optional[dict] = None

class EsgScoreResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    period: str
    scoring_profile_id: UUID
    overall_score: float
    environmental_score: float
    social_score: float
    governance_score: float
    completeness_score: float
    score_breakdown: Optional[dict] = None
    calculated_at: datetime

    class Config:
        from_attributes = True

# ESG Evidence Schemas
class EsgEvidenceCreate(BaseModel):
    kpi_value_id: UUID
    source_description: str
    source_entity_type: str
    source_entity_id: Optional[UUID] = None
    evidence_file_path: Optional[str] = None
    cryptographic_hash: Optional[str] = None
    calculation_steps: dict
    lineage_path: dict

class EsgEvidenceResponse(BaseModel):
    id: UUID
    kpi_value_id: UUID
    tenant_id: UUID
    source_description: str
    source_entity_type: str
    source_entity_id: Optional[UUID] = None
    evidence_file_path: Optional[str] = None
    cryptographic_hash: Optional[str] = None
    calculation_steps: dict
    lineage_path: dict
    audited_by: Optional[UUID] = None
    audited_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Envelopes
class EsgKpiDefinitionResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgKpiDefinitionResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgKpiDefinitionListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgKpiDefinitionResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgKpiValueResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgKpiValueResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgKpiValueListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgKpiValueResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgFrameworkResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgFrameworkResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgFrameworkListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgFrameworkResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class FrameworkMappingResponseEnvelope(BaseModel):
    success: bool
    data: Optional[FrameworkMappingResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class FrameworkMappingListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[FrameworkMappingResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgScoringProfileResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgScoringProfileResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgScoringProfileListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgScoringProfileResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgScoreResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgScoreResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgScoreListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgScoreResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgEvidenceResponseEnvelope(BaseModel):
    success: bool
    data: Optional[EsgEvidenceResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class EsgEvidenceListResponseEnvelope(BaseModel):
    success: bool
    data: Optional[List[EsgEvidenceResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


# ==========================================
# Sprint 6 AI Copilot Schemas
# ==========================================

class AiInsightResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    insight_type: str
    title: str
    description: Optional[str] = None
    severity: InsightSeverity
    confidence_score: float
    source_entity: Optional[str] = None
    source_reference: Optional[str] = None
    insight_metadata: Optional[dict] = None
    status: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class AiInsightListResponse(BaseModel):
    success: bool
    data: Optional[List[AiInsightResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class AiInsightResponseEnvelope(BaseModel):
    success: bool
    data: Optional[AiInsightResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class CarbonForecastResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    forecast_period: str
    forecast_method: str
    predicted_emissions: float
    lower_bound: float
    upper_bound: float
    forecast_metadata: Optional[dict] = None
    forecast_confidence_score: float
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class CarbonForecastCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    forecast_period: str
    forecast_method: ForecastMethod

class CarbonForecastListResponse(BaseModel):
    success: bool
    data: Optional[List[CarbonForecastResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class CarbonForecastResponseEnvelope(BaseModel):
    success: bool
    data: Optional[CarbonForecastResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class ScenarioSimulationCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    scenario_name: str
    scenario_description: Optional[str] = None
    scenario_type: ScenarioType
    baseline_reduction_percent: float

    @field_validator("baseline_reduction_percent")
    @classmethod
    def validate_percent(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError("baseline_reduction_percent must be between 0.0 and 100.0")
        return v


class ScenarioSimulationResponseData(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    scenario_name: str
    scenario_description: Optional[str] = None
    input_parameters: dict
    baseline_emissions: float
    simulated_emissions: float
    emission_reduction: float
    reduction_percentage: float
    scenario_type: str
    simulation_confidence_score: float
    simulation_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ScenarioSimulationResponse(BaseModel):
    success: bool
    data: Optional[ScenarioSimulationResponseData] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class ScenarioSimulationListResponse(BaseModel):
    success: bool
    data: Optional[List[ScenarioSimulationResponseData]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class AiRecommendationCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None


class AiRecommendationResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    recommendation_type: RecommendationType
    title: str
    description: Optional[str] = None
    estimated_emission_reduction: float
    estimated_cost_reduction: Optional[float] = None
    priority: RecommendationPriority
    status: str
    recommendation_confidence_score: float
    recommendation_metadata: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class AiRecommendationListResponse(BaseModel):
    success: bool
    data: Optional[List[AiRecommendationResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None

class AiRecommendationResponseEnvelope(BaseModel):
    success: bool
    data: Optional[AiRecommendationResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None


class RecommendationEvidenceResponse(BaseModel):
    id: UUID
    recommendation_id: UUID
    entity_type: str
    entity_id: UUID
    evidence_payload: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RecommendationEvidenceResponseEnvelope(BaseModel):
    success: bool
    data: Optional[RecommendationEvidenceResponse] = None
    metadata: Optional[dict] = None
    errors: Optional[List[ErrorDetail]] = None

class RecommendationEvidenceListResponse(BaseModel):
    success: bool
    data: Optional[List[RecommendationEvidenceResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class AiExplainabilityCreate(BaseModel):
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    entity_type: ExplainabilityType
    entity_id: UUID


class AiExplainabilityResponse(BaseModel):
    id: UUID
    entity_type: ExplainabilityType
    entity_id: UUID
    explanation_payload: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiExplainabilityListResponse(BaseModel):
    success: bool
    data: Optional[List[AiExplainabilityResponse]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class AiCopilotRequest(BaseModel):
    workspace_id: UUID
    project_id: UUID
    analysis_id: Optional[UUID] = None
    request_type: AIRequestType
    provider: AIProvider
    entity_type: ExplainabilityType
    entity_id: UUID
    user_query: Optional[str] = None


class AiCopilotResponseSchema(BaseModel):
    id: UUID
    provider: AIProvider
    request_type: AIRequestType
    response_text: str
    token_count: int
    execution_time_ms: int
    model_name: Optional[str] = None
    prompt_hash: Optional[str] = None
    response_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AiCopilotListResponse(BaseModel):
    success: bool
    data: Optional[List[AiCopilotResponseSchema]] = None
    metadata: Optional[StandardMetadata] = None
    errors: Optional[List[ErrorDetail]] = None


class SustainAiSettingsResponse(BaseModel):
    workspace_id: UUID
    provider: str
    model_name: str
    quality_mode: str
    prompt_style: str
    response_style: str
    settings_version: int

    class Config:
        from_attributes = True


class SustainAiSettingsUpdate(BaseModel):
    provider: str
    model_name: str
    quality_mode: str
    prompt_style: str
    response_style: str







