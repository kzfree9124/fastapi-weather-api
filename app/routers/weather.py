from fastapi import APIRouter, Request
from app.schemas.weather import WeatherResponse, ForecastResponse
from app.services.weather_service import WeatherService
from app.core.cache import get_redis

router = APIRouter(prefix="/weather", tags=["weather"])

@router.get("/current", response_model=WeatherResponse)
async def get_weather(city: str, request: Request):
    redis = get_redis(request.app)
    data = await WeatherService.fetch_weather(city, redis)
    return WeatherResponse(**data)
        
@router.get("/weekly", response_model=ForecastResponse)
async def get_weekly_weather(city: str, request: Request):
    redis = get_redis(request.app)
    data = await WeatherService.fetch_weekly(city, redis)
    return ForecastResponse(**data)