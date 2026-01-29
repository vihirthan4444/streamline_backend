from fastapi import FastAPI
from app.api.v1.api import api_router
from app.core.database import engine, Base
# Import all models so Base metadata is populated
from app.models import tenant, user, user_tenant, module, tenant_module, theme, product, order, stock, shift, payment, audit_log

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Streamline API")

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "streamline"}
