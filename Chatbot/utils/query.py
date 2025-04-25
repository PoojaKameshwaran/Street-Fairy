# utils/query.py

import streamlit as st
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import requests
import os

# --- Correct Chroma Path (absolute from project root)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
CHROMA_DIR = os.path.join(ROOT_DIR, ".chroma")

# --- Load Chroma Collection ---
@st.cache_resource(show_spinner=False)
def load_chroma_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = chroma_client.get_or_create_collection(
        name="street_fairy_business_kb",
        embedding_function=embedding_fn
    )
    return collection

# --- Run semantic search ---
def run_similarity_search(query_input, top_k=5):
    try:
        collection = load_chroma_collection()
        
        results = collection.query(
            query_texts=[query_input],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        docs = []
        for doc, meta, score in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
            docs.append({
                "DOCUMENT": doc,
                "CATEGORIES": meta.get("categories", ""),
                "NAME": meta.get("name", ""),
                "STATE": meta.get("state", ""),
                "CITY": meta.get("city", ""),
                "LATITUDE": meta.get("latitude", ""),
                "LONGITUDE": meta.get("longitude", ""),
                "SIMILARITY_SCORE": round(score, 4)
            })
        return docs

    except Exception as e:
        st.error(f"Failed to search Chroma: {e}")
        return []

# --- Query Ollama LLM ---
def query_ollama(prompt, model="mistral"):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": model,
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]
