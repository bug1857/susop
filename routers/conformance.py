from fastapi import APIRouter, Depends, status, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from uuid import UUID, uuid4
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.schemas.schemas import (
    ReferenceModelCreate,
    ReferenceModelUpdate,
    ReferenceModelResponseEnvelope,
    ReferenceModelListResponseEnvelope,
    StandardSuccessEnvelope
)
from app.models.models import User, ReferenceModel, Workspace, Project, UserRole

router = APIRouter(prefix="/conformance", tags=["conformance"])

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

@router.post("/reference-models", response_model=ReferenceModelResponseEnvelope, status_code=status.HTTP_201_CREATED)
def upload_reference_model(
    payload: ReferenceModelCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Enforce active workspace role checks (Requires Admin, Manager, or Analyst)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(payload.workspace_id, current_user.id, db)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(payload.project_id, current_user.id, db)
        
        # Verify workspace
        workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        # Verify project belongs to workspace
        project = db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.workspace_id != payload.workspace_id:
            raise HTTPException(status_code=400, detail="Project does not belong to the workspace")
            
        tenant_id = workspace.organization_id
        
        # Lineage and Versioning
        version = 1
        if payload.parent_model_id:
            parent_model = db.query(ReferenceModel).filter(
                ReferenceModel.id == payload.parent_model_id,
                ReferenceModel.tenant_id == tenant_id
            ).first()
            if not parent_model:
                raise HTTPException(status_code=404, detail="Parent reference model not found")
            if parent_model.workspace_id != payload.workspace_id or parent_model.project_id != payload.project_id:
                raise HTTPException(status_code=400, detail="Parent reference model context mismatch")
            version = parent_model.version + 1
            
        new_model = ReferenceModel(
            id=uuid4(),
            tenant_id=tenant_id,
            workspace_id=payload.workspace_id,
            project_id=payload.project_id,
            model_name=payload.model_name,
            version=version,
            parent_model_id=payload.parent_model_id,
            status="active",
            model_definition=payload.model_definition,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        
        # Trigger Audit Log
        log_activity(
            db,
            user_id=current_user.id,
            action="reference_model_uploaded",
            tenant_id=tenant_id,
            details=f"Uploaded reference model '{payload.model_name}' (Version {version}) for project {payload.project_id}"
        )
        
        return {
            "success": True,
            "data": new_model,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/reference-models", response_model=ReferenceModelListResponseEnvelope)
def list_reference_models(
    workspace_id: UUID = Query(..., description="Scope to specific workspace"),
    project_id: Optional[UUID] = Query(None, description="Scope to specific project"),
    limit: int = Query(10, ge=1, le=100, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort direction"),
    start_date: Optional[datetime] = Query(None, description="Start date filtering"),
    end_date: Optional[datetime] = Query(None, description="End date filtering"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate workspace access role
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
        
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(status_code=404, detail="Workspace not found")
            
        tenant_id = workspace.organization_id
        
        query = db.query(ReferenceModel).filter(
            ReferenceModel.tenant_id == tenant_id,
            ReferenceModel.workspace_id == workspace_id
        )
        
        if project_id:
            # Validate project access role and context
            RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_project_role(project_id, current_user.id, db)
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(status_code=404, detail="Project not found")
            if project.workspace_id != workspace_id:
                raise HTTPException(status_code=400, detail="Project does not belong to the workspace")
            query = query.filter(ReferenceModel.project_id == project_id)
            
        # Date filtering
        if start_date:
            query = query.filter(ReferenceModel.created_at >= start_date)
        if end_date:
            query = query.filter(ReferenceModel.created_at <= end_date)
            
        # Total count before limit/offset
        total_count = query.count()
        
        # Sorting column determination
        if sort_by == "model_name":
            sort_col = ReferenceModel.model_name
        elif sort_by == "version":
            sort_col = ReferenceModel.version
        else:
            sort_col = ReferenceModel.created_at
            
        if sort_order.lower() == "asc":
            query = query.order_by(sort_col.asc())
        else:
            query = query.order_by(sort_col.desc())
            
        models = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": models,
            "metadata": {
                "limit": limit,
                "offset": offset,
                "total": total_count,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.get("/reference-models/{id}", response_model=ReferenceModelResponseEnvelope)
def get_reference_model(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Fetch the model first
        model = db.query(ReferenceModel).filter(ReferenceModel.id == id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Reference model not found")

        # Verify tenant isolation (prevent UUID probing)
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == model.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Reference model not found")
            
        # Verify access role to workspace/project
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(model.workspace_id, current_user.id, db)
        RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_project_role(model.project_id, current_user.id, db)
        
        # Verify tenant isolation
        workspace = db.query(Workspace).filter(Workspace.id == model.workspace_id).first()
        if not workspace or model.tenant_id != workspace.organization_id:
            raise HTTPException(status_code=403, detail="Tenant access denied")
            
        return {
            "success": True,
            "data": model,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.put("/reference-models/{id}", response_model=ReferenceModelResponseEnvelope)
def update_reference_model(
    id: UUID,
    payload: ReferenceModelUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Fetch the model
        model = db.query(ReferenceModel).filter(ReferenceModel.id == id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Reference model not found")

        # Verify tenant isolation (prevent UUID probing)
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == model.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Reference model not found")
            
        # Verify write roles
        RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(model.workspace_id, current_user.id, db)
        RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(model.project_id, current_user.id, db)
        
        # Verify tenant isolation
        workspace = db.query(Workspace).filter(Workspace.id == model.workspace_id).first()
        if not workspace or model.tenant_id != workspace.organization_id:
            raise HTTPException(status_code=403, detail="Tenant access denied")
            
        # Apply updates
        if payload.model_name is not None:
            model.model_name = payload.model_name
        if payload.model_definition is not None:
            model.model_definition = payload.model_definition
        if payload.status is not None:
            model.status = payload.status
            
        db.commit()
        db.refresh(model)
        
        # Trigger Audit Log
        log_activity(
            db,
            user_id=current_user.id,
            action="reference_model_updated",
            tenant_id=model.tenant_id,
            details=f"Updated reference model '{model.model_name}' (ID: {id})"
        )
        
        return {
            "success": True,
            "data": model,
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)


@router.delete("/reference-models/{id}", response_model=StandardSuccessEnvelope)
def delete_reference_model(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Fetch the model
        model = db.query(ReferenceModel).filter(ReferenceModel.id == id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Reference model not found")

        # Verify tenant isolation (prevent UUID probing)
        role_record = db.query(UserRole).filter(
            UserRole.user_id == current_user.id,
            UserRole.organization_id == model.tenant_id
        ).first()
        if not role_record:
            raise HTTPException(status_code=404, detail="Reference model not found")
            
        # Verify write roles
        RoleChecker(["Admin", "Manager"]).check_workspace_role(model.workspace_id, current_user.id, db)
        RoleChecker(["Admin", "Manager"]).check_project_role(model.project_id, current_user.id, db)
        
        # Verify tenant isolation
        workspace = db.query(Workspace).filter(Workspace.id == model.workspace_id).first()
        if not workspace or model.tenant_id != workspace.organization_id:
            raise HTTPException(status_code=403, detail="Tenant access denied")
            
        tenant_id = model.tenant_id
        model_name = model.model_name
        
        # Perform deletion
        db.delete(model)
        db.commit()
        
        # Trigger Audit Log
        log_activity(
            db,
            user_id=current_user.id,
            action="reference_model_deleted",
            tenant_id=tenant_id,
            details=f"Deleted reference model '{model_name}' (ID: {id})"
        )
        
        return {
            "success": True,
            "data": {"message": "Reference model deleted successfully", "id": str(id)},
            "metadata": None,
            "errors": None
        }
    except HTTPException as he:
        return wrap_http_exception(he)
    except Exception as e:
        return wrap_unexpected_exception(e)
