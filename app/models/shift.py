from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Shift(Base):
    __tablename__ = "shift"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False)
    cashier_id = Column(String, ForeignKey("user.id"), nullable=False)
    
    opened_at = Column(DateTime, default=datetime.datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    opening_cash = Column(Float, default=0.0)
    closing_cash = Column(Float, nullable=True)
    
    expected_cash = Column(Float, nullable=True)
    difference = Column(Float, nullable=True)
    note = Column(String, nullable=True)

    cashier = relationship("User")
    tenant = relationship("Tenant")
