"""Compare team retrievers on the checked-in expected-term questions."""

import argparse
import hashlib
import json
import re
from pathlib import Path

from advisor_hub.information import DATA, keyword_search, semantic_search

TOP_K = 3


def term_matches(term, text):
    return re.search(rf"(?<!\w){re.escape(term.casefold())}(?!\w)", text.casefold()) is not None


def evaluate_method(search, questions, top_k):
    rows = []
    for item in questions:
        ranked = search(item["question"], top_k=top_k)
        passages = []
        seen = set()
        all_terms = item["expected_terms"]
        for rank, passage in enumerate(ranked, start=1):
            matched = [term for term in all_terms if term_matches(term, passage["text"])]
            seen.update(matched)
            passages.append({
                "rank": rank, "title": passage["title"], "url": passage["source_url"],
                "matched_terms": matched, "score": round(passage["score"], 6),
                "passage_sha256": hashlib.sha256(passage["text"].encode("utf-8")).hexdigest(),
            })
        rows.append({
            "question": item["question"], "expected_terms": all_terms, "passages": passages,
            "missing_terms": [term for term in all_terms if term not in seen],
            "term_coverage": len(seen) / len(all_terms),
        })
    return {
        "status": "executed",
        "all_terms_at_k": sum(not row["missing_terms"] for row in rows),
        "mean_term_coverage_at_k": sum(row["term_coverage"] for row in rows) / len(rows),
        "questions": rows,
    }


def compare(top_k=TOP_K):
    corpus = (DATA / "chunks.json").read_bytes()
    question_data = (DATA / "evaluation_questions.json").read_bytes()
    questions = json.loads(question_data)

    def bm25(question, top_k):
        from src.information_assistant.bm25_baseline import bm25_search

        return bm25_search(question, top_k=top_k)

    results = {}
    for name, search in (("keyword_overlap", keyword_search), ("bm25", bm25), ("semantic", semantic_search)):
        try:
            results[name] = evaluate_method(search, questions, top_k)
        except (ImportError, OSError, RuntimeError, ValueError) as error:
            results[name] = {"status": "blocked", "reason": str(error)}
    return {
        "top_k": top_k, "question_count": len(questions), "chunk_count": len(json.loads(corpus)),
        "corpus_sha256": hashlib.sha256(corpus).hexdigest(),
        "question_set_sha256": hashlib.sha256(question_data).hexdigest(),
        "metric_note": "Case-insensitive whole-term matches in the union of retrieved passages. "
                       "Question fixtures contain expected terms and no relevance judgments. "
                       "Coverage measures a retrieval diagnostic, not answer accuracy.",
        "methods": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = compare()
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return int(any(method["status"] == "blocked" for method in report["methods"].values()))


if __name__ == "__main__":
    raise SystemExit(main())
