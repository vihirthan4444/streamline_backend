from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Product ---
class ProductBase(BaseModel):
    sku: str
    name: str
    price: float
    barcode: Optional[str] = None
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: str
    tenant_id: str
    class Config:
        from_attributes = True

# --- Stock Event ---
class StockEventCreate(BaseModel):
    product_id: str
    event_type: str # SALE, PURCHASE, ADJUSTMENT
    quantity: int
    source_id: Optional[str] = None

# --- Order ---
class OrderItemCreate(BaseModel):
    product_id: str
    qty: int
    price: float

class OrderCreate(BaseModel):
    id: Optional[str] = None # Allow client-side ID for offline sync
    cashier_id: str
    shift_id: Optional[str] = None
    total: float
    status: str = "PAID"
    created_at: Optional[datetime] = None
    items: List[OrderItemCreate]

class OrderResponse(BaseModel):
    id: str
    total: float
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# --- Shift ---
class ShiftCreate(BaseModel):
    opening_cash: float

class ShiftClose(BaseModel):
    closing_cash: float

class ShiftResponse(BaseModel):
    id: str
    cashier_id: str
    opened_at: datetime
    closed_at: Optional[datetime]
    opening_cash: float
    closing_cash: Optional[float]
    class Config:
        from_attributes = True

# --- Sync ---
class SyncBatch(BaseModel):
    orders: List[OrderCreate]
    stock_events: List[StockEventCreate]

class SyncResponse(BaseModel):
    success: bool
    processed_orders: int
    processed_events: int
    errors: List[str] = []
