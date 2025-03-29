import streamlit as st
from snowflake.snowpark.context import get_active_session

session = get_active_session()

st.set_page_config(page_title="💡 AI-Powered Business Recommender", layout="wide")
st.title("🔍 STREET FAIRY - Business Recommendation Assistant")
st.markdown("Describe what you're looking for, and get smart suggestions based on real reviews.")

user_query = st.text_input("📝 What are you looking for?", placeholder="e.g., best Italian food in LA")

if user_query:
    with st.spinner("🤖 Understanding your query..."):

        # Step 1: Extract topic using LLM
        extract_sql = f"""
            SELECT snowflake.cortex.complete(
                'snowflake-arctic',
                'Given this user query: "{user_query}", extract a single keyword or phrase that best represents the business type or theme to help match Yelp reviews. Return only that.'
            ) AS keyword
        """
        keyword = session.sql(extract_sql).collect()[0]['KEYWORD'].strip('"').strip()

        st.success(f"🔑 Interpreted topic: **{keyword}**")

        # Step 2: Fetch top 6 reviews containing that keyword
        reviews_sql = f"""
            SELECT business_id, text AS review_text, stars
            FROM STREET_FAIRY.PUBLIC.RELEVANT_REVIEWS
            WHERE LOWER(text) LIKE '%{keyword.lower()}%'
            LIMIT 6
        """
        reviews_df = session.sql(reviews_sql).to_pandas()

        if reviews_df.empty:
            st.warning("⚠️ No matching reviews found.")
        else:
            # Step 3: Join with business table
            business_ids = tuple(reviews_df['BUSINESS_ID'].unique())
            business_id_list = ",".join(f"'{bid}'" for bid in business_ids)

            business_sql = f"""
                SELECT business_id, name, city, state
                FROM STREET_FAIRY.PUBLIC.FILTERED_BUSINESSES
                WHERE business_id IN ({business_id_list})
            """
            business_df = session.sql(business_sql).to_pandas()
            merged_df = reviews_df.merge(business_df, on="BUSINESS_ID", how="left")

            # Step 4: Build summarized prompt for LLM
            rows_for_llm = ""
            for i, row in merged_df.iterrows():
                # Truncate long review text to avoid token overflow
                review_text = row['REVIEW_TEXT']
                if len(review_text) > 400:
                    review_text = review_text[:400] + "..."

                rows_for_llm += f"""
Review {i+1}:
Business: {row['NAME']} ({row['CITY']}, {row['STATE']})
Stars: {row['STARS']}
Review: {review_text}
"""

            prompt = f"""
You are a helpful assistant recommending businesses based on user reviews.

User query: "{user_query}"

Here are some matching reviews:
{rows_for_llm}

Choose the top 3 most suitable businesses and summarize why each one is recommended.

Format your answer in Markdown.
            """

            # Step 5: Run Snowflake Cortex LLM
            final_sql = f"""
                SELECT snowflake.cortex.complete('snowflake-arctic', $$ {prompt} $$) AS response
            """
            llm_output = session.sql(final_sql).collect()[0]['RESPONSE']
            st.markdown("### 💡 Top Recommendations")
            st.markdown(llm_output)

else:
    st.info("Enter a request above to get recommendations from real Yelp reviews.")
