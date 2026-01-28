from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class UserTenant(Base):
    __tablename__ = "user_tenant"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("user.id"), nullable=False)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False)
    role = Column(String, nullable=False) # OWNER, ADMIN, STAFF, CASHIER

    user = relationship("User", back_populates="tenants")
    tenant = relationship("Tenant", back_populates="users")
