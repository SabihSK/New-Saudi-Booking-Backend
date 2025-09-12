from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.features.users.models import User, UserRole
from app.features.providers.models import Provider
from typing import List


async def list_users(session: AsyncSession) -> List[User]:
    stmt = select(User)
    result = await session.exec(stmt)
    return result.all()


async def list_providers(session: AsyncSession) -> List[Provider]:
    stmt = select(Provider)
    result = await session.exec(stmt)
    return result.all()


async def change_user_role(
    user_id: int, new_role: UserRole, session: AsyncSession
) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await session.exec(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = new_role
    await session.commit()
    await session.refresh(user)
    return user


async def deactivate_user(user_id: int, session: AsyncSession) -> None:
    stmt = select(User).where(User.id == user_id)
    result = await session.exec(stmt)
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await session.delete(user)
    await session.commit()


async def review_provider(
    provider_id: int, approve: bool, session: AsyncSession, current_user: User
) -> Provider:
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to review providers",
        )

    stmt = select(Provider).where(Provider.id == provider_id)
    result = await session.exec(stmt)
    provider = result.first()
    print(provider)
    print(provider_id)
    print(Provider.id)

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.status = "approved" if approve else "rejected"
    await session.commit()
    await session.refresh(provider)

    return provider
