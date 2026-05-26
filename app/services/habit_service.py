"""
HabitService
────────────
Calculates daily and overall habit scores and streak info.
"""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.models.habit import HabitLog
from app.models.profile import UserProfile


HABIT_WEIGHTS = {
    "cleansed_face": 20,
    "moisturized": 15,
    "applied_sunscreen": 20,
    "washed_hair": 10,
    "drank_water": 15,
    "slept_enough": 10,
    "exercised": 10,
}


def calculate_daily_score(log: HabitLog) -> float:
    """Compute a 0–100 score for a single habit log entry."""
    score = 0.0
    for field, weight in HABIT_WEIGHTS.items():
        if getattr(log, field, False):
            score += weight
    return round(score, 1)


def update_habit_score(db: Session, user_id: int) -> float:
    """
    Recompute the rolling 30-day average habit score and save it to the profile.
    Returns the new overall score.
    """
    thirty_days_ago = date.today() - timedelta(days=30)
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == user_id, HabitLog.log_date >= thirty_days_ago)
        .all()
    )
    if not logs:
        return 0.0
    avg = sum(l.daily_score for l in logs) / len(logs)
    avg = round(avg, 1)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        profile.habit_score = avg
        db.commit()
    return avg


def compute_streak(db: Session, user_id: int) -> tuple[int, int]:
    """
    Returns (current_streak, best_streak) in days.
    A day counts if daily_score >= 50.
    """
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == user_id)
        .order_by(HabitLog.log_date.desc())
        .all()
    )
    if not logs:
        return 0, 0

    dates = {l.log_date: l.daily_score for l in logs}
    today = date.today()

    # Current streak
    current = 0
    check = today
    while check in dates and dates[check] >= 50:
        current += 1
        check -= timedelta(days=1)

    # Best streak
    best = 0
    run = 0
    prev = None
    for log in reversed(logs):  # ascending order
        if log.daily_score >= 50:
            if prev is None or log.log_date - prev == timedelta(days=1):
                run += 1
            else:
                run = 1
            best = max(best, run)
        else:
            run = 0
        prev = log.log_date

    return current, best


def weekly_scores(db: Session, user_id: int) -> list[dict]:
    """Return last 7 days of scores (for dashboard chart)."""
    seven_days_ago = date.today() - timedelta(days=6)
    logs = (
        db.query(HabitLog)
        .filter(HabitLog.user_id == user_id, HabitLog.log_date >= seven_days_ago)
        .all()
    )
    log_map = {l.log_date: l.daily_score for l in logs}
    result = []
    for i in range(7):
        d = seven_days_ago + timedelta(days=i)
        result.append({"date": d.isoformat(), "score": log_map.get(d, 0.0)})
    return result
