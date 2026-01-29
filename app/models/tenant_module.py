from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class TenantModule(Base):
    __tablename__ = "tenant_module"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False)
    module_id = Column(String, ForeignKey("module.id"), nullable=False)
    enabled = Column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="modules")
    module = relationship("Module")
