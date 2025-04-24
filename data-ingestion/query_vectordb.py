import chromadb
from sentence_transformers import SentenceTransformer

# Custom embedding function (same as used during ingestion)
class MyEmbeddingFunction:
    def __init__(self):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def __call__(self, texts):
        return self.model.encode(texts).tolist()

# Connect to local persistent ChromaDB
chroma_client = chromadb.PersistentClient(path=".chroma")

# Use no internal embedding since we precompute
collection = chroma_client.get_or_create_collection(
    name="street_fairy_business_kb",
    embedding_function=None  # Disables internal embedding; we'll embed manually
)

# Instantiate our embedding function
embedding_fn = MyEmbeddingFunction()

while True:
    # 🔍 Get user query
    query = input("Ask Street Fairy: ")

    # Embed the query using the same model
    embedded_query = embedding_fn([query])

    # Run semantic search using the precomputed query embedding
    results = collection.query(
        query_embeddings=embedded_query,
        n_results=5,
        include=["documents", "metadatas", "distances"]
    )

    # Print results
    print("\n🎯 Top Results:")
    for i, (doc, meta, score) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0]), 1):
        print(f"\n#{i}")
        print("📄", doc.strip())
        print("📎 Categories:", meta.get("categories"))
        print("📏 Similarity Score:", round(score, 4))

    ready = input("Do you want to ask the fairy anything else? Yes or No\n")
    if ready.lower() == "no":
        break
