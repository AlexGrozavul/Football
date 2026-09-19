"""THROWAWAY PROBE 2 - terms follow-up, coverage, page format.

Probe 1 established robots.txt is real and permits everything except
/lay-gfx/, so content pages may be read. This reads the remaining legal
pages in full, then measures coverage and page-format consistency.

Polite: 0.7s between requests, ordinary browser UA, ~70 requests total.
"""
import re, sys, time, urllib.request, urllib.error
from collections import Counter

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LAST = [0.0]

def get(url, timeout=45):
    gap = time.time() - LAST[0]
    if gap < 0.7:
        time.sleep(0.7 - gap)
    LAST[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "en,pl;q=0.8"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read(), url
    except Exception as e:
        return None, ("ERROR: %s" % e).encode(), url

def text_of(html):
    s = re.sub(rb"(?is)<(script|style)[^>]*>.*?</\1>", b" ", html)
    s = re.sub(rb"(?s)<[^>]+>", b" ", s)
    s = s.decode("utf-8", "replace")
    s = s.replace("-->", " ")
    return re.sub(r"\s+", " ", s).strip()

TARGET = ["fra", "ita", "sui", "aut", "srb", "gre", "ger", "rou",
          "che", "swi", "srp", "grc", "deu", "rom", "ron"]

# ====================================================== 1. remaining legal text
print("#" * 70)
print("PART 1  the legal pages probe 1 had not read")
print("#" * 70)
for url in ("https://stadiumdb.com/copyrights",
            "https://stadiumdb.com/contact_us",
            "https://stadiumdb.com/faq",
            "https://stadiumdb.com/links",
            "https://stadiony.net/prawa_autorskie",
            "https://stadiony.net/o_serwisie"):
    st, body, final = get(url)
    txt = text_of(body)
    print("\n=== %s -> HTTP %s, %d chars of text" % (url, st, len(txt)))
    if st != 200:
        print("    (not a real page)")
        continue
    # strip the shared nav prefix so the page's own words are visible
    for marker in ("Copyrights", "Contact", "Prawa autorskie", "O Serwisie", "FAQ"):
        i = txt.rfind(marker)
        if i > 200:
            txt = txt[i:]
            break
    print("    " + txt[:1800].replace("\n", " "))

# ====================================================== 2. country index
print("\n" + "#" * 70)
print("PART 2  how the site indexes countries, and how many stadiums each has")
print("#" * 70)
st, body, final = get("https://stadiumdb.com/stadiums")
print("/stadiums -> HTTP %s, %d bytes" % (st, len(body)))
links = re.findall(rb'href="(/stadiums/[a-z]{3})"', body)
codes = sorted(set(l.decode() for l in links))
print("country index links found: %d" % len(codes))
print("  " + " ".join(c.split("/")[-1] for c in codes))

def country_page(code):
    return get("https://stadiumdb.com/stadiums/%s" % code)

# which of our targets exist?
present = []
for c in TARGET:
    if "/stadiums/%s" % c in codes:
        present.append(c)
print("\ntargets present in the index: %s" % present)

# ====================================================== 3. coverage per country
print("\n" + "#" * 70)
print("PART 3  coverage: stadium count and capacity distribution per country")
print("#" * 70)
harvest = {}
for c in present:
    st, body, final = country_page(c)
    # stadium links on a country page
    urls = sorted(set(re.findall((r'href="(/stadiums/%s/[a-z0-9_\-]+)"' % c).encode(), body)))
    urls = [u.decode() for u in urls]
    # capacities in the listing table
    caps = [int(x.decode().replace(" ", "").replace(",", ""))
            for x in re.findall(rb'>\s*([0-9][0-9 ,]{2,9})\s*<', body)
            if x.decode().strip().replace(" ", "").replace(",", "").isdigit()
            and 500 <= int(x.decode().replace(" ", "").replace(",", "")) <= 120000]
    harvest[c] = urls
    caps.sort()
    med = caps[len(caps) // 2] if caps else 0
    print("%s  stadium links=%-5d  listing numbers 500-120k: n=%-4d min=%-7s med=%-7s"
          % (c, len(urls), len(caps), caps[0] if caps else "-", med))

# ====================================================== 4. tier-2 presence
print("\n" + "#" * 70)
print("PART 4  are SECOND-TIER grounds there, or only the big ones?")
print("#" * 70)
print("NOTE: the club/ground pairs below are the probe author's own input,")
print("      not read from any source. They are a test input to be confirmed.")
PROBE_T2 = {
 "fra": ["amiens", "guingamp", "laval", "rodez", "pau", "annecy", "bastia", "dunkerque"],
 "ita": ["cesena", "catanzaro", "carrarese", "sudtirol", "modena", "cittadella", "reggiana"],
 "sui": ["aarau", "wil", "schaffhausen", "stade_nyonnais", "bellinzona", "vaduz"],
 "aut": ["amstetten", "kapfenberg", "liefering", "st_polten", "admira", "sturm_graz_ii"],
 "srb": ["kolubara", "radnicki_sremska", "grafičar", "jedinstvo", "loznica"],
 "gre": ["kalamata", "chania", "niki_volou", "makedonikos", "ilioupoli"],
}
for c, needles in PROBE_T2.items():
    if c not in harvest:
        print("%s  -- country not in index" % c)
        continue
    blob = " ".join(harvest[c])
    hit = [n for n in needles if n.split("_")[0] in blob]
    print("%s  %d/%d probe names appear in the %d harvested stadium URLs: %s"
          % (c, len(hit), len(needles), len(harvest[c]), hit or "none"))

# ====================================================== 5. page format
print("\n" + "#" * 70)
print("PART 5  per-stadium page format consistency")
print("#" * 70)
FIELDS = {
    "capacity":   rb"(?i)>\s*Capacity\s*<",
    "country":    rb"(?i)>\s*Country\s*<",
    "city":       rb"(?i)>\s*City\s*<",
    "clubs":      rb"(?i)>\s*Clubs?\s*<",
    "inaugur":    rb"(?i)>\s*Inauguration\s*<",
    "address":    rb"(?i)>\s*Address\s*<",
    "floodlight": rb"(?i)>\s*Floodlights\s*<",
    "coords":     rb"(?i)(google\.[a-z.]+/maps|maps\.google|latitude|data-lat|\bLL\b|geo:)",
}
import random
random.seed(7)
sample = []
for c in present:
    us = harvest.get(c, [])
    for u in random.sample(us, min(3, len(us))):
        sample.append(u)
print("sampling %d stadium pages across %d countries\n" % (len(sample), len(present)))
print("%-46s %s" % ("page", " ".join("%-10s" % f for f in FIELDS)))
tally = Counter()
capvals = []
for u in sample:
    st, body, final = get("https://stadiumdb.com" + u)
    row = []
    for f, pat in FIELDS.items():
        ok = bool(re.search(pat, body))
        row.append("%-10s" % ("yes" if ok else "NO"))
        if ok:
            tally[f] += 1
    m = re.search(rb"(?is)>\s*Capacity\s*<.{0,200}?([0-9][0-9 ,\xa0]{2,9})", body)
    capvals.append(m.group(1).decode("utf-8", "replace").strip() if m else None)
    print("%-46s %s  cap=%r" % (u[:46], " ".join(row), capvals[-1]))

print("\nfield present in N of %d sampled pages:" % len(sample))
for f in FIELDS:
    print("   %-12s %d" % (f, tally[f]))
print("capacity value parsed on %d of %d" % (sum(1 for c in capvals if c), len(capvals)))

print("\n" + "#" * 70)
print("HEADLINE REPEAT")
print("#" * 70)
for c in present:
    print("%s stadiums harvested: %d" % (c, len(harvest.get(c, []))))
print("capacity field present: %d/%d sampled pages" % (tally["capacity"], len(sample)))
print("coords-ish present:     %d/%d sampled pages" % (tally["coords"], len(sample)))
