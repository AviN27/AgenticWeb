import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from aiokafka import AIOKafkaConsumer
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("chat_ws")

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
# Topics to stream to the frontend chat UI
TOPICS = [
    os.getenv("VOICE_TOPIC_OUT", "transcript"),
    "agent.out.ride",
    "agent.out.food",
    "agent.out.mart",
    os.getenv("AGENT_CMD_TOPIC", "agent.cmd"),
    "agent.out.clarify"
]

app = FastAPI()

@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    await websocket.accept()
    log.info("WebSocket /ws/chat connection accepted")
    consumer = AIOKafkaConsumer(*TOPICS, bootstrap_servers=BOOTSTRAP, group_id="chat_ws_relay", auto_offset_reset="latest")
    await consumer.start()
    try:
        while True:
            try:
                msg = await asyncio.wait_for(consumer.getone(), timeout=1.0)
                data = json.loads(msg.value)
                # Attach topic info for frontend parsing
                data["_topic"] = msg.topic
                await websocket.send_text(json.dumps(data))
            except asyncio.TimeoutError:
                # Allow for disconnects
                if websocket.client_state.name != "CONNECTED":
                    break
            except Exception as e:
                log.error(f"Error in chat_ws relay: {e}", exc_info=True)
                break
    except WebSocketDisconnect:
        log.info("WebSocket /ws/chat disconnected")
    finally:
        await consumer.stop()
        await websocket.close() 