from pydantic import BaseModel, ConfigDict
from datetime import datetime


class AvailabilityCreate(BaseModel):
    field_id: int
    day_of_week: int
    start_time: datetime
    end_time: datetime

    model_config = ConfigDict(from_attributes=True)
