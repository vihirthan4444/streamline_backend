from fastapi import APIRouter
from app.api.v1.endpoints import auth, tenant, config, pos, reports, stock, billing, marketplace, system, app_version

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenant.router, prefix="/tenant", tags=["tenant"])
api_router.include_router(config.router, prefix="/config", tags=["config"])
api_router.include_router(pos.router, prefix="/pos", tags=["pos"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(stock.router, prefix="/stock", tags=["stock"])
api_router.include_router(billing.router, prefix="/billing", tags=["billing"])
api_router.include_router(marketplace.router, prefix="/marketplace", tags=["marketplace"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
api_router.include_router(app_version.router, prefix="/app/version", tags=["app_version"])
