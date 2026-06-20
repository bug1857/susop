from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ReferenceModel

class ReferenceModelRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[ReferenceModel]:
        return self.db.query(ReferenceModel).filter(
            ReferenceModel.id == id,
            ReferenceModel.tenant_id == tenant_id
        ).first()

    def get_by_project(self, project_id: UUID, tenant_id: UUID) -> List[ReferenceModel]:
        return self.db.query(ReferenceModel).filter(
            ReferenceModel.project_id == project_id,
            ReferenceModel.tenant_id == tenant_id
        ).all()

    def create(self, model: ReferenceModel) -> ReferenceModel:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model
