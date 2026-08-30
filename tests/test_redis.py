import pytest
import json
import httpx
from httpx import AsyncClient
from app.main import app
from tests.utils.fake_redis import FakeRedis

# キャッシュテスト
@pytest.mark.asyncio
async def test_cached_current_weather():
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
        
@pytest.mark.asyncio
async def test_cached_weekly_weather():
    app.state.redis = FakeRedis()
    
    cached_data = [
        {"date": "2024-01-01", "temp": 11.0, "humidity": 52.5, "condition": "厚い雲"}
    ]
    
    await app.state.redis.set("weekly:Tokyo", json.dumps(cached_data))
    
    transport = httpx.ASGITransport(app=app)
        
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/weather/weekly?city=Tokyo")
        
    data = res.json()
    assert data["cached"] is True
    assert len(data["weekly"]) == 1