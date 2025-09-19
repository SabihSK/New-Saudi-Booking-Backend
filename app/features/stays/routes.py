from datetime import date
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.core.db import get_session
from app.core.security.permissions import require_role
from app.features.users.models import User
from app.features.providers.services import get_provider_by_user


from app.features.stays import services
from app.features.stays.schemas import (
    StayCreate,
    StayRead,
    ReviewCreate,
    ReviewRead,
    AmenityCreate,
    AmenityRead,
    PropertyTypeCreate,
    PropertyTypeRead,
)

router = APIRouter(prefix="/stays", tags=["stays"])


@router.get("/", response_model=List[StayRead])
async def search_stays(
    city: Optional[str] = None,
    country: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    min_rating: Optional[float] = None,
    adults: Optional[int] = None,
    children: Optional[int] = None,
    rooms: Optional[int] = None,
    amenities: Optional[List[int]] = Query(None),
    property_type_id: Optional[int] = None,
    sort_by: str = "price_asc",
    page: int = 1,
    page_size: int = 20,
    check_in: Optional[date] = None,
    check_out: Optional[date] = None,
    session: AsyncSession = Depends(get_session),
):
    return await services.search_stays(
        session=session,
        city=city,
        country=country,
        price_min=price_min,
        price_max=price_max,
        min_rating=min_rating,
        adults=adults,
        children=children,
        rooms=rooms,
        amenities=amenities,
        property_type_id=property_type_id,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
        check_in=check_in,
        check_out=check_out,
    )


@router.get("/featured", response_model=List[StayRead])
async def featured_stays(session: AsyncSession = Depends(get_session)):
    return await services.get_featured_stays(session)


@router.get("/{stay_id}", response_model=StayRead)
async def get_stay_detail(
    stay_id: int,
    check_in: Optional[date] = None,
    check_out: Optional[date] = None,
    rooms: int = 1,
    session: AsyncSession = Depends(get_session),
):
    stay_data = await services.get_single_stay_detail(
        stay_id,
        session,
        check_in,
        check_out,
        rooms,
    )
    return stay_data


@router.get("/{stay_id}/reviews", response_model=List[ReviewRead])
async def list_reviews(
    stay_id: int,
    session: AsyncSession = Depends(get_session),
):
    stmt = await session.exec(
        services.select(services.Review).where(
            services.Review.stay_id == stay_id,
        )
    )
    return stmt.all()


provider_stays_router = APIRouter(
    prefix="/providers/stays",
    tags=["provider-stays"],
)


@provider_stays_router.get("/", response_model=List[StayRead])
async def get_my_stays(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    return await services.get_stays_by_provider(current_user, session)


@provider_stays_router.post("/", response_model=StayRead)
async def create_stay(
    stay_in: StayCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.create_stay(stay_in, provider, session)


@provider_stays_router.put("/{stay_id}", response_model=StayRead)
async def update_stay(
    stay_id: int,
    stay_in: StayCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.update_stay(stay_id, stay_in, provider, session)


@provider_stays_router.delete("/{stay_id}", status_code=204)
async def delete_stay(
    stay_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    await services.delete_stay(stay_id, provider, session)
    return None


@provider_stays_router.post("/{stay_id}/images")
async def upload_image(
    stay_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.upload_stay_image(stay_id, provider, file, session)


@provider_stays_router.post("/{stay_id}/amenities", response_model=StayRead)
async def assign_amenities(
    stay_id: int,
    amenity_ids: List[int],
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    provider = await get_provider_by_user(current_user, session)
    return await services.assign_amenities(
        stay_id,
        amenity_ids,
        provider,
        session,
    )


@router.post("/{stay_id}/reviews", response_model=ReviewRead)
async def add_review(
    stay_id: int,
    review_in: ReviewCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("customer")),
):
    return await services.add_review(stay_id, current_user, review_in, session)


admin_stays_router = APIRouter(prefix="/admin/stays", tags=["admin-stays"])


# ---- Amenities ----
@admin_stays_router.post("/amenities", response_model=AmenityRead)
async def create_amenity(
    amenity_in: AmenityCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.create_amenity(amenity_in, session)


@admin_stays_router.get("/amenities", response_model=List[AmenityRead])
async def list_amenities(session: AsyncSession = Depends(get_session)):
    return await services.list_amenities(session)


@admin_stays_router.delete("/amenities/{amenity_id}", status_code=204)
async def delete_amenity(
    amenity_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    await services.delete_amenity(amenity_id, session)
    return None


# ---- Property Types ----
@admin_stays_router.post("/property-types", response_model=PropertyTypeRead)
async def create_property_type(
    pt_in: PropertyTypeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    return await services.create_property_type(pt_in, session)


@admin_stays_router.get(
    "/property-types",
    response_model=List[PropertyTypeRead],
)
async def list_property_types(session: AsyncSession = Depends(get_session)):
    return await services.list_property_types(session)


@admin_stays_router.delete("/property-types/{pt_id}", status_code=204)
async def delete_property_type(
    pt_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(require_role("admin")),
):
    await services.delete_property_type(pt_id, session)
    return None
