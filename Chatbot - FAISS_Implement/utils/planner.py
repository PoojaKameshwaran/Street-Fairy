# utils/recommendation.py
import streamlit as st
from utils.database import load_data_from_snowflake
from utils.query import run_similarity_search, query_ollama


@st.cache_data  ### Added
def display_preference_based_recommendations():
    df = load_data_from_snowflake()
    preferences = st.session_state.get("user_info", {}).get("preferences", "")
    user_location = st.session_state.get("user_location", "")

    if preferences:
        st.markdown("### 🌟 Based on your previous visits why can't you plan for this? !!")
        preference_based_results = run_similarity_search(user_location,query_input=preferences, df=df)
        top_2 = preference_based_results.head(1)

        expected_columns = ["NAME", "CATEGORIES"]
        available_columns = [col for col in expected_columns if col in top_2.columns]

        if not top_2.empty and available_columns:
            # Iterate over top 2 recommendations and build a friendly, engaging business description
            for index, row in top_2.iterrows():
                business_str = f"""
                - **{row['NAME']}**: Located in {row['CITY']}, {row['STATE']}, this place offers an amazing selection of {row['CATEGORIES']}. 
                Whether you're craving comfort food, southern specialties, or a fantastic barbecue, {row['NAME']} has something to offer.
                """

                # Display the business information in Streamlit
                st.markdown(f"### Recommendation for you:")
                st.markdown(f"**Business Name**: {row['NAME']}")
                st.markdown(f"**Categories**: {row['CATEGORIES']}")
                st.markdown(f"**Location**: {row['CITY']}, {row['STATE']}")
                st.markdown(f"\n**What makes it special:** {business_str}")

        else:
            st.info("No specific matches found for your preferences, or required columns are missing.")
