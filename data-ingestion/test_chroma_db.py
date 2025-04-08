import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ✅ Custom embedding function wrapper
class MyEmbeddingFunction:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def __call__(self, texts):
        return self.model.encode(texts).tolist()

# ✅ Initialize Chroma (persistent)
chroma_client = chromadb.PersistentClient(
    path=".chroma",
    settings=Settings(anonymized_telemetry=False)
)

# ✅ Create or reset the test collection
collection_name = "test_kb"
try:
    chroma_client.delete_collection(name=collection_name)
except:
    pass

collection = chroma_client.create_collection(
    name=collection_name,
    embedding_function=MyEmbeddingFunction()
)

# ✅ Add two simple docs
collection.add(
    documents=["The food at this restaurant is amazing!", "This place has terrible service."],
    ids=["doc1", "doc2"],
    metadatas=[{"sentiment": "positive"}, {"sentiment": "negative"}]
)

# ✅ Run a query
results = collection.query(
    query_texts=["I loved the food"],
    n_results=2
)

# ✅ Print results
print("🔍 Query Results:")
for doc, score in zip(results['documents'][0], results['distances'][0]):
    print(f"- {doc} (distance: {score:.4f})")