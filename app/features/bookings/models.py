from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import date


class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    stay_id: int = Field(foreign_key="stay.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)

    check_in: date
    check_out: date
    rooms: int
