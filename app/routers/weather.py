from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.user import User
from app.models.profile import UserProfile
from app.services.weather_service import get_weather
from app.utils.auth import get_current_user
from app.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/weather", tags=["Weather"])


@router.get("")
async def current_weather(
    city: str = Query(None, description="City name. Defaults to user's profile city."),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch current weather for a city.
    Falls back to the user's profile city if no query param is provided.
    """
    if not city:
        profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
        city = (profile.location_city if profile else None) or "Mumbai"

    weather = await get_weather(city)
    if weather is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found or weather data unavailable.")
    return weather
