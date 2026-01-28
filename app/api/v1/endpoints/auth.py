from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.models import User, UserTenant
from app.schemas import auth as auth_schemas

router = APIRouter()

@router.post("/register", response_model=auth_schemas.Token)
def register(user_in: auth_schemas.UserCreate, db: Session = Depends(deps.get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this username already exists in the system.",
        )
    user = User(
        email=user_in.email,
        password_hash=security.get_password_hash(user_in.password),
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    access_token = security.create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=auth_schemas.Token)
def login(
    login_data: auth_schemas.UserLogin, 
    db: Session = Depends(deps.get_db)
):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = security.create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/select-tenant", response_model=auth_schemas.Token)
def select_tenant(
    tenant_id: str = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    association = db.query(UserTenant).filter(
        UserTenant.user_id == current_user.id,
        UserTenant.tenant_id == tenant_id
    ).first()
    
    if not association:
        raise HTTPException(status_code=403, detail="Not a member of this tenant")
        
    access_token = security.create_access_token(
        subject=current_user.id,
        tenant_id=tenant_id,
        role=association.role
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=auth_schemas.UserOut)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user
