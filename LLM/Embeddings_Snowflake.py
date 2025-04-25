import snowflake.connector
import pandas as pd
import numpy as np
import json
import faiss
import pickle
from sentence_transformers import SentenceTransformer ##    LLM model
from langchain.schema import Document
import base64
import binascii
from dotenv import load_dotenv
import os
load_dotenv()

snowflake_user = os.getenv('SNOWFLAKE_USER')
snowflake_password = os.getenv('SNOWFLAKE_PASSWORD')
snowflake_account = os.getenv('SNOWFLAKE_ACCOUNT')
snowflake_warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
snowflake_database = os.getenv('SNOWFLAKE_DATABASE')
snowflake_schema = os.getenv('SNOWFLAKE_SCHEMA')


# Snowflake connection setup
conn = snowflake.connector.connect(
    user=snowflake_user,
    password=snowflake_password,
    account=snowflake_account,
    warehouse=snowflake_warehouse,
    database=snowflake_database,
    schema=snowflake_schema
)

# Snowflake connection setup (assuming `conn` is already established)
cursor = conn.cursor()


truncate_query_2 = "TRUNCATE TABLE BUSINESS_EMBEDDINGS;"


cursor.execute(truncate_query_2)
cursor.close()

cursor = conn.cursor()

# Query to get the business data from Snowflake
query = r"""
SELECT business_id,name,latitude,longitude,categories,attributes,state ,POSTAL_CODE,stars, hours
FROM ENGINEERED_BUSINESSES
"""

# Fetching data into a DataFrame
df = pd.read_sql(query, conn)

#def flatten_attributes(attr_json):
#    if isinstance(attr_json, dict):
#        return ", ".join([f"{key},{value}" for key, value in attr_json.items()])
#    return ""

# Apply flattening of attributes
#df["FLATTENED_ATTRIBUTES"] = df["ATTRIBUTES"].apply(lambda x: flatten_attributes(json.loads(x)))
#df['combined_info'] = df['CATEGORIES'] + " " + df['FLATTENED_ATTRIBUTES']

def attributes_to_text(attr_json):
    if not isinstance(attr_json, dict):
        return ""
    
    descriptions = []
    for key, value in attr_json.items():
        if value.lower() in ['true', 'yes']:
            if "Ambience_" in key:
                descriptions.append(f"Ambience is {key.split('_')[-1]}")
            elif "BusinessParking" in key:
                descriptions.append(f"Has {key.split('_')[-1]} parking")
            else:
                descriptions.append(f"{key.replace('_', ' ')} available")
        elif value.lower() not in ['false', 'no', 'null']:
            descriptions.append(f"{key.replace('_', ' ')} is {value}")
    
    return ". ".join(descriptions)

def hours_to_text(hours_json):
    if not isinstance(hours_json, dict):
        return ""
    
    return ". ".join([
        f"Open on {day} from {time.replace(':0', ':00')}"
        for day, time in hours_json.items() if time != "0:0-0:0"
    ])



df["FLATTENED_ATTRIBUTES"] = df["ATTRIBUTES"].apply(lambda x: attributes_to_text(json.loads(x)) if pd.notnull(x) else "")
df["HOURS"] = df["HOURS"].apply(lambda x: hours_to_text(json.loads(x)) if pd.notnull(x) else "")
#df = df[~df["FLATTENED_ATTRIBUTES"].str.contains("RestaurantsPriceRange", na=False)]
df["FLATTENED_ATTRIBUTES"] = df["FLATTENED_ATTRIBUTES"].str.replace("RestaurantsPriceRange", "Price Range", regex=False)


df["combined_info"] = (
    "Categories: " + df["CATEGORIES"].fillna("") + ". " +
    df["FLATTENED_ATTRIBUTES"].fillna("") + ". " +
    df["HOURS"].fillna("") + ". " +
    "Rated " + df["STARS"].astype(str) + " stars."
)



df = df.drop_duplicates()
df = df.reset_index(drop=True)

# Load the SentenceTransformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2') 


# Encode categories and attributes separately
category_embeddings = model.encode(df['combined_info'].tolist(), show_progress_bar=True)

category_embeddings = np.array(category_embeddings, dtype=np.float32)

# Create FAISS index for combined embeddings
combined_index = faiss.IndexFlatL2(category_embeddings.shape[1]) 
combined_index.add(category_embeddings)

#faiss.write_index(combined_index, "faiss_combined_businesses.index")



#cursor.execute("PUT file://faiss_combined_businesses.index @faiss_index_stage auto_compress=false")

def escape_string(s):
    if isinstance(s, str):
        return s.replace("'", "''").replace("\n", " ").replace("\r", " ")
    return s


for idx, row in df.iterrows():

    business_id = (row['BUSINESS_ID'])
    name = escape_string(row['NAME'])
    latitude = row['LATITUDE']
    longitude = row['LONGITUDE']
    state = (row['STATE'])
    categories = escape_string(row['CATEGORIES'])
    flattened_attributes = escape_string(row['combined_info'])
    embedding_str = json.dumps(category_embeddings[idx].tolist())  # Ensure that embedding is properly serialized
    
    # Construct SQL statement and print for debugging
    insert_query = """
    INSERT INTO BUSINESS_EMBEDDINGS (
        BUSINESS_ID, 
        NAME, 
        LATITUDE, 
        LONGITUDE, 
        STATE, 
        CATEGORIES, 
        FLATTENED_ATTRIBUTES, 
        EMBEDDING
    ) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

data_to_insert = []

for idx, row in df.iterrows():
    business_id = row['BUSINESS_ID']
    name = escape_string(row['NAME'])
    latitude = row['LATITUDE']
    longitude = row['LONGITUDE']
    state = row['STATE']
    categories = escape_string(row['CATEGORIES'])
    flattened_attributes = escape_string(row['combined_info'])
    embedding_str = json.dumps(category_embeddings[idx].tolist())

    data_to_insert.append((
        business_id,
        name,
        latitude,
        longitude,
        state,
        categories,
        flattened_attributes,
        embedding_str
    ))

# Now batch insert
cursor.executemany(insert_query, data_to_insert)
conn.commit()
cursor.close()