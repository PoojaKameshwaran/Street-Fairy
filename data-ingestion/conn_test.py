# This is a simple check to see if Python can connect to Snowflake

import snowflake.connector

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    "user": "FINCH",
    "password": "Bettyboop5022!",
    "account": "pdb57018",  
    "warehouse": "PROC_XS",
    "database": "STREET_FAIRY",
    "schema": "PUBLIC"
}

try:
    # Establish connection
    conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
    cur = conn.cursor()

    # Run a simple query to check connection
    cur.execute("SELECT CURRENT_VERSION()")
    version = cur.fetchone()

    print(f"✅ Successfully connected to Snowflake! Snowflake Version: {version[0]}")

    # Close connection
    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Connection failed: {e}")
