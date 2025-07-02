"""Mock food‑ordering agent. Listens agent.cmd, writes agent.out.food."""
import os, json, asyncio, logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("food_agent")

BOOT=os.getenv("KAFKA_BOOTSTRAP","localhost:9092").split(",")
CMD="agent.cmd"; OUT="agent.out.food"

async def main():
    c=AIOKafkaConsumer(CMD,bootstrap_servers=BOOT,group_id="food_agent",auto_offset_reset="latest")
    p=AIOKafkaProducer(bootstrap_servers=BOOT)
    await c.start(); await p.start(); log.info("Food agent up…")
    try:
        async for msg in c:
            e=json.loads(msg.value)
            if e.get("tool")!="order_food": continue
            res={"trace_id":e["trace_id"],"status":"confirmed","eta":"25 min","total":"20.50 SGD"}
            await p.send_and_wait(OUT,json.dumps(res).encode())
            log.info(f"Food order → {res}")
    finally:
        await c.stop(); await p.stop()

if __name__=="__main__":
    asyncio.run(main()) #!/usr/bin/env python3
