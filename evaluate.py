"""
COMP 365 team project - evaluation metrics (Evaluation lead: Jarren Woodward)

One small script that scores each component against the targets in the pitch:
  triage  : macro-F1 (>= 0.80) and urgent recall (>= 95%)      [Aim 4]
  qa      : answered correctly (>= 85%) and cited correctly (>= 90%) [Aim 3]
  recs    : precision@5 vs a most-popular baseline, eligibility 100% [Aim 2]
  sched   : valid schedules 100%, graduation term matches/beats advisor >= 90% [Aim 1]

Only the standard library is used, so it runs anywhere (Colab, Docker, laptop).

Usage:
  python evaluate.py selftest
  python evaluate.py triage  triage_preds.csv
  python evaluate.py qa      qa_results.csv
  python evaluate.py recs    recs.json
  python evaluate.py sched   schedules.csv

Input formats are described above each function.
"""
import csv
import json
import sys
from collections import defaultdict


# ---------- Aim 4: triage ----------
# CSV columns: id, true_topic, pred_topic, true_urgent, pred_urgent   (urgent = 1/0)
def macro_f1(true, pred):
    labels = sorted(set(true) | set(pred))
    f1s = {}
    for lab in labels:
        tp = sum(1 for t, p in zip(true, pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(true, pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(true, pred) if t == lab and p != lab)
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s[lab] = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return sum(f1s.values()) / len(f1s), f1s


def score_triage(rows):
    topic_f1, per_class = macro_f1([r["true_topic"] for r in rows],
                                   [r["pred_topic"] for r in rows])
    urgent = [r for r in rows if int(r["true_urgent"]) == 1]
    caught = sum(1 for r in urgent if int(r["pred_urgent"]) == 1)
    urgent_recall = caught / len(urgent) if urgent else float("nan")
    return {"n": len(rows), "macro_f1": topic_f1, "per_class_f1": per_class,
            "urgent_n": len(urgent), "urgent_recall": urgent_recall,
            "meets_f1_target": topic_f1 >= 0.80,
            "meets_urgent_target": urgent_recall >= 0.95}


# ---------- Aim 3: cited Q&A ----------
# CSV columns: id, answerable (1/0), answer_correct (1/0),
#              citation_correct (1/0), referred_to_advisor (1/0)
def score_qa(rows):
    correct = 0
    for r in rows:
        if int(r["answerable"]) == 1:
            correct += int(r["answer_correct"])
        else:  # unsupported questions are correct only if referred to an advisor
            correct += int(r["referred_to_advisor"])
    answered = [r for r in rows if int(r["answerable"]) == 1]
    cited = sum(int(r["citation_correct"]) for r in answered)
    acc = correct / len(rows)
    cite = cited / len(answered) if answered else float("nan")
    return {"n": len(rows), "accuracy": acc, "citation_accuracy": cite,
            "meets_accuracy_target": acc >= 0.85, "meets_citation_target": cite >= 0.90}


# ---------- Aim 2: elective recommender ----------
# JSON: {"students": [{"id": "s1", "recs": [5 course ids], "popular": [5 course ids],
#                      "liked": [held-out course ids rated >= 4],
#                      "eligible": [course ids that are eligible + degree-applicable]}]}
def precision_at_k(recs, liked, k=5):
    return len(set(recs[:k]) & set(liked)) / k


def score_recs(data, k=5):
    ours, base, ok, total = [], [], 0, 0
    for s in data["students"]:
        ours.append(precision_at_k(s["recs"], s["liked"], k))
        base.append(precision_at_k(s["popular"], s["liked"], k))
        ok += sum(1 for c in s["recs"][:k] if c in set(s["eligible"]))
        total += len(s["recs"][:k])
    p_ours, p_base = sum(ours) / len(ours), sum(base) / len(base)
    elig = ok / total
    return {"n": len(ours), f"precision@{k}": p_ours, f"popular_precision@{k}": p_base,
            "eligible_rate": elig, "beats_baseline": p_ours > p_base,
            "meets_eligibility_target": elig == 1.0}


# ---------- Aim 1: schedule builder / graduation planner ----------
# CSV columns: id, is_transfer (1/0), schedule_valid (1/0),
#              planner_grad_term, advisor_grad_term   (integers, e.g. 1 = Fall 2027 ...)
def score_sched(rows):
    valid = sum(int(r["schedule_valid"]) for r in rows) / len(rows)
    beats = sum(1 for r in rows
                if int(r["planner_grad_term"]) <= int(r["advisor_grad_term"])) / len(rows)
    return {"n": len(rows), "transfers": sum(int(r["is_transfer"]) for r in rows),
            "valid_rate": valid, "match_or_beat_rate": beats,
            "meets_valid_target": valid == 1.0, "meets_grad_target": beats >= 0.90}


# ---------- plumbing ----------
def read_csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def show(result):
    for k, v in result.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")


def selftest():
    # tiny made-up data, ONLY to prove the math works (not project results)
    t = [{"true_topic": "a", "pred_topic": "a", "true_urgent": 1, "pred_urgent": 1},
         {"true_topic": "b", "pred_topic": "a", "true_urgent": 0, "pred_urgent": 0},
         {"true_topic": "b", "pred_topic": "b", "true_urgent": 1, "pred_urgent": 0}]
    r = score_triage(t)
    assert abs(r["urgent_recall"] - 0.5) < 1e-9 and abs(r["macro_f1"] - 2/3) < 1e-9
    q = [{"answerable": 1, "answer_correct": 1, "citation_correct": 1, "referred_to_advisor": 0},
         {"answerable": 0, "answer_correct": 0, "citation_correct": 0, "referred_to_advisor": 1}]
    assert score_qa(q)["accuracy"] == 1.0
    d = {"students": [{"id": "s", "recs": list("abcde"), "popular": list("vwxyz"),
                       "liked": list("abz"), "eligible": list("abcde")}]}
    rr = score_recs(d)
    assert rr["precision@5"] == 0.4 and rr["popular_precision@5"] == 0.2
    s = [{"is_transfer": 1, "schedule_valid": 1, "planner_grad_term": 8, "advisor_grad_term": 9}]
    assert score_sched(s)["match_or_beat_rate"] == 1.0
    print("selftest passed")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "selftest":
        selftest()
    else:
        cmd, path = sys.argv[1], sys.argv[2]
        if cmd == "triage":
            show(score_triage(read_csv(path)))
        elif cmd == "qa":
            show(score_qa(read_csv(path)))
        elif cmd == "recs":
            show(score_recs(json.load(open(path))))
        elif cmd == "sched":
            show(score_sched(read_csv(path)))
        else:
            print(__doc__)
