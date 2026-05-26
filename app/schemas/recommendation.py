from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.recommendation import RecommendationType


class RecommendationOut(BaseModel):
    id: int
    user_id: int
    rec_type: RecommendationType
    title: str
    content: str
    weather_context: Optional[dict]
    image_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateRoutineRequest(BaseModel):
    include_weather: bool = True


class GenerateProductsRequest(BaseModel):
    category: str = "skincare"   # skincare | haircare | both
