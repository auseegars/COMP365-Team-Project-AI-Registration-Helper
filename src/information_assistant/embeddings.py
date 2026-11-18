# Owner: Kamryn Schmidt


import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "information_assistant"

CHUNKS_FILE = DATA / "chunks.json"
EMBEDDINGS_FILE = DATA / "embeddings.npy"

MODEL_NAME = "all-MiniLM-L6-v2"


def build_index():
    chunks = json.loads(
        CHUNKS_FILE.read_text(encoding="utf-8")
    )

    if not chunks:
        raise ValueError("No chunks found. Run chunk.py first.")

    model = SentenceTransformer(MODEL_NAME)

    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    np.save(EMBEDDINGS_FILE, embeddings)

    print(f"Created embeddings for {len(chunks)} chunks")
    print(f"Embedding dimensions: {embeddings.shape[1]}")
    print(f"Saved to {EMBEDDINGS_FILE}")


if __name__ == "__main__":
    build_index()
