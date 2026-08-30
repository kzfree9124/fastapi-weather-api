from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    WEATHER_API_BASE_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    WEATHER_FORECAST_URL: str = "https://api.openweathermap.org/data/2.5/forecast"
    WEATHER_API_KEY: str | None = None
    
    model_config = ConfigDict(env_file=".env")
    
settings = Settings()