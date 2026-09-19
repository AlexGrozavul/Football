"""THROWAWAY PROBE 5 - adaptive: detect the stadium link shape, don't guess."""
import re, time, urllib.request, urllib.error, random
from collections import Counter

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LAST=[0.0]
def get(url, timeout=45):
    g=time.time()-LAST[0]
    if g<0.6: time.sleep(0.6-g)
    LAST[0]=time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent":UA}), timeout=timeout) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e: return e.code, e.read()
    except Exception as e: return None, ("ERROR: %s"%e).encode()

SECTIONS = {"stadiums","designs","constructions","lists","news","assets","img",
            "rss","historical","tournaments","about_us","contact_us","faq","links",
            "copyrights","privacy_policy","competitions","stadiony_wg_pojemnosci"}

print("#"*70); print("PART A  raw href shapes on ONE country page (fra)"); print("#"*70)
st, body = get("https://stadiumdb.com/stadiums/fra")
print("HTTP %s  %d bytes" % (st, len(body)))
hrefs=[h.decode("utf-8","replace") for h in re.findall(rb'href="([^"]+)"', body)]
print("total hrefs: %d" % len(hrefs))
shapes=Counter()
for h in hrefs:
    m=re.match(r"^https://stadiumdb\.com/(.+)$", h)
    if not m: continue
    parts=[p for p in m.group(1).split("?")[0].split("/") if p]
    if not parts: continue
    shapes["/".join([parts[0]]+["<slug>"]*(len(parts)-1))]+=1
for s,n in shapes.most_common(12): print("   %-40s %d" % (s,n))
print("\n12 sample hrefs under the commonest non-section first segment:")
cand=[h for h in hrefs if re.match(r"^https://stadiumdb\.com/[^/]+/[^/]+$",h)
      and h.split("/")[3] not in SECTIONS]
for h in cand[:12]: print("   %s" % h)

print("\nRAW markup of one listing row:")
m=re.search(rb'(?is)<tr[^>]*>.{0,900}?</tr>', body[body.find(b'<table'):] if b'<table' in body else body)
print((m.group(0).decode("utf-8","replace") if m else "no <tr> found")[:900])

# ---- adaptive stadium-link detector
def stadium_links(body, code):
    out=set()
    for h in re.findall(rb'href="(https://stadiumdb\.com/[^"]+)"', body):
        h=h.decode("utf-8","replace")
        parts=[p for p in h[len("https://stadiumdb.com/"):].split("?")[0].split("/") if p]
        if len(parts)==2 and parts[0] not in SECTIONS:
            out.add("/".join(parts))
    return sorted(out)

print("\n"+"#"*70); print("PART B  coverage per country (Serbia is 'ser')"); print("#"*70)
TARGET=["fra","ita","sui","aut","ser","gre","ger","rou","pol"]
harvest={}
for c in TARGET:
    st, body = get("https://stadiumdb.com/stadiums/%s" % c)
    # cut the footer off before counting numbers
    cut = body.find(b'About us')
    core = body[:cut] if cut > 1000 else body
    links = stadium_links(core, c)
    harvest[c]=links
    caps=sorted(int(x.replace(" ","").replace(",","")) for x in
        re.findall(r"\b(\d{1,3}(?:[ ,]\d{3})+|\d{3,6})\b",
                   re.sub(r"\s+"," ",re.sub(r"(?s)<[^>]+>"," ",
                          core.decode("utf-8","replace"))))
        if 300<=int(x.replace(" ","").replace(",",""))<=130000)
    n=len(caps)
    print("%s HTTP %s links=%-4d caps n=%-4d min=%-6s p10=%-6s p25=%-6s med=%-6s max=%-6s"
          %(c,st,len(links),n,caps[0] if n else "-",caps[n//10] if n else "-",
            caps[n//4] if n else "-",caps[n//2] if n else "-",caps[-1] if n else "-"))

print("\n"+"#"*70); print("PART C  second-tier smoke test (author's own recollection)"); print("#"*70)
PROBE={"fra":["amiens","guingamp","laval","rodez","pau","annecy","bastia","dunkerque","clermont","troyes","grenoble","caen"],
 "ita":["cesena","catanzaro","carrarese","sudtirol","modena","cittadella","reggiana","bari","spezia","frosinone","palermo"],
 "sui":["aarau","wil","schaffhausen","nyon","bellinzona","vaduz","thun","sion"],
 "aut":["amstetten","kapfenberg","liefering","polten","admira","ried","steyr"],
 "ser":["kolubara","radnicki","jedinstvo","loznica","javor","backa","mladost","cukaricki"],
 "gre":["kalamata","chania","niki","makedonikos","ilioupoli","kavala","levadiakos"]}
for c,needles in PROBE.items():
    blob=" ".join(harvest.get(c,[]))
    hit=[n for n in needles if n in blob]
    print("%s %2d/%2d among %3d stadiums | %s"%(c,len(hit),len(needles),
          len(harvest.get(c,[])), ",".join(hit) or "NONE"))

print("\n"+"#"*70); print("PART D  per-stadium page format"); print("#"*70)
FIELDS={"Capacity":rb"(?i)>\s*Capacity\s*<","Country":rb"(?i)>\s*Country\s*<",
 "City":rb"(?i)>\s*City\s*<","Clubs":rb"(?i)>\s*Clubs?\s*<",
 "Inaugur":rb"(?i)>\s*Inauguration\s*<","Address":rb"(?i)>\s*Address\s*<",
 "Floodl":rb"(?i)>\s*Floodlights\s*<",
 "coords":rb"(?i)(maps\.google|google\.[a-z.]+/maps|data-lat|openstreetmap|latitude)"}
random.seed(11)
sample=[]
for c in TARGET:
    hs=harvest.get(c,[])
    for s_ in random.sample(hs,min(3,len(hs))): sample.append(s_)
print("sampling %d pages\n"%len(sample))
print("%-40s %s"%("page"," ".join("%-8s"%f[:8] for f in FIELDS)))
tally=Counter(); got=0; first_raw=None
for s_ in sample:
    st, body = get("https://stadiumdb.com/"+s_)
    row=[]
    for f,p in FIELDS.items():
        ok=bool(re.search(p,body)); row.append("%-8s"%("yes" if ok else "NO"))
        if ok: tally[f]+=1
    m=re.search(rb"(?is)>\s*Capacity\s*<.{0,400}?([0-9][0-9 ,\xc2\xa0]{2,9})",body)
    v=m.group(1).decode("utf-8","replace").strip() if m else None
    if v: got+=1
    if first_raw is None and st==200: first_raw=(s_,body)
    print("%-40s %s cap=%s"%(s_[:40]," ".join(row),v))
print("\npresent in N of %d:"%len(sample))
for f in FIELDS: print("   %-9s %d"%(f,tally[f]))
print("capacity parsed: %d/%d"%(got,len(sample)))
if first_raw:
    s_,body=first_raw
    i=body.lower().find(b"capacity")
    print("\nRAW markup around Capacity on %s:\n%s"%(s_,
          body[max(0,i-500):i+700].decode("utf-8","replace")))

print("\n"+"#"*70); print("HEADLINE REPEAT"); print("#"*70)
for c in TARGET: print("  %s stadiums: %d"%(c,len(harvest.get(c,[]))))
print("Capacity field %d/%d   coords %d/%d"%(tally["Capacity"],len(sample),
                                             tally["coords"],len(sample)))
