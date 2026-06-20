from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import ProcessVariant

class ProcessVariantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessVariant]:
        return self.db.query(ProcessVariant).filter(
            ProcessVariant.analysis_id == analysis_id,
            ProcessVariant.tenant_id == tenant_id,
            ProcessVariant.is_deleted == False
        ).all()

    def create(self, variant: ProcessVariant) -> ProcessVariant:
        self.db.add(variant)
        self.db.commit()
        self.db.refresh(variant)
        return variant
