"""
services/state_tracker/main.py

State Tracker:
- Tracks lifecycle of commands from agent.cmd and agent.out.* topics.
- Persists state in RedisJSON under key state:{trace_id}.
- Emits status updates to agent.status topic.
"""
import os
import json
import asyncio
import time
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import redis.asyncio as redis

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("state_tracker")

# Configuration
BOOTSTRAP     = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CMD_TOPIC     = os.getenv("AGENT_CMD_TOPIC", "agent.cmd")
RIDE_OUT      = os.getenv("RIDE_OUT_TOPIC", "agent.out.ride")
FOOD_OUT      = os.getenv("FOOD_OUT_TOPIC", "agent.out.food")
MART_OUT      = os.getenv("MART_OUT_TOPIC", "agent.out.mart")
STATUS_TOPIC  = os.getenv("STATUS_TOPIC", "agent.status")
REDIS_URL     = os.getenv("REDIS_URL", "redis://localhost:6379")

async def main():
    # RedisJSON client
    r = redis.Redis.from_url(REDIS_URL, decode_responses=True)

    # Kafka setup
    consumer = AIOKafkaConsumer(
        CMD_TOPIC, RIDE_OUT, FOOD_OUT, MART_OUT,
        bootstrap_servers=BOOTSTRAP,
        group_id="state_tracker",
        auto_offset_reset="earliest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start()
    await producer.start()
    log.info("State Tracker listening on cmd and out topics...")

    try:
        async for msg in consumer:
            topic = msg.topic
            data = json.loads(msg.value)
            trace_id = data.get("trace_id")
            key = f"state:{trace_id}"
            now = int(time.time() * 1000)

            if topic == CMD_TOPIC:
                # New command: initialize state
                state = {
                    "trace_id": trace_id,
                    "tool": data.get("tool"),
                    "arguments": data.get("arguments"),
                    "status": "pending",
                    "created_at": now,
                    "updated_at": now,
                    "result": None,
                    "history": [
                        {"ts": now, "status": "pending"}
                    ]
                }
                # Store as JSON
                await r.json().set(key, "$", state)
                log.info(f"Initialized state for {trace_id}")
                # Emit status update
                upd = {"trace_id": trace_id, "status": "pending"}
                await producer.send_and_wait(STATUS_TOPIC, json.dumps(upd).encode())

            else:
                # agent.out messages: update result and status
                # Determine outcome
                tool = data.get("tool")
                status = data.get("status") or "confirmed"
                result = data
                # Fetch existing state
                state = await r.json().get(key)
                if not state:
                    log.warning(f"No state found for trace_id {trace_id}")
                    continue
                # Update fields
                state["status"] = status
                state["result"] = result
                state["updated_at"] = now
                state.setdefault("history", []).append({"ts": now, "status": status})
                # Persist
                await r.json().set(key, "$", state)
                log.info(f"Updated state {trace_id} to {status}")
                # Emit status update including result
                upd = {"trace_id": trace_id, "status": status, "result": result}
                await producer.send_and_wait(STATUS_TOPIC, json.dumps(upd).encode())
    finally:
        await consumer.stop()
        await producer.stop()
        await r.close()

if __name__ == "__main__":
    asyncio.run(main())