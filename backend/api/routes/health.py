from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION
    }

@router.get("/init-db", tags=["system"])
async def init_db():
    try:
        from database import engine, Base
        from models import ingest, search, vector
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return {"status": "success", "message": "Tables created successfully!"}
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error creating tables: {e}")
        return {"status": "error", "message": str(e)}
