from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from app.api import api_router
from app.core.config import settings
from app.core.db import init_db
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        title="Booking Platform API",
        debug=settings.DEBUG,
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include routers
    fastapi_app.include_router(api_router)

    return fastapi_app


app = create_app()

app.mount("/app/upload", StaticFiles(directory="app/upload"), name="upload")
