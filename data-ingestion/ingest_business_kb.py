import os
import json
import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from tqdm import tqdm

# ------------------------
# STEP 1: Connect to Snowflake
# ------------------------
def get_snowpark_session():
    with open("key.json", "r") as f:
        creds = json.load(f)
    return snowpark.Session.builder.configs(creds).create()

# ------------------------
# STEP 2: Pull enriched businesses table
# ------------------------
def fetch_business_data(session):
    return session.table("ENGINEERED_BUSINESSES").collect()

# ------------------------
# STEP 3: Format business row
# ------------------------
def format_for_chroma(row):
    row_dict = row.as_dict()
    biz_id = row_dict["BUSINESS_ID"]

    # Graceful fallback for all fields
    name = row_dict.get("NAME") or "Unknown Business"
    address = row_dict.get("ADDRESS") or ""
    city = row_dict.get("CITY") or ""
    state = row_dict.get("STATE") or ""
    postal_code = row_dict.get("POSTAL_CODE") or ""
    categories = row_dict.get("CATEGORIES") or ""
    stars = try_cast_value(row_dict.get("STARS", 0))
    reviews = try_cast_value(row_dict.get("REVIEW_COUNT", 0))
    lat = try_cast_value(row_dict.get("LATITUDE"))
    lon = try_cast_value(row_dict.get("LONGITUDE"))
    raw_attrs = row_dict.get("ATTRIBUTES") or "{}"
    raw_hours = row_dict.get("HOURS")
    if raw_hours in [None, "None", "", {}]:
        hours = {}
    else:
        try:
            hours = json.loads(raw_hours)
            if not isinstance(hours, dict):
                hours = {}
        except Exception:
            hours = {}
    
    try:
        attr_dict = {
            k: try_cast_value(v)
            for k, v in json.loads(raw_attrs).items()
            if v is not None
        }
    except Exception:
        attr_dict = {}

    # Flatten for doc
    attr_text = ", ".join(f"{k}={v}" for k, v in attr_dict.items())
    hours_text = ", ".join(f"{k}: {v}" for k, v in hours.items())

    doc = f"""Business Name: {name}
Address: {address}, {city}, {state} {postal_code}
Categories: {categories}
Rating: {stars} stars ({reviews} reviews)
Attributes: {attr_text}
Hours: {hours_text}
"""

    # Metadata: exclude any fields that are None
    metadata = {
        "name": name,
        "city": city,
        "state": state,
        "stars": stars,
        "review_count": reviews,
        "latitude": lat,
        "longitude": lon,
        "categories": categories
    }

    # Merge flat attributes into metadata (only primitives allowed)
    for k, v in attr_dict.items():
        if isinstance(v, (str, int, float, bool)):
            metadata[k] = v

    return biz_id, doc, metadata

# ------------------------
# Helper: Cast values
# ------------------------
def try_cast_value(value):
    if isinstance(value, str):
        v = value.strip('"').strip("'")
        if v.lower() == "true":
            return True
        elif v.lower() == "false":
            return False
        elif v.isdigit():
            return int(v)
        try:
            return float(v)
        except:
            return v
    return value

# ------------------------
# STEP 4: Ingest to ChromaDB
# ------------------------
def ingest_to_chroma(formatted_docs, batch_size=1000):
    chroma_client = chromadb.PersistentClient(path=".chroma")
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection("street_fairy_business_kb", embedding_function=embedding_fn)

    total = len(formatted_docs)
    print(f"📦 Starting ingestion of {total} business records into ChromaDB...")

    for i in tqdm(range(0, total, batch_size), desc="🔄 Ingesting"):
        batch = formatted_docs[i:i + batch_size]
        ids = [biz_id for biz_id, doc, meta in batch]
        docs = [doc for biz_id, doc, meta in batch]
        metas = [meta for biz_id, doc, meta in batch]

        collection.add(
            documents=docs,
            ids=ids,
            metadatas=metas
        )

    print(f"✅ Finished ingesting {total} businesses into ChromaDB!")

# ------------------------
# ENTRY POINT
# ------------------------
if __name__ == "__main__":
    session = get_snowpark_session()
    raw_rows = fetch_business_data(session)
    formatted = [format_for_chroma(row) for row in raw_rows]

    # Deduplicate business IDs
    seen = set()
    deduped = []
    for biz_id, doc, meta in formatted:
        if biz_id not in seen:
            seen.add(biz_id)
            deduped.append((biz_id, doc, meta))

    ingest_to_chroma(deduped)