# This file loads all 3 .json files to snowflake as raw files where each record contains just one VARIANT column
# the VARIANT field will be processed using dbt pipelines 

import boto3
import snowflake.connector
import os
from snowflake.connector import DictCursor

# Snowflake connection parameters
SNOWFLAKE_ACCOUNT = "pdb57018"
SNOWFLAKE_USER = "<use_your_username>"
SNOWFLAKE_PASSWORD = "<use_your_password>"
SNOWFLAKE_WAREHOUSE = "PROC_XS"
SNOWFLAKE_DATABASE = "STREET_FAIRY"
SNOWFLAKE_SCHEMA = "PUBLIC"
SNOWFLAKE_STAGE = "MY_S3_STAGE"

SNOWFLAKE_TABLES = ["BUSINESS_RAW1", "REVIEWS_RAW1", "USERS_RAW1"]
S3_PREFIXES = ["raw/yelp_academic_dataset_business.json", 
               "raw/yelp_academic_dataset_review.json",
                "raw/yelp_academic_dataset_user.json" ]

S3_BUCKET = "street-fairy"

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

for i in range(len(SNOWFLAKE_TABLES)):
    # Create table (assuming semi-structured JSON data)
    cursor.execute(f"""
        CREATE OR REPLACE TABLE {SNOWFLAKE_TABLES[i]} (
            raw_data VARIANT
        );
    """)

    # Copy JSON data from S3 to Snowflake
    cursor.execute(f"""
        COPY INTO {SNOWFLAKE_TABLES[i]}
        FROM @"{SNOWFLAKE_STAGE}"
        FILES = ('{S3_PREFIXES[i]}')
        FILE_FORMAT = (TYPE = 'JSON');
    """)

    print(f"{SNOWFLAKE_TABLES[i]} CREATED SUCCESSFULLY!")

print("Data load complete!")

# Close connections
cursor.close()
conn.close()
