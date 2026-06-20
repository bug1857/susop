from uuid import UUID
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.models import EmissionFactor, Organization

class EmissionFactorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, id: UUID, tenant_id: UUID) -> Optional[EmissionFactor]:
        return self.db.query(EmissionFactor).filter(
            EmissionFactor.id == id,
            EmissionFactor.tenant_id == tenant_id
        ).first()

    def get_by_activity(self, activity_name: str, tenant_id: UUID) -> Optional[EmissionFactor]:
        return self.db.query(EmissionFactor).filter(
            EmissionFactor.activity_name == activity_name,
            EmissionFactor.tenant_id == tenant_id
        ).first()

    def get_all(self, tenant_id: UUID) -> List[EmissionFactor]:
        return self.db.query(EmissionFactor).filter(
            EmissionFactor.tenant_id == tenant_id
        ).all()

    def create(self, factor: EmissionFactor) -> EmissionFactor:
        self.db.add(factor)
        self.db.commit()
        self.db.refresh(factor)
        return factor

    def resolve_factor(self, activity_name: str, tenant_id: UUID) -> Optional[EmissionFactor]:
        # 1. Priority 1: Tenant-specific factor
        factor = self.db.query(EmissionFactor).filter(
            EmissionFactor.activity_name == activity_name,
            EmissionFactor.tenant_id == tenant_id
        ).order_by(EmissionFactor.effective_date.desc()).first()
        if factor:
            return factor

        # 2. Priority 2: Global factor (Organization named "Global" or "System")
        global_org = self.db.query(Organization).filter(
            Organization.name.in_(["Global", "System"])
        ).first()
        if global_org:
            factor = self.db.query(EmissionFactor).filter(
                EmissionFactor.activity_name == activity_name,
                EmissionFactor.tenant_id == global_org.id
            ).order_by(EmissionFactor.effective_date.desc()).first()
            if factor:
                return factor

        # 3. Fallback: Return any default/available factor for this activity name
        factor = self.db.query(EmissionFactor).filter(
            EmissionFactor.activity_name == activity_name
        ).order_by(EmissionFactor.effective_date.desc()).first()
        
        return factor
