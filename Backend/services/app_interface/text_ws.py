import os
import json
import uuid
import time
import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaProducer

# Configure logging
tlogging = logging.getLogger("ingress.text")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# Kafka setup
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TRANS_TOPIC = os.getenv("VOICE_TOPIC_OUT", "transcript")

app = FastAPI()
producer: AIOKafkaProducer | None = None

@app.on_event("startup")
async def startup():
    global producer
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await producer.start()
    logging.info(f"Text ingress producer started, topic={TRANS_TOPIC}")

@app.on_event("shutdown")
async def shutdown():
    if producer:
        await producer.stop()
        logging.info("Text ingress producer stopped")

@app.websocket("/ws/text")
async def ws_text(ws: WebSocket):
    await ws.accept()
    logging.info("WebSocket /ws/text connection accepted")
    try:
        while True:
            msg = await ws.receive_text()
            trace_id = str(uuid.uuid4())
            user_id = ws.query_params.get("user_id", "demo-user")
            envelope = {
                "trace_id": trace_id,
                "user_id": user_id,
                "ts_epoch_ms": int(time.time() * 1000),
                "text": msg
            }
            await producer.send_and_wait(TRANS_TOPIC, json.dumps(envelope).encode())
            logging.info(f"Published text envelope: {envelope}")
    except WebSocketDisconnect:
        logging.info("WebSocket /ws/text disconnected")
    except Exception as e:
        logging.error(f"Error in /ws/text: {e}")
        await ws.close()