# screens/chat.py
import streamlit as st
from utils.query import run_similarity_search, query_ollama
from utils.database import load_data_from_snowflake, save_preferences
from utils.planner import display_preference_based_recommendations  # Added by Deepana

def screen_2():
    st.title("🧚‍♀️ Chat with Street Fairy")

    # Scrollable chat history + truly sticky chat input
    st.markdown(
        """
        <style>
        /* Make the entire main container scrollable */
        .block-container {
            height: 90vh;
            overflow-y: auto;
            padding-bottom: 120px; /* Enough space for sticky input */
        }

        /* Sticky chat input at the bottom */
        section[data-testid="stChatInput"] {
            position: fixed;
            bottom: 1rem;
            width: 85%;
            left: 7%;
            right: 7%;
            z-index: 1000;
            background: transparent;
            box-shadow: none;
            border: none;
        }

        /* Remove ugly border above the chat input */
        section[data-testid="stChatInput"] > div:first-child {
            border-top: none;
            background: transparent;
            box-shadow: none;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "feedback" not in st.session_state:
        st.session_state.feedback = {"liked": set(), "disliked": set()}
    if "remaining_recs" not in st.session_state:
        st.session_state.remaining_recs = []

    if "user_info" not in st.session_state:
        st.warning("Please log in first.")
        return

    # ---------------- Chat history area ----------------
    with st.container():
        chat_placeholder = st.container()
        with chat_placeholder:
            st.markdown('<div class="chat-history">', unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            st.markdown('</div>', unsafe_allow_html=True)

    # ---------------- Chat input area ----------------
    with st.container():
        st.markdown('<div class="chat-input">', unsafe_allow_html=True)
        user_location = st.text_input("📍Where are you located?", placeholder="e.g., Florida")
        user_message = st.chat_input("What are you looking for today?")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # -------------- Handle user input --------------
    if user_message:
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        if any(x in user_message.lower() for x in ["not a fan", "don't like", "dislike", "another", "next"]):
            if st.session_state.remaining_recs:
                next_suggestion = st.session_state.remaining_recs.pop(0)
                st.session_state.feedback["disliked"].update(next_suggestion["CATEGORIES"].split(","))

                retry_prompt = f"""
                You are Street Fairy 🧚‍♀️. The last suggestion wasn't a hit.
                Here's another business to consider:

                - {next_suggestion['NAME']} ({next_suggestion['CATEGORIES']} in {next_suggestion['CITY']}, {next_suggestion['STATE']})

                Please describe it warmly and concisely without inventing anything.
                """
                with st.spinner("🧚‍♀️ Finding another magical place..."):
                    response = query_ollama(retry_prompt, model="mistral")

                st.session_state.chat_history.append({"role": "assistant", "content": response})
                st.rerun()  # Refresh the page to show new message
                return
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": "🧚‍♀️ No more suggestions left! Try a different query."})
                st.rerun()
                return

        # New query flow
        df=load_data_from_snowflake()
        with st.spinner("🧚‍♀️ Street Fairy is thinking..."):
            results = run_similarity_search(user_location,user_message,df)

        if results.empty:
            st.session_state.chat_history.append({"role": "assistant", "content": "⚠️ No good results found. Try something different?"})
            st.rerun()
            return

        top_results = results[:5]
        st.session_state.remaining_recs = results[5:]

        business_str = "\n".join([
            f"- {b['NAME']} ({b['CATEGORIES']} in {b.get('CITY', '')}, {b['STATE']})"
            for _, b in top_results.iterrows()
        ])

        recommendation_prompt = f"""
        You are Street Fairy 🧚‍♀️ suggesting lovely places.

        The user asked: "{user_message}"
        Here are 5 real businesses found:

        {business_str}

        ✅ Recommend 2-3 options warmly.
        ✅ Mention names, locations, and something special about them.
        🚫 Do not invent fake businesses.
        """

        try:
            with st.spinner("🧚‍♀️ Preparing magic suggestions..."):
                recommendation = query_ollama(recommendation_prompt, model="mistral")

            st.session_state.chat_history.append({"role": "assistant", "content": recommendation})
            st.rerun()

        except Exception as e:
            st.session_state.chat_history.append({"role": "assistant", "content": f"⚠️ Oops, Fairy magic failed: {e}"})
            st.rerun()

    # 🌟 Show preference-based recommendations
    st.session_state["user_location"] = user_location 
    
    display_preference_based_recommendations()