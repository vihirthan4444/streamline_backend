from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    
    action = Column(String, nullable=False) # SHIFT_CLOSE, STOCK_ADJUST, ORDER_VOID
    entity = Column(String, nullable=False) # Shift, Product, Order
    entity_id = Column(String, nullable=True)
    
    before_state = Column(Text, nullable=True) # JSON string
    after_state = Column(Text, nullable=True) # JSON string
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    tenant = relationship("Tenant")
