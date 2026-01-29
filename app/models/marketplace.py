import uuid
from sqlalchemy import Column, String, Float, Boolean, JSON
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class ThemeStore(Base):
    __tablename__ = "theme_store"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    preview_url = Column(String)
    price = Column(Float, default=0.0)
    properties = Column(JSON, nullable=False) # The actual theme JSON
    is_public = Column(Boolean, default=True)

class ModuleStore(Base):
    __tablename__ = "module_store"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, default=0.0)
    is_public = Column(Boolean, default=True)
