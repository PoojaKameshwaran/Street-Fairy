import snowflake.connector

# Snowflake connection parameters
SNOWFLAKE_ACCOUNT = "pdb57018"
SNOWFLAKE_USER = "<use_your_username>"
SNOWFLAKE_PASSWORD = "<use_your_password>"
SNOWFLAKE_WAREHOUSE = "PROC_XS"
SNOWFLAKE_DATABASE = "STREET_FAIRY"
SNOWFLAKE_SCHEMA = "PUBLIC"
SNOWFLAKE_STAGE = "MY_S3_STAGE"
SNOWFLAKE_TABLE = "REVIEWS_NEW1"
SNOWFLAKE_STAGE_TABLE = "REVIEWS_STAGE"  # Staging table for raw JSON
S3_BUCKET = "street-fairy"
S3_PREFIX = "raw/yelp_academic_dataset_review.json"  # Adjust based on folder structure

# Connect to Snowflake
conn = snowflake.connector.connect(
    user=SNOWFLAKE_USER,
    password=SNOWFLAKE_PASSWORD,
    account=SNOWFLAKE_ACCOUNT,
    warehouse=SNOWFLAKE_WAREHOUSE,
    database=SNOWFLAKE_DATABASE,
    schema=SNOWFLAKE_SCHEMA
)
cursor = conn.cursor()

# Step 1: Create a Staging Table for Raw JSON Data (VARIANT)
cursor.execute(f"""
    CREATE OR REPLACE TABLE {SNOWFLAKE_STAGE_TABLE} (
        raw_data VARIANT
    );
""")

# Step 2: Load Raw JSON into the Staging Table
cursor.execute(f"""
    COPY INTO {SNOWFLAKE_STAGE_TABLE}
    FROM @"{SNOWFLAKE_STAGE}"
    FILES = ('{S3_PREFIX}')
    FILE_FORMAT = (TYPE = 'JSON', STRIP_OUTER_ARRAY = TRUE)
    ON_ERROR = 'CONTINUE';  -- Skip bad records instead of failing the load
""")

# Step 3: Create the Final Structured Table
cursor.execute(f"""
    CREATE OR REPLACE TABLE {SNOWFLAKE_TABLE} (
        review_id STRING,
        user_id STRING,
        business_id STRING,
        stars FLOAT,
        useful INT,
        funny INT,
        cool INT,
        text STRING,
        date STRING
    );
""")

# Step 4: Transform and Insert Data from Staging Table to Final Table
cursor.execute(f"""
    INSERT INTO {SNOWFLAKE_TABLE}
    SELECT 
        raw_data:review_id::STRING,
        raw_data:user_id::STRING,
        raw_data:business_id::STRING,
        raw_data:stars::FLOAT,
        raw_data:useful::INT,
        raw_data:funny::INT,
        raw_data:cool::INT,
        raw_data:text::STRING,
        raw_data:date::STRING
    FROM {SNOWFLAKE_STAGE_TABLE};
""")

cursor.execute(f"""
        DROP TABLE {SNOWFLAKE_STAGE_TABLE};
""")

print("Optimized Data Load Complete!")

# Close connections
cursor.close()
conn.close()
