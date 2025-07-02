from fastapi import APIRouter
from pydantic import BaseModel
import uuid, time

class MartItem(BaseModel):
    name: str
    quantity: int

class MartRequest(BaseModel):
    mart_id: str
    items: list[MartItem]
    delivery_address: str
    time: str

class MartResponse(BaseModel):
    trace_id: str
    status: str
    eta: str
    total: str
    ts_epoch_ms: int

router = APIRouter()

@router.post("/purchase", response_model=MartResponse)
async def order_mart(req: MartRequest):
    # TODO: call real GrabMart API
    now = int(time.time()*1000)
    return MartResponse(
        trace_id=str(uuid.uuid4()),
        status="confirmed",
        eta="45 min",
        total="35.00 SGD",
        ts_epoch_ms=now
    )