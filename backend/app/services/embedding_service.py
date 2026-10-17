from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

@lru_cache(maxsize=1)
def model():
    return SentenceTransformer(MODEL_NAME)

def embed(texts):
    vectors = model().encode(texts, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
    return np.asarray(vectors, dtype="float32")
