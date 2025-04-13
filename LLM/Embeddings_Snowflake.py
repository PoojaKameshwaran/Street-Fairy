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

# Snowflake connection setup
conn = snowflake.connector.connect(
    user='BOA',
    password='Kavinkumar3006$',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
)

# Snowflake connection setup (assuming `conn` is already established)
cursor = conn.cursor()


truncate_query_2 = "TRUNCATE TABLE BUSINESS_EMBEDDINGS;"


cursor.execute(truncate_query_2)
cursor.close()

cursor = conn.cursor()

# Query to get the business data from Snowflake
query = r"""
SELECT business_id,name,latitude,longitude,categories,attributes,state
FROM ENGINEERED_BUSINESSES
"""

# Fetching data into a DataFrame
df = pd.read_sql(query, conn)

def flatten_attributes(attr_json):
    if isinstance(attr_json, dict):
        return ", ".join([f"{key},{value}" for key, value in attr_json.items()])
    return ""

# Apply flattening of attributes
df["FLATTENED_ATTRIBUTES"] = df["ATTRIBUTES"].apply(lambda x: flatten_attributes(json.loads(x)))
df['combined_info'] = df['CATEGORIES'] + " " + df['FLATTENED_ATTRIBUTES']

# Drop duplicates from the DataFrame
df = df.drop_duplicates()

# Load the SentenceTransformer model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2') 


# Encode categories and attributes separately
category_embeddings = model.encode(df['combined_info'].tolist(), show_progress_bar=True)

category_embeddings = np.array(category_embeddings, dtype=np.float32)

# Create FAISS index for combined embeddings
combined_index = faiss.IndexFlatL2(category_embeddings.shape[1]) 
combined_index.add(category_embeddings)

faiss.write_index(combined_index, "faiss_combined_businesses.index")



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
    flattened_attributes = escape_string(row['FLATTENED_ATTRIBUTES'])
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
    flattened_attributes = escape_string(row['FLATTENED_ATTRIBUTES'])
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