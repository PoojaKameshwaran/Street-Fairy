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
from chatbotfunction import process_chat_input
from utils import load_data_from_snowflake, get_lat_lon, run_similarity_search 

# --- Connect to Snowflake ---
@st.cache_resource
def get_snowflake_connection():
    conn = snowflake.connector.connect(
    user='',
    password='',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
    )
    return conn

def screen_0():
    st.title("🔐 Welcome to Street Fairy")

    # Ask if user is existing or new
    option = st.radio("Are you an existing user?", ("Yes", "No"))

    if option == "Yes":
        # Existing user login
        user_id = st.text_input("Enter your User ID")
        password = st.text_input("Enter your Password", type="password")

        if st.button("Login"):
            conn = get_snowflake_connection() 
            cursor = conn.cursor()
            query = f"""
                SELECT user_id_login,NAME,CATEGORIES FROM PUBLIC.User_Preference
                WHERE User_Id_Login = '{user_id}' AND User_Id_Password = '{password}'
            """
            cursor.execute(query)
            result = cursor.fetchone()
            conn.close()

            if result:
                st.success("Login successful!")
                st.session_state.user_info = {
                    "user_name": result[1],
                    "user_id": result[0],
                    "preferences": result[2]
                }
                st.session_state.screen = 2  # Go to recommendation screen
            else:
                st.error("Invalid credentials!")

    elif option == "No":
        # New user registration
        st.markdown("### 👤 New User Registration")
        user_name = st.text_input("Enter your Name:")
        user_id = st.text_input("Choose a User ID")
        password = st.text_input("Choose a Password", type="password")
        preferences_input = st.text_area("Enter your preferences")

        if st.button("Register"):
            if user_name and user_id and password and preferences_input:
                conn = get_snowflake_connection() 
                cursor = conn.cursor()
                insert_query = f"""
                    INSERT INTO PUBLIC.User_Preference (User_Id_Login, User_Id_Password, NAME, CATEGORIES)
                    VALUES ('{user_id}', '{password}', '{user_name}', '{preferences_input}')
                """
                try:
                    cursor.execute(insert_query)
                    conn.commit()
                    conn.close()
                    st.success("User registered successfully!")
                    st.session_state.user_info = {
                        "user_name": user_name,
                        "user_id": user_id,
                        "preferences": preferences_input
                    }
                    st.session_state.screen = 2  # Go to recommendation screen
                except Exception as e:
                    st.error(f"User ID already exists or failed to register: {e}")
            else:
                st.warning("Please complete all fields.")


def screen_2():
    st.title("🔍 STREET FAIRY RECOMMENDER")

    location_input = st.text_input("Enter your location (e.g., Tampa):")
    query_input = st.text_input("Please post your requirements?")

    if st.button("Find Recommendations"):
        with st.spinner("Loading recommendations..."):
            df = load_data_from_snowflake()
            if df is None or df.empty:
                st.error("Failed to load data from Snowflake.")
            elif not location_input or not query_input:
                st.warning("Please enter both location and restaurant type.")
            else:
                results = run_similarity_search(location_input, query_input, df)
                if not results.empty:
                    st.success(f"Found {len(results)} results!")
                    st.dataframe(results)
                    st.download_button("Download CSV", data=results.to_csv(index=False), file_name="LLM_Model.csv")
                    results = run_similarity_search(location_input, query_input, df)
                    if not results.empty:
                        st.session_state["last_results"] = results
                    # ✅ Second recommendation based on preferences
                    preferences = st.session_state.get("user_info", {}).get("preferences", "")
                    print(f"Preferences: {preferences}")
                    if preferences:
                        st.markdown("### 🌟 Based on your previous visits, here are 2 suggestions:")
                        preference_based_results = run_similarity_search(location_input, preferences, df)
                        top_2 = preference_based_results.head(2)  # Adjust to show top 2 results

                        # Updated expected column
                        expected_columns = ["NAME", "CATEGORIES", "DISTANCE"]
                        available_columns = [col for col in expected_columns if col in top_2.columns]

                        if not top_2.empty and available_columns:
                            st.table(top_2[available_columns])
                        else:
                            st.info("No specific matches found for your preferences, or required columns are missing.")
  
    # 👇 Add this at the bottom to enable chat-based follow-up
    st.markdown("---")
    st.subheader("💬 Follow-up Chat")

    user_input = st.chat_input("Ask me follow-up questions?")

    if user_input:
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            # Use stored last results if available
            if "last_results" in st.session_state:
                response = process_chat_input(user_input,location_input)  # Handle follow-ups
            else:
                # Use structured inputs only if no previous result exists
                response = process_chat_input(query_input, location_input)

            st.markdown(response)

# --- Main Function ---
def main():
    if "screen" not in st.session_state:
        st.session_state.screen = 0  # Start at welcome/login/registration screen

    if st.session_state.screen == 0:
        screen_0()  # Login & registration
    elif st.session_state.screen == 2:
        screen_2()  # Recommendations

if __name__ == "__main__":
    main()