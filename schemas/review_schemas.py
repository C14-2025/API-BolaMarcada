from pydantic import BaseModel, Field
from typing import Optional


class ReviewBase(BaseModel):
    user_id: str
    sports_center_id: int
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    comment: Optional[str] = None

    class Config:
        from_attributes = True


class ReviewCreate(ReviewBase):
    pass


class ReviewResponse(BaseModel):
    id: str
    user_id: int
    sports_center_id: int
    rating: int
    comment: Optional[str]

    class Config:
        from_attributes = True