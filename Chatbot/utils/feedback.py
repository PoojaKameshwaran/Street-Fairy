import streamlit as st
from utils.database import save_preferences  # We will call save_preferences from database.py

# Function to handle user feedback (like or dislike)
def handle_feedback(is_liked, user_message, suggestion, user_id, last_results):
    if is_liked:
        # Extract all unique categories from all shown business results
        all_categories = set()
        for business in last_results:
            cats = [c.strip().lower() for c in business.get('CATEGORIES', '').split(',')]
            all_categories.update(cats)
        all_categories.discard('')  # Remove empty strings if any

        st.session_state.feedback["liked"].update(all_categories)
        st.success("Thank you for the feedback! Glad you liked it.")

        # Update user preferences in Snowflake with all unique categories
        save_preferences(user_id, "like", list(all_categories))

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "You liked this suggestion!"
        })
        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "Glad you liked our suggestion! What else are you looking for?"
        })

    else:
        disliked_categories = [c.strip().lower() for c in suggestion['CATEGORIES'].split(",")]
        st.session_state.feedback["disliked"].update(disliked_categories)
        st.warning("Sorry that you didn't like it. Let's refine the suggestion.")

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": "You disliked this suggestion! "
        })

        refined_preference = st.chat_input("Can you give your preferences? (e.g., 'Italian, vegetarian, near park')")

        if refined_preference:
            refined_preference_list = [p.strip() for p in refined_preference.split(",")]
            save_preferences(user_id, "dislike", refined_preference_list)
            st.success(f"Your preferences have been updated with: {refined_preference}")
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"Got it! Your preferences have been updated. Are you looking for anything else?"
            })
        else:
            st.warning("Please provide more details to refine the suggestion.")
