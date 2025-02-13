import pandas as pd
import json
import snowflake.connector
from concurrent.futures import ThreadPoolExecutor

# Snowflake connection parameters
SNOWFLAKE_CONFIG = {
    "user": "FINCH",
    "password": "Bettyboop5022!",
    "account": "https://pdb57018.snowflakecomputing.com",
    "warehouse": "PROC_XS",
    "database": "STREET_FAIRY",
    "schema": "PUBLIC"
}

# Define batch upload function
def upload_json_to_snowflake(json_file_path, table_name, chunk_size=100000):
    """
    Reads a JSON Lines file and uploads it to Snowflake in batches.

    Parameters:
        json_file_path (str): Path to the JSON file.
        table_name (str): Snowflake table name.
        chunk_size (int): Number of rows to insert per batch.
    """
    try:
        # Establish Snowflake connection
        conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        cur = conn.cursor()

        # Read JSON and upload in batches
        batch = []
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line in f:
                batch.append(json.loads(line))  # Convert JSON to dictionary
                
                # Process batch
                if len(batch) >= chunk_size:
                    df = pd.DataFrame(batch)
                    data = [tuple(row) for row in df.itertuples(index=False)]
                    
                    # Create SQL INSERT query
                    columns = ', '.join(df.columns)
                    placeholders = ', '.join(['%s'] * len(df.columns))
                    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                    
                    # Execute batch insert
                    cur.executemany(insert_query, data)
                    conn.commit()
                    print(f"Inserted {len(data)} rows into {table_name} from {json_file_path}...")

                    # Clear batch
                    batch = []

        # Insert remaining records
        if batch:
            df = pd.DataFrame(batch)
            data = [tuple(row) for row in df.itertuples(index=False)]
            insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cur.executemany(insert_query, data)
            conn.commit()
            print(f"Inserted final {len(data)} rows into {table_name} from {json_file_path}...")

        # Close connection
        cur.close()
        conn.close()
        print(f"✅ Upload complete for {json_file_path}!")

    except Exception as e:
        print(f"❌ Error uploading {json_file_path}: {e}")

# List of JSON files to upload
json_files = [
    "C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp_academic_dataset_business.json",
    "C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp_academic_dataset_review.json",
    "C:\Users\pooja\Desktop\NEU\Spring '25\DAMG 7374\yelp_academic_dataset_user.json"
]

# Snowflake table names (each file uploads to a different table)
table_names = ["business_raw", "reviews_raw", "users_raw"]

# Execute uploads in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    executor.map(upload_json_to_snowflake, json_files, table_names)
    
print("✅ All files uploaded concurrently!")