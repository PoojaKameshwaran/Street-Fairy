import sys, os, json
import pandas as pd
import snowflake.connector
from typing import Tuple
from snowflake.connector.pandas_tools import write_pandas

# ── Ensure project root is on path for config import ───────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import SF_CONFIG, BATCH_SIZE

def get_conn() -> snowflake.connector.SnowflakeConnection:
    """Return a Snowflake connection using SF_CONFIG."""
    return snowflake.connector.connect(**SF_CONFIG)

def drop_table_if_exists(table_name: str) -> None:
    """Drop the table if it already exists in Snowflake."""
    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table_name}")
    cur.close()
    conn.close()

def create_table_from_df(table_name: str, df: pd.DataFrame) -> None:
    """
    Create a new Snowflake table named table_name with
    every column as STRING. (EMBEDDING will hold JSON text.)
    """
    cols = []
    for col in df.columns:
        cols.append(f'"{col}" STRING')
    create = f"CREATE TABLE {table_name} ({', '.join(cols)})"

    conn = get_conn()
    cur  = conn.cursor()
    cur.execute(create)
    cur.close()
    conn.close()

def write_df_to_snowflake(df: pd.DataFrame, table_name: str) -> Tuple[bool,int,int]:
    """
    Bulk‐upload the DataFrame to an existing table using write_pandas.
    Returns (success, nchunks, nrows).
    """
    conn = get_conn()
    success, nchunks, nrows, _ = write_pandas(
        conn,
        df,
        table_name,
        auto_create_table=False
    )
    conn.close()
    return success, nchunks, nrows
