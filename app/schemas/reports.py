from pydantic import BaseModel
from typing import List, Optional

class DailySales(BaseModel):
    date: str
    total_sales: float
    cash_sales: float
    card_sales: float
    order_count: int

class CashierSales(BaseModel):
    cashier_name: str
    total_sales: float
    order_count: int

class ProductSales(BaseModel):
    product_name: str
    qty_sold: int
    revenue: float

class ReconcileRequest(BaseModel):
    product_id: str
    physical_count: int
    reason: str
