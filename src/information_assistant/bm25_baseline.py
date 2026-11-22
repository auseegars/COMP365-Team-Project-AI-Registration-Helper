# Owner: Kamryn Schmidt


import json
import re
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "information_assistant"


def tokenize(text):
    return re.findall(r"\b\w+\b", text.lower())


def bm25_search(question, top_k=3):
    chunks = json.loads(
        (DATA / "chunks.json").read_text(encoding="utf-8")
    )

    if not chunks:
        return []

    corpus = [tokenize(chunk["text"]) for chunk in chunks]
    model = BM25Okapi(corpus)

    scores = model.get_scores(tokenize(question))
    indices = np.argsort(scores)[::-1][:top_k]

    results = []

    for index in indices:
        if scores[index] <= 0:
            continue

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

    for number, result in enumerate(
        bm25_search(question), start=1
    ):
        print(f"\n--- BM25 Result {number} ---")
        print(f"Score: {result['score']:.3f}")
        print(f"Source: {result['source_url']}")
        print(f"Text: {result['text'][:500]}")
