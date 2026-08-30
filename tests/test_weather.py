import json
import pytest
import httpx
from httpx import AsyncClient
import respx
from app.main import app
from app.core.config import settings
from tests.utils.fake_redis import FakeRedis

# 現在の天気テスト
# -----------------------------
# current: キャッシュあり
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weather_cached():
    app.state.redis = FakeRedis()

    cached_data = {
        "city": "Tokyo",
        "condition": "厚い雲",
        "temp": 20.5,
        "humidity": 60,
        "cached": False
    }

    await app.state.redis.set("weather:Tokyo", json.dumps(cached_data))

    transport = httpx.ASGITransport(app=app)
                
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/weather/current?city=Tokyo")

    data = res.json()
    assert data["cached"] is True
    assert data["city"] == "Tokyo"

# -----------------------------
# current: キャッシュなし
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weather_normal():
    app.state.redis = FakeRedis()
    
    mock_response = {
        "weather": [{"description": "厚い雲"}],
        "main": {"temp": 20.5, "humidity": 60}
    }
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(200, json=mock_response)
        
        transport = httpx.ASGITransport(app=app)
            
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/weather/current?city=Tokyo")
            
    assert res.status_code == 200
    data = res.json()
    
    assert data["city"] == "Tokyo"
    assert data["condition"] == "厚い雲"
    assert data["temp"] == 20.5
    assert data["humidity"] == 60
    assert data["cached"] is False
    
# -----------------------------
# current: API が 500
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weather_api_error():
    app.state.redis = FakeRedis()
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(500)
        
        transport = httpx.ASGITransport(app=app)
                    
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(RuntimeError):
                await ac.get("/weather/current?city=Tokyo")

# -----------------------------
# current: httpx.RequestError
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weather_request_error():
    app.state.redis = FakeRedis()
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).side_effect = httpx.RequestError("boom")
        
        transport = httpx.ASGITransport(app=app)
        
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(RuntimeError):
                await ac.get("/weather/current?city=Tokyo")
                
# -----------------------------
# current: JSON 壊れている
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weather_invalid_json():
    app.state.redis = FakeRedis()
    
    mock_response = {
        "weather": [{}],    # description が無い
        "main": {"temp": 20.5, "humidity": 60}
    }
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/weather?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(200, json=mock_response)
        
        transport = httpx.ASGITransport(app=app)
        
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(KeyError):
                await ac.get("/weather/current?city=Tokyo")
 
# 週間天気予報テスト
# -----------------------------
# weekly: キャッシュあり
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weekly_cached():
    app.state.redis = FakeRedis()
    
    cached_data = [
        {"date": "2024-01-01", "condition": "厚い雲", "temp": 10.0, "humidity": 50}
    ]
    
    await app.state.redis.set("weekly:Tokyo", json.dumps(cached_data))
    
    transport = httpx.ASGITransport(app=app)
    
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/weather/weekly?city=Tokyo")
    
    data = res.json()
    assert data["cached"] is True
    assert len(data["weekly"]) == 1

# -----------------------------
# weekly: キャッシュなし
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weekly_normal():
    app.state.redis = FakeRedis()
    
    mock_response = {
        "list": [
            {
                "dt_txt": "2024-01-01 00:00:00",
                "main": {"temp": 10, "humidity": 50},
                "weather": [{"description": "厚い雲"}]
            },
            {
                "dt_txt": "2024-01-01 03:00:00",
                "main": {"temp": 12, "humidity": 55},
                "weather": [{"description": "厚い雲"}]
            },
            {
                "dt_txt": "2024-01-02 00:00:00",
                "main": {"temp": 8, "humidity": 60},
                "weather": [{"description": "小雨"}]
            }
        ]
    }
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(200, json=mock_response)
        
        transport = httpx.ASGITransport(app=app)
                    
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            res = await ac.get("/weather/weekly?city=Tokyo")
            
    assert res.status_code == 200
    data = res.json()
    
    assert data["city"] == "Tokyo"
    assert data["cached"] is False
    assert len(data["weekly"]) == 2  # 2日分

    day1 = data["weekly"][0]
    assert day1["date"] == "2024-01-01"
    assert day1["temp"] == 11.0  # (10 + 12) / 2
    assert day1["humidity"] == 52.5
    assert day1["condition"] == "厚い雲"
    
# -----------------------------
# weekly: API が 500
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weekly_api_error():
    app.state.redis = FakeRedis()
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(500)
        
        transport = httpx.ASGITransport(app=app)
        
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(RuntimeError):
                await ac.get("/weather/weekly?city=Tokyo")
                
# -----------------------------
# weekly: httpx.RequestError
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weekly_request_error():
    app.state.redis = FakeRedis()
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).side_effect = httpx.RequestError("boom")
        
        transport = httpx.ASGITransport(app=app)
                
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(RuntimeError):
                await ac.get("/weather/weekly?city=Tokyo")
                
# -----------------------------
# weekly: JSON 壊れている
# -----------------------------
@pytest.mark.asyncio
async def test_fetch_weekly_invalid_json():
    app.state.redis = FakeRedis()
    
    mock_response = {
        "list": [
            {
                "dt_txt": "2024-01-01 00:00:00",
                "weather": [{}],  # description が無い
                "main": {"temp": 10, "humidity": 50}
            }
        ]
    }
    
    with respx.mock:
        respx.get(
            f"https://api.openweathermap.org/data/2.5/forecast?q=Tokyo&appid={settings.WEATHER_API_KEY}&units=metric&lang=ja"
        ).respond(200, json=mock_response)
        
        transport = httpx.ASGITransport(app=app)
        
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            with pytest.raises(KeyError):
                await ac.get("/weather/weekly?city=Tokyo")