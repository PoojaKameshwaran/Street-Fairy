### ✅ street_fairy_demo.py (Enhanced with Location + Fallback + Hybrid Geotagging)

import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from math import radians, sin, cos, sqrt, atan2
import json
import googlemaps
import os
import re
import pgeocode

# -------------------------
# 0. Helper: Haversine distance
# -------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# -------------------------
# 1. Load Local LLM (phi-2 / falcon)
# -------------------------
@st.cache_resource(show_spinner=False)
def load_llm():
    model_name = "tiiuae/falcon-rw-1b"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=128)
    return HuggingFacePipeline(pipeline=pipe)

# -------------------------
# 2. Load ChromaDB as raw vectorstore (not just retriever)
# -------------------------
@st.cache_resource(show_spinner=False)
def load_vectorstore():
    embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Chroma(
        persist_directory=".chroma",
        collection_name="street_fairy_business_kb",
        embedding_function=embedding_fn
    )

# -------------------------
# 3. Load Google Maps Client
# -------------------------
@st.cache_resource(show_spinner=False)
def load_gmaps():
    with open("gmaps_api_key.txt", "r") as f:
        key = f.read().strip()
    return googlemaps.Client(key=key)

# -------------------------
# 4. RAG Chain Constructor
# -------------------------
def build_rag_chain(llm, retriever):
    prompt_template = PromptTemplate.from_template("""
You are Street Fairy, a helpful and friendly local guide.
Use the following business information to answer the user's question.

{context}

User's question: {question}

Respond conversationally and include specific places where applicable.
""")
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt_template}
    )

# -------------------------
# 5. Streamlit UI
# -------------------------
st.set_page_config(page_title="Street Fairy 🧚", layout="wide")
st.title("🧚 Street Fairy - You name it, the fairy will find it!")

st.markdown("Enter a zipcode or a general location in your query, and I'll find nearby places for you ✨")
query = st.text_input("What are you looking for today?")

lat, lon = None, None
zipcode_found = None

if query:
    # Try ZIP extraction
    zip_match = re.search(r"\b\d{5}\b", query)
    if zip_match:
        zipcode_found = zip_match.group()
        nomi = pgeocode.Nominatim("us")
        location = nomi.query_postal_code(zipcode_found)
        lat, lon = location.latitude, location.longitude
    else:
        # Try geocoding general location
        gmaps = load_gmaps()
        geo_result = gmaps.geocode(query)
        if geo_result:
            geo = geo_result[0]["geometry"]["location"]
            lat, lon = geo["lat"], geo["lng"]

if query:
    with st.spinner("Street Fairy is finding the best spots..."):
        vectordb = load_vectorstore()
        all_results = vectordb.similarity_search_with_score(query, k=30)

        # Filter by distance
        if lat and lon:
            filtered = []
            for doc, score in all_results:
                meta = doc.metadata
                try:
                    dist = haversine(lat, lon, float(meta.get("latitude")), float(meta.get("longitude")))
                    if dist <= 10:  # km radius
                        doc.metadata["distance_km"] = round(dist, 2)
                        filtered.append((doc, score))
                except:
                    continue
        else:
            filtered = all_results[:5]  # no filtering if no location

        # Fallback to Google Maps if needed
        if len(filtered) == 0 and lat and lon:
            st.info("No local matches found — asking Google Maps for help ✨")
            gmaps = load_gmaps()
            fallback = gmaps.places_nearby(location=(lat, lon), radius=5000, keyword=query)
            response = f"Found {len(fallback['results'])} results via Google Maps:\n\n"
            for place in fallback['results'][:3]:
                response += f"\n🏢 {place['name']}\n📍 {place['vicinity']}\n⭐ Rating: {place.get('rating', 'N/A')}\n"
        else:
            # Use LangChain RAG
            llm = load_llm()
            retriever = vectordb.as_retriever(search_kwargs={"k": 5})
            rag = build_rag_chain(llm, retriever)
            response = rag.run(query)

    st.success("Here are some magical suggestions ✨")
    st.write(response)

st.caption("Built with ❤️")
