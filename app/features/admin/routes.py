from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.db import get_session
from app.core.security.permissions import require_role
from app.features.users.models import User, UserRole
from app.features.users.schemas import UserRead
from app.features.providers.schemas import ProviderRead
from app.features.admin import services

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserRead])
async def get_all_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.list_users(session)


@router.get("/providers", response_model=List[ProviderRead])
async def get_all_providers(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.list_providers(session)


@router.put("/users/{user_id}/role", response_model=UserRead)
async def change_role(
    user_id: int,
    new_role: UserRole,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.change_user_role(user_id, new_role, session)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user_as_admin(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    await services.deactivate_user(user_id, session)
    return None


@router.put(
    "/providers/{provider_id}/review",
    response_model=ProviderRead,
    summary="Approve or reject a provider - Review Provider",
    description="Approve or reject a provider",
)
async def review_provider(
    provider_id: int,
    approve: bool,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.review_provider(
        provider_id,
        approve,
        session,
        current_user,
    )
