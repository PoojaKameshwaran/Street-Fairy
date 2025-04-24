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



def load_data_from_snowflake():
    conn = snowflake.connector.connect(
    user='BOA',
    password='Kavinkumar3006$',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
    )
    cursor = conn.cursor()

    query = """
    SELECT BUSINESS_ID, NAME, LATITUDE, LONGITUDE, STATE,
        CATEGORIES, FLATTENED_ATTRIBUTES,
        PARSE_JSON(embedding)::VECTOR(FLOAT, 384) AS EMBEDDING
    FROM BUSINESS_EMBEDDINGS
    """

    cursor.execute(query)  # ✅ Run the query
    df = cursor.fetch_pandas_all()  # ✅ Get results as DataFrame

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
def run_similarity_search(user_location, query_input, df):
    # Get location coordinates (latitude and longitude) from user input
    latitude, longitude = get_lat_lon(user_location)
    if latitude is None:
        return pd.DataFrame()  # If location lookup fails, return empty DataFrame
    
    # Filter businesses based on distance from the user (5 km radius)
    df['DISTANCE'] = df.apply(lambda row: geodesic((latitude, longitude), (row['LATITUDE'], row['LONGITUDE'])).km, axis=1)
    df_filtered = df[df['DISTANCE'] <= 5].copy()  # Filter businesses within 5 km of user
    
    if df_filtered.empty:
        return pd.DataFrame()  # Return empty if no businesses are within the 5 km range
        ##add 

    # Get the user query directly from Streamlit input
    if not query_input:
        return pd.DataFrame()  # Return empty DataFrame if no query is provided
        ##add 

    # Use SentenceTransformer to encode user query (query_input) into a query embedding
    embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    query_embedding = embedding_model.encode([query_input])  # Encode the user text into an embedding
    #query_embedding = np.array(query_embedding).reshape(1, -1) 
    query_embedding = np.array(query_embedding, dtype=np.float32).reshape(1, -1)  # Ensure the shape is correct (1, embedding_dim)
   
    # Prepare FAISS index and business embeddings for similarity comparison
    embedding_size = len(df_filtered['EMBEDDING'].iloc[0])  # Length of each business embedding
    index = faiss.IndexFlatL2(embedding_size)  # Initialize FAISS index for L2 (Euclidean) similarity
    df_filtered['EMBEDDING'] = df_filtered['EMBEDDING'].apply(lambda x: np.array(x, dtype=float))
    # Stack the business embeddings into a single matrix
    all_embeddings = np.vstack(df_filtered['EMBEDDING'].values)
    index.add(all_embeddings)  # Add all business embeddings to the FAISS index

    # Perform the similarity search with the user query embedding
    k = min(20, len(df_filtered))  # Get top 20 nearest neighbors or fewer if less data
    distances, indices = index.search(query_embedding, k)  # Search for k closest matches

    results = []
    for idx in indices[0]:  # Loop through the indices of the top k results
        if idx < len(df_filtered):
            row = df_filtered.iloc[idx]  # Get the corresponding row from the filtered DataFrame
            cosine_sim = cosine_similarity(query_embedding, row['EMBEDDING'].reshape(1, -1))[0][0]  # Calculate cosine similarity
            #dist = euclidean(query_embedding.flatten(), row['EMBEDDING'].flatten())
            #if cosine_sim >= round(avg_sim, 4):  # Only consider matches with a positive similarity score
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

    # Return the results sorted by distance and similarity score
    return pd.DataFrame(results).sort_values(by=['SIMILARITY_SCORE'], ascending=[False]).head(2)
    #return pd.DataFrame(results)

