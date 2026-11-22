# Owner: Kamryn Schmidt


import json
from pathlib import Path

try:
    from .retrieve import search
    from .bm25_baseline import bm25_search
except ImportError:
    from retrieve import search
    from bm25_baseline import bm25_search

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "information_assistant"

QUESTIONS = DATA / "evaluation_questions.json"


def matches_expected_terms(results, terms):
    if not results:
        return False

    top_text = results[0]["text"].lower()

    return all(term.lower() in top_text for term in terms)


def evaluate():
    questions = json.loads(
        QUESTIONS.read_text(encoding="utf-8")
    )

    semantic_correct = 0
    bm25_correct = 0

    print("\nRETRIEVAL COMPARISON")
    print("-" * 65)

    for item in questions:
        question = item["question"]
        terms = item["expected_terms"]

        semantic_results = search(question, top_k=3)
        bm25_results = bm25_search(question, top_k=3)

        semantic_hit = matches_expected_terms(
            semantic_results, terms
        )
        bm25_hit = matches_expected_terms(
            bm25_results, terms
        )

        semantic_correct += int(semantic_hit)
        bm25_correct += int(bm25_hit)

        print(f"\nQuestion: {question}")
        print(f"Semantic: {'PASS' if semantic_hit else 'FAIL'}")
        print(f"BM25: {'PASS' if bm25_hit else 'FAIL'}")

    total = len(questions)

    print("\nFINAL RESULTS")
    print("-" * 65)
    print(f"Questions evaluated: {total}")
    print(
        f"Semantic term-match rate: "
        f"{semantic_correct / total:.1%}"
    )
    print(
        f"BM25 term-match rate: "
        f"{bm25_correct / total:.1%}"
    )


if __name__ == "__main__":
    evaluate()
