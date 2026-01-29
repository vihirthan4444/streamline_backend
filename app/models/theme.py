from sqlalchemy import Column, String, JSON
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Theme(Base):
    __tablename__ = "theme"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    properties = Column(JSON, nullable=False) # Stores colors, fonts, logoUrl
