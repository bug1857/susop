from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import HTTPException, status
from app.models.models import EsgKpiDefinition, EsgKpiValue, Workspace, Project
from app.repositories.esg_kpi_repository import EsgKpiRepository
from app.core.audit import log_activity

class EsgKpiService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = EsgKpiRepository(db)

    def create_kpi_definition(self, tenant_id: UUID, user_id: UUID, payload: dict) -> EsgKpiDefinition:
        kpi_code = payload.get("kpi_code")
        version = payload.get("version", 1)
        name = payload.get("name")
        category = payload.get("category")
        description = payload.get("description")
        unit = payload.get("unit")
        source_type = payload.get("source_type")
        calculation_method = payload.get("calculation_method")
        effective_from = payload.get("effective_from")
        effective_to = payload.get("effective_to")
        parent_kpi_id = payload.get("parent_kpi_id")

        if not kpi_code or not name or not category or not unit or not source_type or not effective_from:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required KPI definition fields")

        # Convert strings to datetime objects
        if isinstance(effective_from, str):
            effective_from = datetime.fromisoformat(effective_from.replace("Z", "+00:00"))
        if isinstance(effective_to, str) and effective_to:
            effective_to = datetime.fromisoformat(effective_to.replace("Z", "+00:00"))

        if effective_to and effective_from > effective_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="effective_from must be less than or equal to effective_to")

        # Unique code + version constraint per tenant
        existing = self.repo.get_definition_by_code_version(kpi_code, version, tenant_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"KPI code '{kpi_code}' with version {version} already exists for this tenant."
            )

        # Parent KPI Lineage Validation
        if parent_kpi_id:
            parent = self.repo.get_definition_by_id(parent_kpi_id, tenant_id)
            if not parent:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent KPI definition not found")
            if parent.kpi_code != kpi_code:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent KPI code must match child KPI code")
            if parent.version >= version:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent KPI version must be strictly less than child version")

        new_def = EsgKpiDefinition(
            tenant_id=tenant_id,
            kpi_code=kpi_code,
            version=version,
            name=name,
            category=category,
            description=description,
            unit=unit,
            source_type=source_type,
            calculation_method=calculation_method,
            effective_from=effective_from,
            effective_to=effective_to,
            parent_kpi_id=parent_kpi_id,
            is_active=True,
            is_deleted=False
        )
        created = self.repo.create_definition(new_def)
        log_activity(self.db, user_id, "kpi_created", tenant_id, f"Created KPI definition: {kpi_code} v{version}")
        return created

    def update_kpi_definition(self, id: UUID, tenant_id: UUID, user_id: UUID, payload: dict) -> EsgKpiDefinition:
        definition = self.repo.get_definition_by_id(id, tenant_id)
        if not definition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI definition not found")

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
            eff_from = payload["effective_from"]
            if isinstance(eff_from, str):
                eff_from = datetime.fromisoformat(eff_from.replace("Z", "+00:00"))
            definition.effective_from = eff_from
        if "effective_to" in payload:
            eff_to = payload["effective_to"]
            if isinstance(eff_to, str) and eff_to:
                eff_to = datetime.fromisoformat(eff_to.replace("Z", "+00:00"))
            definition.effective_to = eff_to

        if definition.effective_to and definition.effective_from > definition.effective_to:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="effective_from must be less than or equal to effective_to")

        self.db.commit()
        self.db.refresh(definition)
        log_activity(self.db, user_id, "kpi_updated", tenant_id, f"Updated KPI definition: {definition.kpi_code} v{definition.version}")
        return definition

    def retrieve_definitions(self, tenant_id: UUID) -> List[EsgKpiDefinition]:
        return self.repo.get_active_definitions(tenant_id)

    def retrieve_versions(self, kpi_code: str, tenant_id: UUID) -> List[EsgKpiDefinition]:
        return self.repo.get_definitions_by_code(kpi_code, tenant_id)

    def activate_deactivate_kpi(self, id: UUID, tenant_id: UUID, user_id: UUID, is_active: bool) -> EsgKpiDefinition:
        definition = self.repo.get_definition_by_id(id, tenant_id)
        if not definition:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI definition not found")

        definition.is_active = is_active
        self.db.commit()
        self.db.refresh(definition)
        log_activity(
            self.db, 
            user_id, 
            "kpi_activated" if is_active else "kpi_deactivated", 
            tenant_id, 
            f"Set KPI {definition.kpi_code} v{definition.version} is_active to {is_active}"
        )
        return definition

    def record_kpi_value(self, tenant_id: UUID, user_id: UUID, payload: dict) -> EsgKpiValue:
        kpi_definition_id = payload.get("kpi_definition_id")
        workspace_id = payload.get("workspace_id")
        project_id = payload.get("project_id")
        period = payload.get("period")
        value = payload.get("value")
        is_manual = payload.get("is_manual", True)

        if not kpi_definition_id or not workspace_id or not period or value is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing required KPI value fields")

        # Validate KPI definition exists
        kpi_def = self.repo.get_definition_by_id(kpi_definition_id, tenant_id)
        if not kpi_def:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KPI definition not found")

        # Validate Workspace exists and is tenant-scoped
        workspace = self.db.query(Workspace).filter(Workspace.id == workspace_id, Workspace.organization_id == tenant_id).first()
        if not workspace:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found or unauthorized")

        # Validate Project exists, is tenant-scoped and workspace-scoped
        if project_id:
            project = self.db.query(Project).filter(
                Project.id == project_id, 
                Project.workspace_id == workspace_id
            ).first()
            if not project:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized")

        new_val = EsgKpiValue(
            kpi_definition_id=kpi_definition_id,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            project_id=project_id,
            period=period,
            value=value,
            is_manual=is_manual,
            is_deleted=False,
            recorded_by=user_id,
            calculated_at=datetime.utcnow()
        )
        created = self.repo.create_value(new_val)
        log_activity(self.db, user_id, "kpi_value_recorded", tenant_id, f"Recorded KPI value {value} for period {period}")
        return created
