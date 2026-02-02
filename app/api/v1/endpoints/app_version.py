from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.app_version import AppVersion
from pydantic import BaseModel

router = APIRouter()

class VersionInfo(BaseModel):
    version: str
    build: int
    url: str
    force: bool

class VersionResponse(BaseModel):
    android: VersionInfo
    windows: VersionInfo
    changelog: str = ""

@router.get("", response_model=VersionResponse)
def get_app_version(db: Session = Depends(deps.get_db)):
    # Fetch latest android version
    android_ver = db.query(AppVersion).filter(AppVersion.platform == 'android').order_by(AppVersion.build_number.desc()).first()
    
    # Fetch latest windows version
    windows_ver = db.query(AppVersion).filter(AppVersion.platform == 'windows').order_by(AppVersion.build_number.desc()).first()

    # Default fallback if DB is empty
    default_info = VersionInfo(version="1.0.0", build=1, url="", force=False)

    return VersionResponse(
        android=VersionInfo(
            version=android_ver.version_name,
            build=android_ver.build_number,
            url=android_ver.download_url,
            force=android_ver.force_update
        ) if android_ver else default_info,
        windows=VersionInfo(
            version=windows_ver.version_name,
            build=windows_ver.build_number,
            url=windows_ver.download_url,
            force=windows_ver.force_update
        ) if windows_ver else default_info,
        changelog=android_ver.changelog if android_ver else "Initial Release"
    )
