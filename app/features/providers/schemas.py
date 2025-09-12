from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProviderBase(BaseModel):
    company_name: str
    contact_number: str
    address: Optional[str] = None


class ProviderCreate(ProviderBase):
    tax_id: Optional[str] = None
    business_license_number: Optional[str] = None
    website: Optional[str] = None


class ProviderRead(ProviderBase):
    id: int
    user_id: int
    tax_id: Optional[str] = None
    business_license_number: Optional[str] = None
    website: Optional[str] = None
    document_path: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderUpdate(BaseModel):
    company_name: Optional[str] = None
    contact_number: Optional[str] = None
    address: Optional[str] = None
