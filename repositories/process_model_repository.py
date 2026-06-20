from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ProcessModel

class ProcessModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessModel]:
        return self.db.query(ProcessModel).filter(
            ProcessModel.analysis_id == analysis_id,
            ProcessModel.tenant_id == tenant_id,
            ProcessModel.is_deleted == False
        ).all()

    def create(self, model: ProcessModel) -> ProcessModel:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
