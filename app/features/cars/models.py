from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime


class CarType(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)

    cars: List["Car"] = Relationship(back_populates="car_type")


# ✅ single definition of CarFeatureLink (link table)
class CarFeatureLink(SQLModel, table=True):
    car_id: int = Field(foreign_key="car.id", primary_key=True)
    feature_id: int = Field(foreign_key="carfeature.id", primary_key=True)


class CarFeature(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, nullable=False)

    # cars <-> features many-to-many
    cars: List["Car"] = Relationship(
        back_populates="features", link_model=CarFeatureLink
    )


class Car(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    provider_id: int = Field(foreign_key="provider.id", nullable=False)
    car_type_id: int = Field(foreign_key="cartype.id", nullable=False)

    # Core fields
    name: str
    brand: str
    year: int
    description: str
    city: str
    country: str

    # Rental details
    price_per_day: float
    seats: int
    transmission: str
    fuel_type: str
    is_featured: bool = Field(default=False)

    # Stats
    rating_avg: Optional[float] = 0.0
    review_count: int = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    images: List["CarImage"] = Relationship(
        back_populates="car",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    car_type: Optional[CarType] = Relationship(back_populates="cars")

    # ✅ direct Car.features → List[CarFeature]
    features: List[CarFeature] = Relationship(
        back_populates="cars", link_model=CarFeatureLink
    )

    reviews: List["CarReview"] = Relationship(
        back_populates="car",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class CarImage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="car.id", nullable=False)
    image_path: str

    car: Optional[Car] = Relationship(back_populates="images")


class CarReview(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    car_id: int = Field(foreign_key="car.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)

    rating: int
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    car: Optional[Car] = Relationship(back_populates="reviews")
