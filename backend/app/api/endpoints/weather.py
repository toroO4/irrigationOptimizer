import random
from fastapi import APIRouter
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["Weather"])

@router.get("/weather/live", summary="Get Live Weather")
async def get_live_weather():
    """
    Fetch live weather data.
    
    In a real scenario, this would query an external service like OpenWeatherMap
    or an on-farm IoT station. For now, it returns realistic simulated data.
    """
    # Simulate slightly varying realistic weather data
    temperature = round(random.uniform(28.0, 35.0), 1)
    humidity = int(random.uniform(40, 65))
    wind_speed = int(random.uniform(5, 18))
    rain_prob = int(random.uniform(0, 30))
    
    conditions = ["Sunny / Clear", "Partly Cloudy", "Mostly Clear"]
    condition = random.choice(conditions)

    return {
        "location": "Maharashtra, India",
        "temperature_c": temperature,
        "condition": condition,
        "humidity_percent": humidity,
        "wind_speed_kmh": wind_speed,
        "rain_probability_percent": rain_prob,
        "evapotranspiration_mm": round(random.uniform(4.0, 7.0), 2),
        "updated_at": "Just now"
    }
