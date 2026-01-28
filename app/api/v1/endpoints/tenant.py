from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Tenant, UserTenant, User
from app.schemas import tenant as tenant_schemas

router = APIRouter()

@router.post("/create", response_model=tenant_schemas.TenantResponse)
def create_tenant(
    tenant_in: tenant_schemas.TenantCreate,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    # Create Tenant
    tenant = Tenant(name=tenant_in.name, business_type=tenant_in.business_type)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    # Associate User as OWNER
    association = UserTenant(
        user_id=current_user.id,
        tenant_id=tenant.id,
        role="OWNER" 
    )
    db.add(association)
    db.commit()
    
    return tenant

@router.get("/my", response_model=List[tenant_schemas.TenantResponse])
def read_my_tenants(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(deps.get_db)
):
    # Join Tenant and UserTenant
    tenants = db.query(Tenant).join(UserTenant).filter(UserTenant.user_id == current_user.id).all()
    return tenants
