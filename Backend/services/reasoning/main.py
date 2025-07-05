import os
import json
import time
import asyncio
import logging
import json
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool
import redis.asyncio as aioredis
import httpx

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("reasoning")

# ── Configuration ──────────────────────────────────────────────────────────
BOOTSTRAP   = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TRANS_TOPIC = os.getenv("VOICE_TOPIC_OUT",  "transcript")
CMD_TOPIC   = os.getenv("AGENT_CMD_TOPIC",  "agent.cmd")
ERROR_TOPIC = os.getenv("ERROR_TOPIC",      "agent.error")
REDIS_URL   = os.getenv("REDIS_URL", "redis://localhost:6379")

# Redis client
redis = aioredis.from_url(REDIS_URL)

# ── Tool schemas ───────────────────────────────────────────────────────────
book_ride_tool = StructuredTool(
    name="book_ride",
    description="Book a ride from pickup to dropoff.",
    args_schema={
        "type": "object",
        "properties": {"pickup":{"type":"string"},"dropoff":{"type":"string"},"time":{"type":"string","format":"date-time"}},
        "required":["pickup","dropoff"]
    }
)
order_food_tool = StructuredTool(
    name="order_food",
    description="Order dishes from a restaurant.",
    args_schema={
        "type":"object",
        "properties": {"restaurant_id":{"type":"string"},"items":{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"},"quantity":{"type":"integer","minimum":1}},"required":["name","quantity"]}},"delivery_address":{"type":"string"},"time":{"type":"string","format":"date-time"}},
        "required":["restaurant_id","items"]
    }
)
order_mart_tool = StructuredTool(
    name="order_mart",
    description="Order grocery items from a local mart.",
    args_schema={
        "type":"object",
        "properties": {"mart_id":{"type":"string"},"items":{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"},"quantity":{"type":"integer","minimum":1}},"required":["name","quantity"]}},"delivery_address":{"type":"string"},"time":{"type":"string","format":"date-time"}},
        "required":["mart_id","items"]
    }
)
TOOLS = [book_ride_tool, order_food_tool, order_mart_tool]

# ── Initialize LLMs ─────────────────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0, convert_system_message_to_human=True, api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyABDDCwsQWHFAcwgrIaPCRcYW5OojKro-A"))
clarify_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0, convert_system_message_to_human=True, api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyABDDCwsQWHFAcwgrIaPCRcYW5OojKro-A"))

# ── Clarify checker prompt ──────────────────────────────────────────────────
CLARIFY_PROMPT = """
You are a slot-checker that runs BEFORE using static profile or semantic memory.
TOOLS:
 • book_ride(pickup: string, dropoff: string)
 • order_food(restaurant_id: string, items: [{name,quantity}])
 • order_mart(mart_id: string, items: [{name,quantity}])

Behavior:
 • If the only missing information corresponds to user favourites (e.g., favorite restaurant, mart) or can be inferred from semantic memory (e.g., "what I had last week"), do NOT ask for clarification—set needs_clarification to false.
 • Otherwise, respond with exactly one JSON object and nothing else.

JSON schema:
  needs_clarification: boolean
  question: string (empty if no clarification needed)

Do not wrap JSON in markdown, prose, or backticks.

Examples:
 Input: "Order food"
 Output: {"needs_clarification":true,"question":"Which restaurant would you like?"}
 Input: "Order my usual lunch"
 Output: {"needs_clarification":false,"question":""}
 Input: "What did I order last week?"
 Output: {"needs_clarification":false,"question":""}
"""

# ── Assistant system prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a Grab multi-domain assistant.  
If transcript is about booking a ride, call tool book_ride.  
If ordering food, call tool order_food.  
If ordering groceries, call tool order_mart.  
Return JSON only via tool calls—no prose.
"""

# ── Main loop ───────────────────────────────────────────────────────────────
async def reason_loop():
    consumer = AIOKafkaConsumer(TRANS_TOPIC, bootstrap_servers=BOOTSTRAP, group_id="reasoning", auto_offset_reset="latest")
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    error_producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)

    await consumer.start(); await producer.start(); await error_producer.start()
    log.info(f"Listening on {TRANS_TOPIC}…")

    async for msg in consumer:
        try:
            entry    = json.loads(msg.value)
            trace_id = entry.get("trace_id")
            user_id  = entry.get("user_id", "demo-user")
            text     = entry.get("text","").strip()
            if not text:
                raise ValueError("Transcript text missing")
            log.info(f"Transcript received: {text!r}")

            # load or seed state
            state_key = f"state:{trace_id}"
            state = await redis.json().get(state_key) or {}
            if not state:
                tool = None
                if "food" in text.lower(): tool = "order_food"
                elif "mart" in text.lower(): tool = "order_mart"
                elif "ride" in text.lower(): tool = "book_ride"
                schema = next((t.args_schema for t in TOOLS if t.name==tool), {})
                slots = {s: None for s in schema.get("required", [])}
                state = {"slots": slots}
            slots = state.get("slots", {})

            # merge last answer
            last_slot = state.get("last_slot")
            if last_slot:
                slots[last_slot] = text
                state.pop("last_slot", None)

            # determine missing slots
            missing_slots = [k for k, v in slots.items() if v is None]
            # skip clarify if none
            if not missing_slots:
                await redis.delete(state_key)
                final_args = slots.copy()
            else:
                # Clarify Stage
                clarify_input = {**slots, "last_input": text}
                check = clarify_llm.invoke([
                    SystemMessage(content=CLARIFY_PROMPT),
                    HumanMessage(content=json.dumps(clarify_input))
                ])
                log.info(f"Clarify check result: {check.content}")
                result = json.loads(check.content)
                if result.get("needs_clarification"):
                    # determine which slot to ask next
                    slot_to_ask = result.get("slot") if result.get("slot") in missing_slots else missing_slots[0]
                    new_state = {"slots": slots, "last_slot": slot_to_ask, "step": state.get("step", 0) + 1}
                    await redis.json().set(state_key, '$', new_state)
                    clarify_cmd = {
                        "trace_id": trace_id,
                        "tool": "clarify",
                        "arguments": {"question": result.get("question", "")}
                    }
                    await producer.send_and_wait(CMD_TOPIC, json.dumps(clarify_cmd).encode())
                    log.info(f"Published clarify → {CMD_TOPIC}: {clarify_cmd}")
                    continue
                # completed clarify
                await redis.delete(state_key)
                final_args = slots.copy()

            # optional context enrich
            profile, few_shots = {}, []
            # try:
            #     r1 = await httpx.AsyncClient().get(
            #         f"http://localhost:8001/v1/users/{user_id}/profile",
            #         timeout=2.0
            #     )
            #     if r1.status_code == 200:
            #         profile = r1.json()
            # except Exception:
            #     pass
            try:
                sem = {"query": text, "top_k": 2}
                r2 = await httpx.AsyncClient().post(
                    f"http://localhost:8002/v1/users/{user_id}/retrieve",
                    json=sem,
                    timeout=3.0
                )
                if r2.status_code == 200:
                    few_shots = r2.json()
                    for shot in few_shots:
                        svc = shot.get("service")
                        if svc == "order_food":
                            # auto-fill restaurant_id and items from memory if slots empty
                            if slots.get("restaurant_id") is None:
                                slots["restaurant_id"] = shot.get("restaurant_id")
                            if slots.get("items") is None and shot.get("items_json"):
                                slots["items"] = json.loads(shot["items_json"])
                        elif svc == "order_mart":
                            if slots.get("mart_id") is None:
                                slots["mart_id"] = shot.get("mart_id")
                            if slots.get("items") is None and shot.get("items_json"):
                                slots["items"] = json.loads(shot["items_json"])
                        elif svc == "book_ride":
                            if slots.get("pickup") is None:
                                slots["pickup"]  = shot.get("pickup")
                            if slots.get("dropoff") is None:
                                slots["dropoff"] = shot.get("dropoff")
            except Exception:
                pass

            # main LLM invocation
            context = f"User Profile: {profile}\nPast Interactions: {few_shots}\n\n"+SYSTEM_PROMPT
            messages = [SystemMessage(content=context), HumanMessage(content=json.dumps(final_args))]
            response = llm.invoke(messages, tools=TOOLS)
            calls    = response.tool_calls or []
            if not calls:
                fallback = {"trace_id":trace_id, "tool":"clarify","arguments":{"question":"Could you clarify?"}}
                await producer.send_and_wait(CMD_TOPIC, json.dumps(fallback).encode())
                continue
            for tc in calls:
                cmd = {"trace_id":trace_id, "tool":tc["name"], "arguments":tc["args"]}
                await producer.send_and_wait(CMD_TOPIC, json.dumps(cmd).encode())
                log.info(f"Published → {CMD_TOPIC}: {cmd}")

        except Exception as e:
            raw = msg.value.decode(errors="replace")
            err = {"trace_id": trace_id if 'trace_id' in locals() else None, "error": str(e), "raw": raw}
            await error_producer.send_and_wait(ERROR_TOPIC, json.dumps(err).encode())
            log.error(f"Published DLQ → {ERROR_TOPIC}: {err}", exc_info=True)

    await consumer.stop(); await producer.stop(); await error_producer.stop()

if __name__ == "__main__":
    asyncio.run(reason_loop())