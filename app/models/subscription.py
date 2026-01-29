import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plan"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False) # Free, Starter, Pro
    price = Column(Float, nullable=False)
    max_users = Column(Integer, default=1)
    modules_allowed = Column(String) # JSON string: ["POS", "SALON"]
    is_active = Column(Boolean, default=True)

class TenantSubscription(Base):
    __tablename__ = "tenant_subscription"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), unique=True, nullable=False, index=True)
    plan_id = Column(String, ForeignKey("subscription_plan.id"), nullable=False, index=True)
    
    start_date = Column(DateTime, default=datetime.datetime.utcnow)
    end_date = Column(DateTime, nullable=True) # None = Lifetime or recurring
    status = Column(String, default="ACTIVE", index=True) # ACTIVE, EXPIRED, CANCELLED

    tenant = relationship("Tenant")
    plan = relationship("SubscriptionPlan")
