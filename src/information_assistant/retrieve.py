# Owner: Kamryn Schmidt


import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "information_assistant"

MODEL_NAME = "all-MiniLM-L6-v2"


def search(question, top_k=3):
    chunks = json.loads(
        (DATA / "chunks.json").read_text(encoding="utf-8")
    )

    embeddings = np.load(DATA / "embeddings.npy")

    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding counts do not match")

    model = SentenceTransformer(MODEL_NAME)

    question_embedding = model.encode(
        question,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )

    # Both question and document vectors are normalized.
    # Dot product therefore measures cosine similarity.
    scores = embeddings @ question_embedding

    top_indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in top_indices:
        chunk = chunks[int(index)]

        results.append({
            "score": float(scores[index]),
            "text": chunk["text"],
            "source_url": chunk["source_url"],
            "title": chunk["title"],
        })

    return results


if __name__ == "__main__":
    question = input("Ask a registration question: ").strip()

    if not question:
        print("Please enter a question.")
    else:
        results = search(question)

        for number, result in enumerate(results, start=1):
            print(f"\n--- Result {number} ---")
            print(f"Similarity: {result['score']:.3f}")
            print(f"Source: {result['source_url']}")
            print(f"Text: {result['text'][:700]}")
