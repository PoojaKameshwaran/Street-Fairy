import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

# Connect to the local persistent vector DB
chroma_client = chromadb.PersistentClient(path=".chroma")

# Use the same embedding function as during ingestion
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get the collection
collection = chroma_client.get_or_create_collection(
    name="street_fairy_business_kb",
    embedding_function=embedding_fn
)

while(True):

    # 🔍 Your natural language query
    query = input("Ask Street Fairy: ")

    # Run semantic search
    results = collection.query(
        query_texts=[query],
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
    if(ready == "no" or ready == 'No'):
        break