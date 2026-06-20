from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User, UserRole, Workspace, Project

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = decode_access_token(token)
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

class RoleChecker:
    def __init__(self, required_roles: list[str]):
        self.required_roles = required_roles

    def check_org_role(self, org_id: UUID, user_id: UUID, db: Session) -> str:
        role_record = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == org_id
        ).first()
        if not role_record:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not a member of this organization"
            )
        if role_record.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires roles: {self.required_roles}"
            )
        return role_record.role

    def check_workspace_role(self, workspace_id: UUID, user_id: UUID, db: Session) -> str:
        workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        # Anti-enumeration check
        role_record = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == workspace.organization_id
        ).first()
        if not role_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found"
            )
        if role_record.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires roles: {self.required_roles}"
            )
        return role_record.role

    def check_project_role(self, project_id: UUID, user_id: UUID, db: Session) -> str:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        # Anti-enumeration check
        workspace = db.query(Workspace).filter(Workspace.id == project.workspace_id).first()
        if not workspace:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        role_record = db.query(UserRole).filter(
            UserRole.user_id == user_id,
            UserRole.organization_id == workspace.organization_id
        ).first()
        if not role_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        if role_record.role not in self.required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Action requires roles: {self.required_roles}"
            )
        return role_record.role
