"""THROWAWAY probe 2. Remove with the temporary workflow step that runs it."""
import re, sys, time, urllib.parse

sys.path.insert(0, "tools")
import check_rosters as CR
import diagnose_p118_rank as RANK

ITEMS = ["Q136715692", "Q24884611", "Q1024390", "Q926152", "Q1386940",
         "Q113541238", "Q368104", "Q55625185"]
PROPS = ["P31", "P17", "P115", "P118", "P571", "P576", "P1365", "P1366",
         "P155", "P156", "P1889"]

HEAD = []


def times(e, prop):
    out = []
    for st in (e.get("claims") or {}).get(prop) or []:
        v = (((st.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {})
        if isinstance(v, dict) and v.get("time"):
            out.append(v["time"].lstrip("+")[:10])
    return out


def qids(e, prop):
    out = []
    for st in (e.get("claims") or {}).get(prop) or []:
        snak = st.get("mainsnak") or {}
        v = (snak.get("datavalue") or {}).get("value") or {}
        vid = v.get("id") if isinstance(v, dict) else None
        out.append(f"{vid or '<' + (snak.get('snaktype') or '?') + '>'}"
                   f"/{st.get('rank')}")
    return out


def descriptions(e):
    d = e.get("descriptions") or {}
    out = []
    for lang in ("en", "ro", "de"):
        v = d.get(lang)
        if isinstance(v, dict):
            v = v.get("value")
        if v:
            out.append(f"{lang}={v}")
    return "; ".join(out)


print("=" * 72)
print("PROBE 2: Hermannstadt, Politehnica Iasi, Bihor -- identity and prose")
print("=" * 72)

# ---------------------------------------------------------- 1. the items
print("\n--- ITEMS")
q = urllib.parse.urlencode({
    "action": "wbgetentities", "ids": "|".join(ITEMS),
    "props": "claims|labels|descriptions|sitelinks",
    "languages": "en|de|ro", "format": "json", "formatversion": "2"})
data, err = CR.get_json_with_retry(f"{CR.WIKIDATA_API}?{q}", "items")
ents = {}
if err or not data or data.get("error"):
    print(f"    READ FAILED: {err or data.get('error')}")
else:
    ents = {k: v for k, v in (data.get("entities") or {}).items()
            if k.startswith("Q") and not v.get("missing")}
for cid in ITEMS:
    e = ents.get(cid)
    if not e:
        print(f"    {cid}: NOT READ / missing")
        continue
    print(f"    {cid}  {RANK.label_of(e)!r}  sitelinks={RANK.sitelink_count(e)}")
    print(f"        desc: {descriptions(e) or '(none)'}")
    print(f"        enwiki: {CR.enwiki_title(e)!r}")
    for prop in PROPS:
        vals = times(e, prop) or qids(e, prop)
        if vals:
            print(f"        {prop}: {', '.join(vals)}")

# --------------------------------------------------- 2. the article prose
NEEDLES = ["Hermannstadt", "Politehnica Ia", "Poli Ia", "Bihor",
           "Farul", "exclud", "withdr", "relegat", "promot", "dissolv",
           "licen", "insolven"]
for article in ("2026–27 Liga I", "2026–27 Liga II"):
    print(f"\n--- PROSE OF {article!r}")
    page, real, err = CR.fetch_article(article)
    if err:
        print(f"    FETCH FAILED: {err}")
        continue
    # Tables out, so what is left is the page's own sentences.
    prose = re.sub(r"<table.*?</table>", " ", page, flags=re.S)
    prose = CR.text_of(prose)
    for needle in NEEDLES:
        for m in re.finditer(re.escape(needle), prose, re.I):
            s = max(0, m.start() - 130)
            snippet = prose[s:m.end() + 130].strip()
            line = f"    [{needle}] ...{snippet}..."
            print(line)
            if needle in ("Hermannstadt", "Politehnica Ia", "Poli Ia"):
                HEAD.append(line)
            break   # one hit per needle is enough to see the sentence
    time.sleep(2)

# ------------------------------------------- 3. the clubs' own articles
for article in ("FC Hermannstadt", "Politehnica Iași"):
    print(f"\n--- CLUB ARTICLE {article!r}")
    page, real, err = CR.fetch_article(article)
    if err:
        print(f"    FETCH FAILED: {err}")
        continue
    print(f"    resolved to {real!r}")
    infobox = re.search(r'<table[^>]*class="[^"]*infobox[^"]*"[^>]*>.*?</table>',
                        page, re.S)
    if infobox:
        rows = re.findall(r"<tr[^>]*>(.*?)</tr>", infobox.group(0), re.S)
        for tr in rows:
            flat = CR.text_of(tr)
            if re.search(r"league|liga|season|founded|dissolv|ground", flat, re.I):
                print(f"      infobox: {flat[:150]}")
    first = CR.text_of(re.sub(r"<table.*?</table>", " ", page, flags=re.S))
    line = f"    lead: {first[:420]}"
    print(line)
    HEAD.append(f"    {real}: {first[:240]}")
    time.sleep(2)

print("\n" + "=" * 72)
print("HEADLINES REPEATED")
print("=" * 72)
for line in HEAD:
    print(line)
