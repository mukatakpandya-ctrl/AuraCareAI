"""
GeminiService
─────────────
Wraps google-generativeai for:
  1. Skin/hair image analysis
  2. Personalized routine generation (optionally weather-aware)
  3. Product recommendations
  4. Conversational grooming coach
"""
import json
import base64
from pathlib import Path
from typing import Optional

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config import get_settings

settings = get_settings()

# ── Configure SDK ─────────────────────────────────────────────────────
genai.configure(api_key=settings.GEMINI_API_KEY)

_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

_model = genai.GenerativeModel(
    model_name=settings.GEMINI_MODEL,
    safety_settings=_SAFETY,
)

# ── System prompt for the grooming coach chatbot ──────────────────────
COACH_SYSTEM = """You are AuraCare Grooming Coach — a friendly, knowledgeable AI assistant
specializing in skincare, haircare, and personal wellness. You give practical,
evidence-based grooming advice. You are NOT a medical professional and always
recommend consulting a dermatologist for clinical concerns.
Keep answers concise, warm, and actionable. Use bullet points when listing steps."""


def _text(response) -> str:
    """Extract text from a Gemini response safely."""
    try:
        return response.text.strip()
    except Exception:
        return "I'm sorry, I couldn't generate a response right now."


# ── 1. Skin & Hair Image Analysis ────────────────────────────────────
def analyze_skin_image(image_path: str, profile_context: dict) -> dict:
    """
    Analyze a selfie for skin/hair concerns using Gemini Vision.
    Returns a structured JSON-friendly dict.
    """
    img_bytes = Path(image_path).read_bytes()
    img_b64 = base64.b64encode(img_bytes).decode()
    mime = "image/jpeg" if image_path.lower().endswith((".jpg", ".jpeg")) else "image/png"

    prompt = f"""
You are an AI grooming analyst. Analyze the uploaded selfie and provide a structured assessment.

User's self-reported profile:
- Skin type: {profile_context.get('skin_type', 'unknown')}
- Hair type: {profile_context.get('hair_type', 'unknown')}
- Known concerns: {profile_context.get('skin_concerns', [])}

Respond ONLY with a valid JSON object (no markdown, no explanation) with this exact schema:
{{
  "detected_skin_type": "oily|dry|combination|sensitive|normal",
  "detected_concerns": ["e.g. acne", "dark circles", "uneven tone"],
  "skin_health_score": 75,
  "hair_observations": "brief observation about visible hair",
  "immediate_recommendations": ["short actionable tip 1", "tip 2", "tip 3"],
  "positive_observations": ["what looks healthy"]
}}
"""
    response = _model.generate_content([
        {"mime_type": mime, "data": img_b64},
        prompt,
    ])
    raw = _text(response)
    # Strip code fences if present
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_analysis": raw, "error": "Could not parse structured response"}


# ── 2. Personalized Routine Generation ───────────────────────────────
def generate_grooming_routine(profile: dict, weather: Optional[dict] = None) -> str:
    """Generate a personalized AM/PM grooming routine."""
    weather_ctx = ""
    if weather:
        weather_ctx = f"""
Current Weather in {weather.get('city', 'your city')}:
- Temperature: {weather.get('temp_c', '?')}°C, Feels like: {weather.get('feels_like_c', '?')}°C
- Humidity: {weather.get('humidity', '?')}%
- UV Index: {weather.get('uv_index', 'unknown')}
- Condition: {weather.get('description', '?')}
- Pollution AQI: {weather.get('aqi', 'unknown')}
Tailor all product texture, SPF, and hydration advice to these conditions.
"""

    prompt = f"""
You are AuraCare Grooming Coach. Create a personalized daily grooming routine.

USER PROFILE:
- Skin type: {profile.get('skin_type', 'unknown')}
- Hair type: {profile.get('hair_type', 'unknown')}
- Skin concerns: {profile.get('skin_concerns', [])}
- Hair concerns: {profile.get('hair_concerns', [])}
- Sleep: {profile.get('sleep_hours', '?')} hrs/night
- Water intake: {profile.get('water_intake_liters', '?')} L/day
- Activity level: {profile.get('activity_level', 'unknown')}
- Budget: {profile.get('budget', 'medium')}

{weather_ctx}

Structure your response as:
## 🌅 Morning Routine
(step-by-step AM skincare + hair)

## 🌙 Evening Routine
(step-by-step PM skincare)

## 💧 Lifestyle Tips
(hydration, sleep, diet based on profile)

## ⚠️ Watch Out For
(weather-specific or concern-specific cautions)

Be specific, practical, and budget-conscious. Mention Indian drugstore/affordable brands when relevant.
"""
    return _text(_model.generate_content(prompt))


# ── 3. Product Recommendations ────────────────────────────────────────
def recommend_products(profile: dict, category: str = "skincare") -> str:
    """Generate budget-appropriate product recommendations."""
    budget_map = {"low": "under ₹500", "medium": "₹500–₹2000", "high": "above ₹2000"}
    budget_label = budget_map.get(profile.get("budget", "medium"), "₹500–₹2000")

    # Build category lists outside f-string (backslashes not allowed in f-strings on Python 3.11)
    skin_items = (
        "- Cleanser\n- Toner\n- Moisturiser\n- SPF Sunscreen\n- Targeted treatment (serum/spot treatment)"
        if category in ("skincare", "both") else ""
    )
    hair_items = (
        "- Shampoo\n- Conditioner\n- Hair mask/treatment\n- Scalp care"
        if category in ("haircare", "both") else ""
    )

    prompt = f"""
You are a knowledgeable beauty advisor. Recommend specific {category} products.

USER:
- Skin type: {profile.get('skin_type', 'unknown')}
- Hair type: {profile.get('hair_type', 'unknown')}
- Concerns: {profile.get('skin_concerns', [])} | {profile.get('hair_concerns', [])}
- Budget: {budget_label} per product
- Location: India

For each product category provide:
1. Product name (brand + variant)
2. Why it suits this user
3. Approximate price in INR
4. Where to buy (Nykaa, Amazon, Flipkart, etc.)

Categories to cover for {category}:
{skin_items}
{hair_items}

Format with clear headings. Keep it concise and affordable.
"""
    return _text(_model.generate_content(prompt))


# ── 4. Grooming Coach Chatbot ─────────────────────────────────────────
def chat_with_coach(
    user_message: str,
    history: list[dict],
    user_profile: dict,
) -> str:
    """
    Multi-turn conversational grooming coach.
    history = [{"role": "user"|"model", "parts": ["text"]}]
    """
    profile_ctx = f"""
[USER CONTEXT]
Skin: {user_profile.get('skin_type','unknown')} | Hair: {user_profile.get('hair_type','unknown')}
Concerns: {user_profile.get('skin_concerns',[])} | Habit score: {user_profile.get('habit_score',0)}/100
"""
    # Prepend system context as first user turn if history is empty
    if not history:
        history = [
            {"role": "user", "parts": [COACH_SYSTEM + "\n" + profile_ctx + "\nHello!"]},
            {"role": "model", "parts": ["Hello! I'm your AuraCare Grooming Coach. How can I help you with your skincare or haircare today? 😊"]},
        ]

    chat = _model.start_chat(history=history)
    response = chat.send_message(user_message)
    return _text(response)
