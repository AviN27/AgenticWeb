import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pinecone import Pinecone
from pinecone import ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# ── Configuration ─────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyABDDCwsQWHFAcwgrIaPCRcYW5OojKro-A")
PINECONE_KEY   = os.getenv("PINECONE_KEY", "pcsk_5GgCax_QTbiMCfwMRi9TYn9PbLTrvzmepew5UMuciV8p2PXyRFj9eARnMveT2mNDppT92w")
PINECONE_ENV   = os.getenv("PINECONE_ENV","us-east-1")
INDEX_NAME     = "user-interactions"
DIMENSION      = 3072

# ── Initialize FastAPI ────────────────────────────────────────────────────────
app = FastAPI(title="Semantic Context Service")

# ── Initialize Pinecone ───────────────────────────────────────────────────────
pc = Pinecone(api_key=PINECONE_KEY)
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index(INDEX_NAME)

# ── Initialize Gemini embedder ────────────────────────────────────────────────
embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    temperature=0.0,
    google_api_key=GOOGLE_API_KEY
)

# ── Models ─────────────────────────────────────────────────────────────────────
class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 3

class Interaction(BaseModel):
    trace_id: str
    user_id: str
    text: str
    timestamp: int
    score: float
    trace_id:    str
    user_id:      str
    text:         str
    timestamp:    int
    score:        float
    service:      str | None = None
    restaurant_id:str | None = None
    mart_id:      str | None = None
    location:     str | None = None
    items_json:   str | None = None

# ── Endpoint ───────────────────────────────────────────────────────────────────
@app.post("/v1/users/{user_id}/retrieve", response_model=list[Interaction])
async def retrieve(user_id: str, body: RetrieveRequest):
    # 1) embed the query text
    qemb = embedder.embed_query(body.query)

    # 2) query Pinecone with a user filter
    try:
        res = index.query(
            vector=qemb,
            top_k=body.top_k,
            filter={"user_id": user_id},
            include_metadata=True,
        )
    except Exception as e:
        raise HTTPException(500, f"Pinecone query failed: {e}")

    # 3) format results
    interactions = []
    for match in res.matches:
        m = match.metadata or {}
        interactions.append(Interaction(
            trace_id     = match.id,
            user_id      = m.get("user_id",""),
            text         = m.get("text",""),
            timestamp    = m.get("timestamp",0),
            score        = match.score,
            service      = m.get("service"),
            restaurant_id= m.get("restaurant_id"),
            mart_id      = m.get("mart_id"),
            location     = m.get("location"),
            items_json   = m.get("items_json")
        ))
    print(f"Retrieved {interactions}")
    return interactions