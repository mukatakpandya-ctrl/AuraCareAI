from datetime import datetime, date
from sqlalchemy import Column, Integer, Boolean, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class HabitLog(Base):
    __tablename__ = "habit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(Date, default=date.today, nullable=False)

    # Daily grooming habits
    cleansed_face = Column(Boolean, default=False)
    moisturized = Column(Boolean, default=False)
    applied_sunscreen = Column(Boolean, default=False)
    washed_hair = Column(Boolean, default=False)
    drank_water = Column(Boolean, default=False)       # Met daily water goal
    slept_enough = Column(Boolean, default=False)      # Met sleep goal
    exercised = Column(Boolean, default=False)

    # Quantitative
    actual_water_liters = Column(Float, nullable=True)
    actual_sleep_hours = Column(Float, nullable=True)

    # Computed daily score (0–100)
    daily_score = Column(Float, default=0.0)

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="habits")
