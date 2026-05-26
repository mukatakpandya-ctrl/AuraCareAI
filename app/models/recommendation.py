from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class RecommendationType(str, enum.Enum):
    routine = "routine"
    product = "product"
    weather = "weather"
    image_analysis = "image_analysis"


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rec_type = Column(Enum(RecommendationType), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)          # Full AI-generated text
    weather_context = Column(Text, nullable=True)   # JSON weather snapshot
    image_path = Column(String(512), nullable=True) # If generated from image
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="recommendations")
