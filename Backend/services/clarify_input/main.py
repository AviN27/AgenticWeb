import os
import json
import time
import asyncio
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import redis.asyncio as aioredis

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("clarify_input")

# Configuration
BOOTSTRAP    = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CLARIFY_TOPIC= os.getenv("AGENT_OUT_CLARIFY_TOPIC", "agent.out.clarify")
TRANSCRIPT_TOPIC  = os.getenv("VOICE_TOPIC_OUT", "transcript")
REDIS_URL    = os.getenv("REDIS_URL", "redis://localhost:6379")
POLL_INTERVAL= float(os.getenv("CLARIFY_POLL_INTERVAL", "1.0"))

# Redis client
redis = aioredis.from_url(REDIS_URL)

async def handle_clarify(entry, producer):
    trace_id = entry.get("trace_id")
    user_id  = entry.get("user_id", "demo-user")
    log.info(f"Waiting for clarification answer for trace_id={trace_id}")
    key = f"clarify:{trace_id}"
    while True:
        # Check for user's answer in Redis JSON
        answer = await redis.json().get(key)
        if answer is not None:
            # Build transcript envelope
            ts = int(time.time() * 1000)
            envelope = {
                "trace_id":    trace_id,
                "user_id":     user_id,
                "ts_epoch_ms": int(time.time() * 1000),
                "text":        answer,
                "is_clarification": True,
            }
            await producer.send_and_wait(TRANSCRIPT_TOPIC, json.dumps(envelope).encode())
            log.info(f"Published clarified text to {TRANSCRIPT_TOPIC} for trace_id={trace_id}")
            # Optionally delete the Redis key
            await redis.delete(key)
            break
        await asyncio.sleep(POLL_INTERVAL)

async def main():
    # Kafka setup
    consumer = AIOKafkaConsumer(
        CLARIFY_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="clarify_input",
        auto_offset_reset="latest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)

    await consumer.start()
    await producer.start()
    log.info(f"Clarify Proxy listening on {CLARIFY_TOPIC}…")

    try:
        async for msg in consumer:
            try:
                entry = json.loads(msg.value)
                log.info(f"Received clarify request: {entry}")
                # Spawn task to poll Redis and forward when ready
                asyncio.create_task(handle_clarify(entry, producer))
            except Exception as e:
                log.error(f"Error processing clarify message: {e}")
    finally:
        await consumer.stop()
        await producer.stop()

if __name__ == "__main__":
    asyncio.run(main())