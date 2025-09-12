from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# -------- Amenity --------
class AmenityBase(BaseModel):
    name: str


class AmenityCreate(AmenityBase):
    pass


class AmenityRead(AmenityBase):
    id: int

    class Config:
        from_attributes = True


# -------- Property Type --------
class PropertyTypeBase(BaseModel):
    name: str


class PropertyTypeCreate(PropertyTypeBase):
    pass


class PropertyTypeRead(PropertyTypeBase):
    id: int

    class Config:
        from_attributes = True


# -------- Stay --------
class StayBase(BaseModel):
    name: str
    description: str
    address_line: Optional[str] = None
    street: str
    city: str
    country: str
    price_per_night: float
    service_fee: float = 0.0
    tax_percent: float = 0.0
    rooms: int
    max_adults: int
    max_children: int


class StayCreate(StayBase):
    property_type_id: int = 1
    amenity_ids: List[int] = []


class PriceBreakdown(BaseModel):
    subtotal: float
    service_fee: float
    taxes: float
    total: float


class StayImageRead(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True


class StayRead(StayBase):
    id: int
    property_type_id: int
    provider_id: int
    is_featured: bool
    rating_avg: float
    review_count: int
    created_at: datetime
    amenities: List[AmenityRead] = []
    images: List[StayImageRead] = []
    price_breakdown: Optional[PriceBreakdown] = None

    class Config:
        from_attributes = True


# -------- Reviews --------
class ReviewBase(BaseModel):
    rating: int
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    pass


class ReviewRead(ReviewBase):
    id: int
    user_id: int
    stay_id: int
    created_at: datetime

    class Config:
        from_attributes = True
