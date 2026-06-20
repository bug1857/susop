from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.models.models import (
    User, UserRole, EsgKpiDefinition, EsgKpiValue, EsgFramework, 
    FrameworkMapping, EsgScoringProfile, EsgScore, EsgEvidence, Workspace, Project
)
from app.schemas.schemas import (
    EsgKpiDefinitionCreate,
    EsgKpiDefinitionResponseEnvelope,
    EsgKpiDefinitionListResponseEnvelope,
    EsgKpiValueCreate,
    EsgKpiValueResponseEnvelope,
    EsgKpiValueListResponseEnvelope,
    EsgScoringProfileCreate,
    EsgScoringProfileResponseEnvelope,
    EsgScoringProfileListResponseEnvelope,
    EsgScoreResponseEnvelope,
    EsgScoreListResponseEnvelope,
    EsgEvidenceResponseEnvelope,
    EsgEvidenceListResponseEnvelope,
    FrameworkMappingListResponseEnvelope,
    EsgFrameworkResponseEnvelope,
    EsgFrameworkListResponseEnvelope
)
from app.services.esg_kpi_service import EsgKpiService
from app.services.esg_scoring_service import EsgScoringService
from app.services.esg_evidence_service import EsgEvidenceService
from app.services.esg_framework_service import EsgFrameworkService

router = APIRouter(prefix="/esg", tags=["esg"])

# Request Schema for triggering ESG calculation
class EsgCalculateRequest(BaseModel):
    workspace_id: UUID
    period: str
    tenant_id: Optional[UUID] = None

def wrap_http_exception(he: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=he.status_code,
        content={
            "success": False,
            "data": None,
            "metadata": None,
            "errors": [{"code": "HTTP_ERROR", "message": he.detail}]
        }
    )

def wrap_unexpected_exception(e: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "metadata": None,
            "errors": [{"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred."}]
        }
    )

def get_tenant_context(user_id: UUID, db: Session, tenant_id: Optional[UUID] = None) -> UUID:
    if tenant_id:
        role = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == tenant_id
        ).first()
        if not role:
            # Enforce anti-enumeration check
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
        return tenant_id

    role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="User does not belong to any organization"
        )
    return role.organization_id

# ==========================================
# 1. KPI APIs
# ==========================================

@router.post("/kpis", response_model=EsgKpiDefinitionResponseEnvelope, status_code=status.HTTP_201_CREATED)
def create_kpi_definition(
    payload: EsgKpiDefinitionCreate, 
    tenant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        kpi_service = EsgKpiService(db)
        res = kpi_service.create_kpi_definition(resolved_tenant_id, current_user.id, payload.dict())
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/kpis", response_model=EsgKpiDefinitionListResponseEnvelope)
def list_kpi_definitions(
    tenant_id: Optional[UUID] = Query(None),
    category: Optional[str] = Query(None),
    active: Optional[bool] = Query(None),
    kpi_code: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        query = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.tenant_id == resolved_tenant_id,
            EsgKpiDefinition.is_deleted == False
        )
        if category:
            query = query.filter(EsgKpiDefinition.category == category)
        if active is not None:
            query = query.filter(EsgKpiDefinition.is_active == active)
        if kpi_code:
            query = query.filter(EsgKpiDefinition.kpi_code == kpi_code)
            
        safe_sort_fields = {"kpi_code", "name", "category", "version", "created_at"}
        if sort_by not in safe_sort_fields:
            sort_by = "created_at"
        sort_col = getattr(EsgKpiDefinition, sort_by, EsgKpiDefinition.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())
            
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        log_activity(db, current_user.id, "Framework mapping viewed", resolved_tenant_id, "Listed ESG KPI definitions")
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/kpis/{id}", response_model=EsgKpiDefinitionResponseEnvelope)
def retrieve_kpi_definition(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        definition = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.id == id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not definition:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == definition.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(definition.tenant_id, current_user.id, db)
        
        log_activity(db, current_user.id, "Framework mapping viewed", definition.tenant_id, f"Viewed KPI: {definition.kpi_code}")
        return {
            "success": True,
            "data": definition,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/kpis/{id}/versions", response_model=EsgKpiDefinitionListResponseEnvelope)
def retrieve_kpi_versions(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        definition = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.id == id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not definition:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == definition.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(definition.tenant_id, current_user.id, db)
        
        kpi_service = EsgKpiService(db)
        versions = kpi_service.retrieve_versions(definition.kpi_code, definition.tenant_id)
        
        return {
            "success": True,
            "data": versions,
            "metadata": {"total": len(versions)},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.put("/kpis/{id}", response_model=EsgKpiDefinitionResponseEnvelope)
def update_kpi_definition(
    id: UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        definition = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.id == id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not definition:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == definition.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        RoleChecker(["Admin", "Manager", "Analyst"]).check_org_role(definition.tenant_id, current_user.id, db)
        
        kpi_service = EsgKpiService(db)
        res = kpi_service.update_kpi_definition(id, definition.tenant_id, current_user.id, payload)
        
        log_activity(db, current_user.id, "KPI updated", definition.tenant_id, f"Updated KPI: {definition.kpi_code}")
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

# ==========================================
# 2. KPI VALUE APIs
# ==========================================

@router.post("/kpi-values", response_model=EsgKpiValueResponseEnvelope, status_code=status.HTTP_201_CREATED)
def create_kpi_value(
    payload: EsgKpiValueCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Resolve tenant context from workspace
        workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        tenant_id = workspace.organization_id
        
        # Check permissions for workspace & project
        RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(payload.workspace_id, current_user.id, db)
        if payload.project_id:
            project = db.query(Project).filter(Project.id == payload.project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            if project.workspace_id != payload.workspace_id:
                raise HTTPException(status_code=400, detail="Project context mismatch")
            RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(payload.project_id, current_user.id, db)
            
        # Verify KPI Definition exists and belongs to the tenant
        kpi_def = db.query(EsgKpiDefinition).filter(
            EsgKpiDefinition.id == payload.kpi_definition_id,
            EsgKpiDefinition.tenant_id == tenant_id,
            EsgKpiDefinition.is_deleted == False
        ).first()
        if not kpi_def:
            raise HTTPException(status_code=404, detail="KPI definition not found")
            
        kpi_service = EsgKpiService(db)
        res = kpi_service.record_kpi_value(tenant_id, current_user.id, payload.dict())
        
        log_activity(db, current_user.id, "KPI value recorded", tenant_id, f"Recorded KPI Value: {payload.value} for {kpi_def.kpi_code}")
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/kpi-values", response_model=EsgKpiValueListResponseEnvelope)
def list_kpi_values(
    tenant_id: Optional[UUID] = Query(None),
    workspace_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    period: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("calculated_at"),
    sort_order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = tenant_id
        if workspace_id:
            workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
            if not workspace:
                raise HTTPException(status_code=404, detail="Workspace not found")
            if resolved_tenant_id and resolved_tenant_id != workspace.organization_id:
                raise HTTPException(status_code=400, detail="Tenant context mismatch")
            resolved_tenant_id = workspace.organization_id
            RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
            
        if project_id:
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_project_role(project_id, current_user.id, db)
            
        resolved_tenant_id = get_tenant_context(current_user.id, db, resolved_tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        query = db.query(EsgKpiValue).filter(
            EsgKpiValue.tenant_id == resolved_tenant_id,
            EsgKpiValue.is_deleted == False
        )
        if workspace_id:
            query = query.filter(EsgKpiValue.workspace_id == workspace_id)
        if project_id:
            query = query.filter(EsgKpiValue.project_id == project_id)
        if period:
            query = query.filter(EsgKpiValue.period == period)
            
        safe_sort_fields = {"calculated_at", "period", "value"}
        if sort_by not in safe_sort_fields:
            sort_by = "calculated_at"
        sort_col = getattr(EsgKpiValue, sort_by, EsgKpiValue.calculated_at)
        if sort_order == "desc":
            query = query.order_by(sort_col.desc())
        else:
            query = query.order_by(sort_col.asc())
            
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

# ==========================================
# 3. ESG SCORE APIs
# ==========================================

@router.post("/calculate", response_model=EsgScoreResponseEnvelope)
def calculate_esg_score(
    payload: EsgCalculateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Verify workspace context
        workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        tenant_id = workspace.organization_id
        if payload.tenant_id and payload.tenant_id != tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context mismatch")
            
        RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(payload.workspace_id, current_user.id, db)
        
        scoring_service = EsgScoringService(db)
        res = scoring_service.calculate_esg_score(payload.workspace_id, payload.period, tenant_id, current_user.id)
        
        # log_activity inside calculate_esg_score will handle audit log, but we can do extra here
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/scores", response_model=EsgScoreListResponseEnvelope)
def list_esg_scores(
    workspace_id: UUID,
    period: Optional[str] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
        
        query = db.query(EsgScore).filter(
            EsgScore.workspace_id == workspace_id,
            EsgScore.is_deleted == False
        )
        if period:
            query = query.filter(EsgScore.period == period)
            
        query = query.order_by(EsgScore.calculated_at.desc())
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/scores/{id}", response_model=EsgScoreResponseEnvelope)
def retrieve_esg_score(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        score = db.query(EsgScore).filter(
            EsgScore.id == id,
            EsgScore.is_deleted == False
        ).first()
        if not score:
            raise HTTPException(status_code=404, detail="Score details not found")
            
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == score.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Score details not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(score.tenant_id, current_user.id, db)
        
        return {
            "success": True,
            "data": score,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

# ==========================================
# 4. FRAMEWORK APIs
# ==========================================

@router.get("/frameworks", response_model=EsgFrameworkListResponseEnvelope)
def list_frameworks(
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Frameworks are global resources, only require authentication
        query = db.query(EsgFramework).filter(EsgFramework.is_deleted == False)
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        # Auditing framework mappings viewed
        log_activity(db, current_user.id, "Framework mapping viewed", None, "Listed ESG frameworks")
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/frameworks/{id}", response_model=EsgFrameworkResponseEnvelope)
def retrieve_framework(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        framework = db.query(EsgFramework).filter(
            EsgFramework.id == id,
            EsgFramework.is_deleted == False
        ).first()
        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")
            
        log_activity(db, current_user.id, "Framework mapping viewed", None, f"Viewed ESG framework details: {framework.framework_name}")
        return {
            "success": True,
            "data": framework,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/frameworks/{id}/mappings", response_model=FrameworkMappingListResponseEnvelope)
def retrieve_framework_mappings(
    id: UUID,
    tenant_id: Optional[UUID] = Query(None),
    limit: int = Query(20),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        if offset < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Offset cannot be negative")
        if limit < 1:
            limit = 1
        if limit > 100:
            limit = 100

        framework = db.query(EsgFramework).filter(
            EsgFramework.id == id,
            EsgFramework.is_deleted == False
        ).first()
        if not framework:
            raise HTTPException(status_code=404, detail="Framework not found")
            
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        # Mappings returned are filtered by the tenant's KPI definitions
        query = db.query(FrameworkMapping).join(
            EsgKpiDefinition, FrameworkMapping.kpi_definition_id == EsgKpiDefinition.id
        ).filter(
            FrameworkMapping.framework_id == id,
            FrameworkMapping.is_deleted == False,
            EsgKpiDefinition.tenant_id == resolved_tenant_id,
            EsgKpiDefinition.is_deleted == False
        )
        
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        log_activity(db, current_user.id, "Framework mapping viewed", resolved_tenant_id, f"Viewed mappings for framework: {framework.framework_name}")
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

# ==========================================
# 5. EVIDENCE APIs
# ==========================================

@router.get("/evidence", response_model=EsgEvidenceListResponseEnvelope)
def list_evidence(
    kpi_value_id: Optional[UUID] = Query(None),
    tenant_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = tenant_id
        if kpi_value_id:
            val = db.query(EsgKpiValue).filter(
                EsgKpiValue.id == kpi_value_id,
                EsgKpiValue.is_deleted == False
            ).first()
            if not val:
                raise HTTPException(status_code=404, detail="KPI value not found")
                
            role_record = db.query(UserRole).filter(
                UserRole.user_id == current_user.id,
                UserRole.organization_id == val.tenant_id
            ).first()
            if not role_record:
                raise HTTPException(status_code=404, detail="KPI value not found")
            resolved_tenant_id = val.tenant_id
            
        resolved_tenant_id = get_tenant_context(current_user.id, db, resolved_tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        query = db.query(EsgEvidence).filter(
            EsgEvidence.tenant_id == resolved_tenant_id,
            EsgEvidence.is_deleted == False
        )
        if kpi_value_id:
            query = query.filter(EsgEvidence.kpi_value_id == kpi_value_id)
            
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        log_activity(db, current_user.id, "Evidence accessed", resolved_tenant_id, "Accessed ESG evidence records list")
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/evidence/{id}", response_model=EsgEvidenceResponseEnvelope)
def retrieve_evidence(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        evidence = db.query(EsgEvidence).filter(
            EsgEvidence.id == id,
            EsgEvidence.is_deleted == False
        ).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
            
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == evidence.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Evidence not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(evidence.tenant_id, current_user.id, db)
        
        log_activity(db, current_user.id, "Evidence accessed", evidence.tenant_id, f"Accessed evidence record details: {evidence.id}")
        return {
            "success": True,
            "data": evidence,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/evidence/{id}/lineage")
def retrieve_evidence_lineage(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        evidence = db.query(EsgEvidence).filter(
            EsgEvidence.id == id,
            EsgEvidence.is_deleted == False
        ).first()
        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")
            
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == evidence.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Evidence not found")
            
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(evidence.tenant_id, current_user.id, db)
        
        log_activity(db, current_user.id, "Evidence accessed", evidence.tenant_id, f"Accessed evidence lineage: {evidence.id}")
        return {
            "success": True,
            "data": {
                "kpi_value_id": str(evidence.kpi_value_id),
                "lineage_path": evidence.lineage_path,
                "source_entity_type": evidence.source_entity_type,
                "source_entity_id": str(evidence.source_entity_id) if evidence.source_entity_id else None
            },
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/evidence/kpi-value/{kpi_value_id}/lineage")
def retrieve_evidence_lineage_by_kpi(
    kpi_value_id: UUID,
    tenant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        val = db.query(EsgKpiValue).filter(
            EsgKpiValue.id == kpi_value_id,
            EsgKpiValue.is_deleted == False
        ).first()
        if not val:
            raise HTTPException(status_code=404, detail="KPI value not found")
            
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == val.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="KPI value not found")
            
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id or val.tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        evidence_service = EsgEvidenceService(db)
        res = evidence_service.get_lineage_path(kpi_value_id, resolved_tenant_id)
        
        log_activity(db, current_user.id, "Evidence accessed", resolved_tenant_id, f"Accessed evidence lineage for KPI value: {kpi_value_id}")
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

# ==========================================
# Extra: Scoring Profile Configuration APIs
# ==========================================

@router.post("/scoring-profiles", response_model=EsgScoringProfileResponseEnvelope, status_code=status.HTTP_201_CREATED)
def configure_scoring_profile(
    payload: EsgScoringProfileCreate,
    tenant_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id)
        RoleChecker(["Admin", "Manager"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        scoring_service = EsgScoringService(db)
        res = scoring_service.configure_scoring_profile(resolved_tenant_id, current_user.id, payload.dict())
        return {
            "success": True,
            "data": res,
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)

@router.get("/scoring-profiles", response_model=EsgScoringProfileListResponseEnvelope)
def list_scoring_profiles(
    tenant_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        resolved_tenant_id = get_tenant_context(current_user.id, db, tenant_id)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(resolved_tenant_id, current_user.id, db)
        
        query = db.query(EsgScoringProfile).filter(
            EsgScoringProfile.tenant_id == resolved_tenant_id,
            EsgScoringProfile.is_deleted == False
        )
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": results,
            "metadata": {"total": total, "limit": limit, "offset": offset},
            "errors": []
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)
