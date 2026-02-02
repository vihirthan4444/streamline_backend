from fastapi import APIRouter, Depends, HTTPException, Header
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

class VersionUpdatePayload(BaseModel):
    platform: str
    version: str
    build: int
    url: str
    force: bool = False
    changelog: str = None

@router.post("/internal/app/version")
def update_app_version(
    payload: VersionUpdatePayload,
    x_ci_token: str = Header(None, alias="X-CI-TOKEN"),
    db: Session = Depends(deps.get_db)
):
    import os
    if x_ci_token != os.getenv("CI_DEPLOY_TOKEN"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    new_version = AppVersion(
        platform=payload.platform,
        version_name=payload.version,
        build_number=payload.build,
        download_url=payload.url,
        force_update=payload.force,
        changelog=payload.changelog
    )
    
    db.add(new_version)
    db.commit()
    return {"status": "ok", "version": payload.version}
