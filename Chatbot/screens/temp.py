import streamlit as st
from utils.query import run_similarity_search, query_ollama
from utils.database import load_data_from_snowflake
from utils.feedback import handle_feedback

def screen_2():
    st.title("🧚‍♀️Chat with the Fairy")

    # Initialize session state if not already initialized
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "remaining_recs" not in st.session_state:
        st.session_state.remaining_recs = []
    if "feedback_given" not in st.session_state:
        st.session_state.feedback_given = False
    if "feedback_status" not in st.session_state:
        st.session_state.feedback_status = None
    if "last_results" not in st.session_state:
        st.session_state.last_results = []
    if "user_info" not in st.session_state:
        st.session_state.user_info = {"user_id": "test_user"}  # replace as needed

    # Display chat history
    for message in st.session_state.chat_history:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
        else:
            st.chat_message("assistant").markdown(message["content"])

    # Show input box only after feedback has been given, or if no feedback expected yet
    show_query_input = (
        len(st.session_state.chat_history) == 0 or
        st.session_state.feedback_given
    )

    # Use a dynamic key for chat_input based on the feedback status
    if show_query_input:
        user_message_key = f"query_input_{st.session_state.feedback_given}"

        user_message = st.chat_input("What are you looking for?", key=user_message_key)

        if user_message:
            st.chat_message("user").markdown(user_message)
            st.session_state.chat_history.append({"role": "user", "content": user_message})

            # Fetch results based on user input
            df = load_data_from_snowflake()
            results = run_similarity_search(query_input=user_message, df=df)
            if results.empty:
                st.chat_message("assistant").warning("⚠️ No results found. Try asking differently.")
                return

            # Store all shown results for feedback use
            st.session_state.last_results = results.to_dict(orient="records")
            top_result = results.iloc[0]
            st.session_state.remaining_recs = results.iloc[1:].to_dict(orient="records")

            # Show business details
            business_str = f"- {top_result['NAME']} ({top_result['CATEGORIES']}, {top_result.get('CITY', '')}, {top_result['STATE']})"
            rec_prompt = f"""
            You are Street Fairy 🧚‍♀️ helping users find places nearby.
            The user asked: "{user_message}"
            Here's a business we found:
            {business_str}
            Describe what makes it special.
            """

            # Generate AI response
            recommendation = query_ollama(rec_prompt, model="mistral")
            st.session_state.chat_history.append({"role": "assistant", "content": recommendation})

            with st.chat_message("assistant"):
                st.markdown(recommendation)

            # Reset feedback state for new query/answer pair
            st.session_state.feedback_given = False
            st.session_state.feedback_status = None

    # Show feedback buttons only if feedback hasn't been given yet for current recommendation
    if st.session_state.last_results and not st.session_state.feedback_given:
        col1, col2 = st.columns(2)
        with col1:
            feedback_like = st.button("Like", key="like_button")
        with col2:
            feedback_dislike = st.button("Dislike", key="dislike_button")

        if feedback_like:
            # Handle "Like" feedback
            handle_feedback(
                is_liked=True,
                user_message=st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else "",
                suggestion=st.session_state.last_results[0],
                user_id=st.session_state.user_info["user_id"],
                last_results=st.session_state.last_results
            )
            # Mark feedback as given
            st.session_state.feedback_given = True
            st.session_state.feedback_status = "like"
            # Immediately show the next query box (no need for second click)
            st.success("You liked this suggestion!")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Glad you liked it! What else would you like to know?"
            })

            # Force a rerun to show the next query box immediately
            st.experimental_rerun()  # This ensures the UI is updated immediately

        elif feedback_dislike:
            # Handle "Dislike" feedback
            handle_feedback(
                is_liked=False,
                user_message=st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else "",
                suggestion=st.session_state.last_results[0],
                user_id=st.session_state.user_info["user_id"],
                last_results=st.session_state.last_results
            )
            # Mark feedback as given
            st.session_state.feedback_given = True
            st.session_state.feedback_status = "dislike"
            # Immediately show the next query box (no need for second click)
            st.warning("You disliked this suggestion!")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": "Sorry it wasn't helpful! What else can I help you with?"
            })

            # Force a rerun to show the next query box immediately
            st.experimental_rerun()  # This ensures the UI is updated immediately

    elif st.session_state.feedback_given:
        # After feedback is given, show the next input box for the next query
        st.chat_input("What are you looking for?")
