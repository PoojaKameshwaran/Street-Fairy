import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sklearn.metrics.pairwise import cosine_similarity
import faiss
import snowflake.connector

# --- Connect to Snowflake ---
@st.cache_resource
def load_data_from_snowflake():
    conn = snowflake.connector.connect(
    user='',
    password='',
    account='',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM BUSINESS_EMBEDDINGS")
    data = cursor.fetchall()

    columns = ['BUSINESS_ID', 'NAME', 'LATITUDE', 'LONGITUDE', 'STATE', 'CATEGORIES', 'FLATTENED_ATTRIBUTES', 'EMBEDDING']
    df = pd.DataFrame(data, columns=columns)

    df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: x.strip('[]').replace(' ', '').split(',') if isinstance(x, str) else x)
    df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: np.array(x, dtype=float) if isinstance(x, list) else x)

    conn.close()
    return df

# --- Get user location ---
def get_lat_lon(location_query):
    geolocator = Nominatim(user_agent="geopyApp")
    try:
        location = geolocator.geocode(location_query)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

# --- Similarity Search Logic ---
def run_similarity_search(user_text, user_location, df):
    latitude, longitude = get_lat_lon(user_location)
    if latitude is None:
        return pd.DataFrame()

    df['DISTANCE'] = df.apply(lambda row: geodesic((latitude, longitude), (row['LATITUDE'], row['LONGITUDE'])).km, axis=1)
    df_filtered = df[df['DISTANCE'] <= 5].copy()
    
    if df_filtered.empty:
        return pd.DataFrame()

    embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    query_embedding = embedding_model.encode([user_text])
    query_embedding = np.array(query_embedding).reshape(1, -1)

    embedding_size = len(df_filtered['EMBEDDING'].iloc[0])
    index = faiss.IndexFlatL2(embedding_size)
    all_embeddings = np.vstack(df_filtered['EMBEDDING'].values)
    index.add(all_embeddings)

    k = min(20, len(df_filtered))
    distances, indices = index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        if idx < len(df_filtered):
            row = df_filtered.iloc[idx]
            cosine_sim = cosine_similarity(query_embedding, row['EMBEDDING'].reshape(1, -1))[0][0]
            if cosine_sim >= 0:
                results.append({
                    'BUSINESS_ID': row['BUSINESS_ID'],
                    'NAME': row['NAME'],
                    'CATEGORIES': row['CATEGORIES'],
                    'FLATTENED_ATTRIBUTES': row['FLATTENED_ATTRIBUTES'],
                    'STATE': row['STATE'],
                    'LATITUDE': row['LATITUDE'],
                    'LONGITUDE': row['LONGITUDE'],
                    'SIMILARITY_SCORE': cosine_sim,
                    'DISTANCE': row['DISTANCE']
                })
    return pd.DataFrame(results).sort_values(by='DISTANCE').sort_values(by='SIMILARITY_SCORE').head(5)

# --- Streamlit UI ---
st.title("🔍 Restaurant Finder using LLM & FAISS")

location_input = st.text_input("Enter your location (e.g., Tampa):")
query_input = st.text_input("What kind of restaurant are you looking for?")

if st.button("Find Recommendations"):
    with st.spinner("Loading recommendations..."):
        df = load_data_from_snowflake()
        results = run_similarity_search(query_input, location_input, df)
        if not results.empty:
            st.success(f"Found {len(results)} results!")
            st.dataframe(results)
            st.download_button("Download CSV", data=results.to_csv(index=False), file_name="LLM_Model.csv")
        else:
            st.warning("No businesses found within 5 km of your location.")
