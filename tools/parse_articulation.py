"""Parse saved A&T Transfer Articulation Tool pages (HTML) into rows.

Each entry: cc_prefix, cc_number, cc_title, and an ordered list of A&T options
{conn: ''|'AND'|'OR', code, title, credits}.  The page marks the connector
with the <li> class: output-A = AND, output-O = OR.
Usage: python tools/parse_articulation.py <html> -> JSON on stdout
"""
import re, json, sys
from bs4 import BeautifulSoup

def parse_html(path):
    soup = BeautifulSoup(open(path, encoding="utf-8", errors="ignore").read(), "html.parser")
    inst = None
    rows = []
    for top in soup.select("li.top"):
        c1 = top.select_one(".child-1")
        if not c1:
            continue
        pre = c1.select_one(".iname")
        if not pre:
            continue
        divs = c1.find_all("div", recursive=False)
        num = divs[0].get_text(" ", strip=True)[len(pre.get_text(strip=True)):].strip()
        title = divs[1].get_text(" ", strip=True) if len(divs) > 1 else ""
        opts = []
        for li in top.select("ul.secondary > li"):
            cls = " ".join(li.get("class", []))
            conn = "AND" if cls.endswith("A") and "output-A" in cls else ("OR" if "output-O" in cls else "")
            d = li.find_all("div", recursive=False)
            code = d[0].get_text(" ", strip=True)
            if "{{" in code:
                continue
            cr = li.select_one(".credits")
            opts.append({"conn": conn, "code": code, "title": li.select_one(".title").get_text(" ", strip=True),
                         "credits": cr.get_text(strip=True) if cr else ""})
        if opts:
            rows.append({"cc": f"{pre.get_text(strip=True)} {num}", "cc_title": title, "options": opts})
    return rows

if __name__ == "__main__":
    print(json.dumps(parse_html(sys.argv[1]), indent=1))
