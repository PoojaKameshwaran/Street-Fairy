from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

embedding_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vectorstore = Chroma(
    collection_name="street_fairy_kb",
    persist_directory=".chroma",
    embedding_function=embedding_fn
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 5})