from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import CarbonAttribution

class CarbonAttributionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[CarbonAttribution]:
        return self.db.query(CarbonAttribution).filter(
            CarbonAttribution.analysis_id == analysis_id,
            CarbonAttribution.tenant_id == tenant_id
        ).all()

    def create(self, attribution: CarbonAttribution) -> CarbonAttribution:
        self.db.add(attribution)
        self.db.commit()
        self.db.refresh(attribution)
        return attribution

    def create_all(self, attributions: List[CarbonAttribution]) -> List[CarbonAttribution]:
        self.db.add_all(attributions)
        self.db.commit()
        return attributions

