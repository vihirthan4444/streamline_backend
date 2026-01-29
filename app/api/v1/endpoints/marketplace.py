from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Tenant, TenantModule, Theme, Module
from app.models.marketplace import ThemeStore, ModuleStore
from pydantic import BaseModel

router = APIRouter()

class MarketplaceThemeOut(BaseModel):
    id: str
    name: str
    description: str
    preview_url: str
    price: float
    class Config:
        from_attributes = True

class MarketplaceModuleOut(BaseModel):
    id: str
    code: str
    name: str
    description: str
    price: float
    class Config:
        from_attributes = True

@router.get("/themes", response_model=List[MarketplaceThemeOut])
def list_store_themes(db: Session = Depends(deps.get_db)):
    return db.query(ThemeStore).filter(ThemeStore.is_public == True).all()

@router.get("/modules", response_model=List[MarketplaceModuleOut])
def list_store_modules(db: Session = Depends(deps.get_db)):
    return db.query(ModuleStore).filter(ModuleStore.is_public == True).all()

@router.post("/buy-theme/{theme_store_id}")
def buy_theme(
    theme_store_id: str,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    item = db.query(ThemeStore).filter(ThemeStore.id == theme_store_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Theme not found in store")
        
    # Mock Payment Logic
    # ...
    
    # 1. Create actual Theme entry if not exists or just link properties
    theme = db.query(Theme).filter(Theme.name == item.name).first()
    if not theme:
        theme = Theme(name=item.name, properties=item.properties)
        db.add(theme)
        db.commit()
        db.refresh(theme)
        
    # 2. Update Tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    tenant.theme_id = theme.id
    db.commit()
    
    return {"status": "success", "message": f"Theme '{item.name}' applied"}

@router.post("/activate-module/{module_code}")
def activate_module(
    module_code: str,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    
    # Check if module exists in store
    item = db.query(ModuleStore).filter(ModuleStore.code == module_code).first()
    if not item:
        raise HTTPException(status_code=404, detail="Module not found in store")
        
    # Check if system module exists
    module = db.query(Module).filter(Module.code == module_code).first()
    if not module:
         # Auto-create system module if defined in store but not in core (for convenience)
         module = Module(code=item.code, name=item.name)
         db.add(module)
         db.commit()
         db.refresh(module)

    # Enable for tenant
    tm = db.query(TenantModule).filter(
        TenantModule.tenant_id == tenant_id,
        TenantModule.module_id == module.id
    ).first()
    
    if tm:
        tm.enabled = True
    else:
        tm = TenantModule(tenant_id=tenant_id, module_id=module.id, enabled=True)
        db.add(tm)
        
    db.commit()
    return {"status": "success", "message": f"Module '{item.name}' activated"}
