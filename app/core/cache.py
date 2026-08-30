import redis.asyncio as redis
from fastapi import FastAPI

async def init_redis(app: FastAPI):
    app.state.redis = redis.from_url(
        "redis://redis:6379",
        decode_responses=True
    )
    
async def close_redis(app: FastAPI):
    redis_client = app.state.redis
    if redis_client:
        await redis_client.close()

def get_redis(app: FastAPI):
    return app.state.redis