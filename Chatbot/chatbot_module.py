import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import run_similarity_search

# Load embedding model once
@st.cache_resource(show_spinner=False)
def load_embedding_model():
    return SentenceTransformer('paraphrase-MiniLM-L6-v2')

embedding_model = load_embedding_model()


def process_chat_input(user_input, location_input):
    if "last_results" not in st.session_state:
        return "❗ Please run a search first so I know what you're comparing against."

    df = st.session_state.get("last_results")

    # Generate embeddings for the filtered businesses if not already done
    if 'EMBEDDING' not in df.columns:
        with st.spinner("🔍 Embedding business attributes for comparison..."):
            df['EMBEDDING'] = df['FLATTENED_ATTRIBUTES'].fillna("").apply(
                lambda text: embedding_model.encode(text, convert_to_numpy=True)
            )
            st.session_state["last_results"] = df  # Cache embeddings

    # Run similarity search using user input and location
    response = run_similarity_search(location_input, user_input, df)

    if response.empty:
        return "🤷 No relevant results found for your query. Try rephrasing or a different location."

    results = []
    for _, row in response.head(5).iterrows():
        if row["SIMILARITY_SCORE"] >= 0.1:
            results.append({
                "Name": row["NAME"],
                "Categories": row["CATEGORIES"],
                "Flattened Attributes": row["FLATTENED_ATTRIBUTES"],
                "Distance (km)": round(row["DISTANCE"], 2),
                "Similarity Score": round(row["SIMILARITY_SCORE"], 4)
            })

    return results if results else "😕 Nothing matched closely enough. Try tweaking your query."
