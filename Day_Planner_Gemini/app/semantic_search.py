# app/semantic_search.py

from sentence_transformers import SentenceTransformer
import numpy as np

_model = SentenceTransformer("all-mpnet-base-v2")

def semantic_search(query: str, df, embeddings: np.ndarray, index, top_k: int = 30):
    """
    Encode query, search the top_k vectors, return matching rows.
    Default top_k=30 per your requirement.
    """
    qvec = _model.encode([query], convert_to_numpy=True).astype("float32")
    _, idxs = index.search(qvec, top_k)
    return df.iloc[idxs[0]].copy()
