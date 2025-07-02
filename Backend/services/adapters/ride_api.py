from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid, time

class RideRequest(BaseModel):
    pickup: str
    dropoff: str
    time: str  # ISO datetime

class RideResponse(BaseModel):
    trace_id: str
    eta: str
    price: str
    driver: str
    vehicle: str
    ts_epoch_ms: int

router = APIRouter()

@router.post("/book", response_model=RideResponse)
async def book_ride(req: RideRequest):
    # TODO: call real Ride API
    now = int(time.time()*1000)
    return RideResponse(
        trace_id=str(uuid.uuid4()),
        eta="5 min",
        price="7.50 SGD",
        driver="John Doe",
        vehicle="Toyota Prius",
        ts_epoch_ms=now
    )
