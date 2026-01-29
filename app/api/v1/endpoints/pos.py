from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models import Product, Order, OrderItem, StockEvent, Shift
from app.schemas import pos as pos_schemas
import datetime

router = APIRouter()

# --- Products ---
@router.get("/products", response_model=List[pos_schemas.ProductResponse])
def get_products(
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    products = db.query(Product).filter(Product.tenant_id == tenant_id, Product.is_active == True).all()
    return products

@router.post("/products", response_model=pos_schemas.ProductResponse)
def create_product(
    product_in: pos_schemas.ProductCreate,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    product = Product(
        tenant_id=tenant_id,
        sku=product_in.sku,
        name=product_in.name,
        price=product_in.price,
        barcode=product_in.barcode,
        is_active=product_in.is_active
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

# --- Shifts ---
@router.post("/shift/open", response_model=pos_schemas.ShiftResponse)
def open_shift(
    shift_in: pos_schemas.ShiftCreate,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    user_id = current_token.sub 
    
    # Check if open shift exists
    active_shift = db.query(Shift).filter(
        Shift.tenant_id == tenant_id,
        Shift.cashier_id == user_id,
        Shift.closed_at == None
    ).first()
    
    if active_shift:
        raise HTTPException(status_code=400, detail="Shift already open")
        
    shift = Shift(
        tenant_id=tenant_id,
        cashier_id=user_id,
        opening_cash=shift_in.opening_cash
    )
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift

@router.post("/shift/close", response_model=pos_schemas.ShiftResponse)
def close_shift(
    shift_in: pos_schemas.ShiftClose,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    user_id = current_token.sub 
    
    active_shift = db.query(Shift).filter(
        Shift.tenant_id == tenant_id,
        Shift.cashier_id == user_id,
        Shift.closed_at == None
    ).first()
    
    if not active_shift:
        raise HTTPException(status_code=400, detail="No active shift found")
        
    active_shift.closed_at = datetime.datetime.utcnow()
    active_shift.closing_cash = shift_in.closing_cash
    
    db.commit()
    db.refresh(active_shift)
    return active_shift

# --- Sync ---
@router.post("/sync/batch", response_model=pos_schemas.SyncResponse)
def sync_batch(
    batch: pos_schemas.SyncBatch,
    current_token: Any = Depends(deps.get_current_token_payload),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    processed_orders = 0
    processed_events = 0
    errors = []
    
    # Process Orders
    for order_in in batch.orders:
        try:
            # Check Idempotency (if order ID exists, skip)
            # If Client generates UUID, we use it.
            existing = db.query(Order).filter(Order.id == order_in.id).first()
            if existing:
                continue
                
            order = Order(
                id=order_in.id, # Trust client ID for sync
                tenant_id=tenant_id,
                cashier_id=order_in.cashier_id,
                shift_id=order_in.shift_id,
                total=order_in.total,
                status=order_in.status,
                created_at=order_in.created_at or datetime.datetime.utcnow()
            )
            db.add(order)
            
            for item_in in order_in.items:
                item = OrderItem(
                    order_id=order.id,
                    product_id=item_in.product_id,
                    qty=item_in.qty,
                    price=item_in.price
                )
                db.add(item)
            
            processed_orders += 1
            
        except Exception as e:
            errors.append(f"Order {order_in.id} failed: {str(e)}")

    # Process Stock Events
    for event_in in batch.stock_events:
        try:
            # Idempotency check could be added if event has client-side ID
            stock_event = StockEvent(
                tenant_id=tenant_id,
                product_id=event_in.product_id,
                event_type=event_in.event_type,
                quantity=event_in.quantity,
                source_id=event_in.source_id
            )
            db.add(stock_event)
            processed_events += 1
        except Exception as e:
            errors.append(f"Event for {event_in.product_id} failed: {str(e)}")
            
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return pos_schemas.SyncResponse(
            success=False, 
            processed_orders=0, 
            processed_events=0, 
            errors=[f"Commit failed: {str(e)}"]
        )
        
    return pos_schemas.SyncResponse(
        success=True,
        processed_orders=processed_orders,
        processed_events=processed_events,
        errors=errors
    )
