from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from geopy.distance import geodesic
import numpy as np
import pickle
import faiss
import pandas as pd

# Load the FAISS index and business metadata with embeddings from the pickle file
index = faiss.read_index("faiss_combined_businesses.index")


with open("business_metadata_with_documents.pkl", "rb") as f:
    documents = pickle.load(f)


# User's location
user_latitude = 28.2172884
user_longitude = -82.7333444

# **Step 1: Filter Businesses Within 5km**
filtered_documents = []
filtered_indices = []

for idx, doc in enumerate(documents):
    metadata = doc.metadata
    lat = metadata.get('LATITUDE')
    lon = metadata.get('LONGITUDE')

    if lat is not None and lon is not None:
        distance = geodesic((user_latitude, user_longitude), (lat, lon)).km
        if distance <= 5:
            filtered_documents.append(doc)
            filtered_indices.append(idx)  # Keep track of FAISS index positions

# If no businesses are within 5 km, exit
if not filtered_documents:
    print("No businesses found within 5 km.")
    exit()

embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


# **Step 2: Create a New FAISS Index for Filtered Businesses**
embedding_size = embedding_model.get_sentence_embedding_dimension()
filtered_index = faiss.IndexFlatL2(embedding_size)  # Create FAISS index

# Store embeddings for filtered businesses
filtered_embeddings = []

for doc in filtered_documents:
    embedding = np.array(doc.metadata['EMBEDDING']).reshape(1, -1)  # Ensure correct shape
    filtered_index.add(embedding)  # Add to FAISS index
    filtered_embeddings.append(embedding)

# Convert to NumPy array
filtered_embeddings = np.vstack(filtered_embeddings)

# **Step 3: Search using New FAISS Index**
def calculate_similarity_score(query_text):
    query_embedding = embedding_model.encode([query_text], show_progress_bar=False)
    query_embedding = np.array(query_embedding).reshape(1, -1)
    #k=100
    k = min(100, len(filtered_documents))  # Ensure k is valid
    distances, indices = filtered_index.search(query_embedding, k)  # Search within filtered index

    retrieved_businesses_with_scores = []
    
    for idx in indices[0]:
        if idx >= len(filtered_documents):  # Ensure valid index
            continue
        
        business_data = filtered_documents[idx].metadata
        business_embedding = np.array(business_data['EMBEDDING']).reshape(1, -1)

        # Calculate cosine similarity score
        cosine_sim = cosine_similarity(query_embedding, business_embedding)[0][0]
        
        retrieved_businesses_with_scores.append({
            'BUSINESS_ID': business_data['BUSINESS_ID'],
            'NAME': business_data['NAME'],
            'CATEGORIES': business_data.get('CATEGORIES', ''),
            'FLATTENED_ATTRIBUTES': business_data.get('FLATTENED_ATTRIBUTES', ''),
            'LATITUDE': business_data.get('LATITUDE', None),
            'LONGITUDE': business_data.get('LONGITUDE', None),
            'STATE': business_data.get('STATE', None),
            'SIMILARITY_SCORE': cosine_sim,
            'DISTANCE': geodesic((user_latitude, user_longitude), 
                                 (business_data['LATITUDE'], business_data['LONGITUDE'])).km
        })

    return retrieved_businesses_with_scores

# **Run Similarity Search**
query_text = "I want a restaurant nearby"
retrieved_businesses_with_scores = calculate_similarity_score(query_text)

# Convert results to DataFrame
#business_df = pd.DataFrame(retrieved_businesses_with_scores)
#business_df.sort_values(by=['DISTANCE'], ascending=[True]).to_csv('Test_cosine_paraphraseLM.csv', index=False)


# Optionally, print out the documents related to the retrieved businesses
business_data_list = []
for business in retrieved_businesses_with_scores:
    if business['SIMILARITY_SCORE'] >= 0.2:  # Check for a threshold
        business_data_list.append({
            'BUSINESS_ID': business['BUSINESS_ID'],
            'NAME': business['NAME'],
            'CATEGORIES': business['CATEGORIES'],
            'FLATTENED_ATTRIBUTES':business['FLATTENED_ATTRIBUTES'],
            'STATE':business['STATE'],
            'LATITUDE': business['LATITUDE'],
            'LONGITUDE': business['LONGITUDE'],
            'SIMILARITY_SCORE': business['SIMILARITY_SCORE'],
            'DISTANCE':business['DISTANCE']
        })

# Convert the list of dictionaries into a DataFrame and save to CSV
business_df = pd.DataFrame(business_data_list)
business_df.sort_values(by=['DISTANCE'], ascending=[True]).to_csv('Test_cosine_paraphraseLM.csv', index=False)
