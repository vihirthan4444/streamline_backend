from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenant, config, pos

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
api_router.include_router(config.router, prefix="/tenant-config", tags=["config"])
api_router.include_router(pos.router, prefix="/pos", tags=["pos"])
