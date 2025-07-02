"""
Clarify Agent:
Consumes agent.cmd commands where tool=="clarify",
and publishes a user-facing question to agent.out.clarify.
"""
import os
import json
import asyncio
import logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("clarify_agent")

BOOTSTRAP     = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
CMD_TOPIC     = os.getenv("AGENT_CMD_TOPIC", "agent.cmd")
CLARIFY_TOPIC = os.getenv("CLARIFY_OUT_TOPIC", "agent.out.clarify")

async def run_clarify_agent():
    consumer = AIOKafkaConsumer(
        CMD_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="clarify_agent",
        auto_offset_reset="earliest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await consumer.start()
    await producer.start()
    log.info(f"Clarify Agent listening on {CMD_TOPIC}…")

    async for msg in consumer:
        try:
            cmd = json.loads(msg.value)
            if cmd.get("tool") != "clarify":
                continue
            question = cmd["arguments"].get("question", "Could you clarify your request?")
            out = {
                "trace_id": cmd.get("trace_id"),
                "question": question
            }
            await producer.send_and_wait(CLARIFY_TOPIC, json.dumps(out).encode())
            log.info(f"Published clarification to {CLARIFY_TOPIC}: {out}")
        except Exception as e:
            log.error(f"Error in Clarify Agent: {e}", exc_info=True)

    await consumer.stop()
    await producer.stop()

if __name__ == "__main__":
    asyncio.run(run_clarify_agent())