import streamlit as st
from utils.query import run_similarity_search, query_ollama
from utils.database import load_data_from_snowflake
from utils.feedback import handle_feedback

def screen_2():
    st.title("🧚‍♀️Chat with the Fairy")

    # Initialize session state
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

    # Show input box *only after feedback has been given, or if no feedback expected yet*
    show_query_input = (
        len(st.session_state.chat_history) == 0 or
        st.session_state.feedback_given
    )
    if show_query_input:
        user_message = st.chat_input("What are you looking for?")

        if user_message:
            st.chat_message("user").markdown(user_message)
            st.session_state.chat_history.append({"role": "user", "content": user_message})

            df = load_data_from_snowflake()
            results = run_similarity_search(query_input=user_message, df=df)
            if results.empty:
                st.chat_message("assistant").warning("⚠️ No results found. Try asking differently.")
                return

            st.session_state.last_results = results.to_dict(orient="records")
            top_result = results.iloc[0]
            st.session_state.remaining_recs = results.iloc[1:].to_dict(orient="records")

            business_str = f"- {top_result['NAME']} ({top_result['CATEGORIES']}, {top_result.get('CITY', '')}, {top_result['STATE']})"
            rec_prompt = f"""
            You are Street Fairy 🧚‍♀️ helping users find places nearby.
            The user asked: "{user_message}"
            Here's a business we found:
            {business_str}
            Describe what makes it special.
            """

            recommendation = query_ollama(rec_prompt, model="mistral")
            st.session_state.chat_history.append({"role": "assistant", "content": recommendation})

            with st.chat_message("assistant"):
                st.markdown(recommendation)

            # Now, we expect feedback for this query/answer
            st.session_state.feedback_given = False
            st.session_state.feedback_status = None

    # Show feedback buttons if feedback not yet given for last answer
    if st.session_state.last_results and not st.session_state.feedback_given:
        col1, col2 = st.columns(2)
        with col1:
            feedback_like = st.button("Like", key="like_button")
        with col2:
            feedback_dislike = st.button("Dislike", key="dislike_button")

        if feedback_like:
            #feedback_like=False
            handle_feedback(
                is_liked=True,
                user_message=st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else "",
                suggestion=st.session_state.last_results[0],
                user_id=st.session_state.user_info["user_id"],
                last_results=st.session_state.last_results
            )
            st.session_state.feedback_given = True
            st.session_state.feedback_status = "like"

        elif feedback_dislike:
            handle_feedback(
                is_liked=False,
                user_message=st.session_state.chat_history[-2]["content"] if len(st.session_state.chat_history) >= 2 else "",
                suggestion=st.session_state.last_results[0],
                user_id=st.session_state.user_info["user_id"],
                last_results=st.session_state.last_results
            )
            st.session_state.feedback_given = True
            st.session_state.feedback_status = "dislike"

    elif st.session_state.feedback_given:
        # Show feedback status and then user can submit another query
        if st.session_state.feedback_status == "like":
            st.success("You liked this suggestion!")
        elif st.session_state.feedback_status == "dislike":
            st.warning("You disliked this suggestion!")
        # Next input box appears automatically on next rerun as per logic above

