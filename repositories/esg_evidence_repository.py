from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EsgEvidence

class EsgEvidenceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EsgEvidence]:
        return self.db.query(EsgEvidence).filter(
            EsgEvidence.id == id,
            EsgEvidence.tenant_id == tenant_id,
            EsgEvidence.is_deleted == False
        ).first()

    def get_by_kpi_value(self, kpi_value_id: UUID, tenant_id: UUID) -> Optional[EsgEvidence]:
        return self.db.query(EsgEvidence).filter(
            EsgEvidence.kpi_value_id == kpi_value_id,
            EsgEvidence.tenant_id == tenant_id,
            EsgEvidence.is_deleted == False
        ).first()

    def create(self, evidence: EsgEvidence) -> EsgEvidence:
        self.db.add(evidence)
        self.db.commit()
        self.db.refresh(evidence)
        return evidence
