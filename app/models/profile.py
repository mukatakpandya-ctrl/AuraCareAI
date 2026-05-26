from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class SkinType(str, enum.Enum):
    oily = "oily"
    dry = "dry"
    combination = "combination"
    sensitive = "sensitive"
    normal = "normal"


class HairType(str, enum.Enum):
    straight = "straight"
    wavy = "wavy"
    curly = "curly"
    coily = "coily"


class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"


class Budget(str, enum.Enum):
    low = "low"        # < ₹500
    medium = "medium"  # ₹500–₹2000
    high = "high"      # > ₹2000


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Skin & Hair
    skin_type = Column(Enum(SkinType), nullable=True)
    hair_type = Column(Enum(HairType), nullable=True)

    # Lifestyle
    sleep_hours = Column(Float, nullable=True)           # avg hours/night
    water_intake_liters = Column(Float, nullable=True)   # avg liters/day
    activity_level = Column(Enum(ActivityLevel), nullable=True)

    # Concerns & Preferences
    skin_concerns = Column(Text, nullable=True)          # JSON list: ["acne","dark_spots"]
    hair_concerns = Column(Text, nullable=True)          # JSON list: ["dandruff","hair_fall"]
    budget = Column(Enum(Budget), nullable=True)
    location_city = Column(String(120), nullable=True)   # For weather API

    # AI Analysis
    last_skin_analysis = Column(Text, nullable=True)     # JSON result from Gemini
    profile_image_path = Column(String(512), nullable=True)

    # Habit score (0–100)
    habit_score = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="profile")
