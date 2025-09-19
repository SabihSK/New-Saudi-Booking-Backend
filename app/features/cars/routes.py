from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.db import get_session
from app.core.security.permissions import require_role
from app.features.users.models import User
from app.features.providers.services import get_provider_by_user
from . import services
from .schemas import (
    CarCreate,
    CarUpdate,
    CarRead,
    CarTypeCreate,
    CarTypeRead,
    CarFeatureCreate,
    CarFeatureRead,
    CarImageRead,
    CarReviewCreate,
    CarReviewRead,
)

# ------------------ Public APIs ------------------
router = APIRouter(prefix="/cars", tags=["cars"])


@router.get("/", response_model=List[CarRead])
async def search_cars(
    city: Optional[str] = None,
    country: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    seats: Optional[int] = None,
    transmission: Optional[str] = None,
    fuel_type: Optional[str] = None,
    car_type_id: Optional[int] = None,
    pickup_datetime: Optional[datetime] = None,
    dropoff_datetime: Optional[datetime] = None,
    session: AsyncSession = Depends(get_session),
):
    return await services.list_cars(
        session,
        city,
        country,
        min_price,
        max_price,
        seats,
        transmission,
        fuel_type,
        car_type_id,
        pickup_datetime=pickup_datetime,
        dropoff_datetime=dropoff_datetime,
    )


@router.get("/featured", response_model=List[CarRead])
async def featured_cars(session: AsyncSession = Depends(get_session)):
    cars = await services.get_featured_cars(session)
    return cars


@router.get("/{car_id}", response_model=CarRead)
async def get_car(car_id: int, session: AsyncSession = Depends(get_session)):
    return await services.get_car(car_id, session)


# ------------------ Reviews ------------------
@router.get("/{car_id}/reviews", response_model=List[CarReviewRead])
async def list_reviews(
    car_id: int,
    session: AsyncSession = Depends(get_session),
):
    return await services.list_car_reviews(car_id, session)


@router.post("/{car_id}/reviews", response_model=CarReviewRead)
async def add_review(
    car_id: int,
    review_in: CarReviewCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("user")),
):
    return await services.add_car_review(
        car_id,
        current_user,
        review_in,
        session,
    )


# ------------------ Provider APIs ------------------
provider_car_router = APIRouter(
    prefix="/providers/cars",
    tags=["provider-cars"],
)


@provider_car_router.get("/", response_model=List[CarRead])
async def get_my_cars(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.list_provider_cars(provider.id, session)


@provider_car_router.post("/", response_model=CarRead)
async def create_car(
    car_in: CarCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.create_car(car_in, provider.id, session)


@provider_car_router.put("/{car_id}", response_model=CarRead)
async def update_car(
    car_id: int,
    car_in: CarUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.update_car(car_id, car_in, provider.id, session)


@provider_car_router.delete("/{car_id}")
async def delete_car(
    car_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    await services.delete_car(car_id, provider.id, session)
    return {"detail": "Car deleted successfully"}


@provider_car_router.post("/{car_id}/images", response_model=CarImageRead)
async def upload_car_image(
    car_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.upload_car_image(car_id, provider.id, file, session)


# ------------------ Admin APIs ------------------
admin_car_router = APIRouter(prefix="/admin/cars", tags=["admin-cars"])


# ---- Car Types ----
@admin_car_router.post("/types", response_model=CarTypeRead)
async def create_car_type(
    type_in: CarTypeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.create_car_type(type_in, session)


@admin_car_router.get("/types", response_model=List[CarTypeRead])
async def list_car_types(
    session: AsyncSession = Depends(get_session),
):
    return await services.list_car_types(session)


@admin_car_router.delete("/types/{type_id}")
async def delete_car_type(
    type_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    await services.delete_car_type(type_id, session)
    return {"detail": "Car type deleted successfully"}


# ---- Car Features ----
@admin_car_router.post("/features", response_model=CarFeatureRead)
async def create_car_feature(
    feature_in: CarFeatureCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.create_car_feature(feature_in, session)


@admin_car_router.get("/features", response_model=List[CarFeatureRead])
async def list_car_features(
    session: AsyncSession = Depends(get_session),
):
    return await services.list_car_features(session)


@admin_car_router.delete("/features/{feature_id}")
async def delete_car_feature(
    feature_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    await services.delete_car_feature(feature_id, session)
    return {"detail": "Car feature deleted successfully"}
