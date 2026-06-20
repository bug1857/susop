from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import ConformanceDeviation

class DeviationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_result(self, result_id: UUID, tenant_id: UUID) -> List[ConformanceDeviation]:
        return self.db.query(ConformanceDeviation).filter(
            ConformanceDeviation.result_id == result_id,
            ConformanceDeviation.tenant_id == tenant_id
        ).all()

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[ConformanceDeviation]:
        return self.db.query(ConformanceDeviation).filter(
            ConformanceDeviation.analysis_id == analysis_id,
            ConformanceDeviation.tenant_id == tenant_id
        ).all()

    def create(self, deviation: ConformanceDeviation) -> ConformanceDeviation:
        self.db.add(deviation)
        self.db.commit()
        self.db.refresh(deviation)
        return deviation

    def create_all(self, deviations: List[ConformanceDeviation]) -> List[ConformanceDeviation]:
        self.db.add_all(deviations)
        self.db.commit()
        return deviations

