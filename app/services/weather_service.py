"""
WeatherService
──────────────
Fetches current weather + air quality from OpenWeatherMap and returns
a normalized dict used by the recommendation engine.
"""
import httpx
from typing import Optional
from app.config import get_settings

settings = get_settings()

BASE = settings.OPENWEATHER_BASE_URL
KEY = settings.OPENWEATHER_API_KEY


def _uvi_label(uvi: float) -> str:
    if uvi < 3:
        return "Low"
    if uvi < 6:
        return "Moderate"
    if uvi < 8:
        return "High"
    if uvi < 11:
        return "Very High"
    return "Extreme"


def _aqi_label(aqi: int) -> str:
    # OpenWeather AQI: 1=Good…5=Very Poor
    return ["Good", "Fair", "Moderate", "Poor", "Very Poor"][min(aqi - 1, 4)]


async def get_weather(city: str) -> Optional[dict]:
    """
    Fetch current weather for a city.
    Returns a normalized dict or None on failure.
    """
    if not KEY:
        return _mock_weather(city)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Current weather
            r = await client.get(
                f"{BASE}/weather",
                params={"q": city, "appid": KEY, "units": "metric"},
            )
            r.raise_for_status()
            w = r.json()

            lat = w["coord"]["lat"]
            lon = w["coord"]["lon"]

            # Air quality index (separate endpoint)
            aqi_val = None
            try:
                ar = await client.get(
                    f"{BASE}/air_pollution",
                    params={"lat": lat, "lon": lon, "appid": KEY},
                )
                ar.raise_for_status()
                aqi_val = ar.json()["list"][0]["main"]["aqi"]
            except Exception:
                pass

            # UV index (separate endpoint)
            uvi = None
            try:
                ur = await client.get(
                    f"{BASE}/uvi",
                    params={"lat": lat, "lon": lon, "appid": KEY},
                )
                ur.raise_for_status()
                uvi = ur.json().get("value")
            except Exception:
                pass

        return {
            "city": w.get("name", city),
            "country": w.get("sys", {}).get("country"),
            "temp_c": round(w["main"]["temp"], 1),
            "feels_like_c": round(w["main"]["feels_like"], 1),
            "humidity": w["main"]["humidity"],
            "description": w["weather"][0]["description"].capitalize(),
            "icon": w["weather"][0]["icon"],
            "wind_speed_ms": w.get("wind", {}).get("speed"),
            "uv_index": round(uvi, 1) if uvi is not None else None,
            "uv_label": _uvi_label(uvi) if uvi is not None else "unknown",
            "aqi": aqi_val,
            "aqi_label": _aqi_label(aqi_val) if aqi_val else "unknown",
            # Grooming flags
            "high_humidity": w["main"]["humidity"] > 70,
            "high_uv": uvi is not None and uvi >= 6,
            "cold": w["main"]["temp"] < 15,
            "hot": w["main"]["temp"] >= 30,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        raise
    except Exception:
        return None


def _mock_weather(city: str) -> dict:
    """Return a static mock when no API key is configured (dev mode)."""
    return {
        "city": city,
        "country": "IN",
        "temp_c": 32.0,
        "feels_like_c": 35.0,
        "humidity": 55,
        "description": "Partly cloudy",
        "icon": "02d",
        "wind_speed_ms": 3.5,
        "uv_index": 7.0,
        "uv_label": "High",
        "aqi": 2,
        "aqi_label": "Fair",
        "high_humidity": False,
        "high_uv": True,
        "cold": False,
        "hot": True,
        "_mock": True,
    }
