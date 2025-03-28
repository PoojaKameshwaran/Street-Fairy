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

# STEP 2: FETCH BUSINESS ID + CATEGORIES ONLY
def fetch_category_kb(session):
    category_df = session.table("FILTERED_CATEGORIES").select("BUSINESS_ID", "CATEGORIES")
    return category_df.collect()

# STEP 3: FORMAT EACH ROW
def format_for_chroma(row):
    row_dict = row.as_dict()
    business_id = row_dict["BUSINESS_ID"]
    categories = row_dict["CATEGORIES"]

    doc_text = f"""Business ID: {business_id}
Categories: {categories}
"""
    return business_id, doc_text, categories

# STEP 4: INGEST INTO CHROMA WITH BATCHING + PROGRESS
def ingest_to_chroma(formatted_docs, batch_size=1000):
    chroma_client = chromadb.PersistentClient(path=".chroma")
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection("street_fairy_kb", embedding_function=embedding_fn)

    total = len(formatted_docs)
    print(f"📦 Starting ingestion of {total} records into ChromaDB...")

    for i in tqdm(range(0, total, batch_size), desc="🔄 Ingesting"):
        batch = formatted_docs[i:i + batch_size]
        ids = [biz_id for biz_id, doc, cat in batch]
        docs = [doc for biz_id, doc, cat in batch]
        metas = [{"categories": cat} for biz_id, doc, cat in batch]

        collection.add(
            documents=docs,
            ids=ids,
            metadatas=metas
        )

    print(f"✅ Finished ingesting {total} records into ChromaDB!")

# ENTRY POINT
if __name__ == "__main__":
    session = get_snowpark_session()
    raw_rows = fetch_category_kb(session)
    formatted = [format_for_chroma(row) for row in raw_rows]

    # ✅ Remove duplicate business IDs
    seen_ids = set()
    deduped_formatted = []
    for biz_id, doc, cat in formatted:
        if biz_id not in seen_ids:
            seen_ids.add(biz_id)
            deduped_formatted.append((biz_id, doc, cat))

    ingest_to_chroma(deduped_formatted)