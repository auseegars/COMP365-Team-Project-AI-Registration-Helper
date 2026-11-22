"""Hybrid elective recommender for Aggies Enroll.

Owner: Ryan Kevena.  Builds on: src/audit/degree_audit.py (Ayana Seegars: approved elective lists and
eligibility) and data/electives/ (the student survey).

Given a student profile and their interests (from the survey), it recommends electives that
  * still count toward the degree and whose prerequisites are met  -- the eligibility filter, taken
    straight from the degree audit's `elective_options` (unmet elective slots, courses takeable now);
  * match the student's interests  -- content similarity over the course title/department;
  * are liked by peers who share those interests  -- peer ratings from the survey.

Hybrid score = w_interest * interest_similarity + w_peer * peer_rating, both scaled to 0..1, ranked
over the eligible pool only.  Interest similarity uses sentence-transformer embeddings (the same model
as the information assistant) when the library and model are available, and otherwise falls back to a
dependency-free bag-of-words cosine, so the recommender still runs offline and in tests.

CLI:
    python src/electives/recommend.py data/profiles/schedule_demo_profiles.json SYN-CS-05 --interests cybersecurity,ai_ml
    python src/electives/recommend.py <profiles.json> <student_id> --top 5
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import degree_audit as da  # noqa: E402
import survey as sv  # noqa: E402

W_INTEREST = 0.6
W_PEER = 0.4
CURRICULA = ROOT / "data" / "curricula"


# ---------------------------------------------------------------- eligibility (from the degree audit)
def eligible_electives(profile, courses, lists, transfer_map=None):
    """Codes that fill an unmet elective slot and are takeable now, mapped to the slots they fill.

    Returns {code: [slot_id, ...]} using degree_audit.audit().elective_options, so eligibility (counts
    toward the degree + prerequisites met + not already taken/in progress) is decided by Ayana's engine,
    not re-implemented here.
    """
    major = profile["major"]
    curriculum = da.load_curriculum(CURRICULA / f"{major}.json")
    res = da.audit(profile, curriculum, courses, transfer_map or {}, lists)
    by_code = {}
    for slot_id, codes in res.elective_options.items():
        for code in codes:
            by_code.setdefault(da.norm(code), []).append(slot_id)
    return by_code, res


# ---------------------------------------------------------------- interest similarity
def _course_text(code, courses):
    title = courses.get(code, {}).get("title", "")
    dept = code.split()[0]
    return f"{dept} {title}"


class _Similarity:
    """Interest-to-course similarity, 0..1.  Uses embeddings if available, else bag-of-words cosine."""

    def __init__(self, codes, courses):
        self.codes = codes
        self.courses = courses
        self.model = self._try_model()
        if self.model is not None:
            texts = [_course_text(c, courses) for c in codes]
            self.vecs = dict(zip(codes, self.model.encode(texts, normalize_embeddings=True)))
        else:
            self.bags = {c: _bag(sv._words(_course_text(c, courses)) + list(sv.course_tags(courses.get(c, {}).get("title", ""))))
                         for c in codes}

    @staticmethod
    def _try_model():
        try:  # optional: same model as the information assistant
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer("all-MiniLM-L6-v2")
        except Exception:
            return None

    def score(self, code, interests):
        if self.model is not None:
            q = self.model.encode([", ".join(sv.TAG_LABELS.get(t, t) for t in interests)], normalize_embeddings=True)[0]
            v = self.vecs[code]
            return max(0.0, float(sum(a * b for a, b in zip(q, v))))
        q = _bag(sv.interest_text(interests))
        return _cosine(q, self.bags[code])


def _bag(words):
    b = {}
    for w in words:
        b[w] = b.get(w, 0) + 1
    return b


def _cosine(a, b):
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    return dot / (na * nb) if na and nb else 0.0


# ---------------------------------------------------------------- hybrid recommendation
def rank_pool(pool, interests, courses, responses, slots_of=None,
              top=None, w_interest=W_INTEREST, w_peer=W_PEER):
    """Score and rank an arbitrary candidate pool by the hybrid score (no eligibility check here).

    Shared by recommend() (which passes the eligible pool) and evaluate_recommender.py (which passes
    the full approved elective list).  Each result:
    {code, title, score, interest_similarity, peer_rating, n_ratings, slots, why}.
    """
    pool = [c for c in pool if c in courses]
    if not pool:
        return []
    sim = _Similarity(pool, courses)
    peer = sv.aggregate(responses, interests)       # peers who share an interest
    overall = sv.aggregate(responses)               # everyone (fallback)

    results = []
    for code in pool:
        isim = sim.score(code, interests) if interests else 0.0
        pr = peer.get(code) or overall.get(code)
        if pr:
            peer_scaled = (pr["mean"] - 1) / 4.0     # 1..5 -> 0..1
            n = pr["n"]
        else:
            peer_scaled, n = 0.5, 0                  # neutral when nobody has rated it
        score = w_interest * isim + w_peer * peer_scaled
        results.append({
            "code": code,
            "title": courses[code].get("title", ""),
            "score": round(score, 4),
            "interest_similarity": round(isim, 4),
            "peer_rating": round(pr["mean"], 2) if pr else None,
            "n_ratings": n,
            "slots": (slots_of or {}).get(code, []),
            "why": _why(code, interests, courses, isim, pr, n),
        })
    results.sort(key=lambda r: (-r["score"], r["code"]))
    return results[:top] if top else results


def recommend(profile, interests, courses, lists, responses, transfer_map=None,
              top=5, w_interest=W_INTEREST, w_peer=W_PEER):
    """Return the top eligible electives for a student, ranked by the hybrid score.

    The eligibility filter (what counts toward the degree and is takeable now) comes from the degree
    audit; ranking is done by rank_pool().  Returns (results, audit_result).
    """
    interests = list(interests or profile.get("interests", []))
    by_code, audit_res = eligible_electives(profile, courses, lists, transfer_map)
    pool = [c for c in by_code if c in courses]
    if not pool:
        return [], audit_res
    results = rank_pool(pool, interests, courses, responses, slots_of=by_code,
                        top=top, w_interest=w_interest, w_peer=w_peer)
    return results, audit_res


def _why(code, interests, courses, isim, pr, n):
    bits = []
    tags = sv.course_tags(courses.get(code, {}).get("title", "")) & set(interests)
    if tags:
        bits.append("matches your interest in " + ", ".join(sorted(sv.TAG_LABELS.get(t, t) for t in tags)))
    elif isim >= 0.3:
        bits.append("related to your interests")
    if pr and n:
        bits.append(f"rated {pr['mean']:.1f}/5 by {n} {'peer' if n == 1 else 'peers'}")
    bits.append("counts toward an open elective slot")
    return "; ".join(bits)


# ---------------------------------------------------------------- CLI
def _load_profile(profiles_path, student_id):
    data = json.loads(Path(profiles_path).read_text(encoding="utf-8"))
    profs = data["profiles"] if isinstance(data, dict) else data
    for p in profs:
        if p.get("student_id") == student_id:
            return p
    raise SystemExit(f"profile {student_id!r} not found in {profiles_path}")


def main(argv):
    ap = argparse.ArgumentParser(description="Recommend eligible electives for a student.")
    ap.add_argument("profiles")
    ap.add_argument("student_id")
    ap.add_argument("--interests", default="", help="comma-separated interest tags (overrides the profile)")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--json", action="store_true", help="print raw JSON")
    args = ap.parse_args(argv[1:])

    profile = _load_profile(args.profiles, args.student_id)
    interests = [t.strip() for t in args.interests.split(",") if t.strip()]
    courses = da.load_courses(ROOT / "data" / "courses.json")
    lists = da.load_lists(ROOT / "data" / "lists.json")
    transfer_map = da.load_transfer_map(ROOT / "data" / "transfer" / "transfer_map.json")
    responses = sv.load_responses()

    recs, _ = recommend(profile, interests, courses, lists, responses, transfer_map, top=args.top)

    if args.json:
        print(json.dumps(recs, indent=2))
        return 0
    who = args.student_id + (f" (interests: {', '.join(interests)})" if interests else "")
    print(f"Top {len(recs)} electives for {who}:\n")
    if not recs:
        print("  No eligible elective slots open for this student.")
        return 0
    for i, r in enumerate(recs, 1):
        pr = f"{r['peer_rating']}/5 (n={r['n_ratings']})" if r["peer_rating"] is not None else "no ratings yet"
        print(f"{i}. {r['code']}  {r['title']}")
        print(f"     score {r['score']:.2f}  |  interest {r['interest_similarity']:.2f}  |  peers {pr}")
        print(f"     {r['why']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
