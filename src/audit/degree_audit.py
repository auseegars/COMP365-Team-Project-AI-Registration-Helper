"""Degree-audit rule engine for Aggies Enroll.

Owner: Ayana Seegars.  Consumed by: Ryan Travers (schedule builder)
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------- loading
def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_courses(path="data/courses.json"):
    return load_json(path)["courses"]


def load_lists(path="data/lists.json"):
    return {k: v["courses"] for k, v in load_json(path)["lists"].items()}


def load_curriculum(path):
    return load_json(path)


def load_transfer_map(path="data/transfer/transfer_map.json"):
    """Return {(institution_id, cc_course): entry}.  institution_id 'NCCCS' = any NC community college."""
    return {(e["institution_id"], e["cc_course"]): e for e in load_json(path)["equivalencies"]}


_CODE = re.compile(r"^\s*([A-Za-z]{2,5})[\s\-_]*(\d\w*)\s*$")


def norm(code: str) -> str:
    """'comp-167' / 'COMP167' -> 'COMP 167';  'ECEN 4xx' -> 'ECEN 4XX'."""
    m = _CODE.match(code)
    if not m:
        return code.strip().upper()
    return f"{m.group(1).upper()} {m.group(2).upper()}"


def matches(code: str, pattern: str) -> bool:
    """Exact match, or wildcard like 'ECEN 4XX' (same department, same hundreds digit)."""
    code, pattern = norm(code), norm(pattern)
    if pattern.endswith("XX"):
        return code.split()[0] == pattern.split()[0] and code.split()[1][:1] == pattern.split()[1][:1]
    return code == pattern


# ---------------------------------------------------------------- transfer
def apply_transfer_credit(profile, transfer_map):
    """Translate transfer courses into A&T credit.

    profile["transfer"] = [{"institution_id": "GTCC", "course": "MAT 271"}, ...]
    Lookup tries (institution, course) then ('NCCCS', course).
    Returns (ncat_codes_earned, generic_elective_credits, {category: credits}, unmatched).
    """
    by_inst = {}
    for t in profile.get("transfer", []):
        by_inst.setdefault(t["institution_id"], set()).add(norm(t["course"]))
    earned, generic, cats, unmatched = set(), 0.0, {}, []
    for t in profile.get("transfer", []):
        inst, cc = t["institution_id"], norm(t["course"])
        e = transfer_map.get((inst, cc)) or transfer_map.get((inst, t["course"])) \
            or transfer_map.get(("NCCCS", cc)) or transfer_map.get(("NCCCS", t["course"]))
        if e is None or e["status"] == "none":
            unmatched.append(t)
            continue
        if any(norm(r) not in by_inst[inst] for r in e.get("also_requires", [])):
            unmatched.append({**t, "reason": "needs " + ", ".join(e["also_requires"])})
            continue
        if e["status"] == "direct":
            earned.update(norm(c) for c in e["ncat_equivalent"])
        elif e["status"] == "category":
            cats[e["category"]] = cats.get(e["category"], 0.0) + float(e["credits"])
        elif e["status"] == "elective":
            generic += float(e["credits"])
    return earned, generic, cats, unmatched


# ---------------------------------------------------------------- prereqs
def _prereq(code, courses):
    p = courses.get(code, {}).get("prereq")
    return [] if p is None else p


def prereqs_met(code, courses, done):
    """True if every OR-group of `code`'s prerequisites intersects `done`."""
    return all(any(norm(p) in done for p in grp) for grp in _prereq(code, courses))


def prereq_depth(code, courses, _memo=None, _stack=None):
    """Length of the longest prerequisite chain ending at `code` (shallowest option inside an OR-group).
    Used by Caleb's planner to order courses along the critical path."""
    memo = {} if _memo is None else _memo
    stack = set() if _stack is None else _stack
    if code in memo:
        return memo[code]
    if code in stack:
        raise ValueError(f"prerequisite cycle through {code}")
    stack.add(code)
    depth = 0
    for grp in _prereq(code, courses):
        best = min((prereq_depth(norm(p), courses, memo, stack) + 1 for p in grp if norm(p) in courses), default=1)
        depth = max(depth, best)
    stack.discard(code)
    memo[code] = depth
    return depth


# ---------------------------------------------------------------- audit
def elective_pool(req, lists):
    """Approved codes/patterns for an elective slot (inline `approved` plus `list_ref`)."""
    pool = list(req.get("approved") or [])
    if req.get("list_ref"):
        pool += lists[req["list_ref"]]
    return [norm(p) for p in pool]


@dataclass
class AuditResult:
    program_id: str
    satisfied: list = field(default_factory=list)
    remaining: list = field(default_factory=list)          # unmet requirements
    remaining_courses: list = field(default_factory=list)  # concrete required courses, shallowest prereq depth first
    eligible_now: list = field(default_factory=list)       # remaining + prereqs met + not in progress
    elective_options: dict = field(default_factory=dict)   # unmet elective slot id -> courses takeable now
    credits_remaining: float = 0.0
    credits_applied: float = 0.0
    transfer_unmatched: list = field(default_factory=list)
    unverified_prereqs: list = field(default_factory=list)  # eligible courses whose prerequisites are not in the data yet
    warnings: list = field(default_factory=list)

    def to_dict(self):
        return self.__dict__.copy()


def audit(profile, curriculum, courses, transfer_map=None, lists=None):
    """Compare a student profile with a curriculum.

    profile = {"student_id", "major", "completed": [codes], "in_progress": [codes],
               "transfer": [{"institution_id","course"}], "satisfied_electives": [slot ids]}
    Requirement types:
      course   {"id","type":"course","code","term"}
      one_of   {"id","type":"one_of","options":[codes]}
      elective {"id","type":"elective","category","credits","fill","approved"|"list_ref","term"}
    elective.fill:
      list     filled by completed courses in the approved pool (codes or wildcards like 'ECEN 4xx')
      partial  same, but the pool is known to be incomplete (flagged in warnings)
      attest   no machine-readable list: satisfied only if its id is in profile['satisfied_electives']
      any      free elective: any completed course left over, plus generic transfer elective credit
    """
    transfer_map = transfer_map or {}
    lists = lists or {}
    done = {norm(c) for c in profile.get("completed", [])}
    in_prog = {norm(c) for c in profile.get("in_progress", [])}
    t_codes, t_generic, t_cats, unmatched = apply_transfer_credit(profile, transfer_map)
    done |= t_codes
    attested = set(profile.get("satisfied_electives", []))

    res = AuditResult(program_id=curriculum["program_id"], transfer_unmatched=unmatched)
    used = set()

    # Pass 1: fixed courses and one_of choices consume specific codes.
    for req in curriculum["requirements"]:
        if req["type"] == "course":
            code = norm(req["code"])
            if code in done:
                used.add(code); res.satisfied.append(req["id"]); res.credits_applied += courses[code]["credits"]
            else:
                res.remaining.append(req)
        elif req["type"] == "one_of":
            hit = next((norm(o) for o in req["options"] if norm(o) in done and norm(o) not in used), None)
            if hit:
                used.add(hit); res.satisfied.append(req["id"]); res.credits_applied += courses[hit]["credits"]
            else:
                res.remaining.append(req)

    # Pass 2: electives, most constrained first, drawing on leftover completed courses.
    spare = sorted(c for c in done - used if c in courses)
    cat_pool = dict(t_cats)
    generic = t_generic
    carry = {}                                   # overshoot credit carried to the next slot of the same category
    electives = [r for r in curriculum["requirements"] if r["type"] == "elective"]
    order = sorted(electives, key=lambda r: (r.get("fill") == "any", len(elective_pool(r, lists)) or 10**6, r["id"]))
    status = {}
    for req in order:
        need, fill, cat = float(req["credits"]), req.get("fill", "list"), req.get("category")
        got = carry.pop(cat, 0.0) if fill != "attest" else 0.0
        if fill == "attest":
            got = need if req["id"] in attested else 0.0
        else:
            pool = elective_pool(req, lists)
            for code in list(spare):
                if got >= need:
                    break
                if fill == "any" or any(matches(code, p) for p in pool):
                    got += courses[code]["credits"]; used.add(code); spare.remove(code)
            if got < need and cat_pool.get(cat, 0) > 0:
                take = min(need - got, cat_pool[cat]); got += take; cat_pool[cat] -= take
            if got < need and fill == "any" and generic > 0:
                take = min(need - got, generic); got += take; generic -= take
            if got > need:
                carry[cat] = got - need
            if fill == "partial":
                res.warnings.append(f"{req['id']}: approved list is incomplete in the data; confirm with advisor")
        status[req["id"]] = (min(got, need), need)

    for req in electives:
        applied, need = status[req["id"]]
        res.credits_applied += applied
        if applied >= need:
            res.satisfied.append(req["id"])
        else:
            r = dict(req); r["credits_missing"] = need - applied
            res.remaining.append(r)
            pool = elective_pool(req, lists)
            if req.get("fill") != "attest":
                opts = [c for c in courses if c not in done and c not in in_prog
                        and (req.get("fill") == "any" or any(matches(c, p) for p in pool))
                        and prereqs_met(c, courses, done)]
                res.elective_options[req["id"]] = sorted(opts)

    # Remaining concrete courses, shallowest prerequisite chain first
    concrete = []
    for req in res.remaining:
        if req["type"] == "course":
            concrete.append(norm(req["code"]))
        elif req["type"] == "one_of":
            opts = [norm(o) for o in req["options"] if norm(o) in courses]
            if opts:
                concrete.append(min(opts, key=lambda c: prereq_depth(c, courses)))
    memo = {}
    res.remaining_courses = sorted(set(concrete), key=lambda c: (prereq_depth(c, courses, memo), c))
    res.eligible_now = [c for c in res.remaining_courses if c not in in_prog and prereqs_met(c, courses, done)]
    res.unverified_prereqs = [c for c in res.eligible_now if courses[c].get("prereq") is None]
    res.credits_remaining = max(0.0, float(curriculum["total_credits"]) - res.credits_applied)
    for c in in_prog:
        if c not in courses:
            res.warnings.append(f"in-progress course {c} not in courses.json")
    return res
