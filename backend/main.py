import logging
import json
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from api.routes import health

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "time": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
