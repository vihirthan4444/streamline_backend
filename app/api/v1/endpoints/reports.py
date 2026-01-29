from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api import deps
from app.models import Order, Payment, User, OrderItem, Product
from app.schemas import reports as report_schemas
import datetime

router = APIRouter()

@router.get("/daily-sales", response_model=report_schemas.DailySales)
def get_daily_sales(
    date: str = None, # YYYY-MM-DD
    current_token: Any = Depends(deps.RoleChecker(["OWNER", "MANAGER"])),
    subscription: Any = Depends(deps.SubscriptionChecker(required_module="REPORTS")),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    
    # Default to today
    if not date:
        target_date = datetime.date.today()
    else:
        target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        
    # Filter Orders by Date
    # Note: Created_at is datetime. We need to cast or filter by range.
    start = datetime.datetime.combine(target_date, datetime.time.min)
    end = datetime.datetime.combine(target_date, datetime.time.max)
    
    orders_query = db.query(Order).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != 'VOID'
    )
    
    total_sales = orders_query.with_entities(func.sum(Order.total)).scalar() or 0.0
    order_count = orders_query.count()
    
    # Cash vs Card (Aggregation on Payments)
    # This assumes 1:1 or 1:N payment. 
    # We filter payments linked to orders in this date range.
    payments_query = db.query(Payment).join(Order).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != 'VOID'
    )
    
    cash_sales = payments_query.filter(Payment.method == 'CASH').with_entities(func.sum(Payment.amount)).scalar() or 0.0
    card_sales = payments_query.filter(Payment.method == 'CARD').with_entities(func.sum(Payment.amount)).scalar() or 0.0
    
    return report_schemas.DailySales(
        date=str(target_date),
        total_sales=total_sales,
        cash_sales=cash_sales,
        card_sales=card_sales,
        order_count=order_count
    )


@router.get("/cashier-sales", response_model=List[report_schemas.CashierSales])
def get_cashier_sales(
    date: str = None,
    current_token: Any = Depends(deps.RoleChecker(["OWNER", "MANAGER"])),
    subscription: Any = Depends(deps.SubscriptionChecker(required_module="REPORTS")),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    if not date:
        target_date = datetime.date.today()
    else:
        target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    start = datetime.datetime.combine(target_date, datetime.time.min)
    end = datetime.datetime.combine(target_date, datetime.time.max)

    # Group By Cashier
    results = db.query(
        User.email,
        func.sum(Order.total),
        func.count(Order.id)
    ).join(Order, Order.cashier_id == User.id).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != 'VOID'
    ).group_by(User.id).all()
    
    return [
        report_schemas.CashierSales(
            cashier_name=r[0],
            total_sales=r[1] or 0.0,
            order_count=r[2]
        ) for r in results
    ]

@router.get("/product-sales", response_model=List[report_schemas.ProductSales])
def get_product_sales(
    date: str = None,
    current_token: Any = Depends(deps.RoleChecker(["OWNER", "MANAGER"])),
    subscription: Any = Depends(deps.SubscriptionChecker(required_module="REPORTS")),
    db: Session = Depends(deps.get_db)
):
    tenant_id = current_token.tenant_id
    if not date:
        target_date = datetime.date.today()
    else:
        target_date = datetime.datetime.strptime(date, "%Y-%m-%d").date()

    start = datetime.datetime.combine(target_date, datetime.time.min)
    end = datetime.datetime.combine(target_date, datetime.time.max)

    # Top items
    results = db.query(
        Product.name,
        func.sum(OrderItem.qty),
        func.sum(OrderItem.price * OrderItem.qty)
    ).join(OrderItem, OrderItem.product_id == Product.id).join(Order, OrderItem.order_id == Order.id).filter(
        Order.tenant_id == tenant_id,
        Order.created_at >= start,
        Order.created_at <= end,
        Order.status != 'VOID'
    ).group_by(Product.id).order_by(func.sum(OrderItem.qty).desc()).limit(10).all()

    return [
        report_schemas.ProductSales(
            product_name=r[0],
            qty_sold=r[1] or 0,
            revenue=r[2] or 0.0
        ) for r in results
    ]
