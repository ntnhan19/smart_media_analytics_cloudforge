from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware


API_PREFIX = "/api/v1"
FRONTEND_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]


router = APIRouter(prefix=API_PREFIX)


@router.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint — used by Docker healthcheck and monitoring tools.
    Returns {"status": "ok", "version": "0.1.0"} when the service is ready.
    """
    return {
        "status": "ok",
        "version": "0.1.0",
        "service": "echoscene-backend",
    }


@router.get("/media", tags=["media"])
async def list_media_placeholder() -> dict[str, list[dict[str, str]]]:
    return {
        "items": [
            {
                "id": "mock-media-001",
                "title": "EchoScene sample media",
                "status": "ready-for-ingestion",
            }
        ]
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="EchoScene API",
        description="Local-first AI media management API for indexing, searching, and analyzing media assets.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=FRONTEND_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
