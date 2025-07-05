import os
import json
import time
import logging
import asyncio

from fastapi import FastAPI, BackgroundTasks, HTTPException
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiokafka import AIOKafkaProducer
import httpx
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

# ── Logging ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("suggestions")

# ── Config ─────────────────────────────────────────────────────────────────
KAFKA_BOOT   = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
SEMANTIC_URL = os.getenv("SEMANTIC_URL", "http://localhost:8002/v1/users/{user}/retrieve")
SUGGEST_TOPIC = os.getenv("AGENT_SUGGEST_TOPIC", "agent.suggest")

# ── FastAPI App ────────────────────────────────────────────────────────────
app = FastAPI(title="Suggestion Service")

# ── LLM for suggestion phrasing ─────────────────────────────────────────────
suggestion_llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.7,
    convert_system_message_to_human=True,
    api_key=os.getenv("GOOGLE_API_KEY", "AIzaSyABDDCwsQWHFAcwgrIaPCRcYW5OojKro-A")
)

# ── Kafka producer ─────────────────────────────────────────────────────────
producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOT)

# ── Utility Functions ───────────────────────────────────────────────────────
async def fetch_top_interaction(user_id: str, query: str):
    """
    Call semantic service to retrieve top past interaction matching 'query'.
    Returns the 'text' of the first match or None.
    """
    url = SEMANTIC_URL.format(user=user_id)
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json={"query": query, "top_k": 1})
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Semantic service error")
    data = resp.json()
    return data[0] if data else None


def phrase_suggestion(service: str, past_text: str) -> str:
    """
    Generate a one-sentence suggestion based on service domain.
    """
    if service == "book_ride":
        prompt = (
            f"You know the user previously said: \"{past_text}\" as a ride request."
            "\nGenerate exactly one sentence suggestion: \"Shall I book that ride again?\""
        )
    else:
        prompt = (
            f"You know the user previously said: \"{past_text}\"."
            "\nGenerate exactly one sentence suggestion: \"Would you like to reorder {past_text}?\""
        )
    response = suggestion_llm.invoke([
        SystemMessage(content="You are a suggestion assistant that proposes context-aware prompts."),
        HumanMessage(content=prompt)
    ])
    return response.content.strip().strip('"')


async def run_suggestions():
    """
    For each domain, fetch past interaction and publish a suggestion if found.
    Domains and their queries:
      - order_food: "lunch"
      - order_mart: "groceries"
      - book_ride: "commute"
    """
    user_id = "demo-user"  # replace with real user list in production
    specs = [
        ("order_food", "lunch"),
        ("order_mart", "groceries"),
        ("book_ride", "commute")
    ]
    now_ms = int(time.time() * 1000)
    for service, query in specs:
        try:
            past = await fetch_top_interaction(user_id, query)
            if past:
                text = past["text"]
                rest = past.get("restaurant_id") or past.get("mart_id") or ""
                suggestion = phrase_suggestion(service, text, extra=rest)
        except Exception as e:
            log.warning(f"Skipping {service}: semantic fetch failed: {e}")
            continue
        if not past:
            log.info(f"No past data for {service} query '{query}'")
            continue
        suggestion = phrase_suggestion(service, past)
        envelope = {
            "trace_id":    f"suggest-{int(time.time())}",
            "user_id":     user_id,
            "service":     service,
            "past_text":   past,
            "suggestion":  suggestion,
            "ts_epoch_ms": now_ms
        }
        await producer.send_and_wait(SUGGEST_TOPIC, json.dumps(envelope).encode())
        log.info(f"Published suggestion for {service}: {suggestion}")


# ── Startup & Endpoints ─────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    await producer.start()
    sched = AsyncIOScheduler(timezone="Asia/Kolkata")
    # schedule daily at 11:30 AM
    sched.add_job(run_suggestions, "cron", hour=11, minute=30)
    sched.start()
    log.info("Scheduler started for suggestions")

@app.post("/v1/suggestions/run")
async def manual_run(background: BackgroundTasks):
    """
    Trigger suggestions on demand.
    """
    background.add_task(run_suggestions)
    return {"status":"scheduled"}

@app.get("/health")
async def health():
    return {"status":"ok"}
