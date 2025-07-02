"""Mock grocery‑mart agent. Listens agent.cmd, writes agent.out.mart."""
import os, json, asyncio, logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("mart_agent")

BOOT=os.getenv("KAFKA_BOOTSTRAP","localhost:9092").split(",")
CMD="agent.cmd"; OUT="agent.out.mart"

async def main():
    c=AIOKafkaConsumer(CMD,bootstrap_servers=BOOT,group_id="mart_agent",auto_offset_reset="latest")
    p=AIOKafkaProducer(bootstrap_servers=BOOT)
    await c.start(); await p.start(); log.info("Mart agent up…")
    try:
        async for msg in c:
            e=json.loads(msg.value)
            if e.get("tool")!="order_mart": continue
            res={"trace_id":e["trace_id"],"status":"confirmed","eta":"45 min","total":"35.00 SGD"}
            await p.send_and_wait(OUT,json.dumps(res).encode())
            log.info(f"Mart order → {res}")
    finally:
        await c.stop(); await p.stop()

if __name__ == "__main__":
    asyncio.run(main())