from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os, random

class LocationRequest(BaseModel):
    latitude: float
    longitude: float

class Place(BaseModel):
    id: str
    name: str
    type: str  # e.g., "restaurant", "mart", "ride_stand"
    latitude: float
    longitude: float
    distance_km: float

class LocationResponse(BaseModel):
    user_id: str | None
    label: str | None        # e.g., "home","work", or None
    latitude: float
    longitude: float

router = APIRouter()

# Mock user geo-labels
USER_LABELS = {
    "demo-user": {
        "home":    (1.290270, 103.851959),
        "work":    (1.295000, 103.852000)
    }
}

@router.post("/current", response_model=LocationResponse)
async def get_current_location(req: LocationRequest, user_id: str | None = None):
    # Determine if close to home or work
    label = None
    if user_id and user_id in USER_LABELS:
        for k,(lat,lon) in USER_LABELS[user_id].items():
            if abs(lat - req.latitude) < 0.005 and abs(lon - req.longitude) < 0.005:
                label = k
    return LocationResponse(
        user_id=user_id,
        label=label,
        latitude=req.latitude,
        longitude=req.longitude
    )

@router.get("/nearby/{place_type}", response_model=list[Place])
async def get_nearby(place_type: str, latitude: float, longitude: float, radius_km: float = 5.0):
    sample = []
    for i in range(5):
        lat = latitude + random.uniform(-0.01, 0.01)
        lon = longitude + random.uniform(-0.01, 0.01)
        dist = random.uniform(0.1, radius_km)
        sample.append(Place(
            id=f"{place_type}_{i}",
            name=f"{place_type.title()} {i}",
            type=place_type,
            latitude=lat,
            longitude=lon,
            distance_km=round(dist,2)
        ))
    return sample