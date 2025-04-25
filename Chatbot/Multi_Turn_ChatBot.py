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
from dotenv import load_dotenv
import os
from chatbotfunction import process_chat_input,fetch_and_display_recommendations
from utils import load_data_from_snowflake, get_lat_lon, run_similarity_search 
load_dotenv()

snowflake_user = os.getenv('SNOWFLAKE_USER')
snowflake_password = os.getenv('SNOWFLAKE_PASSWORD')
snowflake_account = os.getenv('SNOWFLAKE_ACCOUNT')
snowflake_warehouse = os.getenv('SNOWFLAKE_WAREHOUSE')
snowflake_database = os.getenv('SNOWFLAKE_DATABASE')
snowflake_schema = os.getenv('SNOWFLAKE_SCHEMA')

# --- Connect to Snowflake ---
@st.cache_resource
def get_snowflake_connection():
    conn = snowflake.connector.connect(
    user=snowflake_user,
    password=snowflake_password,
    account=snowflake_account,
    warehouse=snowflake_warehouse,
    database=snowflake_database,
    schema=snowflake_schema
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
        df = load_data_from_snowflake()
        fetch_and_display_recommendations(location_input, query_input)
                # ✅ Second recommendation based on preferences
        preferences = st.session_state.get("user_info", {}).get("preferences", "")
        print(f"Preferences: {preferences}")
        if preferences:
            st.markdown("### 🌟 Based on your previous visits and preferences!!")
            preference_based_results = run_similarity_search(location_input, preferences, df)
            top_2 = preference_based_results.head(2)  # Adjust to show top 2 results

            # Updated expected column
            expected_columns = ["NAME", "CATEGORIES", "DISTANCE"]
            available_columns = [col for col in expected_columns if col in top_2.columns]

            if not top_2.empty and available_columns:
                st.table(top_2[available_columns])
            else:
                st.info("No specific matches found for your preferences, or required columns are missing.")

    if location_input and query_input:
        st.markdown("---")
        st.subheader("💬 Follow-up Chat")

        conversation_option = st.radio(
            "How would you like to handle this question?",
            ["Continue previous conversation", "Start a new conversation"],
            key="conversation_mode"
        )

        if conversation_option == "Continue previous conversation":
            user_input = st.chat_input("Ask me follow-up questions...")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    if "last_results" in st.session_state:
                        response = process_chat_input(user_input, location_input)
                    else:
                        response = process_chat_input(query_input, location_input)
                st.markdown(response)

        elif conversation_option == "Start a new conversation":
            user_input = st.chat_input("Start a new conversation...")
            if user_input:
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    response = fetch_and_display_recommendations(location_input,user_input )
                st.markdown(response)
    else:
        st.info("🔄 Follow-up chat will be available after you enter location and requirements.")

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