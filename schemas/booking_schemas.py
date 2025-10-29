from datetime import datetime
from pydantic import BaseModel, ConfigDict


class BookingCreate(BaseModel):
    user_id: int
    field_id: int
    booking_date: datetime
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)
