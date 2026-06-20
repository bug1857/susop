from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from app.core.database import get_db
from app.core.dependencies import get_current_user, RoleChecker
from app.core.audit import log_activity
from app.models.models import User, Organization, UserRole
from app.schemas.schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate, InviteMemberRequest, UserRoleResponse

router = APIRouter(prefix="/organizations", tags=["organizations"])

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
def create_org(payload: OrganizationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_org = Organization(name=payload.name)
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    
    # Assign creator as Admin
    creator_role = UserRole(
        user_id=current_user.id,
        organization_id=new_org.id,
        role="Admin"
    )
    db.add(creator_role)
    db.commit()
    
    log_activity(db, user_id=current_user.id, action="Organization Created", tenant_id=new_org.id, details=f"Org: {new_org.name}")
    return new_org

@router.get("/", response_model=list[OrganizationResponse])
def list_orgs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Returns only organizations the user belongs to
    orgs = db.query(Organization).join(UserRole).filter(UserRole.user_id == current_user.id).all()
    return orgs

@router.put("/{id}", response_model=OrganizationResponse)
def update_org(id: UUID, payload: OrganizationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Manager"]).check_org_role(id, current_user.id, db)
    org = db.query(Organization).filter(Organization.id == id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Resource not found")
    org.name = payload.name
    db.commit()
    db.refresh(org)
    return org

@router.get("/{id}/members", response_model=list[UserRoleResponse])
def list_members(id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Basic membership check
    RoleChecker(["Admin", "Manager", "Analyst", "Viewer"]).check_org_role(id, current_user.id, db)
    members = db.query(UserRole).filter(UserRole.organization_id == id).all()
    return members

@router.post("/{id}/invite", response_model=UserRoleResponse, status_code=status.HTTP_201_CREATED)
def invite_member(id: UUID, payload: InviteMemberRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    RoleChecker(["Admin", "Manager"]).check_org_role(id, current_user.id, db)
    
    # Check if user exists, if not create a placeholder user
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Create placeholder with blank password hash
        user = User(email=payload.email, hashed_password="")
        db.add(user)
        db.commit()
        db.refresh(user)
        
    # Check if already a member of organization
    existing_role = db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.organization_id == id).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="User is already a member of this organization")
        
    new_role = UserRole(
        user_id=user.id,
        organization_id=id,
        role=payload.role
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    
    log_activity(db, user_id=current_user.id, action="Member Invited", tenant_id=id, details=f"Invited: {payload.email} as {payload.role}")
    return new_role
