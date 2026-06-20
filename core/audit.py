from sqlalchemy.orm import Session
from uuid import UUID
from app.models.models import AuditLog

# Registered Audit Event Action Types for Sprint 4:
# - "reference_model_uploaded"
# - "conformance_started"
# - "conformance_completed"
# - "deviation_detected"
# - "carbon_attribution_completed"
# - "carbon_fitness_calculated"


def log_activity(db: Session, user_id: UUID, action: str, tenant_id: UUID = None, details: str = None):
    audit = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(audit)
    db.commit()
