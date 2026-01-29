from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core import database, security
from app.schemas.auth import TokenPayload
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_db() -> Generator:
    try:
        db = database.SessionLocal()
        yield db
    finally:
        db.close()

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenPayload(**payload)
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == token_data.sub, User.is_deleted == False).first()
    if user is None:
        raise credentials_exception
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_current_token_payload(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, token_payload: TokenPayload = Depends(get_current_token_payload)):
        if token_payload.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The user doesn't have enough privileges",
            )
        return token_payload

class SubscriptionChecker:
    def __init__(self, required_module: str = None):
        self.required_module = required_module

    def __call__(
        self, 
        token_payload: TokenPayload = Depends(get_current_token_payload),
        db: Session = Depends(get_db)
    ):
        from app.models.subscription import TenantSubscription, SubscriptionPlan
        import json
        
        tenant_id = token_payload.tenant_id
        if not tenant_id:
            raise HTTPException(status_code=400, detail="Tenant context missing")
            
        sub = db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.status == "ACTIVE"
        ).first()
        
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Active subscription required"
            )
            
        # Check expiry
        import datetime
        if sub.end_date and sub.end_date < datetime.datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Subscription expired"
            )
            
        # Check module access
        if self.required_module:
            plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
            if not plan:
                 raise HTTPException(status_code=500, detail="Subscription plan not found")
                 
            try:
                allowed_modules = json.loads(plan.modules_allowed)
                if self.required_module not in allowed_modules:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Module '{self.required_module}' not included in your current plan. Upgrade required."
                    )
            except Exception:
                 raise HTTPException(status_code=500, detail="Error parsing plan modules")
                 
        return sub
