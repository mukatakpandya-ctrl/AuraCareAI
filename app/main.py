"""
GlowUp AI / AuraCare — Backend
================================
FastAPI application entry point.

Run locally:
  uvicorn app.main:app --reload --port 8000

Docs:
  http://localhost:8000/docs   (Swagger UI)
  http://localhost:8000/redoc  (ReDoc)
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import init_db
from app.routers import (
    auth_router,
    profile_router,
    analysis_router,
    weather_router,
    recommendations_router,
    habits_router,
    chat_router,
)

settings = get_settings()


# ── Lifespan (startup / shutdown) ─────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    print(f"✅  {settings.APP_NAME} v{settings.APP_VERSION} started")
    yield
    # Shutdown (nothing to clean up for SQLite)
    print("👋  Server shutting down")


# ── App Instance ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
**AuraCare / GlowUp AI** — AI-powered personal grooming assistant backend.

### Features
- 🔐 JWT Authentication
- 👤 Questionnaire-based User Profiling
- 🤖 Gemini AI skin & hair image analysis
- ☁️ Weather-aware recommendations (OpenWeatherMap)
- 💊 Personalized product recommendations
- 📅 Daily habit tracking & scoring
- 💬 Conversational grooming coach chatbot
""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files (serve uploaded images) ─────────────────────────────
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(analysis_router)
app.include_router(weather_router)
app.include_router(recommendations_router)
app.include_router(habits_router)
app.include_router(chat_router)


# ── Health check ──────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
