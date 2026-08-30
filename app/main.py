from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.cache import init_redis, close_redis
from app.routers.weather import router as weather_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis(app)
    yield
    await close_redis(app)

app = FastAPI(lifespan=lifespan)

app.include_router(weather_router)