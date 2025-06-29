"""
Error Agent:
Consumes all messages on agent.error (DLQ),
and logs or forwards them for notification.
"""
import os
import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer

logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("error_agent")

BOOTSTRAP    = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
ERROR_TOPIC  = os.getenv("ERROR_TOPIC", "agent.error")

async def run_error_agent():
    consumer = AIOKafkaConsumer(
        ERROR_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="error_agent",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    log.warning(f"Error Agent listening on {ERROR_TOPIC}…")

    async for msg in consumer:
        try:
            err = json.loads(msg.value)
        except Exception:
            # If even parsing fails, log raw bytes
            log.error(f"Unparseable error record: {msg.value!r}")
            continue
        # Here you could hook into alerting/monitoring systems
        log.error(f"DLQ event from {ERROR_TOPIC}: {json.dumps(err)}")

    await consumer.stop()

if __name__ == "__main__":
    asyncio.run(run_error_agent())