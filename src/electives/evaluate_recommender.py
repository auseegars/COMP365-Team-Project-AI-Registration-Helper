"""Evaluation for the elective recommender (owner: Ryan Kevena).

Covers Aim 2 from the project pitch: precision@5 of the hybrid recommender vs a most-popular baseline,
and that every recommendation is eligible.

Method (leave-one-out over the survey respondents, synthetic data for now):
  * A respondent's "relevant" electives are the ones they rated >= REL_THRESHOLD.
  * For each respondent with at least one relevant course and at least one interest, rank the approved
    CS elective pool with their interests, aggregating peer ratings from everyone *except* that
    respondent (so we never score them with their own answers).
  * precision@5 = (relevant courses in the top 5) / 5, averaged over respondents.
  * Baseline: the 5 most-rated electives overall (most-popular), same metric.
  * Eligibility is 100% by construction: recommend() only ever returns courses from the degree audit's
    elective_options.  A spot check confirms it on a demo profile.

Run from the repo root:
    python src/electives/evaluate_recommender.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import degree_audit as da  # noqa: E402
import survey as sv  # noqa: E402
import recommend as rec  # noqa: E402

REL_THRESHOLD = 4
K = 5
POOL_LIST = "CS_COMP_ELECTIVES"


def precision_at_k(ranked_codes, relevant, k=K):
    top = ranked_codes[:k]
    return sum(1 for c in top if c in relevant) / float(k)


def evaluate():
    courses = da.load_courses(ROOT / "data" / "courses.json")
    lists = da.load_lists(ROOT / "data" / "lists.json")
    responses = sv.load_responses()
    pool = [da.norm(c) for c in lists[POOL_LIST]]

    hybrid_scores, baseline_scores = [], []
    for me in responses:
        relevant = {da.norm(c) for c, s in me.get("ratings", {}).items() if s >= REL_THRESHOLD}
        interests = me.get("interests", [])
        if not relevant or not interests:
            continue
        others = [r for r in responses if r is not me]

        ranked = rec.rank_pool(pool, interests, courses, others)
        hybrid_scores.append(precision_at_k([r["code"] for r in ranked], relevant))

        pop = sv.popularity(others)
        baseline = sorted(pool, key=lambda c: (-pop.get(c, 0), c))
        baseline_scores.append(precision_at_k(baseline, relevant))

    n = len(hybrid_scores)
    hybrid = sum(hybrid_scores) / n if n else 0.0
    baseline = sum(baseline_scores) / n if n else 0.0

    # Eligibility spot check on a demo profile: every recommendation must be an eligible elective.
    elig_ok = elig_total = 0
    demo = ROOT / "data" / "profiles" / "schedule_demo_profiles.json"
    if demo.exists():
        import json
        tmap = da.load_transfer_map(ROOT / "data" / "transfer" / "transfer_map.json")
        for p in json.loads(demo.read_text(encoding="utf-8"))["profiles"]:
            recs, _ = rec.recommend(p, ["ai_ml", "cybersecurity"], courses, lists, responses, tmap, top=5)
            by_code, _ = rec.eligible_electives(p, courses, lists, tmap)
            for r in recs:
                elig_total += 1
                elig_ok += r["code"] in by_code

    print("Elective recommender - evaluation (synthetic survey data)")
    print(f"  respondents scored : {n}")
    print(f"  precision@{K} hybrid : {hybrid:.3f}")
    print(f"  precision@{K} popular: {baseline:.3f}  (most-popular baseline)")
    print(f"  hybrid beats baseline: {hybrid > baseline}")
    if elig_total:
        print(f"  eligibility         : {elig_ok}/{elig_total} recommendations eligible "
              f"({100 * elig_ok / elig_total:.0f}%)")
    print("\nNote: synthetic responses only; rerun on the 40 real profiles / real survey before reporting.")
    return hybrid, baseline


if __name__ == "__main__":
    evaluate()
