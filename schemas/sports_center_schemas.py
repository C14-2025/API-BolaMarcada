from pydantic import BaseModel
from typing import Optional


class SportsCenterCreate(BaseModel):
    user_id: str
    name: str
    cnpj: str
    latitude: float
    longitude: float
    photo_path: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class SportsCenterResponse(BaseModel):
    id: int
    user_id: str
    name: str
    cnpj: str
    latitude: float
    longitude: float
    photo_path: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


class SportsCenterUpdate(BaseModel):
    name: Optional[str] = None
    cnpj: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    photo_path: Optional[str] = None
