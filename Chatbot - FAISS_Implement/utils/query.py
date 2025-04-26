import numpy as np
import streamlit as st
import pandas as pd
import faiss
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import requests
import torch
from geopy.distance import geodesic


def get_lat_lon(location_query):
    """Get latitude and longitude from a location query using geopy."""
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="geopyApp")
    try:
        location = geolocator.geocode(location_query)
        if location:
            return location.latitude, location.longitude
    except:
        return None, None
    return None, None

@st.cache_data ###Added
def run_similarity_search(user_location, query_input, df, top_k=5):
    latitude, longitude = get_lat_lon(user_location)
    if latitude is None:
        return pd.DataFrame()

    # Calculate distances to each business
    df['DISTANCE'] = df.apply(lambda row: geodesic((latitude, longitude), (row['LATITUDE'], row['LONGITUDE'])).km, axis=1)
    
    # Filter businesses within 2 km of the user location
    df_filtered = df[df['DISTANCE'] <= 5].copy()
    
    # Ensure EMBEDDING is in the correct format
    df_filtered["EMBEDDING"] = df_filtered["EMBEDDING"].apply(lambda x: np.array(x, dtype=np.float32))
    df_filtered["EMBEDDING"] = df_filtered["EMBEDDING"].apply(lambda x: x / np.linalg.norm(x))

    # Encode the query input into an embedding
    #device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the model and move it to the device
    model = SentenceTransformer("paraphrase-MiniLM-L6-v2") # This moves the model to the device

    query_emb = model.encode([query_input], convert_to_numpy=True).astype("float32")
    
    # Set up the FAISS index
    index = faiss.IndexFlatL2(query_emb.shape[1])  # L2 distance for cosine similarity
    index.add(np.vstack(df_filtered["EMBEDDING"].values))  # Use filtered embeddings for the index

    k = min(top_k, len(df_filtered))
    
    # Perform the search
    distances, indices = index.search(query_emb, k)

    if len(indices[0]) == 0:
        return pd.DataFrame()

    results = []

    # Loop through the indices of the top-k results from the filtered data
    for idx in indices[0]:
        if idx < len(df_filtered):
            row = df_filtered.iloc[idx]  # Get the corresponding row from the filtered DataFrame
            cosine_sim = cosine_similarity(query_emb.reshape(1, -1), row['EMBEDDING'].reshape(1, -1))[0][0]  # Calculate cosine similarity
            
            # Append the result with the expected fields
            results.append({
                'BUSINESS_ID': row['BUSINESS_ID'],
                'NAME': row['NAME'],
                'CATEGORIES': row['CATEGORIES'],
                'FLATTENED_ATTRIBUTES': row['FLATTENED_ATTRIBUTES'],
                'STATE': row['STATE'],
                'CITY' : row['CITY'],
                'LATITUDE': row['LATITUDE'],
                'LONGITUDE': row['LONGITUDE'],
                'SIMILARITY_SCORE': cosine_sim,
                'DISTANCE': row['DISTANCE']
            })

    # Return the results sorted by similarity score and then by distance (if needed)
    result_df = pd.DataFrame(results).sort_values(by=['SIMILARITY_SCORE', 'DISTANCE'], ascending=[False, True]).head(2)

    # Return the results DataFrame
    return result_df


def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()['response']