"""Build data/ from the catalog HTML guides + the CS handbook transcription.

    python tools/build_data.py <dir-with-the-5-guide-html-files>

Writes: data/courses.json, data/lists.json, data/curricula/*.json, data/transfer/transfer_map.json,
        data/prereq_todo.csv, docs/FIRST_YEAR_CORE.md
Re-run after editing tools/handbook_cs.py or when a new catalog year is saved.

"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "src" / "audit")]
import handbook_cs as H                       # noqa: E402
from degree_audit import norm                 # noqa: E402
from guide_parser import TERM, crosscheck, load_all   # noqa: E402

RETRIEVED = "2026-10-25"
CATALOG_YEAR = "2025-2026"
CAT_URL = "https://catalog.ncat.edu/preview_program.php?catoid=19&poid={poid}&returnto=766"
PROGRAMS = {  # poid -> (id, name)
    "3087": ("CS", "B.S. Computer Science"),
    "3090": ("EE", "B.S. Electrical Engineering"),
    "3093": ("ME", "B.S. Mechanical Engineering"),
    "3092": ("ISE", "B.S. Industrial and Systems Engineering"),
    "3091": ("CPE", "B.S. Computer Engineering"),
    "3086": ("CE", "B.S. Civil Engineering"),
}
NO_TITLE = "(title not in provided sources)"
INSTITUTIONS = [   # the team's 10 target community colleges
    dict(institution_id="GTCC", name="Guilford Technical Community College"),
    dict(institution_id="FTCC", name="Forsyth Technical Community College"),
    dict(institution_id="RCC", name="Rockingham Community College"),
    dict(institution_id="ACC", name="Alamance Community College"),
    dict(institution_id="DDCC", name="Davidson-Davie Community College"),
    dict(institution_id="RANDCC", name="Randolph Community College"),
    dict(institution_id="PCC", name="Piedmont Community College"),
    dict(institution_id="WTCC", name="Wake Technical Community College"),
    dict(institution_id="CCCC", name="Central Carolina Community College"),
    dict(institution_id="SCC", name="Surry Community College"),
]
GENED_BY_CAT = {"humanities": "GENED_HUM", "social_behavioral": "GENED_SOC",
                "african_american": "GENED_AFAM", "global_awareness": "GENED_GLOBAL"}


def categorize(title):
    t = title.lower().replace("&nbsp;", " ")
    if "free" in t: return "free"
    if "tech" in t and "math" in t: return "technical_or_math_science"
    if "technical" in t or re.match(r"^[a-z]{4} 4xx$", t): return "technical"
    if "science elective" in t: return "science"
    if "humanities" in t: return "humanities"
    if "social" in t: return "social_behavioral"
    if "african" in t: return "african_american"
    if "global" in t: return "global_awareness"
    if "business" in t: return "business"
    return "other"


def split_formerly(title):
    m = re.search(r"\s*\((?:[Ff]ormerly ([^)]+))\)", title)
    return (re.sub(r"\s*\([Ff]ormerly [^)]+\)", "", title).strip(), m.group(1) if m else None)


# ------------------------------------------------------------------ courses
courses, conflicts = {}, []


def put(code, title, credits, src, formerly=None, credits_inferred=False, credits_note=None):
    code = norm(code)
    c = courses.get(code)
    if c is None:
        c = courses[code] = dict(title=title or NO_TITLE, credits=credits, prereq=None, prereq_status="unknown",
                                 coreq=[], sources=[])
        if title is None: c["title_missing"] = True
        if credits_inferred: c["credits_inferred"] = True
    else:
        if title and c.get("title_missing"):
            c["title"], c["title_missing"] = title, False
            c.pop("title_missing")
        elif title and c["title"] != title and not c.get("title_missing"):
            conflicts.append(f"{code}: title '{c['title']}' ({c['sources'][0]}) vs '{title}' ({src})")
        if credits is not None and c["credits"] != credits and not credits_inferred:
            if c.get("credits_inferred"):
                c["credits"] = credits; c.pop("credits_inferred", None)
            else:
                conflicts.append(f"{code}: credits {c['credits']} ({c['sources'][0]}) vs {credits} ({src})")
    if src not in c["sources"]: c["sources"].append(src)
    if formerly: c["formerly"] = formerly
    if credits_note: c["credits_note"] = credits_note
    return c


def main(html_dir):
    parsed = load_all(html_dir)
    curricula, lists = {}, {}
    report = []

    # ---- 1. guides -> courses
    for poid, r in parsed.items():
        pid = PROGRAMS[poid][0]
        for it in r["items"]:
            if it["kind"] == "course":
                t, fm = split_formerly(it["title"])
                put(it["code"], t, it["credits"], f"catalog:{pid}", formerly=fm, credits_note=it.get("credits_note"))
    # ---- 2. handbook CS courses (titles only fill gaps; prerequisites always applied)
    for code, (title, cr, prereq, coreq, note, status) in H.CS_COURSES.items():
        c = put(code, title, cr, "handbook")
        c["prereq"], c["prereq_status"], c["coreq"] = prereq, status, coreq
        if note: c["prereq_note"] = note
    for code, (title, cr, inferred) in H.CS_OTHER.items():
        put(code, title, cr, "handbook", credits_inferred=inferred)
    for code in H.CS_MIN_GRADE["C"]:
        courses[code]["min_grade"] = "C"
    courses["MATH 131"]["min_grade_cs"] = "C-"

    # ---- 3. lists
    for name, (title, codes) in {**H.GENED, **H.CS_LISTS}.items():
        lists[name] = dict(title=title, source=H.SOURCE, courses=[norm(c) for c in codes])
    ee, cpe = parsed["3090"], parsed["3091"]
    bsec = re.search(r"\(maximum of 2 courses from a given area\);(.*)$", ee["footnotes"]["b"]).group(1)
    groups = [re.findall(r"ECEN \d{3}", g) for g in re.findall(r"\(([^)]*)\)", bsec)]
    groups = [g for g in groups if g]
    assert [len(g) for g in groups] == [3, 4, 4, 4], groups
    lists["EE_TECH_B"] = dict(title="EE technical electives, areas (max 2 courses from a given area)",
                              source="catalog:EE footnote b", courses=[c for g in groups for c in g], groups=groups)
    lists["EE_TECH_C"] = dict(title="EE technical electives, list c", source="catalog:EE footnote c",
                              courses=re.findall(r"ECEN \d{3}", ee["footnotes"]["c"]))
    cpe_b = re.findall(r"ECEN \d{3}", cpe["footnotes"]["b"])
    cpe_c = [norm(x) for x in re.findall(r"(?:COMP|ECEN) \d(?:\d\d|xx)", cpe["footnotes"]["c"])]
    lists["CPE_TECH_B"] = dict(title="CPE technical electives, list b", source="catalog:CPE footnote b", courses=cpe_b)
    lists["CPE_TECH_BC"] = dict(title="CPE technical electives, list b or c", source="catalog:CPE footnotes b,c",
                                courses=cpe_b + cpe_c)
    for name in ("EE_TECH_B", "EE_TECH_C", "CPE_TECH_B", "CPE_TECH_BC"):
        for code in lists[name]["courses"]:
            if "XX" not in code:
                put(code, None, 3, "list", credits_inferred=True)
    # courses that appear only in lists / prerequisites get placeholders
    for name, l in lists.items():
        for code in l["courses"]:
            if "XX" not in code and code not in courses:
                put(code, None, 3, "list", credits_inferred=True)
    for code, c in list(courses.items()):
        for grp in (c["prereq"] or []):
            for p in grp:
                if norm(p) not in courses:
                    put(p, None, 3, "prereq-reference", credits_inferred=True)

    # ---- 4. curricula from the HTML guides
    for poid, r in parsed.items():
        pid, pname = PROGRAMS[poid]
        reqs = []
        for it in sorted(r["items"], key=lambda x: TERM[(x["year"], x["sem"])]):
            term = TERM[(it["year"], it["sem"])]
            rid = f"{pid}-{len(reqs) + 1:02d}"
            if it["kind"] == "course":
                reqs.append(dict(id=rid, type="course", code=it["code"], term=term))
                continue
            title = it["title"].replace("&nbsp;", "").strip()
            cat = categorize(title)
            e = dict(id=rid, type="elective", label=title, category=cat, credits=it["credits"], term=term)
            if cat in GENED_BY_CAT:
                e.update(fill="list", list_ref=GENED_BY_CAT[cat])
            elif pid == "EE" and re.match(r"^ECEN 4xx$", title):
                e.update(fill="list", list_ref="EE_TECH_B" if it["foot"] == "b" else "EE_TECH_C")
            elif pid == "CPE" and cat == "technical":
                e.update(fill="list", list_ref="CPE_TECH_B" if it["foot"] == "b" else "CPE_TECH_BC")
            elif pid == "ME" and "4xx" in title:
                e.update(fill="partial", approved=["MEEN 4xx"])
            else:
                e.update(fill="attest")            # no machine-readable list in the catalog guide
            reqs.append(e)
        bad, total_sum = crosscheck(r)
        disc = []
        for y, s, want, got in bad:
            disc.append(f"{y} {s}: catalog Semester Total says {want} but the listed courses sum to {got}")
        if total_sum != r["curriculum_total"]:
            disc.append(f"Listed courses sum to {total_sum:g} credits but the catalog states {r['curriculum_total']}")
        mg = {}
        if r["major_c_minus"]:
            mg["C-"] = [norm(c) for c in r["major_c_minus"]]
        notes = [n["text"] for n in r["notes"]]
        if pid == "CPE" and "e" in r["footnotes"]:
            notes.append(r["footnotes"]["e"])
        if pid == "EE": notes.append("Technical electives: max 2 courses from a given area (lists EE_TECH_B groups); not enforced by the audit")
        if pid in ("ISE",): notes.append("Catalog footnote: " + r["footnotes"]["1"])
        curricula[pid] = dict(
            program_id=pid, program_name=pname, catalog_year=CATALOG_YEAR, total_credits=r["curriculum_total"],
            source_url=CAT_URL.format(poid=poid), source_detail="Saved catalog page (curriculum guide)",
            retrieved=RETRIEVED, requirements=reqs, min_grade=mg, notes=notes, known_discrepancies=disc)

    # ---- 5. CS from the handbook
    reqs = []
    for term, kind, payload in sorted(H.CS_PLAN, key=lambda x: x[0]):
        rid = f"CS-{len(reqs) + 1:02d}"
        if kind == "course":
            reqs.append(dict(id=rid, type="course", code=payload, term=term))
        else:
            label, cat, cr, fill, ref = payload
            e = dict(id=rid, type="elective", label=label, category=cat, credits=float(cr), term=term, fill=fill)
            if ref: e["list_ref"] = ref
            reqs.append(e)
    curricula["CS"] = dict(
        program_id="CS", program_name=PROGRAMS["3087"][1], catalog_year=CATALOG_YEAR, total_credits=120,
        source_url=CAT_URL.format(poid="3087"),
        source_detail="CS Undergraduate Handbook (rev. 6/25/2025) p.6, 'Computer Science BS Curriculum (Starting Fall 2023)'; "
                      "the catalog page for CS was not in the saved set - cross-check against it",
        retrieved=RETRIEVED, requirements=reqs, min_grade=H.CS_MIN_GRADE,
        notes=["Other CS tracks in the handbook (pre-calculus, cyber security concentration/certificate, "
               "health informatics, community-college transfer) are not yet encoded",
               "Science elective rule (12 hr from Group 1 or Group 2) is checked by credits from the pool only"],
        known_discrepancies=[])

    # ---- 6. validate sums per term / total
    for pid, cur in curricula.items():
        s = sum(courses[norm(q["code"])]["credits"] if q["type"] == "course" else q["credits"] for q in cur["requirements"])
        report.append(f"{pid}: {len(cur['requirements'])} requirements, {s:g} credits, catalog total {cur['total_credits']}")
        if pid == "CS":
            for t, want in H.CS_SEM_TOTALS.items():
                got = sum(courses[norm(q["code"])]["credits"] if q["type"] == "course" else q["credits"]
                          for q in cur["requirements"] if q["term"] == t)
                assert got == want, (t, got, want)
            assert s == 120, s

    # ---- 7. first-year core = courses in the first two terms of ALL six programs
    first = {pid: {norm(q["code"]) for q in c["requirements"] if q["type"] == "course" and q["term"] <= 2}
             for pid, c in curricula.items()}
    core = sorted(set.intersection(*first.values()))
    terms = {}
    for pid, c in curricula.items():
        for q in c["requirements"]:
            if q["type"] == "course" and norm(q["code"]) in core:
                terms.setdefault(norm(q["code"]), []).append(q["term"])
    core_reqs = [dict(id=f"CORE-{i + 1:02d}", type="course", code=code, term=Counter(terms[code]).most_common(1)[0][0])
                 for i, code in enumerate(core)]
    curricula["CORE"] = dict(
        program_id="CORE", program_name="First-year engineering core (courses in the first two terms of all six programs)",
        catalog_year=CATALOG_YEAR, total_credits=sum(courses[c]["credits"] for c in core),
        source_url="derived", source_detail="Intersection of the six program curricula (tools/build_data.py)",
        retrieved=RETRIEVED, requirements=core_reqs, min_grade={}, notes=[], known_discrepancies=[])
    union = sorted(set.union(*first.values()))
    md = ["# First-year core (derived)", "",
          "The core is the set of courses that appear in the first two terms of **all six** programs.",
          "Generated by `tools/build_data.py`; do not hand-edit.", "",
          "| Course | Credits | " + " | ".join(curricula) .replace("CORE", "") .replace(" | ", " | ").strip(" |") + " |"]
    pids = [p for p in curricula if p != "CORE"]
    md[-1] = "| Course | Credits | " + " | ".join(pids) + " |"
    md.append("|---|---|" + "---|" * len(pids))
    for code in union:
        md.append(f"| {code} {'(core)' if code in core else ''} | {courses[code]['credits']:g} | " +
                  " | ".join("x" if code in first[p] else "" for p in pids) + " |")
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "FIRST_YEAR_CORE.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ---- 8. transfer map
    eq = []
    for cc, ttl, cr, status, tgt, also, note in H.CS_TRANSFER:
        e = dict(institution_id="NCCCS", institution="Any N.C. community college (NCCCS Common Course Library codes)",
                 cc_course=cc, cc_title=ttl, credits=float(cr), status=status, ncat_equivalent=[], also_requires=also,
                 note=note, source="CS Undergraduate Handbook p.12, community-college transfer curriculum dated 2016-06-15",
                 source_url="handbook", guide_year="2016", verified=False)
        if status == "direct": e["ncat_equivalent"] = tgt
        else: e["category"] = tgt
        eq.append(e)

    # ---- 9. usage, write
    used = {}
    for pid, cur in curricula.items():
        if pid == "CORE": continue
        for q in cur["requirements"]:
            if q["type"] == "course": used.setdefault(norm(q["code"]), set()).add(pid)
    for name, l in lists.items():
        for c in l["courses"]:
            used.setdefault(c, set()).add("list:" + name)
    for code, c in courses.items():
        c["used_in"] = sorted(used.get(code, []))
        c["sources"] = sorted(c["sources"])
    out = ROOT / "data"
    (out / "curricula").mkdir(parents=True, exist_ok=True); (out / "transfer").mkdir(parents=True, exist_ok=True)
    json.dump(dict(_note="Hand-encoded from catalog.ncat.edu 2025-2026 guides and the CS handbook; see docs/DATA_DICTIONARY.md",
                   courses=dict(sorted(courses.items()))), open(out / "courses.json", "w"), indent=1)
    json.dump(dict(lists=lists), open(out / "lists.json", "w"), indent=1)
    for pid, cur in curricula.items():
        json.dump(cur, open(out / "curricula" / f"{pid}.json", "w"), indent=1)
    json.dump(dict(_note="SEED from the CS handbook (2016). NOT yet verified against the UNC System Transfer Course Guide.",
                   equivalencies=eq), open(out / "transfer" / "transfer_map.json", "w"), indent=1)
    json.dump(dict(_note="The team's 10 target community colleges. Equivalencies under institution_id 'NCCCS' "
                         "(Common Course Library codes) apply to every one of them; college-specific rows, if any, "
                         "use the id below and take precedence.",
                   institutions=INSTITUTIONS), open(out / "transfer" / "institutions.json", "w"), indent=1)
    todo = [(c, v["title"], v["credits"], ";".join(u for u in v["used_in"] if not u.startswith("list:")) or "(list only)")
            for c, v in sorted(courses.items()) if v["prereq_status"] == "unknown"]
    with open(out / "prereq_todo.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "title", "credits", "used_in", "prereq_cnf (e.g. MATH 131 ; COMP 167|COMP 165)",
                    "coreq", "prereq_note", "catalog_source"])
        for row in todo: w.writerow(list(row) + ["", "", "", ""])

    print("\n".join(report))
    print(f"courses: {len(courses)}  with prereqs from handbook: "
          f"{sum(v['prereq_status'] != 'unknown' for v in courses.values())}  prereq unknown: {len(todo)}")
    print(f"inferred credits: {sum(1 for v in courses.values() if v.get('credits_inferred'))}; "
          f"titles missing: {sum(1 for v in courses.values() if v['title'] == NO_TITLE)}")
    print(f"first-year core ({len(core)}): {core}")
    print(f"transfer equivalencies: {len(eq)}")
    print("conflicts between sources:")
    for c in conflicts: print("  -", c)
    for pid, cur in curricula.items():
        for d in cur["known_discrepancies"]: print(f"  DISCREPANCY {pid}: {d}")


if __name__ == "__main__":
    main(sys.argv[1])
