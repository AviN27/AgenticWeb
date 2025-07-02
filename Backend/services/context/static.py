import os
import logging
from fastapi import FastAPI, HTTPException
import redis.asyncio as aioredis

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("context_static")

# Environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
app = FastAPI(title="Static Context Service")

# Initialize RedisJSON client
r = aioredis.from_url(REDIS_URL, decode_responses=True)

@app.on_event("startup")
async def startup_event():
    log.info(f"Connecting to RedisJSON at {REDIS_URL}")
    # Optionally test connection
    await r.ping()
    log.info("Connected to RedisJSON successfully.")

@app.get("/v1/users/{user_id}/profile")
async def get_profile(user_id: str):
    key = f"user:{user_id}"
    data = await r.json().get(key)
    log.info(f"Fetching profile for user_id={data}")
    if data is None:
        raise HTTPException(status_code=404, detail="User profile not found")
    return data

@app.get("/v1/users/{user_id}/favorites")
async def get_favorites(user_id: str):
    key = f"user:{user_id}"
    data = await r.json().get(key)
    favorites = data['favorites'] if data else None
    log.info(f"Fetching favorites for user_id={user_id}: {favorites}")
    if favorites is None:
        raise HTTPException(status_code=404, detail="User favorites not found")
    return favorites

@app.on_event("shutdown")
async def shutdown_event():
    await r.close()
    log.info("Redis connection closed.") 