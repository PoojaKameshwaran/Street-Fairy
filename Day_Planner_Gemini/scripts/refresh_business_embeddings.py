import os
import sys
import json
import pandas as pd
from sentence_transformers import SentenceTransformer

# ── Ensure project root is on path ─────────────────────────────────────────────
CURRENT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Project imports ─────────────────────────────────────────────────────────────
from scripts.utils.flatten_utils   import flatten_attributes, hours_to_text
from scripts.utils.snowflake_utils import (
    get_conn,
    drop_table_if_exists,
    create_table_from_df,
    write_df_to_snowflake,
)
from config import SOURCE_TABLE, HF_EMB_MODEL, BUSINESS_EMB_TABLE_NEW

def build_description(row) -> str:
    parts = [
        str(row.get("NAME", "")),
        str(row.get("CATEGORIES", "")),
        flatten_attributes(row.get("ATTRIBUTES", {})),
        hours_to_text(row.get("HOURS", {})),
        str(row.get("STATE", "")),
    ]
    return " | ".join(p for p in parts if p)

def main():
    conn = get_conn()

    # 1. Load raw businesses
    df = pd.read_sql(f"SELECT * FROM {SOURCE_TABLE}", conn)
    conn.close()
    print(f"✅ Loaded {len(df)} rows from {SOURCE_TABLE}")

    # 2. Build text for embedding
    df["description"] = df.apply(build_description, axis=1)

    # 3. Generate embeddings
    print("🔄 Generating embeddings...")
    model      = SentenceTransformer(HF_EMB_MODEL)
    embeds     = model.encode(df["description"].tolist(), show_progress_bar=True)
    df["EMBEDDING"] = [json.dumps(vec.tolist()) for vec in embeds]

    # 4. Drop & (re)create table
    print(f"🧹 Dropping table if exists: {BUSINESS_EMB_TABLE_NEW}")
    drop_table_if_exists(BUSINESS_EMB_TABLE_NEW)
    print(f"➕ Creating table: {BUSINESS_EMB_TABLE_NEW}")
    create_table_from_df(BUSINESS_EMB_TABLE_NEW, df)

    # 5. Bulk‐load via write_pandas
    print(f"⬆️ Uploading to {BUSINESS_EMB_TABLE_NEW} via write_pandas…")
    success, nchunks, nrows = write_df_to_snowflake(df, BUSINESS_EMB_TABLE_NEW)
    if success:
        print(f"✅ Uploaded {nrows} rows in {nchunks} chunks.")
    else:
        print("❌ Upload failed!")

if __name__ == "__main__":
    main()
