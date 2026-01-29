from fastapi import APIRouter, Depends, HTTPException, Body, Request
from sqlalchemy.orm import Session
from app.api import deps
from app.core import security
from app.core.limiter import limiter
from app.models import User, UserTenant
from app.schemas import auth as auth_schemas

router = APIRouter()

from datetime import datetime, timedelta
from app.models.user import User, RefreshToken

@router.post("/register", response_model=auth_schemas.Token)
@limiter.limit("5/minute")
def register(request: Request, user_in: auth_schemas.UserCreate, db: Session = Depends(deps.get_db)):
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
    refresh_token_val = security.create_refresh_token()
    
    # Store refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_val,
        expires_at=datetime.utcnow() + timedelta(days=security.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_refresh)
    db.commit()

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token_val,
        "token_type": "bearer"
    }

@router.post("/login", response_model=auth_schemas.Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    login_data: auth_schemas.UserLogin, 
    db: Session = Depends(deps.get_db)
):
    user = db.query(User).filter(User.email == login_data.email, User.is_deleted == False).first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = security.create_access_token(subject=user.id)
    refresh_token_val = security.create_refresh_token()
    
    # Store refresh token
    db_refresh = RefreshToken(
        user_id=user.id,
        token=refresh_token_val,
        expires_at=datetime.utcnow() + timedelta(days=security.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    db.add(db_refresh)
    db.commit()

    return {
        "access_token": access_token, 
        "refresh_token": refresh_token_val,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=auth_schemas.Token)
def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db)
):
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()
    
    if not db_token:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
        
    access_token = security.create_access_token(subject=db_token.user_id)
    # Rotate refresh token (optional but recommended)
    new_refresh_val = security.create_refresh_token()
    db_token.token = new_refresh_val
    db_token.expires_at = datetime.utcnow() + timedelta(days=security.REFRESH_TOKEN_EXPIRE_DAYS)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_val,
        "token_type": "bearer"
    }

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
    # Return same refresh token or issue a new one?
    # Usually refresh tokens are session-bound, not tenant-bound.
    # We'll just return a success, but select-tenant currently returns a full Token.
    # To avoid breaking changes in Flutter, we'll need to return a refresh token here too if requested.
    
    # Find existing refresh token for this user
    db_token = db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False
    ).order_by(RefreshToken.created_at.desc()).first()
    
    refresh_val = db_token.token if db_token else "MISSING"

    return {
        "access_token": access_token, 
        "refresh_token": refresh_val,
        "token_type": "bearer"
    }

@router.get("/me", response_model=auth_schemas.UserOut)
def read_users_me(current_user: User = Depends(deps.get_current_active_user)):
    return current_user
