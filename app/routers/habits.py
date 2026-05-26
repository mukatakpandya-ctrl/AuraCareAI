from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.habit import HabitLog
from app.schemas.habit import HabitLogCreate, HabitLogOut, HabitSummary
from app.services.habit_service import (
    calculate_daily_score,
    update_habit_score,
    compute_streak,
    weekly_scores,
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/habits", tags=["Habit Tracking"])


@router.post("/checkin", response_model=HabitLogOut, status_code=201)
def daily_checkin(
    payload: HabitLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log today's grooming habits. Only one entry per day allowed."""
    log_date = payload.log_date or date.today()

    # Prevent duplicate entries for the same day
    existing = db.query(HabitLog).filter(
        HabitLog.user_id == current_user.id,
        HabitLog.log_date == log_date,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Habit log for {log_date} already exists. Use PUT /habits/{existing.id} to update."
        )

    log = HabitLog(
        user_id=current_user.id,
        log_date=log_date,
        cleansed_face=payload.cleansed_face,
        moisturized=payload.moisturized,
        applied_sunscreen=payload.applied_sunscreen,
        washed_hair=payload.washed_hair,
        drank_water=payload.drank_water,
        slept_enough=payload.slept_enough,
        exercised=payload.exercised,
        actual_water_liters=payload.actual_water_liters,
        actual_sleep_hours=payload.actual_sleep_hours,
        notes=payload.notes,
    )
    log.daily_score = calculate_daily_score(log)
    db.add(log)
    db.commit()
    db.refresh(log)

    # Update rolling habit score on profile
    update_habit_score(db, current_user.id)

    return log


@router.put("/{log_id}", response_model=HabitLogOut)
def update_checkin(
    log_id: int,
    payload: HabitLogCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing habit log entry."""
    log = db.query(HabitLog).filter(
        HabitLog.id == log_id,
        HabitLog.user_id == current_user.id,
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="Habit log not found.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        if field != "log_date":
            setattr(log, field, value)
    log.daily_score = calculate_daily_score(log)
    db.commit()
    db.refresh(log)
    update_habit_score(db, current_user.id)
    return log


@router.get("/summary", response_model=HabitSummary)
def habit_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregated habit stats for the dashboard."""
    from app.models.profile import UserProfile

    logs = db.query(HabitLog).filter(HabitLog.user_id == current_user.id).all()
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    total = len(logs)
    avg_score = round(sum(l.daily_score for l in logs) / total, 1) if total else 0.0
    current_streak, best_streak = compute_streak(db, current_user.id)
    w_scores = weekly_scores(db, current_user.id)

    return HabitSummary(
        total_logs=total,
        avg_daily_score=avg_score,
        current_streak=current_streak,
        best_streak=best_streak,
        habit_score=profile.habit_score if profile else 0.0,
        weekly_scores=w_scores,
    )


@router.get("", response_model=list[HabitLogOut])
def list_habit_logs(
    limit: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List habit logs (most recent first)."""
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == current_user.id)
        .order_by(HabitLog.log_date.desc())
        .limit(limit)
        .all()
    )
    return logs


@router.get("/today", response_model=HabitLogOut)
def today_log(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch today's habit log if it exists."""
    log = db.query(HabitLog).filter(
        HabitLog.user_id == current_user.id,
        HabitLog.log_date == date.today(),
    ).first()
    if not log:
        raise HTTPException(status_code=404, detail="No check-in for today yet.")
    return log
