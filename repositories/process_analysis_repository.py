from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ProcessAnalysis

class ProcessAnalysisRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[ProcessAnalysis]:
        return self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.id == id,
            ProcessAnalysis.tenant_id == tenant_id,
            ProcessAnalysis.is_deleted == False
        ).first()

    def get_by_project(self, project_id: UUID, tenant_id: UUID) -> List[ProcessAnalysis]:
        return self.db.query(ProcessAnalysis).filter(
            ProcessAnalysis.project_id == project_id,
            ProcessAnalysis.tenant_id == tenant_id,
            ProcessAnalysis.is_deleted == False
        ).all()

    def create(self, analysis: ProcessAnalysis) -> ProcessAnalysis:
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def save(self, analysis: ProcessAnalysis) -> ProcessAnalysis:
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
