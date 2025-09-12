import enum
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime


class ProviderStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Provider(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False, index=True)
    company_name: str
    contact_number: str
    address: Optional[str] = None
    tax_id: Optional[str] = None
    business_license_number: Optional[str] = None
    website: Optional[str] = None
    document_path: Optional[str] = None
    status: ProviderStatus = Field(
        default=ProviderStatus.pending,
        nullable=False,
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
    )

    # relationships
    user: Optional["User"] = Relationship(
        back_populates="provider",
    )
    stays: List["Stay"] = Relationship(
        back_populates="provider",
    )
