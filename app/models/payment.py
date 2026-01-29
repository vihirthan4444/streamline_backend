from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Payment(Base):
    __tablename__ = "payment"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False, index=True)
    order_id = Column(String, ForeignKey("order.id"), nullable=False, index=True)
    
    method = Column(String, nullable=False, index=True) # CASH, CARD, QR
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    order = relationship("Order")
    tenant = relationship("Tenant")
