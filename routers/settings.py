from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, UserRole, Workspace, SustainAiSettings
from app.schemas.schemas import SustainAiSettingsResponse, SustainAiSettingsUpdate
from app.services.audit_retention_service import AuditRetentionService

router = APIRouter(prefix="/settings", tags=["settings"])

def get_tenant_context(user_id: UUID, db: Session) -> UUID:
    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User does not belong to any organization"
        )
    return role.organization_id

@router.get("/ai", response_model=SustainAiSettingsResponse)
def get_ai_settings(
    workspace_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resolved_tenant_id = get_tenant_context(current_user.id, db)
    
    # Context security validation
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == resolved_tenant_id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings = db.query(SustainAiSettings).filter(
        SustainAiSettings.workspace_id == workspace_id
    ).first()

    if not settings:
        # Create default settings
        settings = SustainAiSettings(
            workspace_id=workspace_id,
            provider="ollama",
            model_name="qwen3:8b",
            quality_mode="balanced",
            prompt_style="sustainability_officer",
            response_style="executive",
            settings_version=1
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings

@router.put("/ai", response_model=SustainAiSettingsResponse)
def update_ai_settings(
    payload: SustainAiSettingsUpdate,
    workspace_id: UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resolved_tenant_id = get_tenant_context(current_user.id, db)
    
    # Context security validation
    ws = db.query(Workspace).filter(
        Workspace.id == workspace_id,
        Workspace.organization_id == resolved_tenant_id
    ).first()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    settings = db.query(SustainAiSettings).filter(
        SustainAiSettings.workspace_id == workspace_id
    ).first()

    if not settings:
        settings = SustainAiSettings(
            workspace_id=workspace_id,
            provider=payload.provider,
            model_name=payload.model_name,
            quality_mode=payload.quality_mode,
            prompt_style=payload.prompt_style,
            response_style=payload.response_style,
            settings_version=1
        )
        db.add(settings)
    else:
        settings.provider = payload.provider
        settings.model_name = payload.model_name
        settings.quality_mode = payload.quality_mode
        settings.prompt_style = payload.prompt_style
        settings.response_style = payload.response_style
        settings.settings_version = settings.settings_version + 1  # Increment version on edit

    db.commit()
    db.refresh(settings)
    return settings


from app.services.hardware_service import HardwareService

@router.get("/hardware")
def get_system_hardware(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Restrict to verified users
    get_tenant_context(current_user.id, db)
    
    hw = HardwareService.detect_hardware()
    health = HardwareService.get_provider_health()
    return {
        "hardware": hw,
        "health": health
    }

@router.get("/models")
def get_available_models(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    get_tenant_context(current_user.id, db)
    
    return {
        "installed_models": HardwareService.get_installed_models()
    }


@router.delete("/cleanup", summary="Run Audit Log Retention Cleanup")
def run_audit_cleanup(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger the 90-day audit log and AI copilot response retention sweep.
    Only accessible to authenticated users belonging to an organization.
    """
    # Restrict to verified workspace members only
    get_tenant_context(current_user.id, db)

    service = AuditRetentionService(db)
    result = service.run_all()
    return {
        "success": True,
        "data": result
    }
