from app.routers.auth import router as auth_router
from app.routers.profile import router as profile_router
from app.routers.analysis import router as analysis_router
from app.routers.weather import router as weather_router
from app.routers.recommendations import router as recommendations_router
from app.routers.habits import router as habits_router
from app.routers.chat import router as chat_router

__all__ = [
    "auth_router", "profile_router", "analysis_router",
    "weather_router", "recommendations_router", "habits_router", "chat_router",
]
