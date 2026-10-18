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
# ---- broad name search, any tag
BR=[('Chrysoupoli',40.9833,24.7,8000,r'στάδι|stadi|γήπεδο|δημοτικ|municipal|χρυσούπ|chrysoup|νέστος'),
 ('Ermoupoli',37.4440,24.9430,6000,r'δημοτικό στάδιο|municipal stad|βικέλ|vikel|ερμούπ.*(στάδ|γήπεδ)|(στάδ|γήπεδ).*ερμούπ|ellas|ελλάς|ellada'),
 ('Magura-Cisnadie',45.7102,24.1531,8000,r'm[ăa]gura|stadion'),
 ('Matarau',44.5393,26.2029,8000,r'm[ăa]t[ăa]r[ăa]u|stadion'),
 ('Ub',44.4533,20.0689,8000,r'd[žz]aji|џајић|dzaji|стадион|stadion|gradski|градски|jedinstvo|јединство')]
p('## BROAD any-tag name search')
for nm,la,lo,R,rx in BR:
    q=f'[out:json][timeout:90];nwr(around:{R},{la},{lo})[~"^(name|name:.*|alt_name|old_name|official_name)$"~"{rx}",i];out center tags;'
    s2=get('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode())
    if not s2: p(nm,'OVERPASS FAILED'); continue
    els=json.loads(s2).get('elements',[]); rows=[]
    for e in els:
        t=e.get('tags',{});c=e.get('center') or {'lat':e.get('lat'),'lon':e.get('lon')}
        if c.get('lat') is None: continue
        names=' / '.join(v for k,v in t.items() if k=='name' or k.startswith('name:') or k in('alt_name','old_name','official_name'))
        keys=','.join(f"{k}={t[k]}" for k in ('leisure','sport','building','amenity','landuse','place','highway','tourism') if k in t)
        rows.append((int(dist(la,lo,c['lat'],c['lon'])),f"{e['type']}/{e['id']}",f"{c['lat']:.6f},{c['lon']:.6f}",keys,names[:100]))
    p(f'-- {nm}: {len(rows)} named matches (showing facility-like first)')
    fac=[r for r in rows if re.search(r'leisure|sport|building=(stadium|grandstand)|amenity=(community|sports)',r[3])]
    oth=[r for r in rows if r not in fac]
    for x in sorted(fac)[:15]: p('  F',*x)
    for x in sorted(oth)[:6]: p('  o',*x)
# Syros: everything within 350 m of the sports centre
q='[out:json][timeout:90];nwr(around:350,37.431348,24.936195)[~"^(leisure|building|sport)$"~"."];out center tags;'
s2=get('https://overpass-api.de/api/interpreter',data=urllib.parse.urlencode({'data':q}).encode())
p('-- Syros sports-centre neighbourhood (350 m)')
if s2:
    for e in json.loads(s2).get('elements',[]):
        t=e.get('tags',{});c=e.get('center') or {'lat':e.get('lat'),'lon':e.get('lon')}
        if t.get('building')=='yes' and 'name' not in t: continue
        p('  ',e['type']+'/'+str(e['id']),f"{c['lat']:.6f},{c['lon']:.6f}",{k:v for k,v in t.items() if k in('name','leisure','sport','building','surface','capacity','operator')})
head=[l for l in OUT if l.startswith('-- ') or l.startswith('##')]
print('SUMMARY (sections):',*head,sep='\n')
print('\n'.join(OUT))
print('SUMMARY END: lines',len(OUT))
