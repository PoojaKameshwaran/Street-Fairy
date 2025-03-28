from snowflake.snowpark import Session
import json

# Load credentials from key.json
with open("key.json") as f:
    creds = json.load(f)

# Try to connect
try:
    session = Session.builder.configs(creds).create()
    print("✅ Connection to Snowflake successful!")

    # List current database, schema, and role
    context = session.sql("SELECT CURRENT_DATABASE(), CURRENT_SCHEMA(), CURRENT_ROLE()").collect()
    print("📍 Context:", context)

    # Show available tables (limited to 10)
    tables = session.sql("SHOW TABLES").limit(10).collect()
    print("📋 Sample Tables:")
    for t in tables:
        print("   -", t["name"])

except Exception as e:
    print("❌ Connection failed:", e)
