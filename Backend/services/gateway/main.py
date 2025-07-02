import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis.asyncio as aioredis
from aiokafka import AIOKafkaProducer

app = FastAPI(title="GrabHack REST Gateway")

# Kafka Producer
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)

# Redis client for state
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379")
redis = aioredis.from_url(REDIS_URL)

# Pydantic models
class CommandRequest(BaseModel):
    user_id: str
    tool: str
    arguments: dict

class StatusResponse(BaseModel):
    trace_id: str
    status: str
    detail: dict | None = None

@app.on_event("startup")
async def startup():
    await producer.start()

@app.on_event("shutdown")
async def shutdown():
    await producer.stop()

@app.post("/v1/command")
async def post_command(cmd: CommandRequest):
    envelope = {
        "trace_id": cmd.arguments.get("trace_id") or __import__('uuid').uuid4().hex,
        "tool": cmd.tool,
        "user_id": cmd.user_id,
        "arguments": cmd.arguments
    }
    await producer.send_and_wait("agent.cmd", json.dumps(envelope).encode())
    return {"status":"queued","trace_id":envelope['trace_id']}

@app.get("/v1/status/{trace_id}", response_model=StatusResponse)
async def get_status(trace_id: str):
    key = f"status:{trace_id}"
    data = await redis.json().get(key)
    if not data:
        raise HTTPException(404, "Status not found")
    return StatusResponse(trace_id=trace_id, status=data.get("status"), detail=data.get("detail"))