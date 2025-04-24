import streamlit as st
from chatbot_module import process_chat_input
from utils import load_data_from_snowflake
import re

st.set_page_config(page_title="Street Fairy 🧚 Chatbot", layout="centered")

# ---- 🌸 Cozy UI Styling ----
st.markdown("""
    <style>
        body, .main, .block-container {
            background-color: #ffe4e1;  /* Pastel pink */
            color: #333333;
        }
        .block-container {
            border-radius: 12px;
            padding: 2rem;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.05);
        }
        h1, h2, h3, h4, label, .stTextInput label {
            color: #000000 !important;  /* Force black text for labels and headers */
        }
        .stTextInput>div>div>input,
        .stTextInput>div>div>input:focus {
            background-color: #fff5f7;
            color: #000000 !important;
            caret-color: #000000 !important;  /* Black typing cursor */
        }
        .stButton>button {
            background-color: #f9c8d9;
            color: #000000 !important;  /* Ensure button text is always dark */
            border-radius: 10px;
            border: none;
        }
        .stButton>button:hover {
            background-color: #f7a7be;
            color: white;
        }
        .stMarkdown, .stSuccess, .stWarning {
            color: #000000 !important; /* Force black text in output blocks */
        }
    </style>
""", unsafe_allow_html=True)

st.title("🧚 Welcome to Street Fairy!")
st.markdown("Enter what you're looking for and your location, and let the fairy find it for you ✨")

# Initialize session state to store history if not already there
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_results" not in st.session_state:
    with st.spinner("🧚 Summoning fairy magic... please wait..."):
        st.session_state.last_results = load_data_from_snowflake()

# --- User Inputs ---
with st.form(key="chat_form"):
    user_query = st.text_input("What are you in the mood for?", placeholder="e.g., a cozy cafe with great matcha")
    user_location = st.text_input("Where are you?", placeholder="e.g., Boston, MA")
    submit_button = st.form_submit_button(label="✨ Summon the Fairy")

# --- Process and Display Results ---
supported_states = {"PA", "FL", "MO", "IN", "TN"}
if submit_button and user_query and user_location:
    # Pre-check if location is from supported states
    state_match = re.search(r'\b(PA|FL|MO|IN|TN)\b', user_location.upper())

    if not state_match:
        st.warning("""🌎 Sorry! We currently only support locations in:
        **Pennsylvania (PA)**, **Florida (FL)**, **Missouri (MO)**, 
        **Indiana (IN)**, and **Tennessee (TN)**.
        Try searching within these states 💫""")
    else:
        with st.spinner("🧚 Fairy is finding the perfect place just for you..."):
            response = process_chat_input(user_query, user_location)
            st.session_state.chat_history.append((user_query, user_location, response))

# --- Chat History ---
if st.session_state.chat_history:
    st.markdown("---")
    st.subheader("🗣️ Your Fairy Interactions")
    for idx, (query, location, reply) in enumerate(reversed(st.session_state.chat_history), 1):
        st.markdown(f"**You [{location}]**: {query}")
        if isinstance(reply, list):
            for r in reply:
                st.success(f"**🧚 Recommendation:** {r['Name']}\n\n"
                           f"- Categories: {r['Categories']}\n"
                           f"- Attributes: {r['Flattened Attributes']}\n"
                           f"- Distance: {r['Distance (km)']} km\n"
                           f"- Similarity: {r['Similarity Score']}")
        else:
            st.warning(reply)

# --- Footer ---
st.markdown("<small>Made with 💖 by Street Fairy Team</small>", unsafe_allow_html=True)
