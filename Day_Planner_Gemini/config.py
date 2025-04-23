# config.py

import os

# ── Snowflake connection for your scripts ────────────────────────────────────────
SF_CONFIG = {
    "user":      os.getenv("SNOWFLAKE_USER"),
    "password":  os.getenv("SNOWFLAKE_PASSWORD"),
    "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
    "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
    "database":  os.getenv("SNOWFLAKE_DATABASE"),
    "schema":    os.getenv("SNOWFLAKE_SCHEMA"),
}

# ── Table names ─────────────────────────────────────────────────────────────────
SOURCE_TABLE        = "ENGINEERED_BUSINESSES"

BUSINESS_EMB_TABLE_NEW   = "BUSINESS_EMBEDDINGS_NEW"
#BUSINESS_EMB_TABLE_NEW   = "engineered_businesses_embeddings"
REVIEWS_TABLE           = "RELEVANT_REVIEWS"

# ── Embedding settings ─────────────────────────────────────────────────────────
USE_OPENAI_EMB      = False
HF_EMB_MODEL        = "all-mpnet-base-v2"
#HF_EMB_MODEL = "all-MiniLM-L6-v2"  
OPENAI_EMB_MODEL    = "text-embedding-ada-002"

# ── Other constants ─────────────────────────────────────────────────────────────
BATCH_SIZE          = 50
SEARCH_RADIUS_MILES = 30

# Gemini / Google‑GenerativeAI model
LLM_MODEL = "gemini-1.5-flash"
