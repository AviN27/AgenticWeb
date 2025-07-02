import json, uuid, time, os
from fastapi import FastAPI, WebSocket
from aiokafka import AIOKafkaProducer
import asyncio

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC      = os.getenv("VOICE_TOPIC_IN", "inbox")

app = FastAPI()
producer: AIOKafkaProducer | None = None

def ts() -> int:  # epoch‑ms helper
    return int(time.time() * 1000)

@app.on_event("startup")
async def _start():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()

@app.on_event("shutdown")
async def _stop():
    await producer.stop()

@app.websocket("/ws/mic")
async def mic_ws(ws: WebSocket):
    await ws.accept()
    buf = bytearray()
    user_id = "demo‑user"
    trace_id = str(uuid.uuid4())

    while True:
        msg = await ws.receive_bytes()
        # client sends text frame "/end" to delimit utterance
        if msg == b"/end":
            envelope = {
                "trace_id": trace_id,
                "user_id": user_id,
                "ts_epoch_ms": ts(),
                "payload": {
                    "raw_audio": True,
                    "audio_b64": buf.hex()  # hex safer for small hack; switch to b64 if preferred
                }
            }
            await producer.send_and_wait(TOPIC, json.dumps(envelope).encode())
            buf.clear()
            trace_id = str(uuid.uuid4())
        else:
            buf.extend(msg)