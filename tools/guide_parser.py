"""Parse N.C. A&T catalog curriculum-guide HTML pages (saved from catalog.ncat.edu).

Two page layouts are handled:
  * "preview_program ... &print"  (Civil, Computer, Industrial & Systems, Mechanical)
  * "preview_degree_planner ... &print" (Electrical)

Output is a common structure per program:
  items: [{year, sem, kind: course|elective, code?, title, credits, foot, credits_note?}]
  sem_totals: the catalog's own "Semester Total" lines (used to cross-check parsing)
  footnotes: {marker: text}
Standard library + bs4.
"""
from __future__ import annotations

import glob
import re
from pathlib import Path

from bs4 import BeautifulSoup

COURSE = re.compile(r"^([A-Z]{2,5}) (\d{3}[A-Z]?) - (.+)$")
ADHOC = re.compile(r"^(.*?)\s*(\d+(?:\.\d+)?)\s*Credit\(s\)\s*$")
YEAR = re.compile(r"^(Freshman|Sophomore|Junior|Senior) Year$")
SEM = re.compile(r"^(First|Second|Summer\w*)\s*Semester$|^Summer.*$")
MARK = re.compile(r"^(?:[a-e]|\d)(?: or (?:[a-e]|\d))*$")
CREDITS = re.compile(r"^(\d+(?:\.\d+)?)(?: or (\d+(?:\.\d+)?))?$")


def clean(s: str) -> str:
    s = s.replace("\xa0", " ").replace("​", "")
    return re.sub(r"\s+", " ", s).strip()


def _credit_value(m):
    """'0 or 3' -> (3.0, "catalog lists '0 or 3'")."""
    lo, hi = m.group(1), m.group(2)
    if hi is None:
        return float(lo), None
    return max(float(lo), float(hi)), f"catalog lists '{lo} or {hi}'"


def parse_preview(path):
    raw = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    title = clean(soup.title.get_text()).replace("Program: ", "").split(" - North Carolina")[0]
    poid = re.search(r"poid=(\d+)", raw).group(1)
    lines = [clean(l) for l in soup.find("body").get_text("\n").split("\n")]
    lines = [l for l in lines if l]
    a = lines.index("Curriculum Guide")
    b = next(i for i, l in enumerate(lines) if i > a and l.startswith("Major Program Requirements"))
    stated = next((int(m.group(1)) for l in lines
                   if (m := re.search(r"must complete (\d+) credit hours", l))), None)
    out = dict(program=title, poid=poid, stated_total=stated, items=[], sem_totals=[],
               notes=[], unparsed=[], footnotes={}, major_c_minus=[], c_minus_text=None)
    year = sem = None
    in_foot = False
    cur_mark = None
    i = a + 1
    while i < b:
        l = lines[i]
        if in_foot:
            if MARK.match(l):
                cur_mark = l; out["footnotes"][cur_mark] = []
            elif cur_mark:
                out["footnotes"][cur_mark].append(l)
            i += 1
            continue
        if YEAR.match(l):
            year, sem = l, None
        elif SEM.match(l):
            sem = l
        elif l.startswith("Semester Total:"):
            out["sem_totals"].append(dict(year=year, sem=sem, total=int(re.search(r"\d+", l).group())))
        elif l.startswith("Total Credit Hours:"):
            out["curriculum_total"] = int(re.search(r"\d+", l).group())
            in_foot = True
        elif COURSE.match(l):
            m = COURSE.match(l)
            nxt = CREDITS.match(lines[i + 1]) if i + 1 < b else None
            if not nxt:
                out["unparsed"].append(dict(year=year, sem=sem, text=l, why="no credits line"))
            else:
                cr, note = _credit_value(nxt)
                i += 1
                if i + 1 < b and lines[i + 1] == "Credit(s)":
                    i += 1
                it = dict(year=year, sem=sem, kind="course", code=f"{m.group(1)} {m.group(2)}",
                          title=m.group(3), credits=cr, foot=None)
                if note: it["credits_note"] = note
                out["items"].append(it)
        elif (m := ADHOC.match(l)) and not l.startswith("Semester"):
            out["items"].append(dict(year=year, sem=sem, kind="elective", title=m.group(1).strip(),
                                     credits=float(m.group(2)), foot=None, raw=l))
        elif (i + 1 < b and (m := re.match(r"^(\d+(?:\.\d+)?)\s*Credit\(s\)$", lines[i + 1]))
              and not MARK.match(l)):
            out["items"].append(dict(year=year, sem=sem, kind="elective", title=l,
                                     credits=float(m.group(1)), foot=None, raw=l + " " + lines[i + 1]))
            i += 1
        elif MARK.match(l) and out["items"]:
            out["items"][-1]["foot"] = l           # footnote marker belongs to the previous row
        elif l == "Credit(s)":
            pass
        elif re.search(r"\b(increased|reduced) to \d+ credit", l):
            out["notes"].append(dict(year=year, sem=sem, text=l))
        else:
            out["unparsed"].append(dict(year=year, sem=sem, text=l))
        i += 1
    out["footnotes"] = {k: clean(" ".join(v)).replace(" ,", ",") for k, v in out["footnotes"].items()}
    j = next((k for k in range(b, len(lines)) if lines[k].startswith("Students must earn")), None)
    if j is not None:
        out["c_minus_text"] = lines[j]
        k = j + 1
        while k < len(lines) and not lines[k].startswith("Return to"):
            if (m := COURSE.match(lines[k])):
                out["major_c_minus"].append(f"{m.group(1)} {m.group(2)}")
            k += 1
    return out


def parse_planner(path):
    raw = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(raw, "html.parser")
    prog = clean(soup.find(id="acalog-degree-planner-catalog-program").get_text()).replace("Program: ", "")
    poid = re.search(r"poid=(\d+)", raw).group(1)
    stated = int(re.search(r"must complete (\d+) credit hours", raw).group(1))
    out = dict(program=prog, poid=poid, stated_total=stated, items=[], sem_totals=[], notes=[],
               unparsed=[], footnotes={}, major_c_minus=[], c_minus_text=None)
    year = sem = None
    section = "guide"
    foot_text = ""
    for tr in soup.select("tr"):
        core = tr.select_one("td.acalog-core")
        if core:
            h = core.find(["h2", "h3", "h4", "h5"])
            if h is not None:
                t = clean(h.get_text())
                if h.name == "h2":
                    section, year, sem = t, None, None
                    if t.startswith("Major Program"):
                        div = core.find("div", class_="pdp-hideable")
                        out["c_minus_text"] = clean(div.get_text(" ")) if div else None
                elif h.name == "h3" and t.startswith("Total Credit Hours"):
                    out["curriculum_total"] = int(re.search(r"\d+", t).group())
                    foot_text = clean(core.find("div", class_="pdp-hideable").get_text(" "))
                elif h.name == "h3":
                    year = t
                elif h.name == "h4":
                    sem = t
                elif h.name == "h5":
                    out["sem_totals"].append(dict(year=year, sem=sem, total=int(re.search(r"\d+", t).group())))
            continue
        td = tr.select_one("td.course")
        if td:
            foot = "".join(s.get_text() for s in td.find_all("sup")) or None
            for s in td.find_all("sup"):
                s.extract()
            m = COURSE.match(clean(td.get_text()))
            cr = float(clean(tr.select_one("td.credits strong").get_text()))
            if section.startswith("Major Program"):
                out["major_c_minus"].append(f"{m.group(1)} {m.group(2)}")
            else:
                out["items"].append(dict(year=year, sem=sem, kind="course", code=f"{m.group(1)} {m.group(2)}",
                                         title=m.group(3), credits=cr, foot=foot))
            continue
        td = tr.select_one("td.ad-hoc")
        if td:
            for p in td.find_all("p"):
                foot = "".join(s.get_text() for s in p.find_all("sup")) or None
                for s in p.find_all("sup"):
                    s.extract()
                t = clean(p.get_text(" "))
                m = re.match(r"^(.*?)\s*(\d+)\s*Credit\(s\)$", t)
                out["items"].append(dict(year=year, sem=sem, kind="elective", title=m.group(1).strip(),
                                         credits=float(m.group(2)), foot=foot, raw=t))
    # footnote text: "a Capstone ... b Technical Elective (...) c Technical Elective (...) d This course ..."
    parts = re.split(r"(?:^|\s)([a-e])\s+(?=[A-Z])", foot_text)
    for k in range(1, len(parts) - 1, 2):
        out["footnotes"][parts[k]] = parts[k + 1].strip()
    return out


def load_all(html_dir):
    res = {}
    for f in sorted(glob.glob(str(Path(html_dir) / "*.html"))):
        r = parse_planner(f) if "Electrical" in f else parse_preview(f)
        res[r["poid"]] = r
    return res


def crosscheck(r):
    """Compare parsed credits against the catalog's own semester totals."""
    by = {}
    for it in r["items"]:
        k = (it["year"], it["sem"])
        by[k] = by.get(k, 0) + (it["credits"] or 0)
    bad = [(s["year"], s["sem"], s["total"], by.get((s["year"], s["sem"]))) for s in r["sem_totals"]
           if by.get((s["year"], s["sem"])) != s["total"]]
    return bad, sum(by.values())


TERM = {("Freshman Year", "First Semester"): 1, ("Freshman Year", "Second Semester"): 2,
        ("Sophomore Year", "First Semester"): 3, ("Sophomore Year", "Second Semester"): 4,
        ("Junior Year", "First Semester"): 5, ("Junior Year", "Second Semester"): 6,
        ("Senior Year", "First Semester"): 7, ("Senior Year", "Second Semester"): 8}
