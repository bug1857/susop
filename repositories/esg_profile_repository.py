from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EsgScoringProfile

class EsgProfileRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EsgScoringProfile]:
        return self.db.query(EsgScoringProfile).filter(
            EsgScoringProfile.id == id,
            EsgScoringProfile.tenant_id == tenant_id,
            EsgScoringProfile.is_deleted == False
        ).first()

    def get_active_profile(self, tenant_id: UUID) -> Optional[EsgScoringProfile]:
        return self.db.query(EsgScoringProfile).filter(
            EsgScoringProfile.tenant_id == tenant_id,
            EsgScoringProfile.is_active == True,
            EsgScoringProfile.is_deleted == False
        ).first()

    def create(self, profile: EsgScoringProfile) -> EsgScoringProfile:
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
