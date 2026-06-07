from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "ok",
        "version": settings.APP_VERSION
    }
