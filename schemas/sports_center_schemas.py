from pydantic import BaseModel
from typing import Optional


class SportsCenterCreate(BaseModel):
    user_id: int
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
    # user_id: int
    name: str
    cnpj: str
    latitude: float
    longitude: float
    photo_path: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True
