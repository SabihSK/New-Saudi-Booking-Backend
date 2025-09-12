from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status
from app.features.providers.models import Provider
from app.features.providers.schemas import ProviderCreate, ProviderUpdate
from app.features.users.models import User, UserRole


async def create_provider(
    user: User,
    provider_in: ProviderCreate,
    session: AsyncSession,
) -> Provider:
    if user.role != UserRole.provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must have provider role to create provider profile",
        )

    stmt = select(Provider).where(Provider.user_id == user.id)
    existing = await session.exec(stmt)
    if existing.first():
        raise HTTPException(
            status_code=400,
            detail="Provider profile already exists",
        )

    db_provider = Provider(user_id=user.id, **provider_in.dict())
    session.add(db_provider)
    await session.commit()
    await session.refresh(db_provider)
    return db_provider


async def get_provider_by_user(user: User, session: AsyncSession) -> Provider:
    stmt = select(Provider).where(Provider.user_id == user.id)
    result = await session.exec(stmt)
    provider = result.first()
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )
    return provider


async def update_provider(
    user: User, update_in: ProviderUpdate, session: AsyncSession
) -> Provider:
    stmt = select(Provider).where(Provider.user_id == user.id)
    result = await session.exec(stmt)
    provider = result.first()
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )

    if update_in.company_name is not None:
        provider.company_name = update_in.company_name
    if update_in.contact_number is not None:
        provider.contact_number = update_in.contact_number
    if update_in.address is not None:
        provider.address = update_in.address

    await session.commit()
    await session.refresh(provider)
    return provider
