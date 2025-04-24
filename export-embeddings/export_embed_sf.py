import chromadb
import pandas as pd
import numpy as np
import json
from snowflake.snowpark import Session

# ---------------------
# Step 1: Load from ChromaDB
# ---------------------
print("📥 Loading ChromaDB collection...")

client = chromadb.PersistentClient(path=".chroma")
collection = client.get_collection("street_fairy_business_kb")

results = collection.get(include=["documents", "metadatas", "embeddings"], limit=999999)

# ---------------------
# Step 2: Convert to Pandas DataFrame
# ---------------------
print("🧹 Structuring data...")

df = pd.DataFrame({
    "id": results["ids"],
    "text": results["documents"],
    "embedding": results["embeddings"],
    "categories": [meta.get("categories", "") for meta in results["metadatas"]],
    "latitude": [meta.get("latitude") for meta in results["metadatas"]],
    "longitude": [meta.get("longitude") for meta in results["metadatas"]],
    "stars": [meta.get("stars") for meta in results["metadatas"]],
    "review_count": [meta.get("review_count") for meta in results["metadatas"]],
    "city": [meta.get("city") for meta in results["metadatas"]],
    "state": [meta.get("state") for meta in results["metadatas"]],
})

# ---------------------
# Step 3: Flatten Embeddings
# ---------------------
print("📐 Flattening embeddings...")

embedding_matrix = np.array(df["embedding"].tolist())  # shape: (n_samples, n_dims)
embedding_df = pd.DataFrame(embedding_matrix, columns=[f"emb_{i}" for i in range(embedding_matrix.shape[1])])

# Drop original embedding column and merge
df = pd.concat([df.drop(columns=["embedding"]), embedding_df], axis=1)

# ---------------------
# Step 4: Type Casting (Snowflake-safe)
# ---------------------
print("🔢 Casting columns...")

df["latitude"] = df["latitude"].astype(float)
df["longitude"] = df["longitude"].astype(float)
df["stars"] = df["stars"].astype(float)
df["review_count"] = df["review_count"].fillna(0).astype(int)

# ---------------------
# Step 5: Upload to Snowflake
# ---------------------
print("🚀 Uploading to Snowflake...")

# Load Snowflake credentials
with open("key.json") as f:
    creds = json.load(f)

session = Session.builder.configs(creds).create()

# Push to Snowflake

# Clean and lowercase columns
df.columns = [col.replace('"', '').strip().lower() for col in df.columns]

snow_df = session.create_dataframe(df)
snow_df.write.mode("overwrite").save_as_table("STREET_FAIRY_VECTOR_TABLE")

print(f"✅ Successfully pushed {len(df)} records to 'STREET_FAIRY_VECTOR_TABLE'")