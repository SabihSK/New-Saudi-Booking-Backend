from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.config import settings
from app.core.db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield


def create_app() -> FastAPI:
    fastapi_app = FastAPI(
        root_path="/api",
        title="Booking Platform API",
        debug=settings.DEBUG,
        version="0.1.0",
        lifespan=lifespan,
    )

    # ✅ CORS settings
    origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://31.58.144.9",
        "https://yourdomain.com",
    ]

    fastapi_app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Routers
    fastapi_app.include_router(api_router)

    # ✅ Static uploads
    fastapi_app.mount(
        "/app/upload",
        StaticFiles(directory="app/upload"),
        name="upload",
    )

    return fastapi_app


app = create_app()
