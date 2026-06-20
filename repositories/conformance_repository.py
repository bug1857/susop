from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import ConformanceResult

class ConformanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[ConformanceResult]:
        return self.db.query(ConformanceResult).filter(
            ConformanceResult.id == id,
            ConformanceResult.tenant_id == tenant_id
        ).first()

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> Optional[ConformanceResult]:
        return self.db.query(ConformanceResult).filter(
            ConformanceResult.analysis_id == analysis_id,
            ConformanceResult.tenant_id == tenant_id
        ).first()

    def create(self, result: ConformanceResult) -> ConformanceResult:
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result
