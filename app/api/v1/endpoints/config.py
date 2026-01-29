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
        
    # 3. Seed Subscription Plans
    plans_data = [
        {"name": "Free", "price": 0.0, "max_users": 1, "modules_allowed": '["POS"]'},
        {"name": "Starter", "price": 2500.0, "max_users": 3, "modules_allowed": '["POS", "INVENTORY"]'},
        {"name": "Pro", "price": 6500.0, "max_users": 99, "modules_allowed": '["POS", "INVENTORY", "REPORTS", "SALON", "HR"]'}
    ]
    from app.models.subscription import SubscriptionPlan
    for pd in plans_data:
        existing_plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == pd["name"]).first()
        if not existing_plan:
            db.add(SubscriptionPlan(
                name=pd["name"],
                price=pd["price"],
                max_users=pd["max_users"],
                modules_allowed=pd["modules_allowed"]
            ))
            
    # 4. Seed Marketplace Themes
    from app.models.marketplace import ThemeStore
    themes_data = [
        {
            "name": "Dark Pro", 
            "description": "Professional dark mode for late night operations.",
            "preview_url": "https://placehold.co/400x300/000000/FFFFFF.png",
            "price": 9.99,
            "properties": {
                "primaryColor": "#212121",
                "secondaryColor": "#FFD600",
                "fontFamily": "Inter",
                "logoUrl": "https://placehold.co/150x150/000000/FFFFFF.png"
            }
        },
        {
            "name": "Ocean Blue", 
            "description": "Calming blue tones for a pleasant checkout experience.",
            "preview_url": "https://placehold.co/400x300/007BFF/FFFFFF.png",
            "price": 4.99,
            "properties": {
                "primaryColor": "#007BFF",
                "secondaryColor": "#E3F2FD",
                "fontFamily": "Poppins",
                "logoUrl": "https://placehold.co/150x150/007BFF/FFFFFF.png"
            }
        }
    ]
    for td in themes_data:
        existing = db.query(ThemeStore).filter(ThemeStore.name == td["name"]).first()
        if not existing:
            db.add(ThemeStore(**td))

    # 5. Seed Marketplace Modules
    from app.models.marketplace import ModuleStore
    mods_data = [
        {"code": "SALON", "name": "Salon Booking", "description": "Manage appointments and stylists.", "price": 49.0},
        {"code": "HR", "name": "Employee Management", "description": "Rotas, payroll, and performance.", "price": 39.0}
    ]
    for md in mods_data:
        existing = db.query(ModuleStore).filter(ModuleStore.code == md["code"]).first()
        if not existing:
            db.add(ModuleStore(**md))

    db.commit()
    return {"status": "seeded"}
@router.post("/seed-demo-data")
def seed_demo_data(
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    from app.models import Product
    
    # 1. Add sample products
    products_data = [
        {"sku": "COKE-1", "name": "Coca Cola 500ml", "price": 180.0},
        {"sku": "BREAD-1", "name": "Fresh Roast Bread", "price": 220.0},
        {"sku": "MILK-1", "name": "Fresh Milk 1L", "price": 450.0},
    ]
    
    for pd in products_data:
        existing = db.query(Product).filter(Product.tenant_id == tenant_id, Product.sku == pd["sku"]).first()
        if not existing:
            db.add(Product(tenant_id=tenant_id, **pd))
            
    db.commit()
    return {"status": "success", "message": "Demo data loaded"}

@router.post("/admin/activate-plan/{plan_name}")
def activate_plan_manually(
    plan_name: str,
    target_tenant_id: str,
    # In real app, restrict this to super-admins
    db: Session = Depends(deps.get_db)
):
    from app.models.subscription import SubscriptionPlan, TenantSubscription
    import datetime
    
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.name == plan_name).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
        
    # Deactivate existing
    db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == target_tenant_id
    ).update({"status": "INACTIVE"})
    
    # Create new
    new_sub = TenantSubscription(
        tenant_id=target_tenant_id,
        plan_id=plan.id,
        start_date=datetime.datetime.utcnow(),
        end_date=datetime.datetime.utcnow() + datetime.timedelta(days=30),
        status="ACTIVE"
    )
    db.add(new_sub)
    db.commit()
    
    return {"status": "success", "message": f"Plan {plan_name} activated for {target_tenant_id}"}
