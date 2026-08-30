from pydantic import BaseModel

class WeatherResponse(BaseModel):
    city: str
    condition: str
    temp: float    
    humidity: float
    cached: bool
    
class DailyForecast(BaseModel):
    date: str
    temp: float
    humidity: float
    condition: str

class ForecastResponse(BaseModel):
    city: str
    cached: bool
    weekly: list[DailyForecast]