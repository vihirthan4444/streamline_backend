from sqlalchemy import Column, String
from app.core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Module(Base):
    __tablename__ = "module"

    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, nullable=False) # POS, SALON, INVENTORY
    name = Column(String, nullable=False)
