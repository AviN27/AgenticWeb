"""
scripts/embed_history.py

Consumes the transcript Kafka topic, embeds each record’s text
using Gemini (“embed-gecko-001”), and upserts into Pinecone (or RedisVector).
"""
import os, asyncio, json
from aiokafka import AIOKafkaConsumer
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

# ── Configuration ─────────────────────────────────────────────────────────────
API_KEY       = os.getenv("GOOGLE_API_KEY")
BOOTSTRAP     = os.getenv("KAFKA_BOOTSTRAP","localhost:9092").split(",")
PINECONE_KEY  = os.getenv("PINECONE_KEY", "pcsk_5GgCax_QTbiMCfwMRi9TYn9PbLTrvzmepew5UMuciV8p2PXyRFj9eARnMveT2mNDppT92w")
PINECONE_ENV  = os.getenv("PINECONE_ENV","us-east-1")
INDEX_NAME    = "user-interactions"
DIMENSION     = 3072

# ── Initialize Gemini Embeddings ─────────────────────────────────────────────
embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    temperature=0.0,
    api_key=API_KEY
)

# ── Initialize Pinecone client & index ────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    # Create a Serverless index for convenience
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(INDEX_NAME)

# ── Kafka Consumer ───────────────────────────────────────────────────────────

async def main():
    consumer = AIOKafkaConsumer(
        "transcript",
        bootstrap_servers=BOOTSTRAP,
        group_id="embed_history",
        auto_offset_reset="earliest"
    )
    await consumer.start()
    try:
        async for msg in consumer:
            entry = json.loads(msg.value)
            text    = entry.get("text","")
            user_id = entry.get("user_id","unknown")
            ts      = entry.get("ts_epoch_ms",0)

            # 1) compute Gemini embedding
            emb = embedder.embed_query(text)
            await asyncio.sleep(10)  # Add delay to avoid rate limit (429 error)

            # 2) upsert into Pinecone
            meta = {"user_id": user_id, "text": text, "timestamp": ts}
            index.upsert([(entry["trace_id"], emb, meta)])
            print(f"Upserted trace_id={entry['trace_id']}")
            
    finally:
        await consumer.stop()

if __name__=="__main__":
    asyncio.run(main())