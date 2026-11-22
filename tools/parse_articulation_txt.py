"""Best-effort parser for the Alamance printout (text copied from the PDF of the articulation tool).
The printout loses spaces in titles and lists the OR/AND connectors of a page in a block at the end of the
page.  Rows are reconstructed: extra options (second, third ...) take the page's connectors in order.
Each page is checked (number of connectors == number of extra options); pages that don't match are flagged.
"""
import re, json, sys
CC = re.compile(r"^([A-Z]{2,4})\s?(\d{3}[A-Z]?)$")
AT = re.compile(r"^([A-Z]{2,5})\s?(\d[0-9A-Z]{1,4})\s+(\d+(?:\.\d+)?)$")
HDR = re.compile(r"^(LOCATION INSTITUTION|\d\d/\d\d/\d\d, |https://cms-apps|Alamance Community College$)")

def parse(path):
    lines = [l.strip() for l in open(path, encoding="utf-8", errors="ignore").read().replace("\r", "").split("\n")]
    start = next(i for i, l in enumerate(lines) if l.startswith("TRANSFERCOURSES") or l.startswith("TRANSFER COURSES"))
    pages, cur = [], {"recs": [], "conns": []}
    rec = None
    for l in lines[start + 1:]:
        if not l:
            continue
        if l.startswith("LOCATION INSTITUTION"):
            pages.append(cur); cur = {"recs": [], "conns": []}; rec = None; continue
        if HDR.match(l):
            continue
        if l in ("OR", "AND"):
            cur["conns"].append(l); continue
        m = AT.match(l)
        if m and rec is not None:
            code = f"{m.group(1)} {m.group(2)}"
            rec["options"].append({"code": code, "credits": m.group(3), "title": " ".join(rec.pop("_t", []))})
            continue
        m = CC.match(l)
        if m:
            rec = {"cc": f"{m.group(1)} {m.group(2)}", "options": [], "_t": []}
            cur["recs"].append(rec); continue
        if rec is not None:
            rec.setdefault("_t", []).append(l)
    pages.append(cur)
    out, bad = [], []
    for pi, p in enumerate(pages, 1):
        extra = sum(max(0, len(r["options"]) - 1) for r in p["recs"])
        conns = list(p["conns"])
        ok = extra == len(conns)
        if not ok:
            bad.append((pi, extra, len(conns)))
        for r in p["recs"]:
            for j, o in enumerate(r["options"]):
                o["conn"] = (conns.pop(0) if conns else "?") if j > 0 else ""
            r["page"] = pi; r["grouping_reliable"] = ok or len(r["options"]) < 2
            r.pop("_t", None)
            if r["options"]:
                out.append(r)
    return out, bad

if __name__ == "__main__":
    rows, bad = parse(sys.argv[1])
    print(len(rows), "rows; pages with connector mismatch:", bad, file=sys.stderr)
    print(json.dumps(rows, indent=1))
