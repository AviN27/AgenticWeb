from fastapi import APIRouter
from pydantic import BaseModel
import uuid, time

class PaymentRequest(BaseModel):
    user_id: str
    amount: str
    method: str

class PaymentResponse(BaseModel):
    trace_id: str
    status: str
    ts_epoch_ms: int

router = APIRouter()

@router.post("/charge", response_model=PaymentResponse)
async def charge(req: PaymentRequest):
    # TODO: integrate GrabPay SDK
    now = int(time.time()*1000)
    return PaymentResponse(
        trace_id=str(uuid.uuid4()),
        status="success",
        ts_epoch_ms=now
    )