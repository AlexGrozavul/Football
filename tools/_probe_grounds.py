"""THROWAWAY probe #2, 2026-09-26. Stadium articles, their coordinates,
and the Liga II stadiums table. Removed in the same branch."""
import json, re, time, urllib.parse, urllib.request
UA = "football-planner-probe/1.0 (github.com/AlexGrozavul/football)"

def get(url):
    for i in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print("   retry", i, e); time.sleep(15 * (i + 1))
    return None

def wikitext(lang, title):
    time.sleep(4)
    d = get("https://%s.wikipedia.org/w/api.php?action=parse&format=json&formatversion=2"
            "&prop=wikitext&redirects=1&page=%s" % (lang, urllib.parse.quote(title))) or {}
    return d.get("parse", {}).get("wikitext", "")

def item_for(lang, title):
    time.sleep(2)
    d = get("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims|labels"
            "&languages=en|ro&normalize=1&sites=%swiki&titles=%s" % (lang, urllib.parse.quote(title))) or {}
    for k, v in d.get("entities", {}).items():
        if k.startswith("Q"): return k, v
    return None, None

def item(q):
    time.sleep(2)
    d = get("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&props=claims|labels|sitelinks"
            "&languages=en|ro&ids=" + q) or {}
    return d.get("entities", {}).get(q)

def summarise(q, e):
    if not e: print("   no item"); return
    c = e.get("claims", {})
    lab = (e.get("labels", {}).get("ro") or e.get("labels", {}).get("en") or {}).get("value")
    out = [q, lab]
    for p in ("P625", "P131", "P1083", "P466", "P3999", "P5817", "P31"):
        for s in c.get(p, []):
            m = s["mainsnak"]
            if m["snaktype"] != "value": continue
            v = m["datavalue"]["value"]
            if isinstance(v, dict):
                v = ("%.6f,%.6f" % (v["latitude"], v["longitude"])) if "latitude" in v else \
                    v.get("id") or v.get("amount") or v.get("time")
            out.append("%s=%s" % (p, v))
    print("   WD", " ".join(map(str, out)))

FIELDS = re.compile(r"^\s*\|\s*(clubname|fullname|name|nume|ground|stadium|stadion|capacity|capacitate|"
                    r"dissolved|founded|league|season|position|location|coordinates|coord|locatie|"
                    r"tenants|opened|closed|owner|surface)\s*=\s*(.*)$", re.I)

ARTS = [("en", "CSO Băicoi"), ("en", "ACS Mediaș"), ("ro", "ACS Mediaș 2022"),
        ("en", "CSM Vaslui (football)"), ("en", "CSL Ștefănești"),
        ("en", "Ruși-Ciutea Sportsbase"), ("en", "Vasile Enache Stadium"),
        ("en", "Chirică Pușcașu Stadium"), ("en", "Stadionul Municipal (Zalău)"),
        ("en", "Jean Pădureanu Stadium"), ("en", "Gaz Metan Stadium (Mediaș)"),
        ("en", "Stadionul Municipal (Vaslui)"), ("en", "Stadionul Petrolul (Băicoi)"),
        ("en", "Stadionul Municipal (Bacău)"), ("en", "Stadionul Treapt"),
        ("en", "Constantin Anghelache Stadium"), ("ro", "Stadionul Municipal (Bacău)")]
for lang, title in ARTS:
    t = wikitext(lang, title)
    print("\n### ARTICLE", lang, title, "chars:", len(t))
    for line in t.splitlines()[:150]:
        if FIELDS.match(line): print("   ", line.strip()[:220])
    for m in re.finditer(r"\{\{[Cc]oord\|[^}]*\}\}", t):
        print("    COORD", m.group(0)[:160]); break
    body = re.sub(r"\{\{[^{}]*\}\}", "", t)
    body = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", body, flags=re.S)
    first = [l for l in body.splitlines() if l.strip() and not l.strip().startswith(("|", "{", "}", "[[File", "[[Fișier", "<!--"))]
    print("    LEAD", " ".join(first[:3])[:700])
    for kw in ("closed", "derelict", "abandon", "demolish", "închis", "abandonat", "degradat", "ground", "stadium", "stadion"):
        for mm in re.finditer(kw, body, re.I):
            print("    ctx[%s]: %s" % (kw, body[max(0, mm.start()-200):mm.end()+200].replace("\n", " ")))
            break
    if t:
        q, e = item_for(lang, title)
        summarise(q, e)

for q in ("Q28230311", "Q104869165", "Q7596361", "Q1532041", "Q1322113"):
    print("\n### ITEM", q); summarise(q, item(q))

t = wikitext("en", "2026–27 Liga II")
print("\n### LIGA II TABLES")
for tb in re.findall(r"\{\|.*?\n\|\}", t, flags=re.S):
    if re.search(r"[Ss]tadium", tb) and re.search(r"[Cc]apacity", tb):
        print(tb[:9000]); break
t = wikitext("en", "2026–27 Liga III")
print("\n### LIGA III STADIUM-ISH LINES")
for tb in re.findall(r"\{\|.*?\n\|\}", t, flags=re.S):
    if re.search(r"[Ss]tadium", tb):
        for line in tb.splitlines():
            if any(k in line for k in ("Băicoi", "Mediaș", "Zalău", "Vaslui", "Modelu", "Bacău")):
                print("   ", line[:250])
print("\n### DONE")
