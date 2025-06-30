"""
services/reasoning/main.py  (LangChain + Gemini Pro)

Consumes transcripts from Kafka, invokes Gemini with up to three tools
(book_ride, order_food, order_mart), publishes all valid tool calls to agent.cmd,
and handles clarify‐fallbacks and errors via agent.error.
"""

import os
import json
import time
import asyncio
import logging

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import StructuredTool
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

# ── Tool schemas ───────────────────────────────────────────────────────────
book_ride_tool = StructuredTool(
    name="book_ride",
    description="Book a ride from pickup to dropoff at the given date-time.",
    args_schema={
        "type": "object",
        "properties": {
            "pickup":  {"type":"string"},
            "dropoff": {"type":"string"},
            "time":    {"type":"string","format":"date-time"}
        },
        "required": ["pickup","dropoff"]
    }
)

order_food_tool = StructuredTool(
    name="order_food",
    description="Order dishes from a restaurant for delivery.",
    args_schema={
        "type": "object",
        "properties": {
            "restaurant_id":    {"type":"string"},
            "items": {
                "type":"array",
                "items": {
                    "type":"object",
                    "properties": {
                        "name":     {"type":"string"},
                        "quantity": {"type":"integer","minimum":1}
                    },
                    "required":["name","quantity"]
                }
            },
            "delivery_address":{"type":"string"},
            "time":            {"type":"string","format":"date-time"}
        },
        "required": ["restaurant_id","items"]
    }
)

order_mart_tool = StructuredTool(
    name="order_mart",
    description="Order grocery items from a local mart for delivery.",
    args_schema={
        "type": "object",
        "properties": {
            "mart_id":           {"type":"string"},
            "items": {
                "type":"array",
                "items": {
                    "type":"object",
                    "properties": {
                        "name":     {"type":"string"},
                        "quantity": {"type":"integer","minimum":1}
                    },
                    "required":["name","quantity"]
                }
            },
            "delivery_address":  {"type":"string"},
            "time":              {"type":"string","format":"date-time"}
        },
        "required": ["mart_id","items"]
    }
)

TOOLS = [book_ride_tool, order_food_tool, order_mart_tool]

# ── Initialize LLM (Gemini Pro) ─────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.0,
    convert_system_message_to_human=True,
)

SYSTEM_PROMPT = """You are a Grab multi-domain assistant.
If transcript is about booking a ride, call tool book_ride.
If about ordering food, call tool order_food.
If about groceries, call tool order_mart.
Return JSON only via tool calls—no prose responses."""

# ── Main loop ───────────────────────────────────────────────────────────────
async def reason_loop():
    consumer = AIOKafkaConsumer(
        TRANS_TOPIC,
        bootstrap_servers=BOOTSTRAP,
        group_id="reasoning",
        auto_offset_reset="latest"
    )
    producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)
    error_producer = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP)

    await consumer.start()
    await producer.start()
    await error_producer.start()
    log.info(f"Listening on {TRANS_TOPIC}…")

    async for msg in consumer:
        try:
            entry = json.loads(msg.value)
            trace_id = entry.get("trace_id")
            text = entry.get("text", "").strip()
            if not text:
                raise ValueError("Transcript text missing")

            log.info(f"Transcript received: {text!r}")

            try:
                resp = await httpx.get(
                    f"http://localhost:8001/v1/users/{user_id}/profile",
                    timeout=2.0
                )
                profile = resp.json()
            except Exception:
                profile = {}

            few_shots = []
            try:
                sem_req = {"query": text, "top_k": 2}
                resp2 = await httpx.post(
                    f"http://localhost:8002/v1/users/{user_id}/retrieve",
                    json=sem_req,
                    timeout=3.0
                )
                few_shots = resp2.json()
            except Exception:
                few_shots = []
            context_snippet = (
                f"User Profile: {profile}\n"
                f"Similar Past Interactions: {few_shots}\n\n"
            )
            messages = [
                SystemMessage(content=context_snippet + SYSTEM_PROMPT),
                HumanMessage(content=text)
            ]
            response = llm.invoke(messages, tools=TOOLS)
            log.info(f"LLM response: {response}")
            calls = response.tool_calls or []

            # Clarify fallback
            if not calls:
                clarify_cmd = {
                    "trace_id":  trace_id,
                    "tool":      "clarify",
                    "arguments": {"question": "Could you clarify your request?"}
                }
                await producer.send_and_wait(CMD_TOPIC, json.dumps(clarify_cmd).encode())
                log.info(f"Published clarify → {CMD_TOPIC}: {clarify_cmd}")
                continue

            # Publish each tool call
            for tc in calls:
                cmd = {
                    "trace_id":  trace_id,
                    "tool":      tc["name"],
                    "arguments": tc["args"]
                }
                # Basic validation: required args present?
                schema = next((t.args_schema for t in TOOLS if t.name == tc["name"]), None)
                missing = [k for k in schema.get("required", []) if k not in cmd["arguments"]]
                if missing:
                    err = {
                        "trace_id": trace_id,
                        "agent":    tc["name"],
                        "error":    f"Missing required args: {missing}",
                        "raw_args": cmd["arguments"]
                    }
                    await error_producer.send_and_wait(ERROR_TOPIC, json.dumps(err).encode())
                    log.error(f"Published error → {ERROR_TOPIC}: {err}")
                    # ask for clarification
                    clarify_cmd = {
                        "trace_id":  trace_id,
                        "tool":      "clarify",
                        "arguments": {"question": f"Missing information: {missing}. Please clarify."}
                    }
                    await producer.send_and_wait(CMD_TOPIC, json.dumps(clarify_cmd).encode())
                    log.info(f"Published clarify → {CMD_TOPIC}: {clarify_cmd}")
                    continue

                await producer.send_and_wait(CMD_TOPIC, json.dumps(cmd).encode())
                log.info(f"Published → {CMD_TOPIC}: {cmd}")

        except Exception as e:
            # Unexpected error → DLQ
            raw = msg.value.decode(errors="replace")
            err = {"trace_id": None, "error": str(e), "raw": raw}
            await error_producer.send_and_wait(ERROR_TOPIC, json.dumps(err).encode())
            log.error(f"Published DLQ → {ERROR_TOPIC}: {err}", exc_info=True)
            continue

    await consumer.stop()
    await producer.stop()
    await error_producer.stop()

if __name__ == "__main__":
    asyncio.run(reason_loop())