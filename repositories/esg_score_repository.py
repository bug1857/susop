from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EsgScore

class EsgScoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EsgScore]:
        return self.db.query(EsgScore).filter(
            EsgScore.id == id,
            EsgScore.tenant_id == tenant_id,
            EsgScore.is_deleted == False
        ).first()

    def get_by_workspace_period(self, workspace_id: UUID, period: str, tenant_id: UUID) -> Optional[EsgScore]:
        return self.db.query(EsgScore).filter(
            EsgScore.workspace_id == workspace_id,
            EsgScore.period == period,
            EsgScore.tenant_id == tenant_id,
            EsgScore.is_deleted == False
        ).first()

    def create(self, score: EsgScore) -> EsgScore:
        self.db.add(score)
        self.db.commit()
        self.db.refresh(score)
        return score
