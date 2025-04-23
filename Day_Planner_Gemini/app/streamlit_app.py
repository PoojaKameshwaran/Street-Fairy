# app/streamlit_app.py

import sys, os
import streamlit as st

# ── 1) Put app/, scripts/, config/ on sys.path ──────────────────────────────
THIS_DIR     = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
for p in (
    THIS_DIR,
    os.path.join(PROJECT_ROOT, "scripts"),
    os.path.join(PROJECT_ROOT, "config"),
):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── 2) Imports ─────────────────────────────────────────────────────────────────
from snowflake_loader    import load_businesses_and_index
from geocode_utils       import get_coordinates, filter_by_radius
from semantic_search     import semantic_search
from llm_loop            import init_dialog, ask_llm, append_user, append_bot
from config              import SEARCH_RADIUS_MILES

# ── 3) Bootstrap & state init ─────────────────────────────────────────────────
st.set_page_config(page_title="Smart Yelp Planner", layout="wide")
df, embeddings, index = load_businesses_and_index()
init_dialog()

st.title("📍 Smart Yelp Business Planner")

# ── 4) Ask once for the city/state context ────────────────────────────────────
col1, col2 = st.columns(2)
user_city  = col1.text_input("Enter your city:", key="user_city")
user_state = col2.text_input("Enter your state:", key="user_state")
if not user_city or not user_state:
    st.warning("Please provide both city and state to begin planning.")
    st.stop()

# ── 5) Initialize rounds & store for the top‐1 picks ─────────────────────────
if "round" not in st.session_state:
    st.session_state.round     = 1
    st.session_state.recorded  = []
    append_bot(
        f"👋 Welcome! We're building your day in **{user_city}, {user_state}**. "
        "Tell me the first kind of place you'd like to visit."
    )

# ── 6) Render full conversation ───────────────────────────────────────────────
for msg in st.session_state.dialog:
    who = "You" if msg["role"] == "user" else "AI"
    st.markdown(f"**{who}:** {msg['content']}")

# ── 7) One input for each step ─────────────────────────────────────────────────
reply = st.text_input(f"Step {st.session_state.round}/5 — your reply:", key="planner_input")
if reply:
    # build the full query including city/state
    composite = f"{reply} in {user_city} {user_state}"
    append_user(composite)

    # run semantic search on the composite query
    hits   = semantic_search(composite, df, embeddings, index, top_k=30)
    center = get_coordinates(user_city, user_state)
    nearby = filter_by_radius(hits, center, SEARCH_RADIUS_MILES)

    if nearby.empty:
        append_bot(f"😕 No matches found for '{composite}'. Let's move on.")
        st.session_state.recorded.append(None)
    else:
        # pick & display top 3
        top3 = nearby.sort_values("STARS", ascending=False).head(3)
        rec_lines = []
        for i, row in enumerate(top3.itertuples(), start=1):
            rec_lines.append(
                f"{i}. **{row.NAME}** — {row.CITY}, {row.STATE} — ⭐ {row.STARS}"
            )
        append_bot(
            f"For '{composite}', here are my top 3:\n\n" + "\n".join(rec_lines)
        )

        # record only the #1 pick for itinerary
        st.session_state.recorded.append(top3.iloc[0].NAME)

    # advance or finalize
    if st.session_state.round < 5:
        st.session_state.round += 1
        append_bot(f"Great! Where would you like to go next? ({st.session_state.round}/5)")
    else:
        # build the final itinerary prompt using the five recorded names
        picks = [n for n in st.session_state.recorded if n]
        append_bot("Awesome—now let me craft your full day itinerary!")
        prompt = (
            f"I have selected these five places in {user_city}, {user_state}:\n"
            f"{picks}\n\n"
            "Please draft a detailed hourly plan for a single day visiting each in order, "
            "including travel and tips."
        )
        append_user(prompt)
        plan = ask_llm()
        append_bot(plan)
        st.subheader("🗓️ Your Full Day Itinerary")
        st.write(plan)
        st.session_state.round += 1

    # rerun so new messages appear immediately
    st.experimental_rerun()
