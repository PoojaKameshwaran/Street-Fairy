from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import numpy as np
import snowflake.connector
import pickle
import faiss
import pandas as pd
import io


conn = snowflake.connector.connect(
    user='BOA',
    password='',
    account='',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
)
# **Step 1: Fetch the FAISS Index directly from Snowflake Stage into Memory (without local storage)**
cursor = conn.cursor()
#index = faiss.read_index("faiss_combined_businesses.index")


cursor.execute("SELECT * FROM BUSINESS_EMBEDDINGS")
data = cursor.fetchall()

# Convert to pandas DataFrame
columns = ['BUSINESS_ID', 'NAME', 'LATITUDE', 'LONGITUDE', 'STATE', 'CATEGORIES', 'FLATTENED_ATTRIBUTES', 'EMBEDDING']
df = pd.DataFrame(data, columns=columns)


# Convert EMBEDDING column from string to numpy array
#df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: np.fromstring(x, sep=','))
df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: x.strip('[]').replace(' ', '').split(',') if isinstance(x, str) else x)

df['EMBEDDING'] = df['EMBEDDING'].apply(lambda x: np.array(x, dtype=float) if isinstance(x, list) else x)

geolocator = Nominatim(user_agent="geopyApp")

# Function to get latitude and longitude of a location based on the city name
def get_lat_lon(location_query):
    try:
        location = geolocator.geocode(location_query)
        if location:
            return location.latitude, location.longitude
        else:
            print(f"Could not find location: {location_query}")
            return None, None
    except GeocoderTimedOut:
        print("Geocoding service timed out. Please try again.")
        return None, None

# Input: User provides one city name (e.g., "Tampa")
user_location_query = input("Enter the city or location you want to find: ")

# Get latitude and longitude of the user's input city
latitude, longitude = get_lat_lon(user_location_query)

df['DISTANCE'] = df.apply(lambda row: geodesic((latitude, longitude), (row['LATITUDE'], row['LONGITUDE'])).km, axis=1)


df = df[df['DISTANCE'] <= 5]

embedding_size = len( df['EMBEDDING'].iloc[0])  

filtered_index = faiss.IndexFlatL2(embedding_size)  # Create FAISS index
all_embeddings = np.vstack(df['EMBEDDING'].values)  # Convert all embeddings to a numpy array
filtered_index.add(all_embeddings)  # Add to FAISS index



# **Step 2: Search using the FAISS Index**
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
def calculate_similarity_score(query_text):
    query_embedding = embedding_model.encode([query_text], show_progress_bar=False)
    query_embedding = np.array(query_embedding).reshape(1, -1)
    k = min(25, len(df))  # Ensure k is valid
    distances, indices = filtered_index.search(query_embedding, k)  # Search within FAISS index

    retrieved_businesses_with_scores = []

    for idx in indices[0]:
        if idx >= len(df):  # Ensure valid index
            continue
        
        business_data = df.iloc[idx]
        business_embedding = np.array(business_data['EMBEDDING']).reshape(1, -1)

        # Calculate cosine similarity score
        cosine_sim = cosine_similarity(query_embedding, business_embedding)[0][0]
        
        retrieved_businesses_with_scores.append({
            'BUSINESS_ID': business_data['BUSINESS_ID'],
            'NAME': business_data['NAME'],
            'CATEGORIES': business_data.get('CATEGORIES', ''),
            'FLATTENED_ATTRIBUTES': business_data.get('FLATTENED_ATTRIBUTES', ''),
            'LATITUDE': business_data['LATITUDE'],
            'LONGITUDE': business_data['LONGITUDE'],
            'STATE': business_data['STATE'],
            'SIMILARITY_SCORE': cosine_sim,
            'DISTANCE': geodesic((latitude, longitude), 
                                 (business_data['LATITUDE'], business_data['LONGITUDE'])).km
        })

    return retrieved_businesses_with_scores

# **Run Similarity Search**
query_text = input("Query_Input")
retrieved_businesses_with_scores = calculate_similarity_score(query_text)

# Convert results to DataFrame
business_data_list = []
for business in retrieved_businesses_with_scores:
    if business['SIMILARITY_SCORE'] >= 0:  # Check for a threshold
        business_data_list.append({
            'BUSINESS_ID': business['BUSINESS_ID'],
            'NAME': business['NAME'],
            'CATEGORIES': business['CATEGORIES'],
            'FLATTENED_ATTRIBUTES': business['FLATTENED_ATTRIBUTES'],
            'STATE': business['STATE'],
            'LATITUDE': business['LATITUDE'],
            'LONGITUDE': business['LONGITUDE'],
            'SIMILARITY_SCORE': business['SIMILARITY_SCORE'],
            'DISTANCE': business['DISTANCE']
        })

# Convert the list of dictionaries into a DataFrame and save to CSV
business_df = pd.DataFrame(business_data_list)
if not business_df.empty:
    # Sort by similarity score (descending) and take top 5
    top_5_df = business_df.sort_values(by='SIMILARITY_SCORE', ascending=False).head(5)
    top_5_df.to_csv('LLM_Model.csv', index=False)
    print("Top 10 businesses saved to LLM_Model.csv")
else:
    print("No businesses found with a valid similarity score.")

# Close the database connection
conn.close()