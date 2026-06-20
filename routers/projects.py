from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.models.models import User, Project, Workspace
from app.schemas.schemas import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Requires Admin, Manager, or Analyst to create a project
    role = RoleChecker(["Admin", "Manager", "Analyst"]).check_workspace_role(payload.workspace_id, current_user.id, db)
    
    workspace = db.query(Workspace).filter(Workspace.id == payload.workspace_id).first()
    
    new_project = Project(
        workspace_id=payload.workspace_id,
        name=payload.name,
        description=payload.description
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    log_activity(db, user_id=current_user.id, action="Project Created", tenant_id=workspace.organization_id, details=f"Project: {new_project.name}")
    return new_project

@router.get("/", response_model=list[ProjectResponse])
def list_projects(workspace_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_workspace_role(workspace_id, current_user.id, db)
    projects = db.query(Project).filter(Project.workspace_id == workspace_id).all()
    return projects

@router.put("/{id}", response_model=ProjectResponse)
def update_project(id: UUID, payload: ProjectUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Requires Admin, Manager, or Analyst to update/archive a project
    RoleChecker(["Admin", "Manager", "Analyst"]).check_project_role(id, current_user.id, db)
    
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if payload.name is not None:
        project.name = payload.name
    if payload.description is not None:
        project.description = payload.description
    if payload.is_archived is not None:
        project.is_archived = payload.is_archived
        
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_project(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Requires Admin or Manager to delete a project
    RoleChecker(["Admin", "Manager"]).check_project_role(id, current_user.id, db)
    
    project = db.query(Project).filter(Project.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    db.delete(project)
    db.commit()
    return {"message": "Project deleted successfully"}
