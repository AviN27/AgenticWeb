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

def identify_tool(text: str) -> str:
    """
    Ask the LLM which tool to use given the user text.
    Returns the tool name exactly matching one of TOOLS.
    """
    prompt = (
        "Which one of these tools best matches the user's request?"
        " Options: book_ride, order_food, order_mart."
    )
    response = llm.invoke([
        SystemMessage(content=prompt),
        HumanMessage(content=text)
    ])
    # Expect content like 'order_food'
    return response.content.strip()

async def autofill_slots_from_memory(
    text: str,
    user_id: str,
    slots: dict,
    requires_memory: bool,
    top_k: int = 2,
    memory_endpoint: str = "http://localhost:8002/v1/users"
) -> dict:
    """
    If requires_memory is True, retrieves the last `top_k` memory shots for the given text
    and user, then auto‐fills missing slots for food orders, mart purchases, and rides.
    Returns the updated slots dict.
    """
    if not requires_memory:
        return slots

    try:
        payload = {"query": text, "top_k": top_k}
        url = f"{memory_endpoint}/{user_id}/retrieve"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=3.0)

        if response.status_code != 200:
            logging.warning(f"Memory retrieval returned status {response.status_code}")
            return slots

        few_shots = response.json()
        for shot in few_shots:
            svc = shot.get("service")
            # FOOD
            if svc == "order_food":
                if slots.get("restaurant_id") is None:
                    slots["restaurant_id"] = shot.get("restaurant_id")
                if slots.get("items") is None and shot.get("items_json"):
                    slots["items"] = json.loads(shot["items_json"])
            # MART
            elif svc == "order_mart":
                if slots.get("mart_id") is None:
                    slots["mart_id"] = shot.get("mart_id")
                if slots.get("items") is None and shot.get("items_json"):
                    slots["items"] = json.loads(shot["items_json"])
            # RIDE
            elif svc == "book_ride":
                if slots.get("pickup") is None:
                    slots["pickup"] = shot.get("pickup")
                if slots.get("dropoff") is None:
                    slots["dropoff"] = shot.get("dropoff")

    except Exception as e:
        logging.warning(f"Failed to autofill slots from memory: {e}")

    return slots

# ── Assistant system prompt ─────────────────────────────────────────────────
SYSTEM_PROMPT = """
You are a Grab multi-domain assistant.  
If transcript is about booking a ride, call tool book_ride.  
If ordering food, call tool order_food.  
If ordering groceries, call tool order_mart.  
Return JSON only via tool calls—no prose.
"""

TOOL_IDENTIFY_PROMPT = """
Which one of these tools best matches the user request? Only reply with the tool name:
- book_ride
- order_food
- order_mart
"""
EXTRACTION_PROMPT = """
You must extract exactly these keys for the chosen tool:
    • For book_ride(pickup: string, dropoff: string)
    • For order_food(restaurant_id: string, items: [{name,quantity}])
    • For order_mart(mart_id: string, items: [{name,quantity}])

Return a single JSON object with exactly those keys.  
If a slot is not present in the user text, set its value to null.  
Do NOT wrap the JSON in markdown, prose, or backticks.

Example input: "Take me from MG Road to Hutchins Road"
Example output: {"pickup":"MG Road","dropoff":"Hutchins Road","time":null}
Example input: "Order 2 Zinger Burgers and 1 medium fries from KFC"
Example output: {"restaurant_id":"kfc","items":[{"name":"Zinger Burger","quantity":2},{"name":"medium fries","quantity":1}],"delivery_address":null,"time":null}
Example input: "Order 1 kg of apples and 2 kg of rice from the nearest mart"
Example output: {"mart_id":null,"items":[{"name":"apples","quantity":1},{"name":"rice","quantity":2}],"delivery_address":null,"time":null}
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
            is_clarification = entry.get("is_clarification", False)

            temporal_terms = ["yesterday","last week","two weeks ago","a week ago","today"]
            text_lower = text.lower()
            requires_memory = any(term in text_lower for term in temporal_terms)

            if not text:
                raise ValueError("Transcript text missing")
            log.info(f"Transcript received: {text!r}")

            # load or seed state
            tool_name = identify_tool(text)
            schema = next((t.args_schema for t in TOOLS if t.name == tool_name), {})

            if not is_clarification:
                extraction = llm.invoke([
                    SystemMessage(content=f"Tool Schema: {tool_name}. Do not wrap JSON in markdown, prose, or backticks." + EXTRACTION_PROMPT),
                    HumanMessage(content=text)
                ])
                log.info(f"Extraction result: {extraction.content}")
                slots = json.loads(extraction.content)
                log.info(f"Extracted slots for {trace_id}: {slots}")
                missing_slots_initial = [k for k, v in slots.items() if v is None]
                if not missing_slots_initial:
                    final_args = slots.copy()
                    is_clarification = False
                elif requires_memory:
                    slots = await autofill_slots_from_memory(
                        text,
                        user_id,
                        slots,
                        requires_memory
                    )
                    missing_slots_vector = [k for k, v in slots.items() if v is None]
                    if not missing_slots_vector:
                        final_args = slots.copy()
                        is_clarification = False
                    else:
                        is_clarification = True
                        state_key_vector = f"state:{trace_id}"
                        await redis.json().set(state_key_vector, '$', {"slots": slots})
                else:
                    is_clarification = True
                    state_key_initial = f"state:{trace_id}"
                    await redis.json().set(state_key_initial, '$', {"slots": slots})

            # Initialize slot state
            if (is_clarification):
                state_key = f"state:{trace_id}"
                state = await redis.json().get(state_key) or {"slots": {arg: None for arg in schema.get("required", [])}}
                slots = state.get("slots", {})
                log.info(f"Current state for {trace_id}: {state}")
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
            profile = {}
            try:
                r1 = await httpx.AsyncClient().get(
                    f"http://localhost:8001/v1/users/{user_id}/profile",
                    timeout=2.0
                )
                if r1.status_code == 200:
                    profile = r1.json()
            except Exception:
                pass

            # main LLM invocation
            context = f"User Profile: {profile}\n\n"+SYSTEM_PROMPT
            messages = [SystemMessage(content=context), HumanMessage(content=json.dumps(final_args))]
            response = llm.invoke(messages, tools=TOOLS)
            calls = response.tool_calls or []
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