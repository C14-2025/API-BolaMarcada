from typing import Optional
from pydantic import BaseModel, ConfigDict

class SportsCenterCreate(BaseModel):
    user_id: str
    name: str
    cnpj: str
    latitude: float
    longitude: float
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)  # v2

class SportsCenterResponse(BaseModel):
    id: int
    user_id: str
    name: str
    cnpj: str
    latitude: float
    longitude: float
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SportsCenterUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
