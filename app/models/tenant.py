import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
import datetime
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Tenant(Base):
    __tablename__ = "tenant"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    business_type = Column(String) 
    theme_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    users = relationship("UserTenant", back_populates="tenant")
