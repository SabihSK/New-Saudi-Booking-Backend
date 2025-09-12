from typing import List, Optional
from sqlmodel import SQLModel, Field, Column, String, Relationship
import enum
from datetime import datetime


class UserRole(str, enum.Enum):
    customer = "customer"
    provider = "provider"
    admin = "admin"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(
        sa_column=Column(String, unique=True, index=True, nullable=False)
    )
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.customer, nullable=False)
    profile_picture: Optional[str] = None
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    # relationships
    provider: Optional["Provider"] = Relationship(
        back_populates="user",
    )
    reviews: List["Review"] = Relationship(
        back_populates="user",
    )
