import streamlit as st
from screens.login import screen_0
from screens.chat import screen_2  # <-- correct name

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
        screen_0()

    with tab2:
        if "user_info" not in st.session_state:
            st.warning("Please log in first.")
            return
        screen_2()
