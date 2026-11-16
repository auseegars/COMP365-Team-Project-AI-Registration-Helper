"""Compare the CP-SAT schedule builder with the greedy baseline.  Owner: Ryan Travers.

    python src/schedule/evaluate_schedules.py [profiles.json] [sections.json]

Defaults: data/profiles/schedule_demo_profiles.json and data/sections/sample_term.json (both SYNTHETIC).
Writes results/schedule_results.csv (one row per student per method) and prints a summary:
  valid_rate        share of schedules that pass check_schedule (target 100%, Aim 1)
  avg_credits       credits scheduled
  avg_required      required (not elective) courses scheduled
  avg_unlocks       remaining required courses unlocked by what was scheduled (critical-path progress)
  avg_score         the builder's priority score (higher = more urgent requirements covered)

evaluate.py's `sched` command also needs planner_grad_term / advisor_grad_term, which come from the
graduation planner (Caleb) and the hand-verified test profiles; `schedule_valid` here is the column to merge in.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "schedule"))
import schedule_builder as sb  # noqa: E402


def run(profiles_path, sections_path=None, out_path=None):
    courses, lists, tmap, sec_data, by_course = sb.load_all(sections_path=sections_path)
    crn = {s["crn"]: s for ss in by_course.values() for s in ss}
    profiles = json.load(open(profiles_path, encoding="utf-8"))["profiles"]
    rows = []
    for prof in profiles:
        cur = sb.curriculum_for(prof["major"])
        ctx = sb.candidate_courses(prof, cur, courses, tmap, lists)
        for fn in (sb.build_schedule, sb.greedy_schedule):
            r = fn(prof, cur, courses, by_course, tmap, lists, term=sec_data["term"])
            chk = sb.check_schedule(r, prof, cur, courses, crn, tmap, lists)
            req = [it for it in r.items if it["fills"] in ctx.req_info]
            rows.append({
                "id": r.student_id, "major": prof["major"], "is_transfer": int(bool(prof.get("is_transfer"))),
                "method": r.method, "schedule_valid": int(chk["valid"]), "credits": r.total_credits,
                "required_courses": len(req),
                "unlocks": sum(ctx.unlocks.get(it["course"], 0) for it in req),
                "score": r.score, "unverified_prereqs": len(chk["warnings"]),
                "courses": " ".join(it["course"] for it in r.items),
                "problems": " | ".join(chk["problems"])})
    out = Path(out_path or ROOT / "results" / "schedule_results.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    return rows, out


def summarize(rows):
    out = {}
    for method in ("cpsat", "greedy"):
        rs = [r for r in rows if r["method"] == method]
        n = len(rs)
        out[method] = {"n": n,
                       "valid_rate": sum(r["schedule_valid"] for r in rs) / n,
                       "avg_credits": sum(r["credits"] for r in rs) / n,
                       "avg_required": sum(r["required_courses"] for r in rs) / n,
                       "avg_unlocks": sum(r["unlocks"] for r in rs) / n,
                       "avg_score": sum(r["score"] for r in rs) / n,
                       "with_unverified_prereqs": sum(1 for r in rs if r["unverified_prereqs"]) / n}
    return out


if __name__ == "__main__":
    prof = sys.argv[1] if len(sys.argv) > 1 else ROOT / "data" / "profiles" / "schedule_demo_profiles.json"
    secs = sys.argv[2] if len(sys.argv) > 2 else None
    rows, path = run(prof, secs)
    s = summarize(rows)
    print(f"{'metric':<26}{'CP-SAT':>10}{'greedy':>10}")
    for k in ("n", "valid_rate", "avg_credits", "avg_required", "avg_unlocks", "avg_score", "with_unverified_prereqs"):
        a, b = s["cpsat"][k], s["greedy"][k]
        fmt = ((lambda v: f"{v:.0%}") if k in ("valid_rate", "with_unverified_prereqs")
               else (lambda v: f"{v:d}") if k == "n" else (lambda v: f"{v:.1f}"))
        print(f"{k:<26}{fmt(a):>10}{fmt(b):>10}")
    for r in rows:
        if not r["schedule_valid"]:
            print(f"INVALID {r['id']} [{r['method']}]: {r['problems']}")
    print(f"\nwrote {path.relative_to(ROOT)}  (synthetic profiles and sections; not project results)")
