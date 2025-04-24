import chromadb

client = chromadb.PersistentClient(path=".chroma")
collection = client.get_collection("street_fairy_business_kb")

print("Document count:", collection.count())
