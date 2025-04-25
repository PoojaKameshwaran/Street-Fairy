import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
import faiss
import snowflake.connector
import os
import json
import re
import requests

embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

def get_snowflake_connection():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, ".."))
    key_path = os.path.join(root_dir, "key.json")
    with open(key_path, "r") as f:
        creds = json.load(f)
    conn = snowflake.connector.connect(
        user=creds["user"],
        password=creds["password"],
        account=creds["account"],
        warehouse=creds["warehouse"],
        database=creds["database"],
        schema=creds["schema"]
    )
    return conn

def load_data_from_snowflake():
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    query = """
    SELECT BUSINESS_ID, NAME, LATITUDE, LONGITUDE, STATE,
           CATEGORIES, FLATTENED_ATTRIBUTES,
           PARSE_JSON(embedding)::VECTOR(FLOAT, 384) AS EMBEDDING
    FROM BUSINESS_EMBEDDINGS
    """
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    conn.close()
    return df

def get_lat_lon(location_query):
    geolocator = Nominatim(user_agent="geopyApp")
    try:
        location = geolocator.geocode(location_query)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None


def run_similarity_search(query_input, df, top_k=10):
    if not query_input or df.empty:
        return pd.DataFrame()

    df = df.copy()

    # Normalize business embeddings
    df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: np.array(x, dtype=np.float32))
    df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: x / np.linalg.norm(x))

    # Encode user query
    embedding_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    query_embedding = embedding_model.encode([query_input], convert_to_numpy=True).astype("float32")
    query_embedding = query_embedding / np.linalg.norm(query_embedding)

    # Build FAISS index for inner product similarity (cosine proxy)
    index = faiss.IndexFlatIP(query_embedding.shape[1])
    all_embeddings = np.vstack(df["EMBEDDING"].values)
    index.add(all_embeddings)

    # Retrieve top_k most similar entries
    k = min(top_k, len(df))
    distances, indices = index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        if idx < len(df):
            row = df.iloc[idx]
            cosine_sim = cosine_similarity(query_embedding, row["EMBEDDING"].reshape(1, -1))[0][0]
            results.append({
                "BUSINESS_ID": row["BUSINESS_ID"],
                "NAME": row["NAME"],
                "CATEGORIES": row["CATEGORIES"],
                "FLATTENED_ATTRIBUTES": row["FLATTENED_ATTRIBUTES"],
                "STATE": row["STATE"],
                "CITY": row.get("CITY", ""),
                "LATITUDE": row["LATITUDE"],
                "LONGITUDE": row["LONGITUDE"],
                "SIMILARITY_SCORE": cosine_sim
            })

    return pd.DataFrame(results).sort_values(by="SIMILARITY_SCORE", ascending=False)



@st.cache_data(show_spinner=False)
def get_known_cities_and_categories():
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT LOWER(CITY) AS city
            FROM BUSINESS_EMBEDDINGS
            WHERE CITY IS NOT NULL
        """)
        cities = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT LOWER(CATEGORY)
            FROM (
                SELECT TRIM(value) AS CATEGORY
                FROM BUSINESS_EMBEDDINGS,
                     LATERAL FLATTEN(input => SPLIT(CATEGORIES, ',')) 
                WHERE CATEGORIES IS NOT NULL
            )
        """)
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return cities, categories
    except Exception as e:
        print(f"Failed to fetch dynamic city/category lists: {e}")
        return [], []

def extract_intent_from_message(user_message):
    user_message = user_message.lower()
    user_message = re.sub(r"[^\w\s]", "", user_message)
    found_city = None
    found_category = None
    known_cities, known_categories = get_known_cities_and_categories()
    for city in known_cities:
        if re.search(rf"\b{re.escape(city)}\b", user_message):
            found_city = city
            break
    for category in known_categories:
        if re.search(rf"\b{re.escape(category)}\b", user_message):
            found_category = category
            break
    return {
        "location": found_city,
        "category": found_category,
        "is_complete": bool(found_city and found_category)
    }

def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()['response']
