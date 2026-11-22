"""Build data/transfer/transfer_map.json from the A&T Transfer Articulation Tool printouts.

Inputs (not stored in the repo): one saved HTML page per college (+ the Alamance text printout).
Usage: python tools/build_transfer.py <input_dir_with_files> [--out data/transfer/transfer_map.json]
Keeps the NCCCS seed rows (from the 2016 CS handbook, unverified) and adds college-specific rows,
which take precedence in the audit engine.  Only rows that touch a course in courses.json are kept;
the rest are counted in the summary (they only matter for free-elective credit).
"""
import json, sys, csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent)); sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "audit"))
from parse_articulation import parse_html
from parse_articulation_txt import parse as parse_txt
from degree_audit import norm

ROOT = Path(__file__).parent.parent
FILES = {"CCCC": "Central_Carolina_Community_College_Transfer.html", "DDCC": "Davidson_Davie_Transfer.html",
         "FTCC": "Forsyth_CC_Transfer.html", "GTCC": "Guildford_Tech_Transfer.html", "PCC": "Piedmont_CC_Transfer.html",
         "RANDCC": "Randolph_CC_Transfer.html", "RCC": "Rockingham_CC_Transfer.html", "SCC": "Surry_CC_Transfer.html",
         "WTCC": "Wake_Technical_CC_Transfer.html", "ACC": "attachment.txt"}
SRC = "N.C. A&T Transfer Articulation Tool (cms-apps.ncat.edu/transfer-articulation), unofficial guide; grade of C or higher required"


def groups(options):
    """[{'conn','code'}...] -> list of alternatives; AND binds tighter than OR."""
    alts = []
    for o in options:
        if o["conn"] == "OR" or not alts:
            alts.append([])
        alts[-1].append(o)
    return alts


def main(indir, out):
    courses = json.load(open(ROOT / "data/courses.json"))["courses"]
    insts = {i["institution_id"]: i["name"] for i in json.load(open(ROOT / "data/transfer/institutions.json"))["institutions"]}
    old = json.load(open(ROOT / "data/transfer/transfer_map.json"))
    seed = [e for e in old["equivalencies"] if e["institution_id"] == "NCCCS"]
    rows, summary, recheck, credit_diff = list(seed), {}, [], []
    for iid, fn in FILES.items():
        f = next(Path(indir).glob("*" + fn))
        if fn.endswith(".txt"):
            parsed, _bad = parse_txt(f)
        else:
            parsed = parse_html(f)
        kept, seen = 0, set()
        for r in parsed:
            if not any(norm(o["code"]) in courses for o in r["options"]):
                continue
            if len(r["options"]) > 1 and r.get("grouping_reliable") is False:
                recheck.append([iid, r["cc"], " ".join((o["conn"] + " " + o["code"]).strip() for o in r["options"]), f"printout page {r['page']}"])
                continue
            if r["cc"] in seen:
                continue
            seen.add(r["cc"])
            alts, scope_note, cr = [], [], {}
            for g in groups(r["options"]):
                inn = [norm(o["code"]) for o in g if norm(o["code"]) in courses]
                out_ = [norm(o["code"]) for o in g if norm(o["code"]) not in courses]
                if not inn:
                    continue
                if out_:
                    scope_note.append(f"{' + '.join(inn)} also comes with {' + '.join(out_)} (not in our 6 curricula)")
                if inn not in alts:
                    alts.append(inn)
                for o in g:
                    c = norm(o["code"])
                    if c in courses:
                        cr[c] = float(o["credits"])
                        if abs(cr[c] - float(courses[c]["credits"])) > 1e-9:
                            credit_diff.append((iid, r["cc"], c, cr[c], courses[c]["credits"]))
            raw = " ".join((o["conn"] + " " + o["code"]).strip() for o in r["options"])
            e = {"institution_id": iid, "institution": insts[iid], "cc_course": r["cc"], "cc_title": r.get("cc_title") or None,
                 "credits": sum(cr[c] for c in alts[0]), "status": "direct", "ncat_equivalent": alts[0],
                 "also_requires": [], "note": "; ".join(scope_note) or None, "tool_listing": raw,
                 "source": SRC, "source_url": "https://cms-apps.ncat.edu/transfer-articulation/", "guide_year": "2026",
                 "retrieved": "2026-11-10", "verified": True, "ncat_credits": cr}
            if len(alts) > 1:
                e["alternatives"] = alts
                e["note"] = "; ".join(filter(None, ["A&T lists these as OR options: " + " OR ".join(" + ".join(a) for a in alts), e["note"]]))
            rows.append(e); kept += 1
        summary[iid] = (len(parsed), kept)
    doc = {"_note": "NCCCS rows: SEED from the CS handbook (2016), NOT verified. College rows: from the A&T Transfer Articulation Tool "
                    "(retrieved 2026-11-10), limited to equivalencies that touch a course in our 6 curricula. College rows override NCCCS rows.",
           "equivalencies": rows}
    json.dump(doc, open(out, "w"), indent=1)
    (ROOT / "docs").mkdir(exist_ok=True)
    with open(ROOT / "docs" / "transfer_recheck.csv", "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["college", "cc_course", "tool_listing_as_parsed", "where"]); w.writerows(recheck)
    for k, (n, kept) in summary.items():
        print(f"{k:7} entries in tool: {n:5}  kept (touch our curricula): {kept}")
    print("rows total", len(rows), "| recheck", len(recheck), "| credit differences", len(credit_diff))
    for d in credit_diff[:40]:
        print("  credit differs:", d)

if __name__ == "__main__":
    main(sys.argv[1], ROOT / "data/transfer/transfer_map.json")
