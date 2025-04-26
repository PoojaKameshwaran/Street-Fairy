import streamlit as st
from utils.query import run_similarity_search, query_ollama

def screen_2():
    st.title("🧚‍♀️ Chat with Street Fairy")

    # --- Sticky Chat UI Style ---
    st.markdown("""
        <style>
        .block-container { height: 90vh; overflow-y: auto; padding-bottom: 120px; }
        section[data-testid="stChatInput"] {
            position: fixed; bottom: 1rem; width: 85%; left: 7%; right: 7%;
            z-index: 1000; background: transparent; box-shadow: none; border: none;
        }
        section[data-testid="stChatInput"] > div:first-child { border-top: none; background: transparent; box-shadow: none; }
        </style>
    """, unsafe_allow_html=True)

    # --- Session State Initialization ---
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "previous_recommendations" not in st.session_state:
        st.session_state.previous_recommendations = []
    if "current_location" not in st.session_state:
        st.session_state.current_location = None
    if "visited_places" not in st.session_state:
        st.session_state.visited_places = []
    if "mode" not in st.session_state:
        st.session_state.mode = "search"

    # --- 🧚‍♀️ Show Chat History ---
    with st.container():
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # --- 🧚‍♀️ Chat Input ---
    user_message = st.chat_input("Where would you like to go next? ✨")

    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        # --- 🧚‍♀️ If user mentions a previously suggested place ---
        if st.session_state.previous_recommendations:
            matched_place = None
            for place in st.session_state.previous_recommendations:
                if place["NAME"].lower() in user_message.lower():
                    matched_place = place
                    break

            if matched_place:
                # 🎯 User selected this place!
                st.session_state.current_location = (matched_place["LATITUDE"], matched_place["LONGITUDE"])
                st.session_state.visited_places.append(matched_place)
                st.session_state.mode = "planning"  # Switch to planning mode

                celebration_text = f"""
                🎉 Yay! You chose **{matched_place['NAME']}** in {matched_place['CITY']}, {matched_place['STATE']}!
                ⭐ {matched_place.get('STARS', '?')} stars — 📏 {matched_place.get('DISTANCE_KM', '?')} km away

                ✨ Now, tell me where you'd like to go from here!
                For example: "Find me a gym nearby" or "Show me some cozy cafes!"
                """
                st.session_state.chat_history.append({"role": "assistant", "content": celebration_text})
                st.rerun()
                return

        # --- 🧚‍♀️ Normal Search Flow (find new places) ---
        with st.spinner("🧚‍♀️ Searching for magical places..."):
            if st.session_state.mode == "planning" and st.session_state.current_location:
                results = run_similarity_search(user_message, around_location=st.session_state.current_location)
            else:
                results = run_similarity_search(user_message)

        if not results:
            st.session_state.chat_history.append({"role": "assistant", "content": "⚠️ No magical places found! Try asking something else ✨"})
            st.rerun()
            return

        # --- 🔥 Save these results for future matching ---
        st.session_state.previous_recommendations = results[:5]

        # --- 📜 Summarize businesses nicely ---
        business_summaries = "\n\n".join([
            f"✨ **{b['NAME']}** ({b.get('CATEGORIES', 'No categories')})\n"
            f"📍 {b.get('CITY', 'Unknown')}, {b.get('STATE', 'Unknown')} — ⭐ {b.get('STARS', '?')} stars — 📏 {b.get('DISTANCE_KM', '?')} km"
            for b in st.session_state.previous_recommendations
        ])

        recommendation_prompt = f"""
        You are Street Fairy 🧚‍♀️ — a cheerful helper who recommends magical nearby places!

        The user asked: "{user_message}"

        Here are 5 real businesses nearby:

        {business_summaries}

        🎯 Recommend nearest 3-5 places warmly.
        - Mention name, location, distance, and why it's great
        - Sound friendly and concise
        - NEVER invent new businesses
        """

        with st.spinner("🧚‍♀️ Working the fairy magic..."):
            fairy_response = query_ollama(recommendation_prompt)

        st.session_state.chat_history.append({"role": "assistant", "content": fairy_response})
        st.rerun()

