import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from chatbotfunction import process_chat_input, fetch_and_display_recommendations
from utils import load_data_from_snowflake, get_lat_lon, run_similarity_search, get_snowflake_connection, query_ollama
import json

def screen_0():
    st.title("🔐 Welcome to Street Fairy")
    option = st.radio("Are you an existing user?", ("Yes", "No"))

    if option == "Yes":
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
                st.session_state.screen = 2
            else:
                st.error("Invalid credentials!")

    elif option == "No":
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
                    st.session_state.screen = 2
                except Exception as e:
                    st.error(f"User ID already exists or failed to register: {e}")
            else:
                st.warning("Please complete all fields.")

def screen_2():
    st.title("🧚‍♀️ Chat with the Fairy")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "feedback" not in st.session_state:
        st.session_state.feedback = {"liked": set(), "disliked": set()}
    if "remaining_recs" not in st.session_state:
        st.session_state.remaining_recs = []
    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    if "user_info" not in st.session_state:
        st.warning("Please log in first.")
        return

    # Scrollable chat history box
    with st.container():
        chat_box = st.container()
        with chat_box:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    user_message = st.chat_input("Ask for a recommendation or give feedback like 'I liked it' or 'Next'")

    if user_message:
        st.chat_message("user").markdown(user_message)
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        # ----- HANDLE FEEDBACK BEFORE SEARCH -----
        feedback_msg = user_message.lower()

        if any(word in feedback_msg for word in ["i like", "liked it", "great", "perfect", "this works"]):
            if st.session_state.last_result is not None:
                categories = st.session_state.last_result["CATEGORIES"]
                st.session_state.feedback["liked"].update(map(str.strip, categories.lower().split(",")))
                save_preferences()
                st.chat_message("assistant").success("🌟 Glad you liked it! I'll remember that for next time.")
                return

        elif any(word in feedback_msg for word in ["not a fan", "dislike", "something else", "another", "next"]):
            if st.session_state.last_result is not None:
                categories = st.session_state.last_result["CATEGORIES"]
                st.session_state.feedback["disliked"].update(map(str.strip, categories.lower().split(",")))

            if st.session_state.remaining_recs:
                next_suggestion = st.session_state.remaining_recs.pop(0)
                st.session_state.last_result = next_suggestion

                next_prompt = f"""
                You are Street Fairy 🧚‍♀️. Here's another nearby business:

                - {next_suggestion['NAME']} ({next_suggestion['CATEGORIES']}, {next_suggestion.get('CITY', '')}, {next_suggestion['STATE']})

                ✅ Describe what makes it special.
                ✅ Use a friendly tone.
                ✅ Do not invent anything.
                """
                response = query_ollama(next_prompt, model="mistral")
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                return
            else:
                with st.chat_message("assistant"):
                    st.warning("No more suggestions for this query! Try something new?")
                return

        # ----- NEW SEARCH -----
        df = load_data_from_snowflake()
        results = run_similarity_search(query_input=user_message, df=df)

        if results.empty:
            st.chat_message("assistant").warning("⚠️ No results found. Try asking differently.")
            return

        top_result = results.iloc[0]
        st.session_state.remaining_recs = results.iloc[1:].to_dict(orient="records")
        st.session_state.last_result = top_result

        business_str = f"- {top_result['NAME']} ({top_result['CATEGORIES']}, {top_result.get('CITY', '')}, {top_result['STATE']})"

        rec_prompt = f"""
        You are Street Fairy 🧚‍♀️ helping users find places nearby.

        The user asked: "{user_message}"
        Here's a business we found:

        {business_str}

        ✅ Describe what makes it special.
        ✅ Mention name and location.
        ✅ Use a friendly tone.
        🚫 Do not invent anything.
        """

        try:
            recommendation = query_ollama(rec_prompt, model="mistral")

            with st.chat_message("assistant"):
                st.markdown(recommendation)
                st.markdown("What did you think of this suggestion? You can say something like \"I liked it\" or \"Not for me\" ✨")

            st.session_state.chat_history.append({"role": "assistant", "content": recommendation})

        except Exception as e:
            st.chat_message("assistant").error(f"⚠️ LLM call failed: {e}")


def save_preferences():
    try:
        user_id = st.session_state.user_info["user_id"]
        liked = st.session_state.feedback.get("liked", set())
        if liked:
            liked_str = ", ".join(liked).replace("'", "''")
            conn = get_snowflake_connection()
            cursor = conn.cursor()
            update_query = f"""
                UPDATE PUBLIC.User_Preference
                SET CATEGORIES = '{liked_str}'
                WHERE User_Id_Login = '{user_id}'
            """
            cursor.execute(update_query)
            conn.commit()
            conn.close()
            st.toast("✅ Preferences updated!", icon="💾")
    except Exception as e:
        st.error(f"Failed to update preferences: {e}")

def screen_ui():
    st.set_page_config(page_title="Street Fairy 🧚", layout="wide")

    with st.sidebar:
        st.title("🧚‍♀️ Street Fairy")
        st.markdown("You name it, the fairy will find it!")
        if "user_info" in st.session_state:
            st.markdown(f"👤 Logged in as **{st.session_state.user_info.get('user_name')}**")
        st.markdown("---")
        st.markdown("Use the tabs to explore recommendations and chat.")

    tab1, tab2 = st.tabs(["🔐 Login / Register", "🔍 Recommendations & Chat"])

    with tab1:
        st.subheader("Login or Register")
        option = st.radio("Are you a new user?", ("No, I have an account", "Yes, create new account"))

        if option == "No, I have an account":
            user_id = st.text_input("User ID")
            password = st.text_input("Password", type="password")
            if st.button("Login"):
                conn = get_snowflake_connection()
                cursor = conn.cursor()
                query = f"""
                    SELECT user_id_login, NAME, CATEGORIES
                    FROM PUBLIC.User_Preference
                    WHERE User_Id_Login = '{user_id}' AND User_Id_Password = '{password}'
                """
                cursor.execute(query)
                result = cursor.fetchone()
                conn.close()
                if result:
                    st.success("Login successful!")
                    preferences_raw = result[2] or ""
                    parsed_prefs = [cat.strip().lower() for cat in preferences_raw.split(",")]

                    st.session_state.user_info = {
                        "user_name": result[1],
                        "user_id": result[0],
                        "preferences": preferences_raw
                    }

                    st.session_state.feedback = {
                        "liked": set(parsed_prefs),
                        "disliked": set()
                    }

                    st.session_state.screen = 2

        else:
            user_name = st.text_input("Name")
            user_id = st.text_input("Choose a User ID")
            password = st.text_input("Choose a Password", type="password")
            preferences_input = st.text_area("Your food/style preferences")

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
                        st.success("Registered! You can now explore.")
                        st.session_state.user_info = {
                            "user_name": user_name,
                            "user_id": user_id,
                            "preferences": preferences_input
                        }
                        st.session_state.feedback = {
                            "liked": set(preferences_input.split(",")),
                            "disliked": set()
                        }
                        st.session_state.screen = 2
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please complete all fields.")

    with tab2:
        if "user_info" not in st.session_state:
            st.warning("Please log in first.")
            return
        screen_2()

def main():
    screen_ui()

if __name__ == "__main__":
    main()
