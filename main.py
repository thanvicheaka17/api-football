import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
import uvicorn

from app.config import get_settings
from app.database import get_database
from app.router import router

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_database().init()
    yield


app = FastAPI(
    title="API Football",
    description="Local proxy for API-Football with Redis cache and SQLite persistence",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/", tags=["Health"])
def index():
    return {
        "status": "failed",
        "message": "Unauthorized",
    }


@app.get("/health", tags=["Health"])
def database_health():
    return get_database().health()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
    )
