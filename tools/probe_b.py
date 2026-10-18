"""TEMPORARY probe for the place-clubs pass (removed before merge). Read-only."""
import json,re,sys,time,math,urllib.request,urllib.parse,urllib.error
UA="FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
OUT=[]
def p(*a): OUT.append(' '.join(str(x) for x in a))
def get(url,data=None,hdr=None):
    for t in range(4):
        time.sleep(1)
        try:
            h={'User-Agent':UA}; h.update(hdr or {})
            r=urllib.request.urlopen(urllib.request.Request(url,data=data,headers=h),timeout=120)
            return r.read().decode('utf-8','replace')
        except urllib.error.HTTPError as e:
            w=int(e.headers.get('Retry-After') or 60) if e.code==429 else 20
            print('  HTTP',e.code,url[:60],'try',t+1,'wait',w,file=sys.stderr,flush=True); time.sleep(w)
        except Exception as e:
            print('  ERR',e,url[:60],file=sys.stderr,flush=True); time.sleep(10)
    return None
def wd(**q):
    q.update(format='json',maxlag=5)
    s=get('https://www.wikidata.org/w/api.php?'+urllib.parse.urlencode(q))
    return json.loads(s) if s else None
def dist(a,b,c,d):
    R=6371000;f1,f2=math.radians(a),math.radians(c);df=f2-f1;dl=math.radians(d-b)
    h=math.sin(df/2)**2+math.cos(f1)*math.cos(f2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
# ---- 1. Wikidata
grounds="Q65090741 Q131850818 Q28230311 Q3967924 Q110045992 Q132566856 Q24969467 Q7596400".split()
clubs="Q3292651 Q16845757 Q12872753 Q650365 Q39487082 Q66424141 Q18539440 Q55593565 Q1323373 Q1388917".split()
def ent(ids):
    d=wd(action='wbgetentities',ids='|'.join(ids),props='labels|aliases|claims',languages='en|el|sr|ro|it')
    return d.get('entities',{}) if d else {}
def lab(e,l='en'): return (e.get('labels',{}).get(l) or {}).get('value')
def al(e): return {l:[a['value'] for a in v] for l,v in e.get('aliases',{}).items()}
def claim(e,pid):
    out=[]
    for c in e.get('claims',{}).get(pid,[]):
        v=c['mainsnak'].get('datavalue',{}).get('value')
        out.append((c.get('rank'),v.get('id') if isinstance(v,dict) and 'id' in v else (f"{v['latitude']:.6f},{v['longitude']:.6f}" if isinstance(v,dict) and 'latitude' in v else v)))
    return out
E1=ent(grounds); E2=ent(clubs)
extra=set()
for q,e in E2.items():
    for r,v in claim(e,'P115'): extra.add(v)
E3=ent(sorted(extra-set(grounds))) if extra-set(grounds) else {}
p('## WIKIDATA grounds')
for q,e in {**E1,**E3}.items():
    p(q,lab(e),'|el',lab(e,'el'),'|sr',lab(e,'sr'),'| P625',claim(e,'P625'),'| P131',claim(e,'P131'),'| aliases',al(e))
p('## WIKIDATA clubs (P115 ground, P625)')
for q,e in E2.items(): p(q,lab(e),'P115',claim(e,'P115'),'P625',claim(e,'P625'))
p('## WIKIDATA search')
for s,l in [('Municipal Stadium of Chrysoupoli','en'),('Δημοτικό Στάδιο Χρυσούπολης','el'),('Ermoupoli Municipal Stadium','en'),('Δημοτικό Στάδιο Ερμούπολης','el'),('Δημοτικό Στάδιο Ζακύνθου','el'),('Ολυμπιονικών Ζακυνθίων','el'),('Zakynthos Municipal Stadium','en')]:
    d=wd(action='wbsearchentities',search=s,language=l,limit=5,type='item')
    p(s,'->',[(x['id'],x.get('label'),x.get('description')) for x in (d or {}).get('search',[])])
for q in ['Q132566856']:
    pass
# ---- 2. Overpass
ANCH=[('Steaua',44.4129,26.0404,1500,r'steaua|ghencea|decembrie'),
 ('Magura-Cisnadie',45.7102,24.1531,1500,r'm[ăa]gura|cisn'),
 ('Matarau-Stefanesti',44.5393,26.2029,3000,r'm[ăa]t[ăa]r[ăa]u|dumitru|stadion|ștef|stef'),
 ('Marmi-Carrara',44.0653,10.0768,1500,r'marmi|mennea|olimpionici|stadio'),
 ('Chrysoupoli',40.9833,24.7,3000,r'στάδι|stadi|δημοτικ|municipal|χρυσούπ|chrysoup|nestos|νέστος'),
 ('Ermoupoli',37.4440,24.9430,3000,r'ερμούπ|ermoup|syros|σύρο|στάδι|stadi|δημοτικ|municipal'),
 ('Zakynthos',37.7870,20.8990,3000,r'ζάκυνθ|zakynth|zante|στάδι|stadi|δημοτικ|municipal|ολυμπιον|olymp'),
 ('Ub',44.4533,20.0689,3500,r'd[žz]aji|џајић|dzaji|стадион|stadion|gradski|градски|jedinstvo|јединство')]
p('## OVERPASS named leisure=stadium|pitch|sports_centre|track (and building=stadium)')
for nm,la,lo,R,rx in ANCH:
    q=f'[out:json][timeout:90];(nwr(around:{R},{la},{lo})["leisure"~"^(stadium|pitch|sports_centre|track)$"];nwr(around:{R},{la},{lo})["building"="stadium"];);out center tags;'
    s=get('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode())
    if not s: p(nm,'OVERPASS FAILED'); continue
    els=json.loads(s).get('elements',[])
    named=[];unn=0
    for e in els:
        t=e.get('tags',{});c=e.get('center') or {'lat':e.get('lat'),'lon':e.get('lon')}
        names=' / '.join(v for k,v in t.items() if k=='name' or k.startswith('name:') or k in('alt_name','old_name','official_name'))
        if not names: unn+=1; continue
        d=dist(la,lo,c['lat'],c['lon'])
        if re.search(rx,names,re.I) or d<400:
            named.append((int(d),f"{e['type']}/{e['id']}",f"{c['lat']:.6f},{c['lon']:.6f}",t.get('leisure') or t.get('building'),t.get('sport'),names[:120],('cap='+t['capacity']) if 'capacity' in t else ''))
    p(f'-- {nm}: {len(els)} objects, {unn} unnamed, {len(named)} shown')
    for x in sorted(named)[:12]: p('  ',*x)
# ---- 3. StadiumDB
p('## STADIUMDB rows')
for slug,rx in [('ita',r'Carrar|Marmi'),('rou',r'Steaua|Ghencea|Selimb|Cisn|Magura|M[ăa]gura|Stefanesti|Ștef|Mătărău|Clinceni|Pope'),('gre',r'Zakynth|Chrysoup|Syros|Ermoup'),('ser',r'Zemun|Dragan|Ub\b|Uba')]:
    s=get(f'https://stadiumdb.com/stadiums/{slug}')
    if not s: p(slug,'FAILED'); continue
    for tr in re.findall(r'<tr.*?</tr>',s,re.S):
        tx=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',tr)).strip()
        if re.search(rx,tx): p(slug,'|',tx[:200])
head=[l for l in OUT if l.startswith('-- ') or l.startswith('##')]
print('SUMMARY (sections):',*head,sep='\n')
print('\n'.join(OUT))
print('SUMMARY END: lines',len(OUT))
