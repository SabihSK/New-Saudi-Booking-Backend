from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ------------------ Car Types ------------------
class CarTypeBase(BaseModel):
    name: str = Field(
        ...,
        description="Car type name (e.g. SUV, Compact, Luxury)",
    )


class CarTypeCreate(CarTypeBase):
    pass


class CarTypeRead(CarTypeBase):
    id: int

    class Config:
        from_attributes = True


# ------------------ Car Features ------------------
class CarFeatureBase(BaseModel):
    name: str = Field(
        ...,
        description="Feature name (e.g. GPS, AC, Bluetooth)",
    )


class CarFeatureCreate(CarFeatureBase):
    pass


class CarFeatureRead(CarFeatureBase):
    id: int

    class Config:
        from_attributes = True


# ------------------ Car ------------------
class CarBase(BaseModel):
    name: str = Field(..., description="Car model name (e.g. Toyota Camry)")
    brand: str = Field(..., description="Car brand (e.g. Toyota)")
    year: int = Field(
        ...,
        ge=1900,
        le=2100,
        description="Car manufacturing year",
    )
    description: str
    city: str
    country: str
    price_per_day: float = Field(..., ge=0, description="Daily rental price")
    seats: int = Field(..., ge=1, description="Number of seats")
    transmission: str = Field(
        ...,
        description="Transmission type (Automatic / Manual)",
    )
    fuel_type: str = Field(
        ..., description="Fuel type (Gasoline / Diesel / Electric / Hybrid)"
    )


class CarCreate(CarBase):
    car_type_id: int
    feature_ids: Optional[List[int]] = []


class CarUpdate(BaseModel):
    name: Optional[str] = None
    brand: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    description: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    price_per_day: Optional[float] = Field(None, ge=0)
    seats: Optional[int] = Field(None, ge=1)
    transmission: Optional[str] = None
    fuel_type: Optional[str] = None
    is_featured: Optional[bool] = None
    car_type_id: Optional[int] = None
    feature_ids: Optional[List[int]] = None


# ------------------ Car Images ------------------
class CarImageRead(BaseModel):
    id: int
    image_path: str

    class Config:
        from_attributes = True


# ------------------ Car Reviews ------------------
class CarReviewBase(BaseModel):
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Rating from 1 to 5 stars",
    )
    comment: str = Field(..., description="Review comment")


class CarReviewCreate(CarReviewBase):
    pass


class CarReviewRead(CarReviewBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ------------------ Car Read ------------------
class CarRead(CarBase):
    id: int
    provider_id: int
    car_type_id: int
    is_featured: bool
    rating_avg: float
    review_count: int
    created_at: datetime

    images: List[CarImageRead] = []
    features: List[CarFeatureRead] = []
    reviews: List[CarReviewRead] = []

    class Config:
        from_attributes = True
