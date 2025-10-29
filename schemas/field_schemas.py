from typing import Optional
from pydantic import BaseModel, ConfigDict


class FieldCreate(BaseModel):
    sports_center_id: int
    name: str
    field_type: str
    price_per_hour: float
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)  # v2 (substitui class Config)


class FieldUpdate(BaseModel):
    name: Optional[str] = None
    field_type: Optional[str] = None
    price_per_hour: Optional[float] = None
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
