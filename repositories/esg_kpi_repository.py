from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EsgKpiDefinition, EsgKpiValue

class EsgKpiRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_definition_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EsgKpiDefinition]:
        return self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.id == id,
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()

    def get_definition_by_code_version(self, kpi_code: str, version: int, tenant_id: UUID) -> Optional[EsgKpiDefinition]:
        return self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.kpi_code == kpi_code,
            EsgKpiDefinition.version == version,
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()

    def get_definitions(self, tenant_id: UUID) -> List[EsgKpiDefinition]:
        return self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).all()

    def get_definitions_by_code(self, kpi_code: str, tenant_id: UUID) -> List[EsgKpiDefinition]:
        return self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.kpi_code == kpi_code,
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).order_by(EsgKpiDefinition.version.desc()).all()

    def get_active_definitions(self, tenant_id: UUID) -> List[EsgKpiDefinition]:
        return self.db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_active == True,
            EsgKpiDefinition.is_deleted == False
        ).all()

    def create_definition(self, definition: EsgKpiDefinition) -> EsgKpiDefinition:
        self.db.add(definition)
        self.db.commit()
        self.db.refresh(definition)
        return definition

    def get_value_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EsgKpiValue]:
        return self.db.query(EsgKpiValue).filter(
            EsgKpiValue.id == id,
            EsgKpiValue.tenant_id == tenant_id,
            EsgKpiValue.is_deleted == False
        ).first()

    def get_values_by_period(self, workspace_id: UUID, period: str, tenant_id: UUID) -> List[EsgKpiValue]:
        return self.db.query(EsgKpiValue).filter(
            EsgKpiValue.workspace_id == workspace_id,
            EsgKpiValue.period == period,
            EsgKpiValue.tenant_id == tenant_id,
            EsgKpiValue.is_deleted == False
        ).all()

    def create_value(self, value: EsgKpiValue) -> EsgKpiValue:
        self.db.add(value)
        self.db.commit()
        self.db.refresh(value)
        return value
