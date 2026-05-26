import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileOut
from app.utils.auth import get_current_user
from app.utils.helpers import to_json_str, from_json_str

router = APIRouter(prefix="/api/profile", tags=["Profile"])


def _serialize(profile: UserProfile) -> dict:
    """Convert ORM profile to dict with JSON fields parsed."""
    d = {c.name: getattr(profile, c.name) for c in profile.__table__.columns}
    d["skin_concerns"] = from_json_str(d.get("skin_concerns"))
    d["hair_concerns"] = from_json_str(d.get("hair_concerns"))
    d["last_skin_analysis"] = from_json_str(d.get("last_skin_analysis"))
    return d


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create onboarding profile (questionnaire answers)."""
    if db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Profile already exists. Use PUT to update.")

    profile = UserProfile(
        user_id=current_user.id,
        skin_type=payload.skin_type,
        hair_type=payload.hair_type,
        sleep_hours=payload.sleep_hours,
        water_intake_liters=payload.water_intake_liters,
        activity_level=payload.activity_level,
        skin_concerns=to_json_str(payload.skin_concerns) if payload.skin_concerns else None,
        hair_concerns=to_json_str(payload.hair_concerns) if payload.hair_concerns else None,
        budget=payload.budget,
        location_city=payload.location_city,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _serialize(profile)


@router.get("", response_model=dict)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch the current user's profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found. Complete onboarding first.")
    return _serialize(profile)


@router.put("", response_model=dict)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update any profile field."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("skin_concerns", "hair_concerns") and value is not None:
            setattr(profile, field, to_json_str(value))
        else:
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return _serialize(profile)
