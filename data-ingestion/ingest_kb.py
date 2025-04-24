import os
import json
import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from tqdm import tqdm

# STEP 1: CONNECT TO SNOWFLAKE
def get_snowpark_session():
    with open("key.json", "r") as f:
        creds = json.load(f)
    return snowpark.Session.builder.configs(creds).create()

# STEP 2: JOIN FILTERED_CATEGORIES + FILTERED_ATTRIBUTES
def fetch_merged_kb(session):
    category_df = session.table("FILTERED_CATEGORIES").select("BUSINESS_ID", "CATEGORIES")
    attr_df = session.table("EXTRACTED_ATTRIBUTES").select("BUSINESS_ID", "ATTRIBUTES")
    merged = category_df.join(attr_df, on="BUSINESS_ID")
    return merged.collect()

# STEP 3: FORMAT FOR CHROMA (incl. attributes as JSON string)
def format_for_chroma(row):
    row_dict = row.as_dict()
    business_id = row_dict["BUSINESS_ID"]
    categories = row_dict["CATEGORIES"]
    raw_attributes = row_dict.get("ATTRIBUTES", "{}")

    try:
        attr_dict_raw = json.loads(raw_attributes)
    except Exception:
        attr_dict_raw = {}

    # Clean all values
    attributes_dict = {
        k: try_cast_value(v)
        for k, v in attr_dict_raw.items()
        if v is not None
    }

    # Create a flat semantic string version
    attr_text = ", ".join(f"{k}={v}" for k, v in attributes_dict.items())

    doc_text = f"""Business ID: {business_id}
Categories: {categories}
Attributes: {attr_text}
"""

    return business_id, doc_text, categories, attr_text, attributes_dict

# Helper: convert values to bool/int/float/str
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

# STEP 4: INGEST TO CHROMA
def ingest_to_chroma(formatted_docs, batch_size=1000):
    chroma_client = chromadb.PersistentClient(path=".chroma")
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection("street_fairy_kb", embedding_function=embedding_fn)

    total = len(formatted_docs)
    print(f"📦 Starting ingestion of {total} records into ChromaDB...")

    for i in tqdm(range(0, total, batch_size), desc="🔄 Ingesting"):
        batch = formatted_docs[i:i + batch_size]
        ids = [biz_id for biz_id, doc, cat, attr_text, attr_dict in batch]
        docs = [doc for biz_id, doc, cat, attr_text, attr_dict in batch]
        metas = []
        for biz_id, doc, cat, attr_text, attr_dict in batch:
            meta = {
                "categories": cat,
                "attribute_text": attr_text,
            }
            meta.update(attr_dict)  # ✅ Flatten all keys from attr_dict into metadata
            metas.append(meta)


        collection.add(
            documents=docs,
            ids=ids,
            metadatas=metas
        )

    print(f"✅ Finished ingesting {total} records into ChromaDB!")

# ENTRY POINT
if __name__ == "__main__":
    session = get_snowpark_session()
    raw_rows = fetch_merged_kb(session)
    formatted = [format_for_chroma(row) for row in raw_rows]

    # ✅ Deduplicate BUSINESS_IDs
    seen_ids = set()
    deduped_formatted = []
    for biz_id, doc, cat, attr_text, attr_dict in formatted:
        if biz_id not in seen_ids:
            seen_ids.add(biz_id)
            deduped_formatted.append((biz_id, doc, cat, attr_text, attr_dict))

    ingest_to_chroma(deduped_formatted)