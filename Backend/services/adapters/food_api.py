from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid, time

class FoodItem(BaseModel):
    name: str
    quantity: int

class FoodRequest(BaseModel):
    restaurant_id: str
    items: list[FoodItem]
    delivery_address: str
    time: str

class FoodResponse(BaseModel):
    trace_id: str
    status: str
    eta: str
    total: str
    ts_epoch_ms: int

router = APIRouter()

@router.post("/order", response_model=FoodResponse)
async def order_food(req: FoodRequest):
    # TODO: call real GrabFood API
    now = int(time.time()*1000)
    return FoodResponse(
        trace_id=str(uuid.uuid4()),
        status="confirmed",
        eta="25 min",
        total="20.50 SGD",
        ts_epoch_ms=now
    )
