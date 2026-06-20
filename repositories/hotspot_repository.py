from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from app.models.models import EmissionHotspot

class HotspotRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_analysis(self, analysis_id: UUID, tenant_id: UUID) -> List[EmissionHotspot]:
        return self.db.query(EmissionHotspot).filter(
            EmissionHotspot.analysis_id == analysis_id,
            EmissionHotspot.tenant_id == tenant_id
        ).all()

    def create(self, hotspot: EmissionHotspot) -> EmissionHotspot:
        self.db.add(hotspot)
        self.db.commit()
        self.db.refresh(hotspot)
        return hotspot
