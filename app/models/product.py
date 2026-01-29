from sqlalchemy import Column, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Product(Base):
    __tablename__ = "product"

    id = Column(String, primary_key=True, default=generate_uuid)
    tenant_id = Column(String, ForeignKey("tenant.id"), nullable=False, index=True)
    sku = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    barcode = Column(String, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, index=True)

    tenant = relationship("Tenant")
