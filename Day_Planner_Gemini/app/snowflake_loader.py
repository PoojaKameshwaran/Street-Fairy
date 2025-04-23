# app/snowflake_loader.py

import os, sys
import json
import pandas as pd
import numpy as np
import faiss
import streamlit as st

# ── 1) Ensure project root is on sys.path so imports from scripts/ work ──────
THIS_DIR    = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── 2) Project imports now resolve correctly ───────────────────────────────
from scripts.utils.snowflake_utils import get_conn
from config import BUSINESS_EMB_TABLE_NEW as BUSINESS_EMB_TABLE

@st.cache_data(show_spinner=False)
def load_businesses_and_index():
    """
    Fetches BUSINESS_ID, NAME, CITY, STATE, LATITUDE, LONGITUDE, STARS, ATTRIBUTES, EMBEDDING
    from Snowflake, parses embeddings, builds and returns a FAISS index.
    """
    conn = get_conn()
    df = pd.read_sql(
        f"""
        SELECT
          BUSINESS_ID,
          NAME,
          CITY,
          STATE,
          LATITUDE,
          LONGITUDE,
          STARS,
          ATTRIBUTES,
          EMBEDDING
        FROM {BUSINESS_EMB_TABLE}
        """,
        conn
    )
    conn.close()

    # parse the JSON‑string embeddings into a NumPy array
    vectors    = df["EMBEDDING"].apply(json.loads).tolist()
    embeddings = np.array(vectors, dtype="float32")

    # build FAISS index
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return df, embeddings, index
