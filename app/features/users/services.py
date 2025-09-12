from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.features.users.models import User, UserRole
from app.features.users.schemas import UserCreate, UserUpdate
from fastapi import HTTPException, status
from app.core.security.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
)


async def create_user(user_in: UserCreate, session: AsyncSession) -> User:
    if user_in.role == UserRole.admin:
        raise HTTPException(
            status_code=403, detail="Direct admin registration is not allowed"
        )

    stmt = select(User).where(User.email == user_in.email)
    existing = await session.exec(stmt)
    if existing.first():
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role or UserRole.customer,
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def authenticate_user(
    email: str,
    password: str,
    session: AsyncSession,
) -> User:
    stmt = select(User).where(User.email == email)
    result = await session.exec(stmt)
    user = result.first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    return user


async def login_user(email: str, password: str, session: AsyncSession) -> str:
    stmt = select(User).where(User.email == email)
    result = await session.exec(stmt)
    user = result.first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = create_access_token(subject=user.email)
    return token


async def update_user(
    user: User,
    update_in: UserUpdate,
    session: AsyncSession,
) -> User:
    if update_in.full_name is not None:
        user.full_name = update_in.full_name
    if update_in.password is not None:
        user.hashed_password = get_password_hash(update_in.password)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(user: User, session: AsyncSession) -> None:
    await session.delete(user)
    await session.commit()
