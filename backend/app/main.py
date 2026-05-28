from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.quizzes import router as quizzes_router
from app.api.student import router as student_router
from app.core.config import settings
from app.db.database import Base, engine
from app.db.migrate import apply_migrations
from app.db import models  # noqa: F401


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(quizzes_router)
app.include_router(student_router)


@app.get("/")
def root():
    return {"status": "ok", "service": settings.APP_NAME}
