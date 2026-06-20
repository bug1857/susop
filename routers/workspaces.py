from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.models.models import User, Workspace
from app.schemas.schemas import WorkspaceCreate, WorkspaceResponse, WorkspaceUpdate

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(payload: WorkspaceCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Manager"]).check_org_role(payload.organization_id, current_user.id, db)
    
    new_workspace = Workspace(
        organization_id=payload.organization_id,
        name=payload.name
    )
    db.add(new_workspace)
    db.commit()
    db.refresh(new_workspace)
    
    log_activity(db, user_id=current_user.id, action="Workspace Created", tenant_id=payload.organization_id, details=f"Workspace: {new_workspace.name}")
    return new_workspace

@router.get("/", response_model=list[WorkspaceResponse])
def list_workspaces(organization_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(organization_id, current_user.id, db)
    workspaces = db.query(Workspace).filter(Workspace.organization_id == organization_id).all()
    return workspaces

@router.put("/{id}", response_model=WorkspaceResponse)
def update_workspace(id: UUID, payload: WorkspaceUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check permissions based on the workspace's organization context
    RoleChecker(["Admin", "Manager"]).check_workspace_role(id, current_user.id, db)
    
    workspace = db.query(Workspace).filter(Workspace.id == id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    workspace.name = payload.name
    db.commit()
    db.refresh(workspace)
    return workspace
