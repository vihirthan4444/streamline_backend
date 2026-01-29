from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class StockEvent(Base):
    __tablename__ = "stock_event"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False, index=True)
    product_id = Column(String, ForeignKey("product.id"), nullable=False, index=True)
    
    event_type = Column(String, nullable=False, index=True) # SALE, PURCHASE, ADJUSTMENT, RETURN
    quantity = Column(Integer, nullable=False) # Positive or Negative
    source_id = Column(String, nullable=True, index=True) # Order ID or Adjustment ID
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    product = relationship("Product")
    tenant = relationship("Tenant")
