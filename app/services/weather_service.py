import httpx
import json
from collections import Counter
from app.core.config import settings

class WeatherService:    
    # 現在の天気・気温・湿度を取得
    @staticmethod
    async def fetch_weather(city: str, redis) -> dict:
        cache_key = f"weather:{city}"
        
        # キャッシュ確認
        cached = await redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["cached"] = True
            return data
        
        url = f"{settings.WEATHER_API_BASE_URL}?q={city}&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
        except httpx.RequestError as e:
            raise RuntimeError(f"Weather API request failed: {e}") from e
        
        if response.status_code != 200:
            raise RuntimeError(
                f"Weather API returned error: {response.status_code}"
            )
            
        data = response.json()
                
        result = {
            "city": city,
            "condition": data["weather"][0]["description"],
            "temp": round(data["main"]["temp"], 1),
            "humidity": data["main"]["humidity"],
            "cached": False,
        }
        
        # 10分キャッシュ
        await redis.set(cache_key, json.dumps(result), ex=600)
        
        return result
    
    # 週間天気予報を取得
    @staticmethod
    async def fetch_weekly(city: str, redis) -> dict:
        cache_key = f"weekly:{city}"
        
        # キャッシュ確認
        cached = await redis.get(cache_key)
        if cached:
            return {
                "city": city,
                "cached": True,
                "weekly": json.loads(cached)
            }
        
        url = f"{settings.WEATHER_FORECAST_URL}?q={city}&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        
        try:            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
        except httpx.RequestError as e:
            raise RuntimeError(f"Forecast API request faild: {e}") from e
        
        if response.status_code != 200:
            raise RuntimeError(f"Forecast lookup failed: {response.status_code}")
        
        data = response.json()
        
        # 3時間ごとの予報を日ごとにまとめる
        daily = {}
        
        for item in data["list"]:
            dt_txt = item["dt_txt"]
            date = dt_txt.split(" ")[0]
            
            condition = item["weather"][0]["description"]
            temp = item["main"]["temp"]
            humidity = item["main"]["humidity"]
            
            if date not in daily:
                daily[date] = {
                    "conditions": [],
                    "temps": [],
                    "humidities": []
                }
            
            daily[date]["conditions"].append(condition)
            daily[date]["temps"].append(temp)
            daily[date]["humidities"].append(humidity)
            
        # 日ごとに集計
        result = []
        for date, values in daily.items():
            common_condition = Counter(values["conditions"]).most_common(1)[0][0]
            avg_temp = round(sum(values["temps"]) / len(values["temps"]), 1)
            avg_humidity = round(sum(values["humidities"]) / len(values["humidities"]), 1)
            
            result.append({
                "date": date,
                "condition": common_condition,
                "temp": avg_temp,
                "humidity": avg_humidity,
            })
            
        # 10分キャッシュ
        await redis.set(cache_key, json.dumps(result), ex=600)
        
        return {
            "city": city, 
            "cached": False, 
            "weekly": result
            }