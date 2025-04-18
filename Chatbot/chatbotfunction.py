import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import run_similarity_search 


def process_chat_input(user_input,location_input):
    embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    if "last_results" in st.session_state:
        df = st.session_state.get("last_results")
        if 'EMBEDDING' not in df.columns:
            df['EMBEDDING'] = df['FLATTENED_ATTRIBUTES'].fillna("").apply(
                lambda text: embedding_model.encode(text, convert_to_numpy=True)
            )
        response = run_similarity_search(location_input,user_input, df)
        if not response.empty:
            top_result = response.iloc[0]
            if top_result["SIMILARITY_SCORE"]>=0.1: # change as per the results
                top_result = response.iloc[0]  # First (most relevant) result
                return {
                    "Name": top_result["NAME"],
                    "Categories": top_result["CATEGORIES"],
                    "Flattened Attributes": top_result["FLATTENED_ATTRIBUTES"],
                    "Distance (km)": round(top_result["DISTANCE"], 2),
                    "Similarity Score": round(top_result["SIMILARITY_SCORE"], 4)
                }
        else:
            return "No relevant results found for your query."
    else:
        return "No previous results found. Please run a search first."
