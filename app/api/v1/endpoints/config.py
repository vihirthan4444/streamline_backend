from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Tenant, Module, TenantModule, Theme, User
from app.schemas import config as config_schemas

router = APIRouter()

@router.get("/my-modules", response_model=List[config_schemas.TenantModuleResponse])
def get_my_modules(
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")
        
    # Get all potential modules and check if enabled for tenant
    # For now, just return what is explicitly enabled in TenantModule
    # If no TenantModule entry exists, assume disabled.
    
    tenant_modules = db.query(TenantModule).filter(TenantModule.tenant_id == tenant_id).all()
    
    # Also fetch all available system modules to return full list with enabled status?
    # User requirement: "Backend endpoint ... [ {code: POS, enabled: true} ]"
    
    all_modules = db.query(Module).all()
    enabled_map = {tm.module_id: tm.enabled for tm in tenant_modules}
    
    result = []
    for mod in all_modules:
        is_enabled = enabled_map.get(mod.id, False) # Default to false if not linked
        result.append(config_schemas.TenantModuleResponse(
            code=mod.code,
            name=mod.name,
            enabled=is_enabled
        ))
        
    return result

@router.get("/theme", response_model=config_schemas.Theme)
def get_tenant_theme(
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID not found in token")
        
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
        
    if not tenant.theme_id:
        # Return default theme if none set
        default_theme = db.query(Theme).filter(Theme.name == "Default").first()
        if default_theme:
            return default_theme
        
        # Fallback hardcoded if DB is empty of themes
        return config_schemas.Theme(
            id="default",
            name="Default",
            properties={
                "primaryColor": "#2196F3",
                "secondaryColor": "#BBDEFB",
                "fontFamily": "Roboto",
                "logoUrl": "https://placehold.co/200x200.png"
            }
        )

    theme = db.query(Theme).filter(Theme.id == tenant.theme_id).first()
    if not theme:
         raise HTTPException(status_code=404, detail="Theme not found")
         
    return theme

@router.post("/seed-defaults")
def seed_defaults(db: Session = Depends(deps.get_db)):
    # 1. Seed Modules
    modules_data = [
        {"code": "POS", "name": "Point of Sale"},
        {"code": "SALON", "name": "Salon Booking"},
        {"code": "INVENTORY", "name": "Inventory Management"},
        {"code": "HR", "name": "Human Resources"}
    ]
    
    for md in modules_data:
        existing = db.query(Module).filter(Module.code == md["code"]).first()
        if not existing:
            db.add(Module(code=md["code"], name=md["name"]))
    
    # 2. Seed Default Theme
    existing_theme = db.query(Theme).filter(Theme.name == "Default").first()
    if not existing_theme:
        db.add(Theme(
            name="Default",
            properties={
                "primaryColor": "#6200EE",
                "secondaryColor": "#03DAC6",
                "fontFamily": "Roboto",
                "logoUrl": "https://placehold.co/150x150.png" 
            }
        ))
        
    db.commit()
    return {"status": "seeded"}
