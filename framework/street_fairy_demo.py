### ✅ street_fairy_demo.py
# One-file working demo: Streamlit + LangChain + ChromaDB + Local LLM (phi-2)

import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
# -------------------------
# 1. Load Local LLM (phi-2)
# -------------------------
@st.cache_resource(show_spinner=False)
def load_llm():
    model_name = "tiiuae/falcon-rw-1b"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(model_name)
    pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)
    return HuggingFacePipeline(pipeline=pipe)

# -------------------------
# 2. Load ChromaDB Retriever
# -------------------------
@st.cache_resource(show_spinner=False)
def load_retriever():
    embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectordb = Chroma(
        persist_directory=".chroma",
        collection_name="street_fairy_business_kb",
        embedding_function=embedding_fn
    )
    return vectordb.as_retriever(search_kwargs={"k": 5})

# -------------------------
# 3. LangChain RAG Pipeline
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
# 4. Streamlit UI
# -------------------------
st.set_page_config(page_title="Street Fairy 🧚", layout="wide")
st.title("🧚 Street Fairy - You name it, the fairy will find it!")
st.markdown("Ask me anything about local places to visit!")

query = st.text_input("What are you looking for today?")

if query:
    with st.spinner("Street Fairy is finding the best spots..."):
        llm = load_llm()
        retriever = load_retriever()
        rag = build_rag_chain(llm, retriever)

        response = rag.run(query)

    st.success("Here are some magical suggestions ✨")
    st.write(response)

st.caption("Built with ❤️ using LangChain + ChromaDB + Transformers")