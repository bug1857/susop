from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.models.models import User, AuditLog
from app.schemas.schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/", response_model=list[AuditLogResponse])
def list_audit_logs(organization_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Requires Admin or Manager to inspect logs
    RoleChecker(["Admin", "Manager"]).check_org_role(organization_id, current_user.id, db)
    
    logs = db.query(AuditLog).filter(
        AuditLog.tenant_id == organization_id
    ).order_by(AuditLog.created_at.desc()).all()
    
    return logs
