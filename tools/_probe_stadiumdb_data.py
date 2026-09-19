"""THROWAWAY PROBE 6 - the shape is /stadiums/<iso3>/<slug>. Measure for real."""
import re, time, urllib.request, urllib.error, random, json
from collections import Counter

UA=("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
LAST=[0.0]
def get(u,t=45):
    g=time.time()-LAST[0]
    if g<0.6: time.sleep(0.6-g)
    LAST[0]=time.time()
    try:
        with urllib.request.urlopen(urllib.request.Request(u,headers={"User-Agent":UA}),timeout=t) as r:
            return r.status,r.read()
    except urllib.error.HTTPError as e: return e.code,e.read()
    except Exception as e: return None,("ERR %s"%e).encode()

def cells(tr):
    return [re.sub(r"\s+"," ",re.sub(r"(?s)<[^>]+>"," ",c)).strip()
            for c in re.findall(r"(?is)<t[dh][^>]*>(.*?)</t[dh]>", tr)]

TARGET=["fra","ita","sui","aut","ser","gre","ger","rou","pol"]
print("#"*70); print("PART A  coverage per country, parsed from the listing table")
print("#"*70)
print("%-4s %-6s %-7s %s"%("cc","HTTP","stadia","capacity distribution (from the table's Capacity column)"))
harvest={}; rowdata={}
for c in TARGET:
    st,body=get("https://stadiumdb.com/stadiums/%s"%c)
    html=body.decode("utf-8","replace")
    links=sorted(set(re.findall(r'href="https://stadiumdb\.com/stadiums/%s/([a-z0-9_\-]+)"'%c, html)))
    harvest[c]=links
    rows=[]
    for tr in re.findall(r"(?is)<tr.*?</tr>", html):
        cs=cells(tr)
        if len(cs)>=4 and re.fullmatch(r"[\d ,.]+", cs[3] or "x"):
            try: cap=int(re.sub(r"[^\d]","",cs[3]))
            except ValueError: continue
            if cap>0: rows.append((cs[0],cs[1],cs[2],cap))
    rowdata[c]=rows
    caps=sorted(r[3] for r in rows)
    n=len(caps)
    q=lambda p: caps[min(n-1,int(n*p))] if n else "-"
    print("%-4s %-6s %-7d n=%-4d min=%-6s p10=%-6s p25=%-6s med=%-6s p75=%-6s max=%s"
          %(c,st,len(links),n,caps[0] if n else "-",q(.10),q(.25),q(.50),q(.75),caps[-1] if n else "-"))

print("\n"+"#"*70); print("PART B  how far down the pyramid does it go?"); print("#"*70)
print("count of listed grounds under a capacity threshold - a tier-2 ground")
print("in these countries is typically 5,000-20,000:")
print("%-4s %-8s %-8s %-8s %-8s %-8s"%("cc","<3000","<6000","<12000","<20000","total"))
for c in TARGET:
    caps=[r[3] for r in rowdata[c]]
    print("%-4s %-8d %-8d %-8d %-8d %-8d"%(c,
      sum(1 for x in caps if x<3000),sum(1 for x in caps if x<6000),
      sum(1 for x in caps if x<12000),sum(1 for x in caps if x<20000),len(caps)))

print("\n"+"#"*70); print("PART C  does the listing name the CLUB? (needed for any matching)")
print("#"*70)
for c in TARGET:
    rows=rowdata[c]
    withclub=sum(1 for r in rows if r[2].strip())
    print("%-4s %d of %d rows name a club; samples: %s"%(c,withclub,len(rows),
      " | ".join("%s=%s(%d)"%(r[0][:18],r[2][:20] or "-",r[3]) for r in rows[:3])))

print("\n"+"#"*70); print("PART D  second-tier smoke test (author's own recollection)")
print("#"*70)
PROBE={"fra":["amiens","guingamp","laval","rodez","pau","annecy","bastia","dunkerque","clermont","troyes","grenoble","caen"],
 "ita":["cesena","catanzaro","carrarese","sudtirol","modena","cittadella","reggiana","bari","spezia","frosinone","palermo","avellino"],
 "sui":["aarau","wil","schaffhausen","nyon","bellinzona","vaduz","thun","sion","carouge","kriens","rapperswil"],
 "aut":["amstetten","kapfenberg","liefering","polten","admira","ried","steyr"],
 "ser":["kolubara","radnicki","jedinstvo","loznica","javor","backa","mladost","grafi","dubocica","bor"],
 "gre":["kalamata","chania","niki","makedonikos","ilioupoli","kavala","levadiakos","karditsa","syros","kallithea"]}
for c,needles in PROBE.items():
    blob=(" ".join(harvest[c])+" "+" ".join(r[0].lower()+" "+r[1].lower()+" "+r[2].lower()
          for r in rowdata[c]))
    hit=[n for n in needles if n in blob]
    print("%-4s %2d/%2d among %3d | %s"%(c,len(hit),len(needles),len(harvest[c]),
          ",".join(hit) or "NONE"))

print("\n"+"#"*70); print("PART E  per-stadium page format"); print("#"*70)
FIELDS={"Capacity":r"(?i)>\s*Capacity\s*<","Country":r"(?i)>\s*Country\s*<",
 "City":r"(?i)>\s*City\s*<","Clubs":r"(?i)>\s*Clubs?\s*<",
 "Inaugur":r"(?i)>\s*Inauguration\s*<","Address":r"(?i)>\s*Address\s*<",
 "Floodl":r"(?i)>\s*Floodlights\s*<",
 "coords":r"(?i)(maps\.google|google\.[a-z.]+/maps|data-lat|openstreetmap|latitude|geo\.)"}
random.seed(3)
sample=[]
for c in TARGET:
    for s in random.sample(harvest[c],min(3,len(harvest[c]))): sample.append((c,s))
print("sampling %d pages across %d countries\n"%(len(sample),len(TARGET)))
print("%-38s %s"%("page"," ".join("%-8s"%f[:8] for f in FIELDS)))
tally=Counter(); got=0; raw=None
for c,s in sample:
    st,body=get("https://stadiumdb.com/stadiums/%s/%s"%(c,s))
    h=body.decode("utf-8","replace"); row=[]
    for f,p in FIELDS.items():
        ok=bool(re.search(p,h)); row.append("%-8s"%("yes" if ok else "NO"))
        if ok: tally[f]+=1
    m=re.search(r"(?is)>\s*Capacity\s*<.{0,400}?([\d][\d  ,]{2,12})",h)
    v=m.group(1).strip() if m else None
    if v: got+=1
    if raw is None: raw=(c,s,h)
    print("%-38s %s cap=%s"%(("%s/%s"%(c,s))[:38]," ".join(row),v))
print("\npresent in N of %d:"%len(sample))
for f in FIELDS: print("   %-9s %d"%(f,tally[f]))
print("capacity parsed: %d/%d"%(got,len(sample)))
if raw:
    c,s,h=raw; i=h.lower().find("capacity")
    print("\nRAW markup around Capacity (%s/%s):\n%s"%(c,s,h[max(0,i-600):i+500]))

print("\n"+"#"*70); print("HEADLINE REPEAT"); print("#"*70)
for c in TARGET: print("  %-4s %d stadiums"%(c,len(harvest[c])))
print("Capacity %d/%d  Clubs %d/%d  coords %d/%d"%(tally["Capacity"],len(sample),
      tally["Clubs"],len(sample),tally["coords"],len(sample)))
