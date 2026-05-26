from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.recommendation import Recommendation, RecommendationType
from app.services.gemini_service import analyze_skin_image
from app.utils.auth import get_current_user
from app.utils.helpers import save_upload, from_json_str, to_json_str
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/analysis", tags=["Skin & Hair Analysis"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


@router.post("/skin-image", response_model=dict, status_code=status.HTTP_201_CREATED)
async def analyze_skin(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a selfie → Gemini Vision analyses skin/hair concerns.
    Saves result to profile and creates a recommendation record.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {file.content_type} not supported. Use JPEG/PNG/WEBP.")

    contents = await file.read()
    if len(contents) > MAX_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")

    # Persist image
    image_path = save_upload(contents, file.filename or "upload.jpg")

    # Fetch profile context
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    profile_ctx = {}
    if profile:
        profile_ctx = {
            "skin_type": profile.skin_type,
            "hair_type": profile.hair_type,
            "skin_concerns": from_json_str(profile.skin_concerns) or [],
        }

    # Call Gemini
    analysis = analyze_skin_image(image_path, profile_ctx)

    # Update profile with latest analysis
    if profile:
        profile.last_skin_analysis = to_json_str(analysis)
        profile.profile_image_path = image_path
        db.commit()

    # Save recommendation record
    import json
    rec = Recommendation(
        user_id=current_user.id,
        rec_type=RecommendationType.image_analysis,
        title="Skin Analysis Result",
        content=json.dumps(analysis, ensure_ascii=False),
        image_path=image_path,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return {
        "recommendation_id": rec.id,
        "image_path": image_path,
        "analysis": analysis,
    }
