from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Order(Base):
    __tablename__ = "order"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False, index=True)
    cashier_id = Column(String, ForeignKey("user.id"), nullable=False, index=True)
    shift_id = Column(String, ForeignKey("shift.id"), nullable=True, index=True) # Optional backfill
    
    total = Column(Float, nullable=False)
    status = Column(String, default="PAID", index=True) # PAID, VOID
    is_deleted = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    # Relationships
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    cashier = relationship("User")
    tenant = relationship("Tenant")

class OrderItem(Base):
    __tablename__ = "order_item"

    id = Column(String, primary_key=True, default=generate_uuid)
    order_id = Column(String, ForeignKey("order.id"), nullable=False)
    product_id = Column(String, ForeignKey("product.id"), nullable=False)
    
    qty = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
