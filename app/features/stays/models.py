from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime
from app.features.providers.models import Provider
from app.features.users.models import User


class PropertyType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)


class StayAmenity(SQLModel, table=True):
    stay_id: int = Field(foreign_key="stay.id", primary_key=True)
    amenity_id: int = Field(foreign_key="amenity.id", primary_key=True)


class Amenity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)

    stays: List["Stay"] = Relationship(
        back_populates="amenities", link_model=StayAmenity
    )


class Stay(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )
    provider_id: int = Field(
        foreign_key="provider.id",
        nullable=False,
    )
    property_type_id: int = Field(
        foreign_key="propertytype.id",
        nullable=False,
    )

    name: str
    description: str
    address_line: Optional[str] = None
    street: str
    city: str
    country: str
    price_per_night: float
    service_fee: float = Field(default=0.0)
    tax_percent: float = Field(default=0.0)
    rooms: int
    max_adults: int
    max_children: int
    is_featured: bool = Field(default=False)
    rating_avg: Optional[float] = 0.0
    review_count: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    # relationships
    provider: "Provider" = Relationship(
        back_populates="stays",
    )
    amenities: List["Amenity"] = Relationship(
        back_populates="stays", link_model=StayAmenity
    )
    images: List["StayImage"] = Relationship(
        back_populates="stay",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )
    reviews: List["Review"] = Relationship(
        back_populates="stay",
        sa_relationship_kwargs={"cascade": "all, delete"},
    )


class StayImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stay_id: int = Field(foreign_key="stay.id", nullable=False)
    image_path: str

    stay: "Stay" = Relationship(back_populates="images")


class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stay_id: int = Field(foreign_key="stay.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)

    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    stay: "Stay" = Relationship(
        back_populates="reviews",
    )
    user: "User" = Relationship(
        back_populates="reviews",
    )
