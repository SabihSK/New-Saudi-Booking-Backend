import shutil
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.core.security.permissions import get_current_user
from app.features.providers.schemas import (
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
)
from app.features.providers import services
from app.features.users.models import User
from app.core.config import settings
import os

router = APIRouter(prefix="/providers", tags=["providers"])


@router.post("/", response_model=ProviderRead)
async def create_provider(
    provider_in: ProviderCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await services.create_provider(current_user, provider_in, session)


@router.get("/me", response_model=ProviderRead)
async def get_my_provider_profile(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await services.get_provider_by_user(current_user, session)


@router.put("/me", response_model=ProviderRead)
async def update_my_provider_profile(
    update_in: ProviderUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await services.update_provider(current_user, update_in, session)


@router.post("/me/documents", response_model=ProviderRead)
async def upload_provider_document(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    from app.features.providers.services import get_provider_by_user

    provider = await get_provider_by_user(current_user, session)

    os.makedirs(settings.UPLOAD_PROVIDER_DIR, exist_ok=True)
    filepath = os.path.join(
        settings.UPLOAD_PROVIDER_DIR,
        f"provider_{provider.id}_{file.filename}",
    )
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    provider.document_path = filepath
    await session.commit()
    await session.refresh(provider)
    return provider
