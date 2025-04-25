import streamlit as st
from utils.query import run_similarity_search, query_ollama
from utils.database import load_data_from_snowflake, save_preferences


def screen_2():
    st.title("🧚‍♀️Chat with the Fairy")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "remaining_recs" not in st.session_state:
        st.session_state.remaining_recs = []

    user_message = st.chat_input("What are you looking for?")

    if user_message:
        st.chat_message("user").markdown(user_message)
        st.session_state.chat_history.append({"role": "user", "content": user_message})

        if any(x in user_message.lower() for x in ["not a fan", "don't like", "dislike", "another one", "next"]):
            if st.session_state.remaining_recs:
                next_suggestion = st.session_state.remaining_recs.pop(0)
                st.session_state.feedback["disliked"].update(
                    map(str.strip, next_suggestion['CATEGORIES'].lower().split(","))
                )

                next_prompt = f"""
                You are Street Fairy \U0001f9da\ufe0f. The last place wasn't quite right.
                Here's another nearby business:

                - {next_suggestion['NAME']} ({next_suggestion['CATEGORIES']}, {next_suggestion.get('CITY', '')}, {next_suggestion['STATE']})

                Describe what makes it special.
                """
                response = query_ollama(next_prompt, model="mistral")
                with st.chat_message("assistant"):
                    st.markdown(response)
                st.session_state.chat_history.append({"role": "assistant", "content": response})
                return

        df = load_data_from_snowflake()
        results = run_similarity_search(query_input=user_message, df=df)

        if results.empty:
            st.chat_message("assistant").warning("⚠️ No results found. Try asking differently.")
            return

        top_result = results.iloc[0]
        st.session_state.remaining_recs = results.iloc[1:].to_dict(orient="records")

        business_str = f"- {top_result['NAME']} ({top_result['CATEGORIES']}, {top_result.get('CITY', '')}, {top_result['STATE']})"

        rec_prompt = f"""
        You are Street Fairy \U0001f9da\ufe0f helping users find places nearby.
        The user asked: "{user_message}"
        Here's a business we found:
        {business_str}
        Describe what makes it special.
        """

        recommendation = query_ollama(rec_prompt, model="mistral")

        with st.chat_message("assistant"):
            st.markdown(recommendation)
            st.markdown("What did you think of this suggestion? You can say something like 'I liked it' or 'Not for me'. ✨")

        st.session_state.chat_history.append({"role": "assistant", "content": recommendation})