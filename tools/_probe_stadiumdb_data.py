"""THROWAWAY PROBE 4 - coverage and page format, with the real URL shape.

The site links countries as ABSOLUTE urls: https://stadiumdb.com/stadiums/fra
"""
import re, time, urllib.request, urllib.error, random
from collections import Counter

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LAST = [0.0]
def get(url, timeout=45):
    gap = time.time() - LAST[0]
    if gap < 0.6: time.sleep(0.6 - gap)
    LAST[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, ("ERROR: %s" % e).encode()

def text_of(html):
    s = re.sub(rb"(?is)<(script|style)[^>]*>.*?</\1>", b" ", html)
    s = re.sub(rb"(?s)<[^>]+>", b" ", s)
    return re.sub(r"\s+", " ", s.decode("utf-8", "replace")).strip()

print("#"*70); print("PART A  the full country index"); print("#"*70)
st, body = get("https://stadiumdb.com/stadiums")
codes = sorted(set(m.decode() for m in
                   re.findall(rb'href="https://stadiumdb\.com/stadiums/([a-z]{2,3})"', body)))
print("country codes: %d" % len(codes))
print("  " + " ".join(codes))

TARGET = ["fra","ita","sui","aut","srb","gre","ger","rou","pol"]
present = [c for c in TARGET if c in codes]
missing = [c for c in TARGET if c not in codes]
print("\ntargets present: %s" % present)
print("targets NOT in index: %s" % missing)

print("\n"+"#"*70); print("PART B  how many stadiums per country, and how small do they get")
print("#"*70)
harvest = {}
for c in present:
    st, body = get("https://stadiumdb.com/stadiums/%s" % c)
    urls = sorted(set(m.decode() for m in re.findall(
        (r'href="https://stadiumdb\.com/%s/([a-z0-9_\-]+)"' % c).encode(), body)))
    harvest[c] = urls
    txt = text_of(body)
    caps = sorted(int(x.replace(" ","").replace(",","")) for x in
                  re.findall(r"\b(\d{1,3}(?:[ ,]\d{3})+|\d{3,6})\b", txt)
                  if 300 <= int(x.replace(" ","").replace(",","")) <= 130000)
    n = len(caps)
    print("%s  HTTP %s  stadium links=%-5d  numbers on page n=%-4d min=%-6s p25=%-6s med=%-6s"
          % (c, st, len(urls), n,
             caps[0] if n else "-", caps[n//4] if n else "-", caps[n//2] if n else "-"))

print("\n"+"#"*70); print("PART C  are second-tier grounds present?"); print("#"*70)
print("The needles below are the PROBE AUTHOR'S OWN recollection of")
print("second-tier clubs, not read from any source. Treat as a smoke test.")
PROBE = {
 "fra": ["amiens","guingamp","laval","rodez","pau","annecy","bastia","dunkerque",
         "clermont","troyes","grenoble","caen"],
 "ita": ["cesena","catanzaro","carrarese","sudtirol","sud_tirol","modena","cittadella",
         "reggiana","bari","spezia","frosinone","palermo"],
 "sui": ["aarau","wil","schaffhausen","nyon","bellinzona","vaduz","stade_lausanne",
         "thun","sion"],
 "aut": ["amstetten","kapfenberg","liefering","st_polten","admira","ried","rheindorf",
         "vorwarts_steyr","sturm"],
 "srb": ["kolubara","radnicki","jedinstvo","loznica","javor","backa","mladost"],
 "gre": ["kalamata","chania","niki","makedonikos","ilioupoli","kavala","levadiakos"],
}
for c, needles in PROBE.items():
    if c not in harvest:
        print("%s -- not in index" % c); continue
    blob = " ".join(harvest[c])
    hit = [n for n in needles if n in blob]
    print("%s  %2d/%2d needles found among %3d stadiums | found: %s"
          % (c, len(hit), len(needles), len(harvest[c]), ",".join(hit) or "NONE"))

print("\n"+"#"*70); print("PART D  per-stadium page format"); print("#"*70)
FIELDS = {
 "Capacity":  rb"(?i)>\s*Capacity\s*<",
 "Country":   rb"(?i)>\s*Country\s*<",
 "City":      rb"(?i)>\s*City\s*<",
 "Clubs":     rb"(?i)>\s*Clubs?\s*<",
 "Inaugurat": rb"(?i)>\s*Inauguration\s*<",
 "Address":   rb"(?i)>\s*Address\s*<",
 "coords":    rb"(?i)(maps\.google|google\.[a-z.]+/maps|\bdata-lat|latitude|openstreetmap)",
}
random.seed(11)
sample = []
for c in present:
    for slug in random.sample(harvest[c], min(3, len(harvest[c]))):
        sample.append((c, slug))
print("sampling %d pages\n" % len(sample))
hdr = "%-34s %s" % ("page", " ".join("%-9s" % f[:9] for f in FIELDS))
print(hdr)
tally = Counter(); caps = []
for c, slug in sample:
    st, body = get("https://stadiumdb.com/%s/%s" % (c, slug))
    row = []
    for f, pat in FIELDS.items():
        ok = bool(re.search(pat, body))
        row.append("%-9s" % ("yes" if ok else "NO"))
        if ok: tally[f] += 1
    m = re.search(rb"(?is)>\s*Capacity\s*<.{0,300}?([0-9][0-9 ,\xc2\xa0]{2,9})", body)
    v = m.group(1).decode("utf-8","replace").strip() if m else None
    caps.append(v)
    print("%-34s %s cap=%s" % (("%s/%s" % (c, slug))[:34], " ".join(row), v))
print("\nfield present in N of %d:" % len(sample))
for f in FIELDS: print("   %-10s %d" % (f, tally[f]))
print("capacity value parsed: %d/%d" % (sum(1 for x in caps if x), len(caps)))

print("\n"+"#"*70); print("HEADLINE REPEAT"); print("#"*70)
print("country codes in index: %d" % len(codes))
for c in present: print("  %s stadiums: %d" % (c, len(harvest.get(c,[]))))
print("targets NOT in index: %s" % missing)
print("Capacity field: %d/%d   coords: %d/%d" % (tally["Capacity"], len(sample),
                                                 tally["coords"], len(sample)))
