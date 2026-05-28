from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {"status": "ok", "service": settings.APP_NAME}
