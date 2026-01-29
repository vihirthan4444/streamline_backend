from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api import deps
from app.models import StockEvent, AuditLog
from app.schemas import reports as report_schemas
import datetime

router = APIRouter()

@router.post("/reconcile")
def reconcile_stock(
    request: report_schemas.ReconcileRequest,
    current_token: Any = Depends(deps.RoleChecker(["OWNER", "MANAGER"])),
    subscription: Any = Depends(deps.SubscriptionChecker(required_module="INVENTORY")),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    user_id = current_token.sub 
    
    # 1. Calculate Difference logic 
    # In a real app, we might want to fetch current system stock first.
    # For V1, we trust the client sends the physical count, but we need system count to calc diff.
    # Simplification: We assume the request sends the diff, or we calc it here.
    # Let's calculate it here by summing all stock events.
    
    events = db.query(StockEvent).filter(
        StockEvent.product_id == request.product_id,
        StockEvent.tenant_id == tenant_id
    ).all()
    
    system_stock = sum(e.quantity for e in events)
    difference = request.physical_count - system_stock
    
    if difference == 0:
        return {"status": "matched", "difference": 0}
        
    # 2. Create Adjustment Event
    adjustment = StockEvent(
        tenant_id=tenant_id,
        product_id=request.product_id,
        event_type="ADJUSTMENT",
        quantity=difference,
        source_id="RECONCILE"
    )
    db.add(adjustment)
    
    # 3. Create Audit Log
    log = AuditLog(
        tenant_id=tenant_id,
        user_id=user_id,
        action="STOCK_ADJUST",
        entity="Product",
        entity_id=request.product_id,
        before_state=f"System: {system_stock}",
        after_state=f"Physical: {request.physical_count}, Diff: {difference}, Reason: {request.reason}"
    )
    db.add(log)
    
    db.commit()
    return {"status": "adjusted", "difference": difference}
