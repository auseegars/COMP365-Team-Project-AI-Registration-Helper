"""schedule builder for Aggies Enroll.
Owner: Ryan Travers | Builds on: src/audit/degree_audit.py
AI Assistance: Used AI tools to help implement the OR-Tools CP-SAT constraint solver and validation logic.
CLI: python src/schedule/schedule_builder.py data/profiles/schedule_demo_profiles.json SYN-CS-02 [--greedy]
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "audit"))
sys.path.insert(0, str(ROOT / "src" / "schedule"))
import degree_audit as da  # noqa: E402
from sections import blocked_by, load_sections, meeting_blocks, sections_overlap  # noqa: E402

DEFAULT_MAX_CREDITS = 17
FULL_TIME = 12
TERMS_AHEAD = 2


def normalize_profile(profile):
    p = dict(profile)
    p.setdefault("student_id", p.get("id"))
    p["completed"] = [da.norm(c) for c in p.get("completed", p.get("completed_courses", []))]
    p["in_progress"] = [da.norm(c) for c in p.get("in_progress", [])]
    p["transfer"] = p.get("transfer", p.get("transfer_credits", []))
    prefs = p.get("preferences") or {}
    p["max_credits"] = float(prefs.get("max_credits", p.get("max_credits", DEFAULT_MAX_CREDITS)))
    p["avoid_times"] = prefs.get("avoid_times", p.get("avoid_times", []))
    p["preferred_electives"] = [da.norm(c) for c in p.get("preferred_electives", [])]
    return p


def planning_profile(p):
    q = dict(p)
    q["completed"] = sorted(set(p["completed"]) | set(p["in_progress"]))
    q["in_progress"] = []
    return q


def done_codes(p, transfer_map):
    earned, *_ = da.apply_transfer_credit(p, transfer_map or {})
    return set(p["completed"]) | set(p["in_progress"]) | earned


@dataclass
class Candidate:
    code: str
    credits: float
    required_ids: list = field(default_factory=list)
    slots: list = field(default_factory=list)
    term_hint: int = 8
    unverified: bool = False


@dataclass
class Context:
    profile: dict
    audit: da.AuditResult
    candidates: dict
    slot_info: dict
    req_info: dict
    unlocks: dict
    next_term: int
    excluded: dict
    notes: list


def _number(code):
    try:
        return int("".join(ch for ch in code.split()[1] if ch.isdigit())[:3])
    except (IndexError, ValueError):
        return 999


def _remaining_required(audit_res, courses):
    out = []
    for req in audit_res.remaining:
        if req["type"] == "course":
            out.append((req["id"], da.norm(req["code"]), req.get("term") or 0))
        elif req["type"] == "one_of":
            for o in req["options"]:
                if da.norm(o) in courses:
                    out.append((req["id"], da.norm(o), req.get("term") or 0))
    return out


def _unlocks(remaining_codes, courses):
    deps = {c: set() for c in courses}
    for c in remaining_codes:
        stack, seen = [c], set()
        while stack:
            for grp in courses.get(stack.pop(), {}).get("prereq") or []:
                for q in grp:
                    q = da.norm(q)
                    if q not in seen:
                        seen.add(q)
                        stack.append(q)
        for q in seen:
            deps.setdefault(q, set()).add(c)
    return {c: len(v) for c, v in deps.items()}


def lab_lecture(code, courses):
    c = courses.get(code, {})
    if c.get("coreq") or "lab" not in c.get("title", "").lower():
        return None
    dept, num = code.split()[0], _number(code)
    lec = f"{dept} {num - 10}"
    if lec in courses and "lab" not in courses[lec].get("title", "").lower():
        return lec
    return None


def corequisites(code, courses):
    stated = [da.norm(q) for q in courses.get(code, {}).get("coreq") or []]
    lec = lab_lecture(code, courses)
    return stated + ([lec] if lec else [])


def candidate_courses(profile, curriculum, courses, transfer_map=None, lists=None):
    p = normalize_profile(profile)
    plan_p = planning_profile(p)
    res = da.audit(plan_p, curriculum, courses, transfer_map, lists)
    done = done_codes(p, transfer_map)
    next_term = int(res.credits_applied // 15) + 1
    year_level = min(4, (next_term + 1) // 2)
    notes = []
    if p["in_progress"]:
        notes.append("In-progress courses are assumed passed: " + ", ".join(sorted(p["in_progress"])))

    req_rows = _remaining_required(res, courses)
    remaining_codes = {c for _, c, _ in req_rows}
    unlocks = _unlocks(remaining_codes, courses)
    for _, code, term in req_rows:
        unlocks[code] = unlocks.get(code, 0) + sum(
            1 for _, o, ot in req_rows
            if o != code and o.split()[0] == code.split()[0] and _number(o) > _number(code) and ot > term
            and courses[o].get("prereq") is None)
    excluded, cands = {}, {}

    def guard(code, term, elective=False):
        if courses[code].get("prereq") is not None:
            return None
        if elective and _number(code) // 100 > year_level + 1:
            return f"prerequisites not in data; {code[-3]}00-level elective is too advanced for year {year_level}"
        dept = code.split()[0]
        for _, other, oterm in req_rows:
            if other != code and other.split()[0] == dept and _number(other) < _number(code) and oterm < term:
                return f"prerequisites not in data; likely needs {other} first (same department, earlier in plan)"
        return None

    def add(code, term):
        c = cands.get(code)
        if c is None:
            c = cands[code] = Candidate(code, float(courses[code]["credits"]), term_hint=term,
                                        unverified=courses[code].get("prereq") is None)
        c.term_hint = min(c.term_hint, term)
        return c

    req_info = {r["id"]: r for r in res.remaining if r["type"] in ("course", "one_of")}
    for rid, code, term in req_rows:
        if code in done or not da.prereqs_met(code, courses, done):
            continue
        if term > next_term + TERMS_AHEAD:
            excluded[code] = f"catalog plans it for term {term}; student is entering term {next_term}"
            continue
        why = guard(code, term)
        if why:
            excluded[code] = why
            continue
        add(code, term).required_ids.append(rid)

    slot_info = {}
    for req in res.remaining:
        if req["type"] != "elective":
            continue
        if req.get("fill") == "attest":
            notes.append(f"{req['id']} ({req.get('label', req.get('category'))}): no approved list in the data; "
                         "pick this elective with an advisor")
            continue
        opts = res.elective_options.get(req["id"], [])
        term = req.get("term") or 0
        if not opts or term > next_term + TERMS_AHEAD:
            continue
        slot_info[req["id"]] = req
        for code in opts:
            if code in remaining_codes or code in done:
                continue
            why = guard(code, term, elective=True)
            if why:
                excluded.setdefault(code, why)
                continue
            add(code, term).slots.append(req["id"])

    for code in list(cands):
        for q in corequisites(code, courses):
            if q not in done and q not in cands:
                excluded[code] = f"corequisite {q} cannot be taken this term"
                cands.pop(code)
                break
    return Context(p, res, cands, slot_info, req_info, unlocks, next_term, excluded, notes)


def course_value(ctx: Context, code: str, slot: str | None = None) -> int:
    c = ctx.candidates[code]
    if slot is None:
        on_plan = 60 if c.term_hint <= ctx.next_term else 0
        per = 100 + 30 * min(ctx.unlocks.get(code, 0), 10) + on_plan + 5 * max(0, 8 - c.term_hint)
        return int(per * c.credits)
    req = ctx.slot_info[slot]
    term = req.get("term") or 0
    need = float(req.get("credits_missing", req["credits"]))
    on_plan = 60 if term <= ctx.next_term else 0
    per = (20 if req.get("fill") == "any" else 60) + on_plan + 5 * max(0, 8 - term)
    pref = ctx.profile["preferred_electives"]
    bonus = max(0, 200 - 20 * pref.index(code)) if code in pref else 0
    return int(per * min(c.credits, need)) + bonus


@dataclass
class ScheduleResult:
    student_id: str
    method: str
    term: str
    items: list = field(default_factory=list)
    total_credits: float = 0.0
    score: int = 0
    status: str = ""
    notes: list = field(default_factory=list)

    def to_dict(self):
        return self.__dict__.copy()


def _usable_sections(ctx, by_course, code):
    return [s for s in by_course.get(code, [])
            if s.get("seats_open", 0) > 0 and not blocked_by(s, ctx.profile["avoid_times"])]


def _finish(ctx, method, term, picks, courses, status):
    r = ScheduleResult(ctx.profile.get("student_id"), method, term, status=status, notes=list(ctx.notes))
    for s, fills in sorted(picks, key=lambda x: x[0]["course"]):
        code = s["course"]
        r.items.append({"crn": s["crn"], "course": code, "title": courses[code].get("title", ""),
                        "credits": float(courses[code]["credits"]), "fills": fills,
                        "meetings": s["meetings"]})
        r.total_credits += float(courses[code]["credits"])
        r.score += course_value(ctx, code, None if fills in ctx.req_info else fills)
        if ctx.candidates[code].unverified:
            r.notes.append(f"{code}: prerequisites not in our data yet; confirm with advisor before registering")
    if r.total_credits < FULL_TIME:
        r.notes.append(f"Only {r.total_credits:g} credits fit (below full-time {FULL_TIME}); see an advisor")
    return r


def build_schedule(profile, curriculum, courses, by_course, transfer_map=None, lists=None,
                   term="", time_limit=10.0):
    ctx = candidate_courses(profile, curriculum, courses, transfer_map, lists)
    crn = {s["crn"]: s for ss in by_course.values() for s in ss}
    banned = set()
    for _ in range(6):
        picks, status = _solve_cpsat(ctx, courses, by_course, banned, time_limit)
        r = _finish(ctx, "cpsat", term, picks, courses, status)
        bad = [pr.split(":")[0] for pr in check_schedule(r, profile, curriculum, courses, crn, transfer_map,
                                                          lists)["problems"] if "does not count" in pr]
        if not bad:
            break
        banned |= set(bad)
    if banned:
        r.notes.append("Re-solved without " + ", ".join(sorted(banned)) +
                       " (the degree audit would not count them for this student)")
    return r


def _solve_cpsat(ctx, courses, by_course, banned, time_limit):
    from ortools.sat.python import cp_model

    m = cp_model.CpModel()
    sec_vars, chosen, intervals = {}, {}, []
    for code, c in ctx.candidates.items():
        if code in banned:
            continue
        secs = _usable_sections(ctx, by_course, code)
        if not secs:
            ctx.excluded.setdefault(code, "no open section that fits the student's blocked times")
            continue
        vs = []
        for s in secs:
            v = m.NewBoolVar(f"sec_{s['crn']}")
            sec_vars[s["crn"]] = (v, s)
            vs.append(v)
            for a, b in meeting_blocks(s):
                intervals.append(m.NewOptionalIntervalVar(a, b - a, b, v, f"iv_{s['crn']}_{a}"))
        chosen[code] = m.NewBoolVar(f"take_{code}")
        m.Add(sum(vs) == chosen[code])
    m.AddNoOverlap(intervals)

    fill_vars, by_target, slot_credit = {}, {}, {}
    for code, x in chosen.items():
        c = ctx.candidates[code]
        targets = [(rid, None) for rid in c.required_ids] + [(sid, sid) for sid in c.slots]
        vs = []
        for tid, slot in targets:
            y = m.NewBoolVar(f"fill_{code}_{tid}")
            fill_vars[(code, tid)] = (y, slot)
            if slot is None:
                by_target.setdefault(tid, []).append(y)
            else:
                slot_credit.setdefault(tid, []).append((int(round(c.credits * 10)), y))
            vs.append(y)
        m.Add(sum(vs) == x)
    for ys in by_target.values():
        m.Add(sum(ys) <= 1)
    for sid, terms in slot_credit.items():
        need = int(round(float(ctx.slot_info[sid].get("credits_missing", ctx.slot_info[sid]["credits"])) * 10))
        m.Add(sum(cr * y for cr, y in terms) <= max(need, max(cr for cr, _ in terms)))

    for code, x in chosen.items():
        for q in corequisites(code, courses):
            if q in chosen:
                m.AddImplication(x, chosen[q])

    cap = int(round(ctx.profile["max_credits"] * 10))
    m.Add(sum(int(round(ctx.candidates[c].credits * 10)) * x for c, x in chosen.items()) <= cap)

    order = {c: i for i, c in enumerate(sorted(chosen))}
    m.Maximize(sum(course_value(ctx, code, slot) * 1000 * y for (code, _), (y, slot) in fill_vars.items())
               - sum(order[c] * x for c, x in chosen.items()))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 365
    st = solver.Solve(m)
    status = solver.StatusName(st)
    picks = []
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for (code, tid), (y, _) in fill_vars.items():
            if solver.Value(y):
                s = next(s for v, s in sec_vars.values() if s["course"] == code and solver.Value(v))
                picks.append((s, tid))
    return picks, status


def greedy_schedule(profile, curriculum, courses, by_course, transfer_map=None, lists=None, term=""):
    ctx = candidate_courses(profile, curriculum, courses, transfer_map, lists)
    picks, used_targets, credits = [], set(), 0.0
    taken, slot_filled = set(), {}

    def try_add(code, target):
        nonlocal credits
        c = ctx.candidates[code]
        if code in taken or target in used_targets or credits + c.credits > ctx.profile["max_credits"]:
            return False
        if any(q not in taken and q not in done for q in corequisites(code, courses)):
            return False
        for s in _usable_sections(ctx, by_course, code):
            if not any(sections_overlap(s, t) for t, _ in picks):
                picks.append((s, target))
                taken.add(code)
                credits += c.credits
                if target in ctx.slot_info:
                    slot_filled[target] = slot_filled.get(target, 0.0) + c.credits
                    need = float(ctx.slot_info[target].get("credits_missing", ctx.slot_info[target]["credits"]))
                    if slot_filled[target] >= need:
                        used_targets.add(target)
                else:
                    used_targets.add(target)
                return True
        return False

    done = done_codes(ctx.profile, transfer_map)
    order = [c for c in ctx.audit.remaining_courses if c in ctx.candidates and ctx.candidates[c].required_ids]
    order += sorted(c for c in ctx.candidates if ctx.candidates[c].required_ids and c not in order)
    for code in order:
        try_add(code, ctx.candidates[code].required_ids[0])
    for req in curriculum["requirements"]:
        sid = req["id"]
        if sid in ctx.slot_info:
            for code in sorted(c for c in ctx.candidates if sid in ctx.candidates[c].slots):
                if sid in used_targets:
                    break
                try_add(code, sid)
    return _finish(ctx, "greedy", term, picks, courses, "GREEDY")


def check_schedule(schedule, profile, curriculum, courses, sections_by_crn, transfer_map=None, lists=None):
    p = normalize_profile(profile)
    items = schedule.items if hasattr(schedule, "items") and not isinstance(schedule, dict) else schedule["items"]
    done = done_codes(p, transfer_map)
    problems, warnings = [], []
    codes = [it["course"] for it in items]
    secs = []
    for it in items:
        s = sections_by_crn.get(it["crn"])
        if s is None or s["course"] != it["course"]:
            problems.append(f"{it['course']}: section {it['crn']} does not exist for this course")
            continue
        secs.append(s)
        if s.get("seats_open", 0) <= 0:
            problems.append(f"{it['course']}: section {it['crn']} is full")
        if blocked_by(s, p["avoid_times"]):
            problems.append(f"{it['course']}: section {it['crn']} meets during a blocked time")
    if len(set(codes)) != len(codes):
        problems.append("a course is scheduled twice")
    for code in codes:
        if code not in courses:
            problems.append(f"{code}: not in courses.json")
            continue
        if code in done:
            problems.append(f"{code}: already completed, transferred, or in progress")
        if courses[code].get("prereq") is None:
            warnings.append(f"{code}: prerequisites not in data (unverified)")
        elif not da.prereqs_met(code, courses, done):
            problems.append(f"{code}: prerequisites not met")
        for q in corequisites(code, courses):
            if q not in done and q not in codes:
                problems.append(f"{code}: corequisite {q} neither done nor scheduled")
    for i in range(len(secs)):
        for j in range(i + 1, len(secs)):
            if sections_overlap(secs[i], secs[j]):
                problems.append(f"time conflict: {secs[i]['course']} and {secs[j]['course']}")
    total = sum(float(courses[c]["credits"]) for c in codes if c in courses)
    if total > p["max_credits"]:
        problems.append(f"{total:g} credits exceeds the limit of {p['max_credits']:g}")

    base = planning_profile(p)

    def applied(extra):
        q = dict(base)
        q["completed"] = sorted(set(base["completed"]) | set(extra))
        return da.audit(q, curriculum, courses, transfer_map, lists).credits_applied

    full = applied(codes)
    for code in codes:
        if code in courses and code not in done and applied([c for c in codes if c != code]) >= full:
            problems.append(f"{code}: does not count toward any unmet {curriculum['program_id']} requirement")
    return {"valid": not problems, "problems": problems, "warnings": warnings, "credits": total}


def load_all(root=ROOT, sections_path=None):
    d = Path(root) / "data"
    courses = da.load_courses(d / "courses.json")
    lists = da.load_lists(d / "lists.json")
    tmap = da.load_transfer_map(d / "transfer" / "transfer_map.json")
    sec_data, by_course = load_sections(sections_path or d / "sections" / "sample_term.json")
    return courses, lists, tmap, sec_data, by_course


def curriculum_for(major, root=ROOT):
    return da.load_curriculum(Path(root) / "data" / "curricula" / f"{major}.json")


def format_schedule(r: ScheduleResult, check=None):
    lines = [f"{r.student_id}  [{r.method}]  {r.term}  -> {r.total_credits:g} credits  (status {r.status})"]
    for it in r.items:
        when = "; ".join(f"{m['days']} {m['start']}-{m['end']}" for m in it["meetings"])
        lines.append(f"  {it['course']:<9} {it['crn']}  {it['credits']:>3g} cr  fills {it['fills']:<6}  {when:<32} {it['title']}")
    for n in r.notes:
        lines.append(f"  note: {n}")
    if check is not None:
        lines.append(f"  VALID: {check['valid']}" + ("" if check["valid"] else "  " + "; ".join(check["problems"])))
    return "\n".join(lines)


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    profiles = {p.get("student_id", p.get("id")): p for p in json.load(open(argv[1]))["profiles"]}
    prof = profiles[argv[2]]
    courses, lists, tmap, sec_data, by_course = load_all()
    cur = curriculum_for(prof["major"])
    fn = greedy_schedule if "--greedy" in argv else build_schedule
    r = fn(prof, cur, courses, by_course, tmap, lists, term=sec_data["term"])
    crn = {s["crn"]: s for ss in by_course.values() for s in ss}
    print(format_schedule(r, check_schedule(r, prof, cur, courses, crn, tmap, lists)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))