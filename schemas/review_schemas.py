from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

# --------- Fields ---------
class FieldCreate(BaseModel):
    sports_center_id: int
    name: str
    field_type: str
    price_per_hour: float
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)  # v2: substitui class Config/orm_mode


class FieldUpdate(BaseModel):
    # Para PATCH/PUT parcial: precisa ter default None
    name: Optional[str] = None
    field_type: Optional[str] = None
    price_per_hour: Optional[float] = None
    photo_path: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

# --------- Reviews ---------
class ReviewBase(BaseModel):
    user_id: str
    sports_center_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(BaseModel):
    id: str
    user_id: str          # mantido como str p/ ficar consistente com ReviewBase
    sports_center_id: int
    rating: int
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
