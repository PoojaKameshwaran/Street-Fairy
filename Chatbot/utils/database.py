import snowflake.connector
import os
import json
import pandas as pd
import streamlit as st

def get_snowflake_connection():
    key_path = os.path.join(os.path.dirname(__file__), "..", "..", "key.json")
    with open(key_path) as f:
        creds = json.load(f)
    return snowflake.connector.connect(**creds)

def load_data_from_snowflake():
    conn = get_snowflake_connection()
    cursor = conn.cursor()
    query = """
        SELECT BUSINESS_ID, NAME, CITY, STATE, LATITUDE, LONGITUDE, CATEGORIES, FLATTENED_ATTRIBUTES,
        PARSE_JSON(embedding)::VECTOR(FLOAT, 384) AS EMBEDDING
        FROM BUSINESS_EMBEDDINGS
    """
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    conn.close()
    return df

def save_preferences(user_id, feedback_type, new_preferences=None):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()

        # If 'like' feedback, update liked preferences in Snowflake
        if feedback_type == 'like' and new_preferences:
            print("XXXXX")
            liked = st.session_state.feedback.get("liked", set())
            liked.update(new_preferences)
            liked_str = ", ".join(sorted(set(liked))).replace("'", "''")
            update_query = f"""
                UPDATE PUBLIC.User_Preference
                SET CATEGORIES = '{liked_str}'
                WHERE User_Id_Login = '{user_id}'
            """
            cursor.execute(update_query)

        # If 'dislike' feedback, update disliked preferences in Snowflake
        elif feedback_type == 'dislike' and new_preferences:
            disliked = st.session_state.feedback.get("disliked", set())
            disliked.update(new_preferences)
            disliked_str = ", ".join(sorted(set(disliked))).replace("'", "''")
            update_query = f"""
                UPDATE PUBLIC.User_Preference
                SET CATEGORIES = '{disliked_str}'
                WHERE User_Id_Login = '{user_id}'
            """
            cursor.execute(update_query)

        conn.commit()
        conn.close()
        st.toast("✅ Preferences updated successfully!", icon="💾")

    except Exception as e:
        st.error(f"Failed to update preferences: {e}")
