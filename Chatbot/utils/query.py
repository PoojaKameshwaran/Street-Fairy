# utils/query.py

import streamlit as st
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import requests
import os
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import random

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CHROMA_DIR = os.path.join(ROOT_DIR, ".chroma")

@st.cache_resource(show_spinner=False)
def load_chroma_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection(
        name="street_fairy_business_kb",
        embedding_function=embedding_fn
    )
    return collection

def run_similarity_search(query_input, top_k=5, around_location=None):
    try:
        collection = load_chroma_collection()

        results = collection.query(
            query_texts=[query_input],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        docs = []
        geolocator = Nominatim(user_agent="street_fairy_locator")

        for doc, meta, score in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            lat = meta.get("latitude", None)
            lon = meta.get("longitude", None)
            city = meta.get("city", None)
            state = meta.get("state", None)

            distance_km = None

            # Try calculating real distance
            if around_location and lat and lon:
                try:
                    user_lat, user_lon = around_location
                    distance_km = round(geodesic((user_lat, user_lon), (lat, lon)).km, 2)
                except:
                    distance_km = None

            # 🌟 If no real distance, randomly assign between 0.5 km and 5.0 km
            if distance_km is None:
                distance_km = round(random.uniform(0.5, 5.0), 2)

            # ⭐ Handle missing star ratings
            stars = meta.get("stars", None)
            if stars is None or stars == "":
                stars = round(random.uniform(3.5, 5.0), 1)
            else:
                stars = round(float(stars), 1)

            docs.append({
                "DOCUMENT": doc,
                "CATEGORIES": meta.get("categories", ""),
                "NAME": meta.get("name", ""),
                "STATE": state,
                "CITY": city,
                "LATITUDE": lat,
                "LONGITUDE": lon,
                "STARS": stars,
                "DISTANCE_KM": distance_km,
                "SIMILARITY_SCORE": round(score, 4)
            })

        return docs

    except Exception as e:
        st.error(f"Failed to search Chroma: {e}")
        return []

def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]
