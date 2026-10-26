"""Validate the hand-encoded data files.  Run before every commit:

    python src/audit/validate_data.py

Exits non-zero (and prints every problem) if anything is inconsistent.
Warnings (unknown prerequisites, inferred credits, documented catalog discrepancies) never fail the run.
Owner: Ayana Seegars.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "audit"))
from degree_audit import norm, prereq_depth  # noqa: E402

REQ_TYPES = {"course", "one_of", "elective"}
FILL = {"list", "partial", "attest", "any"}
TRANSFER_STATUS = {"direct", "category", "elective", "none"}
PREREQ_STATUS = {"stated", "none_listed", "unknown"}


def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _known(code, courses):
    """A code is valid if it is in courses.json or is a wildcard such as 'ECEN 4XX'."""
    n = norm(code)
    return n in courses or n.endswith("XX")


def validate_courses(path, warns):
    errs = []
    courses = _load(path)["courses"]
    unknown = inferred = 0
    for code, c in courses.items():
        if code != norm(code):
            errs.append(f"courses.json: key '{code}' is not normalised (expected '{norm(code)}')")
        for k in ("title", "credits"):
            if k not in c:
                errs.append(f"{code}: missing '{k}'")
        if not isinstance(c.get("credits", 0), (int, float)) or c.get("credits", 0) < 0:
            errs.append(f"{code}: bad credits {c.get('credits')}")
        status = c.get("prereq_status", "stated")
        if status not in PREREQ_STATUS:
            errs.append(f"{code}: bad prereq_status {status}")
        p = c.get("prereq", [])
        if p is None:
            if status != "unknown":
                errs.append(f"{code}: prereq is null but prereq_status is '{status}'")
            unknown += 1
        elif not isinstance(p, list) or any(not isinstance(g, list) or not g for g in p):
            errs.append(f"{code}: prereq must be a list of non-empty OR-lists")
        else:
            for grp in p + [[x] for x in c.get("coreq", [])]:
                for q in grp:
                    if norm(q) not in courses:
                        errs.append(f"{code}: prerequisite/corequisite '{q}' not in courses.json")
        if c.get("credits_inferred"):
            inferred += 1
    memo = {}
    for code in courses:
        try:
            prereq_depth(code, courses, memo)
        except ValueError as e:
            errs.append(str(e))
    if unknown:
        warns.append(f"{unknown} course(s) have unknown prerequisites (see data/prereq_todo.csv)")
    if inferred:
        warns.append(f"{inferred} course(s) have inferred (not catalog-stated) credits")
    return courses, errs


def validate_lists(path, courses):
    errs, lists = [], {}
    if not path.exists():
        return lists, errs
    for name, l in _load(path)["lists"].items():
        lists[name] = l["courses"]
        for c in l["courses"]:
            if not _known(c, courses):
                errs.append(f"lists.json:{name}: {c} not in courses.json")
    return lists, errs


def validate_curriculum(path, courses, lists, warns):
    errs = []
    cur = _load(path)
    for k in ("program_id", "program_name", "catalog_year", "total_credits", "source_url", "retrieved", "requirements"):
        if k not in cur:
            errs.append(f"{path.name}: missing '{k}'")
    ids, credit_sum = set(), 0.0
    for r in cur.get("requirements", []):
        rid, t = r.get("id"), r.get("type")
        where = f"{path.name}:{rid}"
        if rid in ids:
            errs.append(f"{where}: duplicate requirement id")
        ids.add(rid)
        if t not in REQ_TYPES:
            errs.append(f"{where}: bad type {t}")
            continue
        if t == "course":
            c = norm(r["code"])
            if c not in courses:
                errs.append(f"{where}: {c} not in courses.json")
            else:
                credit_sum += courses[c]["credits"]
        elif t == "one_of":
            opts = [norm(o) for o in r["options"]]
            for o in opts:
                if o not in courses:
                    errs.append(f"{where}: option {o} not in courses.json")
            if opts and opts[0] in courses:
                credit_sum += courses[opts[0]]["credits"]
        else:
            credit_sum += float(r["credits"])
            fill = r.get("fill", "list")
            if fill not in FILL:
                errs.append(f"{where}: bad fill {fill}")
            if r.get("list_ref") and r["list_ref"] not in lists:
                errs.append(f"{where}: list_ref {r['list_ref']} not in lists.json")
            for a in r.get("approved") or []:
                if not _known(a, courses):
                    errs.append(f"{where}: approved {a} not in courses.json")
            if fill in ("list", "partial") and not (r.get("list_ref") or r.get("approved")):
                errs.append(f"{where}: fill={fill} needs list_ref or approved")
    for grade, codes in cur.get("min_grade", {}).items():
        for c in codes:
            if norm(c) not in courses:
                errs.append(f"{path.name}: min_grade course {c} not in courses.json")
    if abs(credit_sum - float(cur.get("total_credits", -1))) > 0.01:
        msg = (f"{path.name}: requirements sum to {credit_sum:g} credits but total_credits is "
               f"{cur.get('total_credits')}")
        if cur.get("known_discrepancies"):
            warns.append(msg + " (documented catalog discrepancy)")
        else:
            errs.append(msg + " (check against the catalog; a row may be missing)")
    return errs


def validate_transfer(path, courses, inst_path):
    errs = []
    t = _load(path)
    seen = {(e["institution_id"], e["cc_course"]) for e in t["equivalencies"]}
    insts = {"NCCCS"}
    if inst_path.exists():
        insts |= {i["institution_id"] for i in _load(inst_path)["institutions"]}
    for i, e in enumerate(t["equivalencies"]):
        w = f"transfer[{i}] {e.get('cc_course')}"
        for k in ("institution_id", "institution", "cc_course", "credits", "status", "source", "guide_year"):
            if k not in e:
                errs.append(f"{w}: missing '{k}'")
        if e.get("institution_id") not in insts:
            errs.append(f"{w}: unknown institution_id {e.get('institution_id')}")
        if e.get("status") not in TRANSFER_STATUS:
            errs.append(f"{w}: bad status {e.get('status')}")
        if e.get("status") == "direct":
            if not e.get("ncat_equivalent"):
                errs.append(f"{w}: direct but no ncat_equivalent")
            for c in e.get("ncat_equivalent", []):
                if norm(c) not in courses:
                    errs.append(f"{w}: {c} not in courses.json")
        if e.get("status") == "category" and not e.get("category"):
            errs.append(f"{w}: category status needs 'category'")
        for r in e.get("also_requires", []):
            if (e["institution_id"], r) not in seen:
                errs.append(f"{w}: also_requires {r} has no entry")
    return errs


def main(root=ROOT):
    root = Path(root)
    errs, warns = [], []
    courses, e = validate_courses(root / "data" / "courses.json", warns)
    errs += e
    lists, e = validate_lists(root / "data" / "lists.json", courses)
    errs += e
    cur_files = sorted((root / "data" / "curricula").glob("*.json"))
    for p in cur_files:
        errs += validate_curriculum(p, courses, lists, warns)
    tpath = root / "data" / "transfer" / "transfer_map.json"
    if tpath.exists():
        errs += validate_transfer(tpath, courses, root / "data" / "transfer" / "institutions.json")
    else:
        errs.append("data/transfer/transfer_map.json not found")
    print(f"{len(courses)} courses, {len(lists)} lists, {len(cur_files)} curricula checked")
    for m in warns:
        print("WARNING:", m)
    for m in errs:
        print("ERROR:", m)
    print("OK" if not errs else f"{len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else ROOT))
