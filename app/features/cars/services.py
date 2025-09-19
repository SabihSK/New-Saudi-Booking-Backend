from datetime import datetime
import os
import uuid
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, delete
from typing import List, Optional

from app.features.users.models import User
from app.features.cars.models import (
    Car,
    CarType,
    CarImage,
    CarFeature,
    CarFeatureLink,
    CarReview,
)
from .schemas import (
    CarCreate,
    CarUpdate,
    CarTypeCreate,
    CarFeatureCreate,
    CarReviewCreate,
)


# ------------------ Car Types ------------------
async def create_car_type(
    type_in: CarTypeCreate,
    session: AsyncSession,
) -> CarType:
    exists = await session.exec(
        select(CarType).where(CarType.name == type_in.name),
    )
    if exists.first():
        raise HTTPException(status_code=400, detail="Car type already exists")

    car_type = CarType(**type_in.dict())
    session.add(car_type)
    await session.commit()
    await session.refresh(car_type)
    return car_type


async def list_car_types(session: AsyncSession) -> List[CarType]:
    result = await session.exec(select(CarType))
    return result.all()


# ------------------ Car Features ------------------
async def create_car_feature(
    feature_in: CarFeatureCreate, session: AsyncSession
) -> CarFeature:
    exists = await session.exec(
        select(CarFeature).where(CarFeature.name == feature_in.name)
    )
    if exists.first():
        raise HTTPException(status_code=400, detail="Feature already exists")

    feature = CarFeature(**feature_in.dict())
    session.add(feature)
    await session.commit()
    await session.refresh(feature)
    return feature


async def list_car_features(session: AsyncSession) -> List[CarFeature]:
    result = await session.exec(select(CarFeature))
    return result.all()


# ------------------ Car CRUD ------------------
async def list_provider_cars(
    provider_id: int,
    session: AsyncSession,
) -> List[Car]:
    result = await session.exec(
        select(Car)
        .options(
            selectinload(Car.images),
            selectinload(Car.features),
            selectinload(Car.reviews),
        )
        .where(Car.provider_id == provider_id)
    )
    return result.all()


async def create_car(
    car_in: CarCreate,
    provider_id: int,
    session: AsyncSession,
) -> Car:
    car = Car(provider_id=provider_id, **car_in.dict(exclude={"feature_ids"}))
    session.add(car)
    await session.commit()
    await session.refresh(car)

    # Attach features if provided
    if car_in.feature_ids:
        for fid in car_in.feature_ids:
            session.add(CarFeatureLink(car_id=car.id, feature_id=fid))
        await session.commit()

    return await get_car(car.id, session)


async def update_car(
    car_id: int, car_in: CarUpdate, provider_id: int, session: AsyncSession
) -> Car:
    result = await session.exec(
        select(Car).where(Car.id == car_id, Car.provider_id == provider_id)
    )
    car = result.first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    for field, value in car_in.dict(
        exclude_unset=True, exclude={"feature_ids"}
    ).items():
        setattr(car, field, value)

    session.add(car)
    await session.commit()

    # Update features if provided
    if car_in.feature_ids is not None:
        await session.exec(
            delete(CarFeatureLink).where(CarFeatureLink.car_id == car.id)
        )
        for fid in car_in.feature_ids:
            session.add(CarFeatureLink(car_id=car.id, feature_id=fid))
        await session.commit()

    return await get_car(car.id, session)


async def delete_car(
    car_id: int,
    provider_id: int,
    session: AsyncSession,
) -> None:
    result = await session.exec(
        select(Car).where(Car.id == car_id, Car.provider_id == provider_id)
    )
    car = result.first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    await session.delete(car)
    await session.commit()


async def get_car(car_id: int, session: AsyncSession) -> Car:
    result = await session.exec(
        select(Car)
        .options(
            selectinload(Car.images),
            selectinload(Car.features),
            selectinload(Car.reviews),
        )
        .where(Car.id == car_id)
    )
    car = result.first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


async def list_cars(
    session: AsyncSession,
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
) -> List[Car]:
    stmt = select(Car).options(
        selectinload(Car.images),
        selectinload(Car.features),
        selectinload(Car.reviews),
    )

    if city:
        stmt = stmt.where(Car.city.ilike(f"%{city}%"))
    if country:
        stmt = stmt.where(Car.country.ilike(f"%{country}%"))
    if min_price is not None:
        stmt = stmt.where(Car.price_per_day >= min_price)
    if max_price is not None:
        stmt = stmt.where(Car.price_per_day <= max_price)
    if seats is not None:
        stmt = stmt.where(Car.seats >= seats)
    if transmission:
        stmt = stmt.where(Car.transmission.ilike(transmission))
    if fuel_type:
        stmt = stmt.where(Car.fuel_type.ilike(fuel_type))
    if car_type_id:
        stmt = stmt.where(Car.car_type_id == car_type_id)

    result = await session.exec(stmt)
    return result.all()


# ------------------ Car Images ------------------
async def upload_car_image(
    car_id: int, provider_id: int, file: UploadFile, session: AsyncSession
) -> CarImage:
    result = await session.exec(
        select(Car).where(Car.id == car_id, Car.provider_id == provider_id)
    )
    car = result.first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    save_path = f"uploads/cars/{filename}"

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(await file.read())

    car_image = CarImage(car_id=car_id, image_path=save_path)
    session.add(car_image)
    await session.commit()
    await session.refresh(car_image)
    return car_image


# ------------------ Reviews ------------------
async def add_car_review(
    car_id: int, user: User, review_in: CarReviewCreate, session: AsyncSession
) -> CarReview:
    result = await session.exec(select(Car).where(Car.id == car_id))
    car = result.first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    review = CarReview(car_id=car_id, user_id=user.id, **review_in.dict())
    session.add(review)

    # Update rating avg
    car.review_count += 1
    car.rating_avg = (
        (car.rating_avg * (car.review_count - 1)) + review.rating
    ) / car.review_count

    session.add(car)
    await session.commit()
    await session.refresh(review)
    return review


async def list_car_reviews(
    car_id: int,
    session: AsyncSession,
) -> List[CarReview]:
    result = await session.exec(
        select(CarReview)
        .where(CarReview.car_id == car_id)
        .order_by(CarReview.created_at.desc())
    )
    return result.all()


# ------------------ Admin Delete ------------------
async def delete_car_type(
    type_id: int,
    session: AsyncSession,
) -> None:
    result = await session.exec(select(CarType).where(CarType.id == type_id))
    car_type = result.first()
    if not car_type:
        raise HTTPException(status_code=404, detail="Car type not found")

    await session.delete(car_type)
    await session.commit()


async def delete_car_feature(
    feature_id: int,
    session: AsyncSession,
) -> None:
    result = await session.exec(
        select(CarFeature).where(CarFeature.id == feature_id),
    )
    feature = result.first()
    if not feature:
        raise HTTPException(status_code=404, detail="Car feature not found")

    await session.delete(feature)
    await session.commit()


# ------------------ Featured Cars ------------------
async def get_featured_cars(session: AsyncSession) -> List[Car]:
    result = await session.exec(
        select(Car)
        .options(
            selectinload(Car.images),
            selectinload(Car.features),
            selectinload(Car.reviews),
        )
        .where(Car.is_featured.is_(True))
        .order_by(Car.created_at.desc())
    )

    return result.all()
