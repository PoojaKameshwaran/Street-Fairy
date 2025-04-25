import snowflake.connector
import os
import json
import streamlit as st

def get_snowflake_connection():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    key_path = os.path.join(root_dir, "key.json")

    with open(key_path, "r") as f:
        creds = json.load(f)

    conn = snowflake.connector.connect(
        user=creds["user"],
        password=creds["password"],
        account=creds["account"],
        warehouse=creds["warehouse"],
        database=creds["database"],
        schema=creds["schema"]
    )
    return conn

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
