from sqlalchemy import Column, String, Integer, Boolean, DateTime, text
from app.core.database import Base
import datetime

class AppVersion(Base):
    __tablename__ = "app_version"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String, nullable=False)  # 'android', 'windows'
    version_name = Column(String, nullable=False) # '1.0.0'
    build_number = Column(Integer, nullable=False) # 1
    download_url = Column(String, nullable=False)
    force_update = Column(Boolean, default=False)
    changelog = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
