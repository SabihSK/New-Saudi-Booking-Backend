import os
import shutil
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_session
from app.core.security.permissions import get_current_user
from app.features.users import services
from app.features.users.schemas import (
    Token,
    UserCreate,
    UserRead,
    UserLogin,
    UserUpdate,
)
from app.features.users.models import User
from app.core.config import settings

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserRead)
async def register(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    return await services.create_user(user_in, session)


@router.post("/login", response_model=Token)
async def login(
    user_in: UserLogin,
    session: AsyncSession = Depends(get_session),
):
    token = await services.login_user(user_in.email, user_in.password, session)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserRead)
async def update_me(
    update_in: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    return await services.update_user(current_user, update_in, session)


@router.delete("/me", status_code=204)
async def delete_me(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    await services.delete_user(current_user, session)
    return None


@router.post("/me/profile-picture", response_model=UserRead)
async def upload_profile_picture(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    os.makedirs(settings.UPLOAD_USER_DIR, exist_ok=True)
    filepath = os.path.join(
        settings.UPLOAD_USER_DIR,
        f"user_{current_user.id}_{file.filename}",
    )
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_picture = filepath
    await session.commit()
    await session.refresh(current_user)
    return current_user
