from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.profile import SkinType, HairType, ActivityLevel, Budget


class ProfileCreate(BaseModel):
    skin_type: Optional[SkinType] = None
    hair_type: Optional[HairType] = None
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    water_intake_liters: Optional[float] = Field(None, ge=0, le=20)
    activity_level: Optional[ActivityLevel] = None
    skin_concerns: Optional[list[str]] = None
    hair_concerns: Optional[list[str]] = None
    budget: Optional[Budget] = None
    location_city: Optional[str] = None


class ProfileUpdate(ProfileCreate):
    pass


class ProfileOut(BaseModel):
    id: int
    user_id: int
    skin_type: Optional[SkinType]
    hair_type: Optional[HairType]
    sleep_hours: Optional[float]
    water_intake_liters: Optional[float]
    activity_level: Optional[ActivityLevel]
    skin_concerns: Optional[list[str]]
    hair_concerns: Optional[list[str]]
    budget: Optional[Budget]
    location_city: Optional[str]
    last_skin_analysis: Optional[dict]
    habit_score: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
