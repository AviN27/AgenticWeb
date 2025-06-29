"""
Reasoning Engine
Consumes transcript, calls GPT‑4o with tool schemas, publishes tool‑calls to agent.cmd.
"""
import os, json, time, asyncio, logging
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import openai

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("reasoning")

BOOTSTRAP   = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092").split(",")
TRANS_TOPIC = os.getenv("VOICE_TOPIC_OUT", "transcript")
CMD_TOPIC   = os.getenv("AGENT_CMD_TOPIC", "agent.cmd")
openai.api_key = os.getenv("OPENAI_API_KEY", "")
MODEL = "gpt-4o"

book_ride = {
    "name": "book_ride",
    "description": "Book a cab from pickup to dropoff at the given time",
    "parameters": {
        "type": "object",
        "properties": {
            "pickup":  {"type": "string", "description": "Pickup location"},
            "dropoff": {"type": "string", "description": "Dropoff location"},
            "time":    {"type": "string", "format": "date-time"}
        },
        "required": ["pickup","dropoff"]
    }
}
order_food = {
    "name": "order_food",
    "description": "Order dishes from a restaurant",
    "parameters": {
        "type": "object",
        "properties": {
            "restaurant_id": {"type":"string"},
            "items":         {
               "type":"array",
               "items":{"type":"object","properties":{
                   "name":{"type":"string"},
                   "quantity":{"type":"integer","minimum":1}
               },"required":["name","quantity"]}
            },
            "delivery_address":{"type":"string"},
            "time":{"type":"string","format":"date-time"}
        },
        "required":["restaurant_id","items"]
    }
}
order_mart =  {
    "name": "order_mart",
    "description": "Order groceries from a local mart",
    "parameters": {
        "type": "object",
        "properties": {
            "mart_id": {"type":"string"},
            "items":   {
               "type":"array",
               "items":{"type":"object","properties":{
                   "name":{"type":"string"},
                   "quantity":{"type":"integer","minimum":1}
               },"required":["name","quantity"]}
            },
            "delivery_address":{"type":"string"},
            "time":{"type":"string","format":"date-time"}
        },
        "required":["mart_id","items"]
    }
}

async def main():
    cons = AIOKafkaConsumer(TRANS_TOPIC, bootstrap_servers=BOOTSTRAP, group_id="reason", auto_offset_reset="latest")
    prod = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    await cons.start(); await prod.start()
    log.info("Reasoning Engine up — waiting transcripts…")
    try:
        async for msg in cons:
            t = json.loads(msg.value)
            prompt = f"User context: home='123 Main', work='456 Market'. Transcript: {t['text']}"
            resp = openai.ChatCompletion.create(
                model=MODEL,
                messages=[{"role":"system","content":prompt}],
                functions=[book_ride, order_food, order_mart],
                function_call="auto"
            )
            fc = resp.choices[0].message
            env = {"trace_id": t.get("trace_id"), "tool": fc.function_name, "arguments": json.loads(fc.arguments)}
            await prod.send_and_wait(CMD_TOPIC, json.dumps(env).encode())
            log.info(f"→ {env}")
    finally:
        await cons.stop(); await prod.stop()

if __name__ == "__main__":
    asyncio.run(main())