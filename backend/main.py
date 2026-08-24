import logging
import json
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from core.limiter import limiter
from api.routes import health, search, ingest, assets, scenes, media, clips, stats

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "client_ip"):
            log_record["client_ip"] = record.client_ip
        if hasattr(record, "endpoint"):
            log_record["endpoint"] = record.endpoint
            
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    # Remove existing handlers
    for h in logger.handlers[:]:
        logger.removeHandler(h)
    logger.addHandler(handler)
    # Also set uvicorn loggers to use our format
    logging.getLogger("uvicorn.access").handlers = [handler]
    logging.getLogger("uvicorn.error").handlers = [handler]

setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-migrate database tables for the workshop
    try:
        from database import engine, Base
        import models.asset
        import models.ingest_job
        import models.scene
        import models.saved_search
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully via Auto-Migration.")
    except Exception as e:
        logger.error(f"Failed to auto-migrate database: {e}")

    # Mask secrets
    config_dict = settings.model_dump()
    if "DATABASE_URL" in config_dict:
        config_dict["DATABASE_URL"] = "***MASKED***"

    logger.info(f"Starting Smart Media Analytics API version {settings.APP_VERSION}")
    logger.info(f"Configuration: {config_dict}")
    yield
    logger.info("Shutting down API")

app = FastAPI(
    title="Smart Media Analytics API",
    description="Local-First Media Asset Management and Semantic Search System",
    version=settings.APP_VERSION,
    lifespan=lifespan
)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


from fastapi import Depends
from api.deps import get_current_user

app.include_router(health.router)
app.include_router(search.router, dependencies=[Depends(get_current_user)])
app.include_router(ingest.router, dependencies=[Depends(get_current_user)])
app.include_router(assets.router, dependencies=[Depends(get_current_user)])
app.include_router(scenes.router, dependencies=[Depends(get_current_user)])
app.include_router(media.router, dependencies=[Depends(get_current_user)])
app.include_router(clips.router, dependencies=[Depends(get_current_user)])
app.include_router(stats.router)
app.include_router(saved_searches.router, dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    # pyrefly: ignore [missing-import]
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)