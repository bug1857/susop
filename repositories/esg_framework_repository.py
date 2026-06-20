from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EsgFramework, FrameworkMapping

class EsgFrameworkRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_framework_by_id(self, id: UUID) -> Optional[EsgFramework]:
        return self.db.query(EsgFramework).filter(
            EsgFramework.id == id,
            EsgFramework.is_deleted == False
        ).first()

    def get_framework_by_name(self, framework_name: str) -> Optional[EsgFramework]:
        return self.db.query(EsgFramework).filter(
            EsgFramework.framework_name == framework_name,
            EsgFramework.is_deleted == False
        ).first()

    def get_frameworks(self) -> List[EsgFramework]:
        return self.db.query(EsgFramework).filter(
            EsgFramework.is_deleted == False
        ).all()

    def create_framework(self, framework: EsgFramework) -> EsgFramework:
        self.db.add(framework)
        self.db.commit()
        self.db.refresh(framework)
        return framework

    def get_mappings_by_framework(self, framework_id: UUID) -> List[FrameworkMapping]:
        return self.db.query(FrameworkMapping).filter(
            FrameworkMapping.framework_id == framework_id,
            FrameworkMapping.is_deleted == False
        ).all()

    def get_mappings_by_kpi(self, kpi_definition_id: UUID) -> List[FrameworkMapping]:
        return self.db.query(FrameworkMapping).filter(
            FrameworkMapping.kpi_definition_id == kpi_definition_id,
            FrameworkMapping.is_deleted == False
        ).all()

    def create_mapping(self, mapping: FrameworkMapping) -> FrameworkMapping:
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        return mapping
