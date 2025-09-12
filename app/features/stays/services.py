from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from fastapi import HTTPException
from typing import List, Optional
from sqlalchemy.orm import selectinload
import os
import shutil

from app.features.stays.models import (
    Stay,
    StayImage,
    Amenity,
    StayAmenity,
    PropertyType,
    Review,
)
from app.features.stays.schemas import (
    AmenityRead,
    PriceBreakdown,
    StayCreate,
    ReviewCreate,
    AmenityCreate,
    PropertyTypeCreate,
    StayImageRead,
    StayRead,
)
from app.features.providers.models import Provider, ProviderStatus
from app.features.users.models import User
from app.core.config import settings


# -------- Providers: Stay CRUD --------
async def create_stay(
    stay_in: StayCreate,
    provider: Provider,
    session: AsyncSession,
) -> StayRead:
    if provider.status != ProviderStatus.approved:
        raise HTTPException(status_code=403, detail="Provider not approved")

    # Create Stay
    stay = Stay(
        provider_id=provider.id,
        **stay_in.dict(exclude={"amenity_ids"}),
    )
    session.add(stay)
    await session.flush()

    # Link amenities
    if stay_in.amenity_ids:
        for amenity_id in stay_in.amenity_ids:
            session.add(StayAmenity(stay_id=stay.id, amenity_id=amenity_id))

    await session.commit()

    # Reload with relationships
    stmt = (
        select(Stay)
        .where(Stay.id == stay.id)
        .options(
            selectinload(Stay.images),
            selectinload(Stay.amenities),
            selectinload(Stay.reviews),
        )
    )
    result = await session.exec(stmt)
    stay = result.one()

    # Compute price breakdown
    subtotal = stay.price_per_night
    taxes = subtotal * stay.tax_percent / 100
    breakdown = PriceBreakdown(
        subtotal=subtotal,
        service_fee=stay.service_fee,
        taxes=taxes,
        total=subtotal + stay.service_fee + taxes,
    )

    # ✅ Return clean Pydantic schema
    return StayRead(
        id=stay.id,
        provider_id=stay.provider_id,
        property_type_id=stay.property_type_id,
        name=stay.name,
        description=stay.description,
        address_line=stay.address_line,
        street=stay.street,
        city=stay.city,
        country=stay.country,
        price_per_night=stay.price_per_night,
        service_fee=stay.service_fee,
        tax_percent=stay.tax_percent,
        rooms=stay.rooms,
        max_adults=stay.max_adults,
        max_children=stay.max_children,
        is_featured=stay.is_featured,
        rating_avg=stay.rating_avg or 0,
        review_count=stay.review_count,
        created_at=stay.created_at,
        amenities=[AmenityRead.from_orm(a) for a in stay.amenities],
        images=[img.image_path for img in stay.images],
        price_breakdown=breakdown,
    )


async def update_stay(
    stay_id: int,
    stay_in: StayCreate,
    provider: Provider,
    session: AsyncSession,
) -> Stay:
    stmt = select(Stay).where(
        Stay.id == stay_id,
        Stay.provider_id == provider.id,
    )
    result = await session.exec(stmt)
    stay = result.first()
    if not stay:
        raise HTTPException(status_code=404, detail="Stay not found")

    for field, value in stay_in.dict().items():
        setattr(stay, field, value)

    await session.commit()
    await session.refresh(stay)
    return stay


async def delete_stay(
    stay_id: int,
    provider: Provider,
    session: AsyncSession,
) -> None:
    stmt = select(Stay).where(
        Stay.id == stay_id,
        Stay.provider_id == provider.id,
    )
    result = await session.exec(stmt)
    stay = result.first()
    if not stay:
        raise HTTPException(status_code=404, detail="Stay not found")

    await session.delete(stay)
    await session.commit()


async def get_single_stay_detail(
    stay_id: int,
    session: AsyncSession,
    check_in: Optional[date],
    check_out: Optional[date],
    rooms: int,
):
    stmt = (
        select(Stay)
        .where(Stay.id == stay_id)
        .options(
            selectinload(Stay.amenities),
            selectinload(Stay.images),
            selectinload(Stay.reviews),
        )
    )
    result = await session.exec(stmt)
    stay = result.first()
    if not stay:
        raise HTTPException(status_code=404, detail="Stay not found")

    stay_data = StayRead.from_orm(stay)

    if check_in and check_out:
        breakdown = calculate_price_breakdown(stay, check_in, check_out, rooms)
        stay_data.price_breakdown = breakdown

    return stay_data


# -------- Stay Images --------


async def upload_stay_image(
    stay_id: int,
    provider: Provider,
    file,
    session: AsyncSession,
) -> StayImage:
    stmt = select(Stay).where(
        Stay.id == stay_id,
        Stay.provider_id == provider.id,
    )
    result = await session.exec(stmt)
    stay = result.first()
    if not stay:
        raise HTTPException(status_code=404, detail="Stay not found")

    os.makedirs(
        settings.UPLOAD_STAYS_DIR,
        exist_ok=True,
    )
    filepath = os.path.join(
        settings.UPLOAD_STAYS_DIR,
        f"stay_{stay.id}_{file.filename}",
    )
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    db_image = StayImage(stay_id=stay.id, image_path=filepath)
    session.add(db_image)
    await session.commit()
    await session.refresh(db_image)
    return db_image


# -------- Amenities --------
async def assign_amenities(
    stay_id: int,
    amenity_ids: List[int],
    provider: Provider,
    session: AsyncSession,
) -> Stay:
    stmt = select(Stay).where(
        Stay.id == stay_id,
        Stay.provider_id == provider.id,
    )
    result = await session.exec(stmt)
    stay = result.first()
    if not stay:
        raise HTTPException(status_code=404, detail="Stay not found")

    # Clear old amenities
    await session.exec(
        select(StayAmenity).where(StayAmenity.stay_id == stay.id).delete()
    )

    # Assign new ones
    for amenity_id in amenity_ids:
        session.add(StayAmenity(stay_id=stay.id, amenity_id=amenity_id))

    await session.commit()
    await session.refresh(stay)
    return stay


# -------- Reviews --------
async def add_review(
    stay_id: int, user: User, review_in: ReviewCreate, session: AsyncSession
) -> Review:
    db_review = Review(
        stay_id=stay_id,
        user_id=user.id,
        rating=review_in.rating,
        comment=review_in.comment,
    )
    session.add(db_review)
    await session.commit()
    await session.refresh(db_review)

    # Update stay rating avg & review count
    avg_stmt = select(func.avg(Review.rating), func.count(Review.id)).where(
        Review.stay_id == stay_id
    )
    avg_result = await session.exec(avg_stmt)
    avg_rating, review_count = avg_result.one()

    stay_stmt = select(Stay).where(Stay.id == stay_id)
    stay_result = await session.exec(stay_stmt)
    stay = stay_result.first()
    if stay:
        stay.rating_avg = round(avg_rating or 0.0, 1)
        stay.review_count = review_count
        await session.commit()

    return db_review


# -------- Admin: Manage Amenities & Property Types --------
async def create_amenity(
    amenity_in: AmenityCreate,
    session: AsyncSession,
) -> Amenity:
    db_amenity = Amenity(name=amenity_in.name)
    session.add(db_amenity)
    await session.commit()
    await session.refresh(db_amenity)
    return db_amenity


async def list_amenities(session: AsyncSession) -> List[Amenity]:
    stmt = select(Amenity)
    result = await session.exec(stmt)
    return result.all()


async def delete_amenity(amenity_id: int, session: AsyncSession) -> None:
    stmt = select(Amenity).where(Amenity.id == amenity_id)
    result = await session.exec(stmt)
    amenity = result.first()
    if not amenity:
        raise HTTPException(status_code=404, detail="Amenity not found")

    await session.delete(amenity)
    await session.commit()


async def create_property_type(
    pt_in: PropertyTypeCreate,
    session: AsyncSession,
) -> PropertyType:
    db_type = PropertyType(name=pt_in.name)
    session.add(db_type)
    await session.commit()
    await session.refresh(db_type)
    return db_type


async def list_property_types(session: AsyncSession) -> List[PropertyType]:
    stmt = select(PropertyType)
    result = await session.exec(stmt)
    return result.all()


async def delete_property_type(pt_id: int, session: AsyncSession) -> None:
    stmt = select(PropertyType).where(PropertyType.id == pt_id)
    result = await session.exec(stmt)
    prop_type = result.first()
    if not prop_type:
        raise HTTPException(status_code=404, detail="Property type not found")

    await session.delete(prop_type)
    await session.commit()


# -------- Public: Search stays --------
async def search_stays(
    session: AsyncSession,
    city: Optional[str] = None,
    country: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    min_rating: Optional[float] = None,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    rooms: Optional[int] = None,
    amenities: Optional[List[int]] = None,
    sort_by: str = "price_asc",
    page: int = 1,
    page_size: int = 20,
    check_in: Optional[date] = None,
    check_out: Optional[date] = None,
) -> List[StayRead]:
    stmt = select(Stay).options(
        selectinload(Stay.amenities),
        selectinload(Stay.images),
        selectinload(Stay.reviews),
    )

    if city:
        stmt = stmt.where(Stay.city.ilike(f"%{city}%"))
    if country:
        stmt = stmt.where(Stay.country.ilike(f"%{country}%"))
    if price_min is not None:
        stmt = stmt.where(Stay.price_per_night >= price_min)
    if price_max is not None:
        stmt = stmt.where(Stay.price_per_night <= price_max)
    if min_rating is not None:
        stmt = stmt.where(Stay.rating_avg >= min_rating)
    if rooms is not None:
        stmt = stmt.where(Stay.rooms >= rooms)
    if adults is not None:
        stmt = stmt.where(Stay.max_adults >= adults)
    if children is not None:
        stmt = stmt.where(Stay.max_children >= children)

    result = await session.exec(stmt)
    stays = result.all()

    # --- Sorting ---
    if sort_by == "price_asc":
        stays.sort(key=lambda s: s.price_per_night)
    elif sort_by == "price_desc":
        stays.sort(key=lambda s: s.price_per_night, reverse=True)
    elif sort_by == "rating_desc":
        stays.sort(key=lambda s: s.rating_avg, reverse=True)
    elif sort_by == "popularity":
        stays.sort(key=lambda s: s.review_count, reverse=True)
    elif sort_by == "featured":
        stays = [s for s in stays if s.is_featured]

    # --- Pagination ---
    start = (page - 1) * page_size
    end = start + page_size
    stays = stays[start:end]

    # --- Map ORM → Schema ---
    results: List[StayRead] = []
    for stay in stays:
        subtotal = stay.price_per_night
        taxes = subtotal * stay.tax_percent / 100
        breakdown = PriceBreakdown(
            subtotal=subtotal,
            service_fee=stay.service_fee,
            taxes=taxes,
            total=subtotal + stay.service_fee + taxes,
        )

        results.append(
            StayRead(
                id=stay.id,
                provider_id=stay.provider_id,
                property_type_id=stay.property_type_id,
                name=stay.name,
                description=stay.description,
                address_line=stay.address_line,
                street=stay.street,
                city=stay.city,
                country=stay.country,
                price_per_night=stay.price_per_night,
                service_fee=stay.service_fee,
                tax_percent=stay.tax_percent,
                rooms=stay.rooms,
                max_adults=stay.max_adults,
                max_children=stay.max_children,
                is_featured=stay.is_featured,
                rating_avg=stay.rating_avg or 0,
                review_count=stay.review_count,
                created_at=stay.created_at,
                amenities=[AmenityRead.from_orm(a) for a in stay.amenities],
                images=[StayImageRead.from_orm(img) for img in stay.images],
                price_breakdown=breakdown,
            )
        )

    return results


def calculate_price_breakdown(
    stay: Stay, check_in: date, check_out: date, rooms: int = 1
) -> dict:
    nights = (check_out - check_in).days
    if nights <= 0:
        raise HTTPException(status_code=400, detail="Invalid date range")

    subtotal = stay.price_per_night * nights * rooms
    service_fee = stay.service_fee
    taxes = subtotal * (stay.tax_percent / 100)
    total = subtotal + service_fee + taxes

    return {
        "subtotal": round(subtotal, 2),
        "service_fee": round(service_fee, 2),
        "taxes": round(taxes, 2),
        "total": round(total, 2),
    }


async def get_stays_by_provider(
    user: User,
    session: AsyncSession,
) -> List[StayRead]:
    stmt = select(Provider).where(Provider.user_id == user.id)
    result = await session.exec(stmt)
    provider = result.first()
    if not provider:
        raise HTTPException(
            status_code=404,
            detail="Provider profile not found",
        )

    stmt = (
        select(Stay)
        .where(Stay.provider_id == provider.id)
        .options(
            selectinload(Stay.images),
            selectinload(Stay.amenities),
            selectinload(Stay.reviews),
        )
    )
    result = await session.exec(stmt)
    stays = result.all()

    return [
        StayRead(
            id=s.id,
            provider_id=s.provider_id,
            property_type_id=s.property_type_id,
            name=s.name,
            description=s.description,
            address_line=s.address_line,
            street=s.street,
            city=s.city,
            country=s.country,
            price_per_night=s.price_per_night,
            service_fee=s.service_fee,
            tax_percent=s.tax_percent,
            rooms=s.rooms,
            max_adults=s.max_adults,
            max_children=s.max_children,
            is_featured=s.is_featured,
            rating_avg=s.rating_avg or 0,
            review_count=s.review_count,
            created_at=s.created_at,
            amenities=[AmenityRead.from_orm(a) for a in s.amenities],
            images=[img.image_path for img in s.images],
            price_breakdown=None,  # you can add breakdown later
        )
        for s in stays
    ]
