from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class VersionInfo(BaseModel):
    latest_version: str
    min_version: str
    force_update: bool
    download_url: str

@router.get("/version", response_model=VersionInfo)
def get_version():
    return {
        "latest_version": "1.1.0",
        "min_version": "1.0.0",
        "force_update": False,
        "download_url": "https://streamline-pos.com/download"
    }
