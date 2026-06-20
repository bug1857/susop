from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import ProcessBottleneck

class ProcessBottleneckRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ProcessBottleneck]:
        return self.db.query(ProcessBottleneck).filter(
            ProcessBottleneck.analysis_id == analysis_id,
            ProcessBottleneck.tenant_id == tenant_id,
            ProcessBottleneck.is_deleted == False
        ).all()

    def create(self, bottleneck: ProcessBottleneck) -> ProcessBottleneck:
        self.db.add(bottleneck)
        self.db.commit()
        self.db.refresh(bottleneck)
        return bottleneck
