# app/llm_loop.py

import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import NotFound
from config import LLM_MODEL

def init_dialog():
    """Initialize empty chat history."""
    if "dialog" not in st.session_state:
        st.session_state.dialog = []

def append_user(msg: str):
    st.session_state.dialog.append({"role":"user", "content":msg})

def append_bot(msg: str):
    st.session_state.dialog.append({"role":"assistant", "content":msg})

def _list_supported_models() -> list[str]:
    genai.configure(api_key=st.secrets["google"]["api_key"])
    models = []
    for m in genai.list_models():
        if "generateContent" in getattr(m, "supported_generation_methods", []) \
           and "vision" not in m.name.lower():
            models.append(m.name)
    return models

def ask_llm() -> str:
    """
    Send the entire dialog to Gemini and get the next turn.
    """
    genai.configure(api_key=st.secrets["google"]["api_key"])
    supported = _list_supported_models()
    if not supported:
        st.error("⚠️ No valid Gemini models available.")
        return ""

    # choose or fallback
    name = LLM_MODEL if LLM_MODEL in supported else supported[0]
    if name != LLM_MODEL:
        st.warning(f"Model '{LLM_MODEL}' unavailable; using '{name}' instead.")
    model = genai.GenerativeModel(model_name=name)

    # build a single string with roles so Gemini sees the back‑and‑forth
    convo = ""
    for m in st.session_state.dialog:
        role = "User" if m["role"]=="user" else "Assistant"
        convo += f"{role}: {m['content']}\n"
    convo += "Assistant:"  # prompt model to continue as assistant

    try:
        resp = model.generate_content(convo)
    except NotFound:
        # optionally retry on a flash model...
        flash = next((m for m in supported if "flash" in m.lower()), None)
        if flash and flash!=name:
            st.warning(f"Retrying with {flash}")
            model = genai.GenerativeModel(model_name=flash)
            resp = model.generate_content(convo)
        else:
            st.error("No fallback model; aborting.")
            return ""

    return resp.text
