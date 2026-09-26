"""THROWAWAY probe, 2026-09-26. Reads Wikidata and Wikipedia for the
Romanian coordinate-review questions and prints the answers. Removed in
the same branch. Writes nothing."""
import json, re, time, urllib.parse, urllib.request

UA = "football-planner-probe/1.0 (github.com/AlexGrozavul/football)"
QIDS = """Q106779019 Q66423967 Q5014447 Q55864953 Q74127553 Q4680389 Q18539440
Q12723169 Q56677281 Q24895825 Q130235269 Q1024395 Q55584106 Q113573276
Q99448017 Q118904605 Q113331350 Q120784310 Q66424146 Q856790""".split()
PROPS = ["P31", "P17", "P118", "P115", "P576", "P571", "P159", "P131",
         "P625", "P1448", "P127", "P156", "P155", "P1366", "P1365"]

def get(url, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            print("   retry", i, e); time.sleep(5)
    return None

def wd(ids):
    out = {}
    for i in range(0, len(ids), 40):
        u = ("https://www.wikidata.org/w/api.php?action=wbgetentities&format=json"
             "&props=labels|claims|sitelinks&languages=en|ro&ids=" + "|".join(ids[i:i+40]))
        d = get(u) or {}
        out.update(d.get("entities", {}))
    return out

def val(s):
    dv = s["mainsnak"]
    if dv["snaktype"] != "value":
        return "<" + dv["snaktype"] + ">"
    v = dv["datavalue"]["value"]
    if isinstance(v, dict):
        if "id" in v: return v["id"]
        if "time" in v: return v["time"][1:11]
        if "latitude" in v: return "%.6f,%.6f" % (v["latitude"], v["longitude"])
        if "text" in v: return v["text"]
    return str(v)

def quals(s):
    q = s.get("qualifiers", {})
    bits = []
    for p in ("P580", "P582"):
        for x in q.get(p, []):
            if x["snaktype"] == "value":
                bits.append(p + "=" + x["datavalue"]["value"]["time"][1:5])
    return " ".join(bits)

ents = wd(QIDS)
refs = set()
for e in ents.values():
    for p in PROPS:
        for s in e.get("claims", {}).get(p, []):
            v = val(s)
            if re.fullmatch(r"Q\d+", v): refs.add(v)
labels = {k: (v.get("labels", {}).get("en") or v.get("labels", {}).get("ro") or {}).get("value", "?")
          for k, v in wd(sorted(refs)).items()}
# coordinates of grounds
grounds = wd(sorted(r for r in refs))
gcoord = {k: val(v["claims"]["P625"][0]) for k, v in grounds.items() if "P625" in v.get("claims", {})}

articles = []
for q in QIDS:
    e = ents.get(q, {})
    lab = (e.get("labels", {}).get("ro") or e.get("labels", {}).get("en") or {}).get("value", "?")
    sl = e.get("sitelinks", {})
    print("\n### ANSWER", q, lab, "| sitelinks:", len(sl),
          "| enwiki:", sl.get("enwiki", {}).get("title"), "| rowiki:", sl.get("rowiki", {}).get("title"))
    for p in PROPS:
        for s in e.get("claims", {}).get(p, []):
            v = val(s)
            extra = labels.get(v, "")
            if p == "P115" and v in gcoord: extra += " @" + gcoord[v]
            print("   %s %s [%s] %s %s" % (p, v, s["rank"], extra, quals(s)))
    for site in ("enwiki", "rowiki"):
        if site in sl:
            articles.append((q, site[:2], sl[site]["title"]))

FIELDS = re.compile(r"^\s*\|\s*(clubname|fullname|ground|stadium|capacity|dissolved|founded|league|season|position|nickname|short name)\s*=\s*(.*)$", re.I)
ROFIELDS = re.compile(r"^\s*\|\s*(nume|nume complet|stadion|capacitate|desființat|desfiintat|fondat|liga|campionat|sezon|poziție)\s*=\s*(.*)$", re.I)

def wikitext(lang, title):
    u = ("https://%s.wikipedia.org/w/api.php?action=parse&format=json&formatversion=2"
         "&prop=wikitext&redirects=1&page=%s" % (lang, urllib.parse.quote(title)))
    d = get(u) or {}
    return d.get("parse", {}).get("wikitext", "")

for q, lang, title in articles:
    t = wikitext(lang, title)
    print("\n### INFOBOX", q, lang, title, "chars:", len(t))
    for line in t.splitlines()[:120]:
        m = FIELDS.match(line) or ROFIELDS.match(line)
        if m: print("   ", line.strip()[:200])
    for kw in ("dissolv", "desfiin", "retras", "withdr", "merged", "fuzion", "succes", "refound"):
        for m in re.finditer(kw, t, re.I):
            print("    ctx[%s]: %s" % (kw, t[max(0, m.start()-150):m.end()+150].replace("\n", " ")))
            break

KEYS = ["Bacău", "Ștefăneșt", "Stefanest", "Bistrița", "Vâlcea", "Vaslui", "Darabani",
        "Modelu", "Mediaș", "Băicoi", "Zalău", "Afumați", "Călărași"]
for art in ("2026–27 Liga II", "2026–27 Liga III"):
    t = wikitext("en", art)
    print("\n### ROSTER", art, "chars:", len(t))
    for line in t.splitlines():
        if any(k in line for k in KEYS) and len(line) < 400:
            print("   ", line.strip()[:300])
print("\n### DONE")
