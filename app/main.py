from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.database import engine, Base
# Import all models so Base metadata is populated
from app.models import tenant, user, user_tenant, module, tenant_module, theme, product, order, stock, shift, payment, audit_log

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.limiter import limiter

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Streamline API")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(api_router)

@app.get("/health")
def health():
    return {"status": "ok", "app": "streamline"}
