from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.subscription import TenantSubscription, SubscriptionPlan
from pydantic import BaseModel

router = APIRouter()

class PlanOut(BaseModel):
    id: str
    name: str
    price: float
    max_users: int
    modules_allowed: str

    class Config:
        from_attributes = True

class SubscriptionOut(BaseModel):
    status: str
    plan_name: str
    modules_allowed: List[str]
    end_date: Any = None

@router.get("/my-subscription", response_model=SubscriptionOut)
def get_my_subscription(
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context missing")
        
    sub = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant_id
    ).first()
    
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
        
    plan = db.query(SubscriptionPlan).filter(SubscriptionPlan.id == sub.plan_id).first()
    
    import json
    return {
        "status": sub.status,
        "plan_name": plan.name if plan else "Unknown",
        "modules_allowed": json.loads(plan.modules_allowed) if plan else [],
        "end_date": sub.end_date
    }

@router.get("/plans", response_model=List[PlanOut])
def get_plans(db: Session = Depends(deps.get_db)):
    return db.query(SubscriptionPlan).filter(SubscriptionPlan.is_active == True).all()
