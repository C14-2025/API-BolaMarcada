from pydantic import BaseModel
from typing import Optional


class FieldCreate(BaseModel):
    sports_center_id: int
    name : str
    field_type: str
    price_per_hour: float
    photo_path: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True

class FieldUpdate(BaseModel):
    name : Optional[str]
    field_type: Optional[str]
    price_per_hour: Optional[float]
    photo_path: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True