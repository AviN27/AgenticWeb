"""Mock ride‑hailing agent. Listens to agent.cmd, outputs to agent.out.ride."""
import os, json, asyncio, logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ride_agent")

BOOT = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092").split(",")
CMD  = "agent.cmd"
OUT  = "agent.out.ride"

async def main():
    c = AIOKafkaConsumer(CMD, bootstrap_servers=BOOT, group_id="ride_agent", auto_offset_reset="latest")
    p = AIOKafkaProducer(bootstrap_servers=BOOT)
    await c.start(); await p.start()
    log.info("Ride agent up…")
    try:
        async for msg in c:
            env = json.loads(msg.value)
            if env.get("tool") != "book_ride":
                continue
            res = {"trace_id": env["trace_id"], "status":"confirmed", "eta":"4 min", "price":"5 SGD"}
            await p.send_and_wait(OUT, json.dumps(res).encode())
            log.info(f"Ride booked → {res}")
    finally:
        await c.stop(); await p.stop()

if __name__ == "__main__":
    asyncio.run(main())