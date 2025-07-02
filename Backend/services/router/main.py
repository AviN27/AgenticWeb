import os
import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("action_router")

# Configuration
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CMD_TOPIC = os.getenv("AGENT_CMD_TOPIC", "agent.cmd")
ADAPTER_GATEWAY = os.getenv("ADAPTER_GATEWAY_URL", "http://localhost:8100")

# Mapping of tool name to (HTTP path, output Kafka topic)
ROUTING = {
    "book_ride":   ("/ride/book",      "agent.out.ride"),
    "order_food":  ("/food/order",     "agent.out.food"),
    "order_mart":  ("/mart/purchase",  "agent.out.mart"),
    "charge":      ("/payment/charge", "agent.out.pay"),
    "clarify":     ("/clarify/proxy",  "agent.out.clarify"),  # optional
}

async def router_loop():
    consumer = AIOKafkaConsumer(
        CMD_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="action_router",
        auto_offset_reset="earliest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)

    await consumer.start()
    await producer.start()
    log.info(f"Action Router listening on topic {CMD_TOPIC}...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            async for msg in consumer:
                try:
                    cmd = json.loads(msg.value)
                    trace_id = cmd.get("trace_id")
                    tool = cmd.get("tool")
                    args = cmd.get("arguments", {})

                    if tool not in ROUTING:
                        log.warning(f"No routing entry for tool {tool}, skipping")
                        continue

                    path, out_topic = ROUTING[tool]
                    url = f"{ADAPTER_GATEWAY}{path}"
                    log.info(f"Dispatching {tool} to {url} args={args}")

                    # Call adapter
                    response = await client.post(url, json=args)
                    response.raise_for_status()
                    payload = response.json()

                    # Ensure trace_id is preserved
                    payload.setdefault("trace_id", trace_id)
                    log.info(f"Received response for {tool}: {payload}")

                    # Publish to Kafka
                    await producer.send_and_wait(out_topic, json.dumps(payload).encode())
                    log.info(f"Published to {out_topic}: {payload}")

                except Exception as e:
                    log.error(f"Error processing message {msg.value}: {e}", exc_info=True)
        finally:
            await consumer.stop()
            await producer.stop()

if __name__ == "__main__":
    asyncio.run(router_loop())