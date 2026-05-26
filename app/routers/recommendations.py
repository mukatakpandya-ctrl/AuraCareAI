from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.recommendation import Recommendation, RecommendationType
from app.schemas.recommendation import RecommendationOut, GenerateRoutineRequest, GenerateProductsRequest
from app.services.gemini_service import generate_grooming_routine, recommend_products
from app.services.weather_service import get_weather
from app.utils.auth import get_current_user
from app.utils.helpers import from_json_str, to_json_str

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


def _get_profile_dict(profile: UserProfile) -> dict:
    return {
        "skin_type": profile.skin_type,
        "hair_type": profile.hair_type,
        "sleep_hours": profile.sleep_hours,
        "water_intake_liters": profile.water_intake_liters,
        "activity_level": profile.activity_level,
        "skin_concerns": from_json_str(profile.skin_concerns) or [],
        "hair_concerns": from_json_str(profile.hair_concerns) or [],
        "budget": profile.budget,
        "location_city": profile.location_city,
        "habit_score": profile.habit_score,
    }


@router.post("/routine", response_model=dict, status_code=201)
async def generate_routine(
    payload: GenerateRoutineRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a personalized AM/PM grooming routine (optionally weather-aware)."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first.")

    profile_dict = _get_profile_dict(profile)
    weather = None
    weather_json = None

    if payload.include_weather and profile.location_city:
        weather = await get_weather(profile.location_city)
        weather_json = to_json_str(weather) if weather else None

    content = generate_grooming_routine(profile_dict, weather)

    rec = Recommendation(
        user_id=current_user.id,
        rec_type=RecommendationType.routine,
        title="Personalized Grooming Routine",
        content=content,
        weather_context=weather_json,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "id": rec.id,
        "title": rec.title,
        "content": content,
        "weather": weather,
        "created_at": rec.created_at,
    }


@router.post("/products", response_model=dict, status_code=201)
def generate_products(
    payload: GenerateProductsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate product recommendations based on user profile and budget."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Complete your profile first.")

    content = recommend_products(_get_profile_dict(profile), payload.category)

    rec = Recommendation(
        user_id=current_user.id,
        rec_type=RecommendationType.product,
        title=f"Product Recommendations — {payload.category.title()}",
        content=content,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "id": rec.id,
        "title": rec.title,
        "content": content,
        "created_at": rec.created_at,
    }


@router.get("", response_model=list[dict])
def list_recommendations(
    rec_type: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List past recommendations for the current user."""
    q = db.query(Recommendation).filter(Recommendation.user_id == current_user.id)
    if rec_type:
        q = q.filter(Recommendation.rec_type == rec_type)
    recs = q.order_by(Recommendation.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "rec_type": r.rec_type,
            "title": r.title,
            "content": r.content,
            "weather_context": from_json_str(r.weather_context),
            "created_at": r.created_at,
        }
        for r in recs
    ]


@router.get("/{rec_id}", response_model=dict)
def get_recommendation(
    rec_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rec = db.query(Recommendation).filter(
        Recommendation.id == rec_id,
        Recommendation.user_id == current_user.id,
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found.")
    return {
        "id": rec.id,
        "rec_type": rec.rec_type,
        "title": rec.title,
        "content": rec.content,
        "weather_context": from_json_str(rec.weather_context),
        "image_path": rec.image_path,
        "created_at": rec.created_at,
    }
