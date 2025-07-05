import time
import random
from datetime import datetime, timedelta
import os
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from pinecone.exceptions import PineconeException
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import json
from google.api_core.exceptions import ResourceExhausted
from langchain_google_genai._common import GoogleGenerativeAIError

# ── Config ───────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyABDDCwsQWHFAcwgrIaPCRcYW5OojKro-A")
PINECONE_KEY   = os.getenv("PINECONE_KEY", "pcsk_5GgCax_QTbiMCfwMRi9TYn9PbLTrvzmepew5UMuciV8p2PXyRFj9eARnMveT2mNDppT92w")
PINECONE_ENV   = os.getenv("PINECONE_ENV","us-east-1")
INDEX_NAME     = "user-interactions"
DIMENSION      = 3072

# Create index if missing
pc = Pinecone(api_key=PINECONE_KEY)                          
if not pc.has_index("user-interactions"):
    pc.create_index(
        name="user-interactions",
        vector_type="dense",
        dimension=3072,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
index = pc.Index("user-interactions")

# ── Clear existing data ──────────────────────────────────────────────────────
# print("Clearing existing index...")
# index.delete(delete_all=True)
# print("Index cleared.")

# try:
#     # 1) Discover all existing namespaces
#     stats = index.describe_index_stats(include_namespaces=True)
#     namespaces = stats.get("namespaces", {}).keys()

#     # 2) For each namespace, delete all vectors in it
#     for ns in namespaces:
#         print(f"  Deleting namespace '{ns}'…")
#         index.delete(delete_all=True, namespace=ns)
#     print("Index cleared.")
# except PineconeException as e:
#     # If there truly are no namespaces, skip
#     if "Namespace not found" in str(e):
#         print("No namespaces to delete, index already clean.")
#     else:
#         # re-raise anything unexpected
#         raise

# ── Sample interaction templates with mixed Western & Indian Bengaluru cuisine ──
rides = [
    {"pickup": "MG Road, Bengaluru", "dropoff": "Koramangala 5th Block, Bengaluru"},
    {"pickup": "Whitefield Railway Station, Bengaluru", "dropoff": "Marathahalli, Bengaluru"},
    {"pickup": "HAL Airport Road, Bengaluru", "dropoff": "Indiranagar, Bengaluru"},
    {"pickup": "Yelahanka New Town, Bengaluru", "dropoff": "Jayanagar 4th Block, Bengaluru"},
    {"pickup": "Brigade Road, Bengaluru", "dropoff": "Electronic City, Bengaluru"},
]

restaurants = [
    {"restaurant_id": "mavalli-tiffin-room", "name": "MTR",       "cuisine": "South Indian", "location": "Church Street"},
    {"restaurant_id": "truffles",            "name": "Truffles",  "cuisine": "Continental",  "location": "Koramangala 5th"},
    {"restaurant_id": "sushi-central",       "name": "Sushi Central", "cuisine": "Japanese", "location": "Indiranagar"},
    {"restaurant_id": "pizza-paradise",      "name": "Pizza Paradise", "cuisine": "Italian",  "location": "Brigade Road"},
    {"restaurant_id": "burrito-bay",         "name": "Burrito Bay",    "cuisine": "Mexican",  "location": "Koramangala 7th"},
    {"restaurant_id": "spice-route",         "name": "Spice Route",    "cuisine": "Indian Fusion", "location": "Church Street"},
    {"restaurant_id": "cafe-cocoa",          "name": "Cafe Cocoa",     "cuisine": "Cafe & Bakery",   "location": "Indiranagar"},
]

marts = [
    {"mart_id": "reliance-fresh", "name": "Reliance Fresh",       "location": "Koramangala 3rd"},
    {"mart_id": "big-bazaar",      "name": "Big Bazaar",           "location": "Brigade Road"},
    {"mart_id": "nandini",         "name": "Nandini Dairy Store",  "location": "Indiranagar"},
    {"mart_id": "sowparnika",      "name": "Sowparnika Trading Co", "location": "Jayanagar 4th"},
]

def random_timestamp(days_back=30):
    now = datetime.utcnow()
    delta = timedelta(days=random.randint(0, days_back),
                      hours=random.randint(0,23),
                      minutes=random.randint(0,59))
    return int((now - delta).timestamp() * 1000)

templates = []
user_id = "demo-user"

# Ride records
for i, ride in enumerate(rides):
    templates.append({
        "id": f"ride-{i}",
        "values": [0]*DIMENSION,  # placeholder vector to be replaced
        "metadata": {
            "user_id": user_id,
            "text": f"Book a ride from {ride['pickup']} to {ride['dropoff']}.",
            "timestamp": random_timestamp(),
            "service": "book_ride",
            "pickup": ride["pickup"],
            "dropoff": ride["dropoff"]
        }
    })

# Food records
offset = len(rides)
for i, rest in enumerate(restaurants):
    item = random.choice(["Masala Dosa","Grilled Chicken Sandwich","Chocolate Croissant","Filter Coffee"])
    qty  = random.randint(1,3)
    templates.append({
        "id": f"food-{offset + i}",
        "values": [0]*DIMENSION,
        "metadata": {
            "user_id": user_id,
            "text": f"Order {qty}x {item} from {rest['name']}.",
            "timestamp": random_timestamp(),
            "service": "order_food",
            "restaurant_id": rest["restaurant_id"],
            "cuisine": rest["cuisine"],
            "location": rest["location"],
            "items": [{"name": item, "quantity": qty}]
        }
    })

# Mart records
offset += len(restaurants)
for i, mart in enumerate(marts):
    item1, item2 = random.choice(["Milk","Eggs","Bread","Butter"]), random.choice(["Tomatoes","Onions","Potatoes"])
    qty1, qty2   = random.randint(1,5), random.randint(1,10)
    templates.append({
        "id": f"mart-{offset + i}",
        "values": [0]*DIMENSION,
        "metadata": {
            "user_id": user_id,
            "text": f"Please get {qty1}x {item1} and {qty2}x {item2} from {mart['name']}.",
            "timestamp": random_timestamp(),
            "service": "order_mart",
            "mart_id": mart["mart_id"],
            "location": mart["location"],
            "items": [{"name": item1, "quantity": qty1}, {"name": item2, "quantity": qty2}]
        }
    })

def safe_embed(query, retries=4, backoff=10):
    for attempt in range(1, retries + 1):
        try:
            return embedder.embed_query(query)
        except GoogleGenerativeAIError as e:
            if isinstance(e.__cause__, ResourceExhausted) and attempt < retries:
                wait = backoff ** attempt
                print(f"Quota hit—waiting {wait}s before retry #{attempt}")
                time.sleep(wait)
            else:
                raise

# ── Embed texts and replace placeholder vectors ──────────────────────────────
print("Embedding texts...")
embedder = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-exp-03-07",
    temperature=0.0,
    google_api_key=GOOGLE_API_KEY
)

upsert_batch = []
for rec in templates:
    rec["values"] = safe_embed(rec["metadata"]["text"])

    meta = rec["metadata"]

    # Serialize any nested list-of-dicts into JSON
    if "items" in meta:
        meta["items_json"] = json.dumps(meta.pop("items"))

    # (Optional) flatten names if you want them searchable
    if "name" in meta:
        if meta.get("service") == "order_food":
            meta["restaurant_name"] = meta["name"]
        elif meta.get("service") == "order_mart":
            meta["mart_name"] = meta["name"]

    # 3) Add (id, vector, metadata) tuple to your batch
    upsert_batch.append((rec["id"], rec["values"], meta))

# ── Upsert into Pinecone ─────────────────────────────────────────────────────
print("Upserting into Pinecone...")
index.upsert(vectors=[(rec["id"], rec["values"], rec["metadata"]) for rec in templates])
print("Done! Test /retrieve for richer Bengaluru context.")
