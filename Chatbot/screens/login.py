import streamlit as st
from utils.database import get_snowflake_connection

def screen_0():
    st.title("\U0001f512 Welcome to Street Fairy")
    option = st.radio("Are you an existing user?", ("Yes", "No"))

    if option == "Yes":
        user_id = st.text_input("Enter your User ID")
        password = st.text_input("Enter your Password", type="password")

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
                st.session_state.user_info = {
                    "user_name": result[1],
                    "user_id": result[0],
                    "preferences": result[2]
                }
                st.session_state.feedback = {
                    "liked": set(result[2].split(",")) if result[2] else set(),
                    "disliked": set()
                }
                st.session_state.screen = 2
            else:
                st.error("Invalid credentials!")

    elif option == "No":
        st.markdown("### \U0001f464 New User Registration")
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
                    st.session_state.feedback = {
                        "liked": set(preferences_input.split(",")),
                        "disliked": set()
                    }
                    st.session_state.screen = 2
                except Exception as e:
                    st.error(f"User ID already exists or failed to register: {e}")
            else:
                st.warning("Please complete all fields.")