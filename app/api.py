from fastapi import APIRouter
from app.features.users.routes import router as users_router
from app.features.providers.routes import router as providers_router
from app.features.admin.routes import router as admin_router
from app.features.stays.routes import (
    router as stays_router,
    provider_stays_router,
    admin_stays_router,
)

api_router = APIRouter()
api_router.include_router(users_router)
api_router.include_router(providers_router)
api_router.include_router(admin_router)
api_router.include_router(stays_router)
api_router.include_router(provider_stays_router)
api_router.include_router(admin_stays_router)
