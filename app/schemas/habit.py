from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional


class HabitLogCreate(BaseModel):
    log_date: Optional[date] = None
    cleansed_face: bool = False
    moisturized: bool = False
    applied_sunscreen: bool = False
    washed_hair: bool = False
    drank_water: bool = False
    slept_enough: bool = False
    exercised: bool = False
    actual_water_liters: Optional[float] = Field(None, ge=0)
    actual_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    notes: Optional[str] = None


class HabitLogOut(BaseModel):
    id: int
    user_id: int
    log_date: date
    cleansed_face: bool
    moisturized: bool
    applied_sunscreen: bool
    washed_hair: bool
    drank_water: bool
    slept_enough: bool
    exercised: bool
    actual_water_liters: Optional[float]
    actual_sleep_hours: Optional[float]
    daily_score: float
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HabitSummary(BaseModel):
    """Aggregated habit stats for dashboard."""
    total_logs: int
    avg_daily_score: float
    current_streak: int          # Consecutive days with score >= 50
    best_streak: int
    habit_score: float           # Overall score stored in profile
    weekly_scores: list[dict]    # [{date, score}] last 7 days
