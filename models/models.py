import enum
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Table, Integer, JSON, Float, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from app.core.database import Base

class InsightSeverity(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ForecastMethod(str, enum.Enum):
    LINEAR_TREND = "LINEAR_TREND"
    MOVING_AVERAGE = "MOVING_AVERAGE"


class ScenarioType(str, enum.Enum):
    EMISSION_REDUCTION = "EMISSION_REDUCTION"
    PROCESS_EFFICIENCY = "PROCESS_EFFICIENCY"
    ENERGY_OPTIMIZATION = "ENERGY_OPTIMIZATION"


class RecommendationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RecommendationType(str, enum.Enum):
    CARBON_HOTSPOT = "CARBON_HOTSPOT"
    PROCESS_BOTTLENECK = "PROCESS_BOTTLENECK"
    CONFORMANCE_RISK = "CONFORMANCE_RISK"
    ESG_RISK = "ESG_RISK"
    DATA_QUALITY = "DATA_QUALITY"


class ExplainabilityType(str, enum.Enum):
    INSIGHT = "INSIGHT"
    FORECAST = "FORECAST"
    SIMULATION = "SIMULATION"
    RECOMMENDATION = "RECOMMENDATION"


class AIProvider(str, enum.Enum):
    OLLAMA = "OLLAMA"


class AIRequestType(str, enum.Enum):
    INSIGHT_SUMMARY = "INSIGHT_SUMMARY"
    FORECAST_EXPLANATION = "FORECAST_EXPLANATION"
    SIMULATION_EXPLANATION = "SIMULATION_EXPLANATION"
    RECOMMENDATION_SUMMARY = "RECOMMENDATION_SUMMARY"
    EXECUTIVE_BRIEF = "EXECUTIVE_BRIEF"
    CHAT = "CHAT"  # Bug 8 fix: was missing, causing SQLAlchemy validator to reject CHAT requests



class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspaces = relationship("Workspace", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("UserRole", back_populates="organization", cascade="all, delete-orphan")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="workspaces")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="workspace", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="projects")

class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False)  # "Admin", "Manager", "Analyst", "Viewer"
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="roles")
    organization = relationship("Organization", back_populates="roles")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # "Login", "Logout", "Org Created", "Workspace Created", "Project Created", "Member Invited"
    details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    original_file_path = Column(String, nullable=False)
    processed_file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # "uploading" | "validation_failed" | "mapping_required" | "ready"
    dataset_type = Column(String, default="csv")  # "csv", "ocel", "json", "xlsx", "pdf"
    version = Column(Integer, default=1)
    parent_dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    is_archived = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    row_count = Column(Integer, nullable=True)
    headers = Column(JSON, nullable=True)
    schema_confidence = Column(JSON, nullable=True)
    mappings = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)

    # Lineage Metadata
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    mapping_saved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    mapping_saved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="datasets")

class ProcessAnalysis(Base):
    __tablename__ = "process_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_version = Column(Integer, default=1, nullable=False)
    parent_analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="SET NULL"), nullable=True)
    status = Column(String, default="pending", nullable=False, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("idx_process_analysis_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_process_analysis_workspace_project", "workspace_id", "project_id"),
        Index("idx_process_analysis_project_dataset", "project_id", "dataset_id"),
        Index("idx_process_analysis_dataset_version", "dataset_id", "analysis_version"),
    )

class ProcessModel(Base):
    __tablename__ = "process_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    activity_count = Column(Integer, nullable=False)
    edge_count = Column(Integer, nullable=False)
    node_count = Column(Integer, nullable=False)
    object_type_count = Column(Integer, nullable=False)
    metadata_fields = Column(JSON, name="metadata", nullable=True)  # custom name mapping or field name 'metadata_fields' mapping to table column 'metadata'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

class ProcessVariant(Base):
    __tablename__ = "process_variants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_name = Column(String, nullable=False)
    frequency = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    activity_sequence = Column(JSON, nullable=False)
    total_emissions = Column(Float, nullable=True)
    average_emissions = Column(Float, nullable=True)
    emissions_per_execution = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

class ProcessBottleneck(Base):
    __tablename__ = "process_bottlenecks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_name = Column(String, nullable=False)
    average_wait_time = Column(Float, nullable=False)
    occurrence_count = Column(Integer, nullable=False)
    metadata_fields = Column(JSON, name="metadata", nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

class ProcessGraph(Base):
    __tablename__ = "process_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    graph_type = Column(String, nullable=False, index=True)
    node_count = Column(Integer, nullable=False)
    edge_count = Column(Integer, nullable=False)
    graph_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

class ReferenceModel(Base):
    __tablename__ = "reference_models"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    model_name = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    parent_model_id = Column(UUID(as_uuid=True), ForeignKey("reference_models.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String, default="active", nullable=False)
    model_definition = Column(JSON, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_ref_model_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_ref_model_workspace_project", "workspace_id", "project_id"),
    )

class ConformanceResult(Base):
    __tablename__ = "conformance_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    fitness_score = Column(Float, nullable=False)
    precision_score = Column(Float, nullable=False)
    carbon_fitness_score = Column(Float, nullable=False)
    carbon_budget = Column(Float, nullable=False)
    actual_emissions = Column(Float, nullable=False)
    excess_emissions = Column(Float, nullable=False)
    budget_exceeded = Column(Boolean, nullable=False)
    conformance_method = Column(String, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    diagnostic_trace_count = Column(Integer, nullable=True)
    non_conforming_trace_count = Column(Integer, nullable=True)
    reference_model_version = Column(Integer, nullable=True)
    reference_model_id = Column(UUID(as_uuid=True), ForeignKey("reference_models.id", ondelete="SET NULL"), nullable=True)
    failure_reason = Column(String, nullable=True)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    analysis_version = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_conf_res_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_conf_res_workspace_project", "workspace_id", "project_id"),
    )

class ConformanceDeviation(Base):
    __tablename__ = "conformance_deviations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    result_id = Column(UUID(as_uuid=True), ForeignKey("conformance_results.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String, nullable=False)
    activity_name = Column(String, nullable=False, index=True)
    deviation_type = Column(String, nullable=False)
    expected_transition = Column(String, nullable=True)
    actual_transition = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    trace_reference = Column(String, nullable=True)
    evidence_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_deviation_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_deviation_workspace_project", "workspace_id", "project_id"),
        Index("idx_deviation_analysis_activity", "analysis_id", "activity_name"),
    )

class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_name = Column(String, nullable=False, index=True)
    factor_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    source_name = Column(String, nullable=False, index=True)
    source_version = Column(String, nullable=False)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class CarbonAttribution(Base):
    __tablename__ = "carbon_attributions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_name = Column(String, nullable=False, index=True)
    emission_factor_id = Column(UUID(as_uuid=True), ForeignKey("emission_factors.id", ondelete="RESTRICT"), nullable=False)
    emissions = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_carb_attr_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_carb_attr_workspace_project", "workspace_id", "project_id"),
        Index("idx_carb_attr_analysis_activity", "analysis_id", "activity_name"),
    )

class EmissionHotspot(Base):
    __tablename__ = "emission_hotspots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_name = Column(String, nullable=False, index=True)
    emissions = Column(Float, nullable=False)
    contribution_percentage = Column(Float, nullable=False)
    severity = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_hotspot_tenant_workspace", "tenant_id", "workspace_id"),
        Index("idx_hotspot_workspace_project", "workspace_id", "project_id"),
        Index("idx_hotspot_analysis_activity", "analysis_id", "activity_name"),
    )

class EsgKpiDefinition(Base):
    __tablename__ = "esg_kpi_definitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_code = Column(String, nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False, index=True)  # "Environmental", "Social", "Governance"
    description = Column(String, nullable=True)
    unit = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # "automated_process", "manual_entry", "external_api"
    calculation_method = Column(JSON, nullable=True)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    parent_kpi_id = Column(UUID(as_uuid=True), ForeignKey("esg_kpi_definitions.id", ondelete="SET NULL"), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_esg_kpi_code_version", "kpi_code", "version"),
    )

class EsgKpiValue(Base):
    __tablename__ = "esg_kpi_values"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_definition_id = Column(UUID(as_uuid=True), ForeignKey("esg_kpi_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    period = Column(String, nullable=False, index=True)  # "2026", "2026-Q1"
    value = Column(Float, nullable=False)
    is_manual = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    recorded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    kpi_definition = relationship("EsgKpiDefinition")

class EsgFramework(Base):
    __tablename__ = "esg_frameworks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_name = Column(String, nullable=False, unique=True, index=True)
    framework_version = Column(String, nullable=False)
    description = Column(String, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FrameworkMapping(Base):
    __tablename__ = "framework_mappings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("esg_frameworks.id", ondelete="CASCADE"), nullable=False, index=True)
    kpi_definition_id = Column(UUID(as_uuid=True), ForeignKey("esg_kpi_definitions.id", ondelete="CASCADE"), nullable=False, index=True)
    framework_section = Column(String, nullable=False)
    framework_principle = Column(String, nullable=True)
    framework_question = Column(String, nullable=False)
    reporting_category = Column(String, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_framework_kpi_mapping", "framework_id", "kpi_definition_id"),
    )

class EsgScoringProfile(Base):
    __tablename__ = "esg_scoring_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    environmental_weight = Column(Float, default=0.40, nullable=False)
    social_weight = Column(Float, default=0.30, nullable=False)
    governance_weight = Column(Float, default=0.30, nullable=False)
    kpi_weights = Column(JSON, nullable=False)  # JSON weights per kpi_code
    is_active = Column(Boolean, default=True, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EsgScore(Base):
    __tablename__ = "esg_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    period = Column(String, nullable=False, index=True)
    scoring_profile_id = Column(UUID(as_uuid=True), ForeignKey("esg_scoring_profiles.id", ondelete="RESTRICT"), nullable=False)
    overall_score = Column(Float, nullable=False)
    environmental_score = Column(Float, nullable=False)
    social_score = Column(Float, nullable=False)
    governance_score = Column(Float, nullable=False)
    completeness_score = Column(Float, nullable=False)
    score_breakdown = Column(JSON, nullable=True)  # detailed scores per KPI
    is_deleted = Column(Boolean, default=False, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class EsgEvidence(Base):
    __tablename__ = "esg_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kpi_value_id = Column(UUID(as_uuid=True), ForeignKey("esg_kpi_values.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    source_description = Column(String, nullable=False)
    source_entity_type = Column(String, nullable=False, index=True)  # dataset, process_analysis, conformance_result, etc.
    source_entity_id = Column(UUID(as_uuid=True), nullable=True)  # reference ID (polymorphic)
    evidence_file_path = Column(String, nullable=True)
    cryptographic_hash = Column(String, nullable=True)
    calculation_steps = Column(JSON, nullable=False)
    lineage_path = Column(JSON, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    audited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    audited_at = Column(DateTime, nullable=True)


class AiInsight(Base):
    __tablename__ = "ai_insights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    insight_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    confidence_score = Column(Float, nullable=False)
    source_entity = Column(String, nullable=True)
    source_reference = Column(String, nullable=True)
    insight_metadata = Column(JSON, nullable=True)
    status = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class CarbonForecast(Base):
    __tablename__ = "carbon_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    forecast_period = Column(String, nullable=False)
    forecast_method = Column(String, nullable=False)
    predicted_emissions = Column(Float, nullable=False)
    lower_bound = Column(Float, nullable=False)
    upper_bound = Column(Float, nullable=False)
    forecast_metadata = Column(JSON, nullable=True)
    forecast_confidence_score = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)


class ScenarioSimulation(Base):
    __tablename__ = "scenario_simulations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    scenario_name = Column(String, nullable=False)
    scenario_description = Column(String, nullable=True)
    input_parameters = Column(JSON, nullable=False)
    baseline_emissions = Column(Float, nullable=False)
    simulated_emissions = Column(Float, nullable=False)
    emission_reduction = Column(Float, nullable=False)
    reduction_percentage = Column(Float, nullable=False)
    scenario_type = Column(String, nullable=False)
    simulation_confidence_score = Column(Float, nullable=False, default=0.0)
    simulation_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    @validates("scenario_type")
    def validate_scenario_type(self, key, value):
        if value not in [e.value for e in ScenarioType]:
            raise ValueError(f"Invalid scenario_type: {value}")
        return value


class AiRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    recommendation_type = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    estimated_emission_reduction = Column(Float, nullable=False)
    estimated_cost_reduction = Column(Float, nullable=True)
    priority = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)
    recommendation_confidence_score = Column(Float, nullable=False, default=0.0)
    recommendation_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    @validates("priority")
    def validate_priority(self, key, value):
        if value not in [e.value for e in RecommendationPriority]:
            raise ValueError(f"Invalid priority: {value}")
        return value

    @validates("recommendation_type")
    def validate_recommendation_type(self, key, value):
        if value not in [e.value for e in RecommendationType]:
            raise ValueError(f"Invalid recommendation_type: {value}")
        return value

    @validates("recommendation_confidence_score")
    def validate_recommendation_confidence_score(self, key, value):
        if not (0.0 <= value <= 100.0):
            raise ValueError("recommendation_confidence_score must be between 0.0 and 100.0")
        return value


class RecommendationEvidence(Base):
    __tablename__ = "recommendation_evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id = Column(UUID(as_uuid=True), ForeignKey("ai_recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    evidence_payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


class AiExplainability(Base):
    __tablename__ = "ai_explainability"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    explanation_payload = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

    @validates("entity_type")
    def validate_entity_type(self, key, value):
        if value not in [e.value for e in ExplainabilityType]:
            raise ValueError(f"Invalid entity_type: {value}")
        return value


class AiCopilotResponse(Base):
    __tablename__ = "ai_copilot_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("process_analyses.id", ondelete="CASCADE"), nullable=True, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    request_type = Column(String, nullable=False, index=True)
    prompt_version = Column(Integer, nullable=False)
    prompt_hash = Column(String, nullable=False)
    response_text = Column(String, nullable=False)
    token_count = Column(Integer, nullable=False)
    execution_time_ms = Column(Integer, nullable=False)
    response_metadata = Column(JSON, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    @validates("provider")
    def validate_provider(self, key, value):
        if value not in [e.value for e in AIProvider]:
            raise ValueError(f"Invalid provider: {value}")
        return value

    @validates("request_type")
    def validate_request_type(self, key, value):
        if value not in [e.value for e in AIRequestType]:
            raise ValueError(f"Invalid request_type: {value}")
        return value

    @validates("token_count")
    def validate_token_count(self, key, value):
        if value < 0:
            raise ValueError("token_count must be non-negative")
        return value

class SustainAiSettings(Base):
    __tablename__ = "sustainai_settings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    quality_mode = Column(String, nullable=False)
    prompt_style = Column(String, nullable=False)
    response_style = Column(String, nullable=False)
    settings_version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AiAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(String, nullable=False)
    selected_intents = Column(JSON, nullable=False)
    intent_confidence = Column(Float, nullable=False)
    provider = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    prompt_style = Column(String, nullable=False)
    response_style = Column(String, nullable=False)
    latency_ms = Column(Integer, nullable=False)
    estimated_cost_usd = Column(Float, nullable=False)
    context_sources = Column(JSON, nullable=False)
    context_budget = Column(JSON, nullable=False)
    fallback_used = Column(Boolean, default=False, nullable=False)
    fallback_provider = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
