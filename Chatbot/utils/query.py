import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import requests

def run_similarity_search(query_input, df, top_k=5):
    df = df.copy()
    df["EMBEDDING"] = df["EMBEDDING"].apply(lambda x: np.array(x, dtype=np.float32))
    df["EMBEDDING"] = df["EMBEDDING"].apply(lambda x: x / np.linalg.norm(x))

    model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    query_emb = model.encode([query_input], convert_to_numpy=True).astype("float32")
    query_emb = query_emb / np.linalg.norm(query_emb)

    index = faiss.IndexFlatIP(query_emb.shape[1])
    index.add(np.vstack(df["EMBEDDING"].values))

    k = min(top_k, len(df))
    distances, indices = index.search(query_emb, k)

    return df.iloc[indices[0]].copy()

def query_ollama(prompt, model="mistral"):
    try:
        response = requests.post("http://localhost:11434/api/generate", json={
            "model": model,
            "prompt": prompt,
            "stream": False
        })
        
        # Check if the response is successful (status code 200)
        if response.status_code == 200:
            response_json = response.json()
            
            # Use .get() to avoid KeyError if 'response' is missing
            response_text = response_json.get('response', 'No response key found in the API response.')
            
            # Return the result, whether it's the response or a default message
            return response_text
        else:
            print("Error: Received non-200 response:", response.status_code)
            print("Response text:", response.text)  # Debugging: print the response text
    except Exception as e:
        print(f"Exception during API request: {e}")
    
    return "Failed to get a valid response from Ollama."

