from geopy.distance import geodesic
import snowflake.connector
import pandas as pd
import numpy as np
import json
import faiss
import pickle
import geocoder #to get current lat lon
import gps #to get current lat lon
from sentence_transformers import SentenceTransformer ##    LLM model
from sklearn.feature_extraction.text import CountVectorizer
from langchain.schema import Document

# Snowflake connection setup
conn = snowflake.connector.connect(
    user='BOA',
    password='',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
)


#g = geocoder.ip('me') 
#user_latitude = g.latlng[0]
#user_longitude = g.latlng[1]

#session = gps.gps(mode=gps.WATCH_ENABLE)
#report = session.next()
    
#if report['class'] == 'TPV':
    #user_latitude = report.lat
    #user_longitude = report.lon
#else:
#    ''

#print(user_latitude)
#print(user_longitude)


# SQL query to fetch the necessary business data
#query = r"""
#SELECT business_id,name,latitude,longitude,categories,attributes
##FROM ENGINEERED_BUSINESSES
#"""
query = r"""
select B.BUSINESS_ID,B.NAME,B.LATITUDE,B.LONGITUDE,B.CATEGORIES,FA.ATTRIBUTES,B.STATE
from PUBLIC.Filtered_Attributes FA 
inner join PUBLIC.BUSINESS_MODEL B
    ON FA.BUSINESS_ID=B.BUSINESS_ID
"""

df = pd.read_sql(query, conn)


def flatten_attributes(attr_json):
    if isinstance(attr_json, dict):
        return ", ".join([f"{key},{value}" for key, value in attr_json.items()])
    return ""


df["FLATTENED_ATTRIBUTES"] = df["ATTRIBUTES"].apply(lambda x: flatten_attributes(json.loads(x)))

df['combined_info'] = df['CATEGORIES'] + " " + df['FLATTENED_ATTRIBUTES']
#+" "+df['LATITUDE'].astype(str)+" "+df["LONGITUDE"].astype(str)

df.drop_duplicates()

#model = SentenceTransformer('all-MiniLM-L6-v2')
#model = SentenceTransformer('all-mpnet-base-v2')
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Encode categories and attributes separately
category_embeddings = model.encode(df['combined_info'] .tolist(), show_progress_bar=True)

category_embeddings = np.array(category_embeddings, dtype=np.float32)

# Create FAISS index for combined embeddings
combined_index = faiss.IndexFlatL2(category_embeddings.shape[1])  # L2 distance for cosine similarity
combined_index.add(category_embeddings)
# Save FAISS index
faiss.write_index(combined_index, "faiss_combined_businesses.index")

# Store metadata for mapping back to businesses
business_metadata_with_embeddings = []

# Create LangChain Documents and store metadata and embeddings
for idx, row in df.iterrows():
    # Create a business metadata dictionary
    business_data = {
        'BUSINESS_ID': row['BUSINESS_ID'],
        'NAME': row['NAME'],
        'LATITUDE': row['LATITUDE'],
        'LONGITUDE': row['LONGITUDE'],
        'STATE':row['STATE'],
        'CATEGORIES': row['CATEGORIES'],
        'FLATTENED_ATTRIBUTES': row['FLATTENED_ATTRIBUTES'],
        'EMBEDDING': category_embeddings[idx].tolist()  # Assuming 'category_embeddings' are pre-computed
    }

    # Create LangChain Document using metadata and embeddings
    document = Document(
        page_content=row['NAME'] + " " + (row['CATEGORIES'] if row['CATEGORIES'] else ""),
        metadata={
            "BUSINESS_ID": row['BUSINESS_ID'],
            "NAME": row['NAME'],
            'LATITUDE': row['LATITUDE'],
            'LONGITUDE': row['LONGITUDE'],
            'STATE':row['STATE'],
            "CATEGORIES": row['CATEGORIES'],
            'FLATTENED_ATTRIBUTES': row['FLATTENED_ATTRIBUTES'],
            "EMBEDDING": category_embeddings[idx].tolist()  # Precomputed embedding
        }
    )
    
    business_metadata_with_embeddings.append(document)

# Save the documents into a pickle file
with open("business_metadata_with_documents.pkl", "wb") as f:
    pickle.dump(business_metadata_with_embeddings, f)
