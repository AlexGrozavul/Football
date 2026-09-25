"""TEMPORARY probe 3 for the France tier 1/2 pass. Removed in the same branch."""
import re, sys, html
sys.path.insert(0, "tools")
import check_rosters as cr

def p(*a): print(" ".join(str(x) for x in a), flush=True)

def infobox_lines(page):
    m = re.search(r'<table class="infobox.*?</table>', page, re.S)
    if not m: return []
    out = []
    for row in re.findall(r"<tr.*?</tr>", m.group(0), re.S):
        t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", row))).strip()
        if re.search(r"League|20\d\d|Dissolved|Founded|Ground", t): out.append(t[:200])
    return out

for art in ["AS Béziers (2007)", "FC Martigues", "US Orléans"]:
    page, real, err = cr.fetch_article(art)
    p("CLUB", art, "->", real, err or "")
    for l in infobox_lines(page or ""): p("    ", l)
    for s in re.findall(r"[^.]{0,160}relegat[^.]{0,160}\.", re.sub(r"<[^>]+>", "", page or ""))[:4]:
        p("    rel:", re.sub(r"\s+", " ", html.unescape(s)).strip()[:300])

for art in ["2026–27 Championnat National", "2026–27 National", "2026–27 Championnat National (France)", "Championnat National"]:
    page, real, err = cr.fetch_article(art)
    p("NATIONAL", art, "->", real, err or "")
    if page and not err:
        tables, shape = cr.roster_tables(page)
        names = []
        for t, h in tables:
            for title, cap in cr.rows_of(t, h):
                if title not in names: names.append(title)
        p("   ", len(tables), shape, len(names), names)
p("=== END OF PROBE 3 ===")
