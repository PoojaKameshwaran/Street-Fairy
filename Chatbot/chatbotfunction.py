import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from utils import load_data_from_snowflake, get_lat_lon, run_similarity_search 


def process_chat_input(user_input, location_input):
    # Initialize the embedding model
    embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

    # Check if "last_results" is available (for follow-up conversation)
    if "last_results" in st.session_state:
        df = st.session_state.get("last_results")

        # Make sure embeddings are generated if not already done
        if 'EMBEDDING' not in df.columns:
            df['EMBEDDING'] = df['FLATTENED_ATTRIBUTES'].fillna("").apply(
                lambda text: embedding_model.encode(text, convert_to_numpy=True)
            )

        # Run similarity search based on location and user input
        response = run_similarity_search(location_input, user_input, df)
        
        if not response.empty:
            top_result = response.iloc[0]  # Get the top result based on similarity score
            if top_result["SIMILARITY_SCORE"] >= 0.1:  # Adjust threshold if needed
                # Return the most relevant result's information
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
            return "No relevant results found for your query."

    # If no previous results (for new conversation), handle new search input
    else:
        "No Results Found"

def fetch_and_display_recommendations(location_input, query_input):
    with st.spinner("Loading recommendations..."):
        df = load_data_from_snowflake()
        if df is None or df.empty:
            st.error("Failed to load data from Snowflake.")
            return None
        elif not location_input or not query_input:
            st.warning("Please enter both location and restaurant type.")
            return None
        else:
            results = run_similarity_search(location_input, query_input, df)
            if not results.empty:
                st.success(f"Found {len(results)} results!")
                st.dataframe(results)
                st.download_button("Download CSV", data=results.to_csv(index=False), file_name="LLM_Model.csv")

                # Save to session state for follow-ups
                st.session_state["last_results"] = results

                # Optional: Log preferences (if needed for next stage)
                preferences = st.session_state.get("user_info", {}).get("preferences", "")
                print(f"Preferences: {preferences}")

                return results
            else:
                st.warning("No results found for your query.")
                return None
