#!/usr/bin/env python3
"""TEMPORARY probe for the capacity audit (phase 1c). Removed before merge.
Reads Wikidata (wbgetentities), Wikipedia (action=parse, wikitext) and
StadiumDB's country tables; posts compact tables as PR comments."""
import csv, glob, html, json, os, re, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request, urllib.robotparser

UA = "FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)"
RUN = os.environ.get("PROBE_RUN", "?")
REPO = os.environ.get("GITHUB_REPOSITORY", "")
PR = os.environ.get("PR_NUMBER", "")
TOKEN = os.environ.get("GH_TOKEN", "")
MODE = os.environ.get("PROBE_MODE", "compare")
LOG, NREQ, LAST = [], {}, {}
LANGS = {"DE": ["de"], "AT": ["de"], "CH": ["de", "fr", "it"], "BE": ["nl", "fr"],
         "NL": ["nl"], "FR": ["fr"], "ES": ["es", "ca"], "IT": ["it"], "PT": ["pt"],
         "RO": ["ro"], "RS": ["sr"], "GR": ["el"], "GB": ["en"]}


def log(msg):
    LOG.append(msg)
    print(msg, flush=True)


def http(url, key, gap, timeout=40, maxbytes=3_000_000):
    wait = LAST.get(key, 0) + gap - time.time()
    if wait > 0:
        time.sleep(wait)
    LAST[key] = time.time()
    NREQ[key] = NREQ.get(key, 0) + 1
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.headers, r.read(maxbytes)


def wm(host, params):
    """Wikimedia API call: one request per second across all Wikimedia hosts, maxlag=5."""
    p = dict(params)
    p.update(format="json", maxlag="5", formatversion="2")
    url = f"https://{host}/w/api.php?" + urllib.parse.urlencode(p)
    for attempt in range(6):
        try:
            _, hdr, body = http(url, "wikimedia", 1.0, maxbytes=30_000_000)
            data = json.loads(body)
            if isinstance(data, dict) and data.get("error", {}).get("code") == "maxlag":
                time.sleep(int(hdr.get("Retry-After") or 5) + 1)
                continue
            return data
        except urllib.error.HTTPError as e:
            if e.code in (429, 503):
                time.sleep(int(e.headers.get("Retry-After") or 10) + 1)
                continue
            log(f"ERR {host} {params.get('page') or params.get('ids','')[:40]} HTTP {e.code}")
            return None
        except Exception as e:
            log(f"ERR {host} {params.get('page') or params.get('ids','')[:40]} {type(e).__name__} {e}")
            time.sleep(3)
    return None


def post(body):
    body = body[:64000]
    if not (TOKEN and PR):
        print(body)
        return
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{PR}/comments",
        data=json.dumps({"body": body}).encode(), method="POST",
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "User-Agent": UA, "Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print("COMMENT FAILED", e)
        print(body[:3000])
    time.sleep(1.5)


def post_chunks(title, lines, limit=56000):
    part, buf, size = 1, [], 0
    for ln in lines:
        if size + len(ln) + 1 > limit and buf:
            post(f"{title} part {part}\n```\n" + "\n".join(buf) + "\n```")
            part, buf, size = part + 1, [], 0
        buf.append(ln)
        size += len(ln) + 1
    if buf:
        post(f"{title} part {part} (last)\n```\n" + "\n".join(buf) + "\n```")


# ---------- scope ----------
def scope():
    man = {}
    for r in csv.DictReader(open("data/clubs-manual.csv", encoding="utf-8")):
        if (r.get("capacity") or "").strip():
            man[r["clubQid"]] = 1
    out = []
    for f in sorted(glob.glob("data/clubs/??.json")):
        cc = f[-7:-5]
        for c in json.load(open(f, encoding="utf-8"))["clubs"]:
            if c["id"] in man or c.get("capacity") is None:
                continue
            out.append(dict(cc=cc, id=c["id"], name=c["name"], tier=c["tier"],
                            venue=c.get("venue") or "", cap=c["capacity"]))
    return out


# ---------- wikitext ----------
KEYS = ["capacit", "capacid", "kapazit", "plätze", "aforo", "capienza", "lotaç", "lotac", "капацитет",
        "kapacitet", "χωρητικ", "fassungs", "zuschauer", "toeschouwers", "capaciteit"]
NOKEY = ["rekord", "record", "schnitt", "average", "moyenne", "media", "récord"]
KEYRE = re.compile(r"^\s*\|\s*([^=|{}\[\]\n<]{1,50}?)\s*=", re.M)
NEXTRE = re.compile(r"^\s*\|\s*[^=|{}\[\]\n<]{1,50}=|^\s*\}\}\s*$", re.M)
WDRE = re.compile(r"#property|#invoke:\s*wikidata|\{\{\s*wikidata|#statements|P1083|\{\{\s*wd\s*\|", re.I)
NUMRE = re.compile(r"(?<![\d.,])(\d{1,3}(?:[.,   '’]\d{3})+|\d{3,6})(?!\d)")
URLRE = re.compile(r"https?://[^\s|\]}<>\"]+")


def clean(v):
    v = re.sub(r"<ref[^>]*?/>", " ", v)
    v = re.sub(r"<ref[^>]*>.*?</ref>", " ", v, flags=re.S)
    v = re.sub(r"<!--.*?-->", " ", v, flags=re.S)
    v = re.sub(r"<br\s*/?>", " ; ", v, flags=re.I)
    v = re.sub(r"<[^>]+>", " ", v)
    v = html.unescape(v).replace(" ", " ").replace(" ", " ").replace(" ", " ")
    v = re.sub(r"\{\{\s*formatnum\s*:", "", v, flags=re.I)
    v = re.sub(r"\{\{[^{}|]*\|", "", v)
    v = v.replace("}}", " ").replace("{{", " ")
    v = re.sub(r"\[\[[^\]|]*\|", "", v).replace("[[", "").replace("]]", "")
    v = v.replace("'''", "").replace("''", "").replace("|", " ")
    return re.sub(r"\s+", " ", v).strip()


def numbers(text):
    out = []
    for m in NUMRE.finditer(text):
        raw = m.group(1)
        n = int(re.sub(r"\D", "", raw))
        if raw.isdigit() and len(raw) == 4 and 1850 <= n <= 2035:
            nxt = text[m.end():m.end() + 1]
            prv = text[max(0, m.start() - 1):m.start()]
            if nxt in (":", ")", "/", "–", "-") or prv in ("(", "/", "–", "-"):
                continue
        if n >= 100:
            out.append(n)
    return out


def infobox_capacity(wt):
    """-> dict(kind L/W/N, fig, allnums, key, raw, refurl, reftext)"""
    found = []
    for m in KEYRE.finditer(wt):
        key = m.group(1).strip().lower()
        if not any(k in key for k in KEYS) or any(k in key for k in NOKEY):
            continue
        nx = NEXTRE.search(wt, m.end())
        val = wt[m.end():nx.start() if nx else m.end() + 1500][:1500].strip()
        if val:
            found.append((key, val))
    if not found:
        return dict(kind="N", fig=None, allnums=[], key="", raw="", refurl="", reftext="")
    for key, val in found:
        if WDRE.search(val):
            return dict(kind="W", fig=None, allnums=[], key=key, raw=val[:200], refurl="", reftext="")
    key, val = found[0]
    nums = numbers(clean(val))
    reftext, refurl = "", ""
    rm = re.search(r"<ref[^>/]*>(.*?)</ref>", val, re.S)
    if rm:
        reftext = rm.group(1)
    else:
        nm = re.search(r"<ref\s+name\s*=\s*\"?([^\"/>]+?)\"?\s*/>", val)
        if nm:
            dm = re.search(r"<ref\s+name\s*=\s*\"?" + re.escape(nm.group(1).strip()) + r"\"?\s*>(.*?)</ref>", wt, re.S)
            reftext = dm.group(1) if dm else f"named-ref:{nm.group(1).strip()}"
    um = [u for u in URLRE.findall(reftext) if "archive." not in u]
    refurl = um[0] if um else (URLRE.findall(reftext) or [""])[0]
    raw = "; ".join(f"{k}={clean(v)[:160]}" for k, v in found[:4])
    if not nums:
        return dict(kind="N", fig=None, allnums=[], key=key, raw=raw, refurl=refurl, reftext=reftext[:300])
    return dict(kind="L", fig=nums[0], allnums=nums[:6], key=key, raw=raw, refurl=refurl,
                reftext=re.sub(r"\s+", " ", reftext)[:300])


SENT_KEY = re.compile(
    r"capacit|capacid|kapazit|plätze|zuschauer|fassungs|aforo|espectador|spettator|posti|capienza|"
    r"toeschouwers|plaatsen|lugares|lotaç|locuri|мест|капацитет|kapacitet|mesta|gledalac|"
    r"χωρητικ|θέσε|θεατ|seat|spectator|places|homologat|omologat|zugelassen|league", re.I)


def body_sentences(wt, want=4):
    lines = [l for l in wt.split("\n") if not l.lstrip().startswith(("|", "{{", "}}", "!", "{|", "[[File", "[[Datei", "[[Fichier"))]
    text = clean("\n".join(lines).replace("\n", " ¶ "))
    out = []
    for s in re.split(r"(?<=[.!?])\s+|¶", text):
        s = s.strip()
        if len(s) > 25 and SENT_KEY.search(s) and numbers(s):
            out.append(s[:260])
            if len(out) >= want:
                break
    return out


def ext_links(wt):
    urls = [u for u in URLRE.findall(wt) if re.search(r"stadiumdb|stadionwelt|europlan|stadiony\.net|worldstadiums", u)]
    return list(dict.fromkeys(urls))[:3]


# ---------- generic page reader (robots first, snippets only) ----------
ROBOTS = {}
SKIP_HOSTS = re.compile(r"wikipedia\.org|wikidata\.org|wikimedia\.org|archive\.org|archive\.(today|is|ph)|"
                        r"books\.google|webcitation|facebook\.com|twitter\.com|x\.com|instagram\.com|youtube\.com")


def allowed(url):
    parts = urllib.parse.urlsplit(url)
    base = f"{parts.scheme}://{parts.netloc}"
    if base not in ROBOTS:
        rp = urllib.robotparser.RobotFileParser()
        try:
            st, _, body = http(base + "/robots.txt", parts.netloc, 2.0, timeout=20, maxbytes=300_000)
            rp.parse(body.decode("utf-8", "replace").splitlines())
            ROBOTS[base] = rp
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                ROBOTS[base] = "closed"
            elif 400 <= e.code < 500:
                rp.parse([])
                ROBOTS[base] = rp
            else:
                ROBOTS[base] = "closed"
        except Exception as e:
            ROBOTS[base] = f"unreachable {type(e).__name__}"
    rp = ROBOTS[base]
    if isinstance(rp, str):
        return False, rp
    return (rp.can_fetch(UA, url) and rp.can_fetch("FootballPlannerBot", url)), "robots"


def figure_forms(n):
    s = str(n)
    if len(s) <= 3:
        return [s]
    a, b = s[:-3], s[-3:]
    return [s, f"{a}.{b}", f"{a},{b}", f"{a} {b}", f"{a} {b}", f"{a}'{b}", f"{a} {b}"]


def read_page(url, figs):
    """-> one-line verdict + snippets (never the page)."""
    host = urllib.parse.urlsplit(url).netloc
    if SKIP_HOSTS.search(host):
        return f"SKIPPED ({host}: not read by rule)"
    ok, why = allowed(url)
    if not ok:
        return f"NOT READ ({why} says no or host closed)"
    try:
        st, hdr, body = http(url, host, 2.0, timeout=25, maxbytes=2_500_000)
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code} (not read, not routed around)"
    except Exception as e:
        return f"FAILED {type(e).__name__}"
    ctype = hdr.get("Content-Type", "")
    if "html" not in ctype and "text" not in ctype:
        return f"HTTP {st} content-type {ctype[:40]} (not parsed)"
    m = re.search(r"charset=([\w-]+)", ctype)
    txt = body.decode(m.group(1) if m else "utf-8", "replace")
    title = re.search(r"<title[^>]*>(.*?)</title>", txt, re.S | re.I)
    title = re.sub(r"\s+", " ", html.unescape(title.group(1))).strip()[:90] if title else ""
    txt = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", txt, flags=re.S | re.I)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", html.unescape(txt))
    out = [f"HTTP {st} title='{title}' textlen={len(txt)}"]
    for label, n in figs:
        hit = None
        for form in figure_forms(n):
            i = txt.find(form)
            if i >= 0:
                hit = txt[max(0, i - 110):i + len(form) + 90]
                break
        out.append(f"   {label} {n}: " + (f"FOUND «{hit.strip()}»" if hit else "not on page"))
    snips = 0
    for m in SENT_KEY.finditer(txt):
        win = txt[max(0, m.start() - 60):m.end() + 110]
        if numbers(win) and not any(win[:50] in o for o in out):
            out.append(f"   kw «{win.strip()}»")
            snips += 1
            if snips >= 3:
                break
    return "\n".join(out)


# ---------- main: compare ----------
def norm(s):
    return re.sub(r"\s+", " ", (s or "").casefold()).strip()


def main_compare():
    clubs = scope()
    log(f"run {RUN}: scope {len(clubs)} clubs")
    ids = [c["id"] for c in clubs]
    p115 = {}
    for i in range(0, len(ids), 50):
        d = wm("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]), "props": "claims"})
        for q, e in ((d or {}).get("entities") or {}).items():
            vs = []
            for st in (e.get("claims") or {}).get("P115", []):
                v = ((st.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
                if v.get("id") and st.get("rank") != "deprecated":
                    vs.append((v["id"], st.get("rank"), "P582" in (st.get("qualifiers") or {})))
            p115[q] = vs
    vids = sorted({v for vs in p115.values() for v, _, _ in vs})
    log(f"venue items named by P115: {len(vids)}")
    V = {}
    for i in range(0, len(vids), 50):
        d = wm("www.wikidata.org", {"action": "wbgetentities", "ids": "|".join(vids[i:i + 50]),
                                    "props": "labels|aliases|sitelinks|claims"})
        for q, e in ((d or {}).get("entities") or {}).items():
            names = {norm(x["value"]) for x in (e.get("labels") or {}).values()}
            for al in (e.get("aliases") or {}).values():
                names |= {norm(x["value"]) for x in al}
            caps = []
            for st in (e.get("claims") or {}).get("P1083", []):
                dv = ((st.get("mainsnak") or {}).get("datavalue") or {}).get("value") or {}
                try:
                    amt = int(float(dv.get("amount", "0")))
                except Exception:
                    continue
                quals = st.get("qualifiers") or {}
                when = ""
                for pq in ("P585", "P580"):
                    if pq in quals:
                        when = (((quals[pq][0].get("datavalue") or {}).get("value") or {}).get("time") or "")[1:5]
                refu = ""
                for ref in st.get("references") or []:
                    for sn in (ref.get("snaks") or {}).get("P854", []):
                        refu = (sn.get("datavalue") or {}).get("value") or ""
                    if not refu and "P143" in (ref.get("snaks") or {}):
                        refu = "imported-from-wikipedia"
                caps.append((amt, st.get("rank", "")[:4], when, refu))
            V[q] = dict(names=names, caps=caps,
                        sl={k: v["title"] for k, v in (e.get("sitelinks") or {}).items()})
    cache = {}

    def article(lang, title, full=False):
        k = (lang, title, full)
        if k not in cache:
            p = {"action": "parse", "page": title, "prop": "wikitext", "redirects": "1"}
            if not full:
                p["section"] = "0"
            d = wm(f"{lang}.wikipedia.org", p)
            cache[k] = ((d or {}).get("parse") or {}).get("wikitext") if d else None
        return cache[k]

    rows = []
    for c in clubs:
        vs = p115.get(c["id"], [])
        cand = [v for v, _, _ in vs if norm(c["venue"]) in V.get(v, {}).get("names", ())]
        how = "L"
        if not cand:
            cand = [v for v, _, _ in vs if any(a == c["cap"] for a, *_ in V.get(v, {}).get("caps", []))]
            how = "C"
        if not cand:
            live = [v for v, r, ended in vs if not ended]
            pref = [v for v, r, ended in vs if not ended and r == "preferred"]
            cand = pref if len(pref) == 1 else (live if len(live) == 1 else [])
            how = "S"
        r = dict(c, vq="", how="X", wiki="", fig=None, kind="", ref="", en=None, enkind="", cls="", raw="", enraw="", allnums=[])
        rows.append(r)
        if not cand:
            r["cls"] = "no-article"
            r["raw"] = f"venue item not identified ({len(vs)} P115 values)"
            continue
        vq = cand[0]
        r["vq"], r["how"] = vq, how
        sl = V[vq]["sl"]
        r["wdcaps"] = V[vq]["caps"]
        tries = [l for l in LANGS[c["cc"]] if f"{l}wiki" in sl]
        if "en" not in tries and "enwiki" in sl:
            tries.append("en")
        if not tries:
            r["cls"] = "no-article"
            r["raw"] = "no sitelink in " + ",".join(LANGS[c["cc"]] + ["en"])
            continue
        results = []
        for l in tries:
            wt = article(l, sl[f"{l}wiki"])
            if wt is None:
                results.append((l, dict(kind="E", fig=None, allnums=[], key="", raw="fetch failed", refurl="", reftext="")))
                continue
            results.append((l, infobox_capacity(wt)))
        r["results"] = results
        r["titles"] = {l: sl[f"{l}wiki"] for l in tries}
        lit = [(l, x) for l, x in results if x["kind"] == "L"]
        for l, x in results:
            if l == "en":
                r["en"], r["enkind"], r["enraw"] = x["fig"], x["kind"], x["raw"]
        if lit:
            l, x = lit[0]
            r.update(wiki=l, fig=x["fig"], kind="L", ref=x["refurl"], raw=x["raw"], allnums=x["allnums"], reftext=x["reftext"])
            r["diff"] = round((x["fig"] - c["cap"]) / c["cap"] * 100, 1)
            r["cls"] = "agrees" if abs(r["diff"]) <= 3 else "differs"
        else:
            l, x = results[0]
            r.update(wiki=l, kind=x["kind"], raw=x["raw"])
            r["cls"] = "not-independent"

    # StadiumDB: robots first, then the repo's own cross-check tool (its country tables)
    sdb = {}
    try:
        st, _, body = http("https://stadiumdb.com/robots.txt", "stadiumdb.com", 2.0, timeout=20)
        log("stadiumdb robots.txt: " + body.decode("utf-8", "replace").replace("\n", " | ")[:200])
        p = subprocess.run([sys.executable, "tools/crosscheck_stadiumdb.py"], capture_output=True, text=True, timeout=1500)
        for ln in p.stdout.splitlines():
            m = re.match(r"^\s*([A-Z]{2}) (.{29}) -> (.{31}) (.{14}) ours\s+(\S+) sdb\s+(\S+)\s+\((.*)\)\s*$", ln)
            if m:
                sdb[(m.group(1), m.group(2).strip())] = (m.group(6), m.group(3).strip(), m.group(7))
        log(f"stadiumdb tool exit {p.returncode}, read-back lines {len(sdb)}")
        for ln in p.stdout.splitlines():
            if "asking StadiumDB" in ln or "grounds," in ln or "HTTP" in ln:
                NREQ["stadiumdb.com"] = NREQ.get("stadiumdb.com", 0) + ("asking" in ln)
        clash = {}
        for rr in csv.DictReader(open("data/clubs/stadiumdb-review.csv", encoding="utf-8")):
            if "do not match" in (rr.get("_verdict") or "") or rr.get("_match") == "ambiguous":
                clash[rr["clubQid"]] = 1
    except Exception as e:
        log(f"ERR stadiumdb {type(e).__name__} {e}")
        clash = {}
    for r in rows:
        s = sdb.get((r["cc"], r["name"][:29].strip()))
        r["sdb"], r["sdbground"] = (s[0], s[1]) if s else ("", "")
        r["sdbclash"] = "!" if r["id"] in clash else ""

    # table
    def grp(t):
        return "t3+" if (t or 0) >= 3 else "t1-2"
    counts = {}
    for r in rows:
        counts[(r["cls"], grp(r["tier"]))] = counts.get((r["cls"], grp(r["tier"])), 0) + 1
    summ = [f"## probe run {RUN}: comparison of {len(rows)} clubs", "", "| class | t1-2 | t3+ | all |", "|---|---|---|---|"]
    for cl in ("agrees", "differs", "not-independent", "no-article"):
        a, b = counts.get((cl, "t1-2"), 0), counts.get((cl, "t3+"), 0)
        summ.append(f"| {cl} | {a} | {b} | {a + b} |")
    summ.append("")
    summ.append("requests: " + ", ".join(f"{k} {v}" for k, v in sorted(NREQ.items())))
    post("\n".join(summ))
    head = "id\tcc\ttier\tmapcap\tvenueQ\tmatch\twiki\tfigure\tkind\tdiff%\tclass\tenfig\tsdb\tallnums\tref"
    lines = [head]
    for r in rows:
        lines.append("\t".join(str(x) for x in (
            r["id"], r["cc"], r["tier"], r["cap"], r["vq"], r["how"], r["wiki"],
            r["fig"] if r["fig"] is not None else "", r["kind"], r.get("diff", ""), r["cls"],
            (r["en"] if r["en"] is not None else r["enkind"]) if r["wiki"] != "en" else "=",
            r["sdb"] + r["sdbclash"], "/".join(map(str, r["allnums"][1:])), r["ref"][:120])))
    post_chunks(f"### run {RUN} TABLE", lines)

    # detail for the differing clubs, priority order
    diff = [r for r in rows if r["cls"] == "differs"]
    diff.sort(key=lambda r: (0 if (r["tier"] or 0) >= 3 else 1, -abs(r["diff"])))
    det = []
    refs_read = 0
    for n, r in enumerate(diff, 1):
        det.append(f"#{n} {r['id']} {r['name']} [{r['cc']} t{r['tier']}] map {r['cap']} | {r['wiki']} {r['fig']} ({r['diff']:+}%) | sdb {r['sdb']}{r['sdbclash']} {r['sdbground']} | venue {r['venue']} = {r['vq']} ({r['how']})")
        det.append("  wd P1083: " + "; ".join(f"{a}[{rk},{w},{u[:70]}]" for a, rk, w, u in r.get("wdcaps", [])))
        for l, x in r.get("results", []):
            det.append(f"  {l}:{r['titles'][l]} [{x['kind']}] {x['raw'][:330]}")
            if x.get("reftext"):
                det.append(f"     ref: {clean(x['reftext'])[:200]} {x['refurl'][:150]}")
        if n <= 75:
            for l in list(r["titles"])[:2]:
                wt = article(l, r["titles"][l], full=True)
                if wt:
                    for s in body_sentences(wt):
                        det.append(f"  {l} text: {s}")
                    for u in ext_links(wt):
                        det.append(f"  {l} link: {u}")
            seen = set()
            for l, x in r.get("results", []):
                u = x.get("refurl")
                if u and u not in seen and refs_read < 90:
                    seen.add(u)
                    refs_read += 1
                    det.append(f"  REF {u[:160]} -> " + read_page(u, [("map", r["cap"]), ("wp", r["fig"])]))
    post_chunks(f"### run {RUN} DIFFERS detail ({len(diff)} clubs, priority order)", det, limit=52000)
    ni = [f"{r['id']}\t{r['cc']}\tt{r['tier']}\t{r['cap']}\t{r['cls']}\t{r['wiki']}\t{r['kind']}\t{r['raw'][:110]}" for r in rows if r["cls"] in ("not-independent", "no-article")]
    post_chunks(f"### run {RUN} NOT-INDEPENDENT and NO-ARTICLE", ni)
    post(f"### run {RUN} LOG\nrequests: " + ", ".join(f"{k} {v}" for k, v in sorted(NREQ.items())) + "\n```\n" + "\n".join(LOG)[-20000:] + "\n```\nDONE run " + RUN)


def main_followup():
    """Later runs: read listed pages (robots first) and listed Wikipedia passages; snippets only."""
    todo = json.load(open(".github/probe/followup.json", encoding="utf-8"))
    out = []
    for item in todo.get("pages", []):
        out.append(f"== {item.get('id','')} {item['url'][:170]}")
        out.append(read_page(item["url"], [(k, v) for k, v in item.get("figs", [])]))
    for item in todo.get("wiki", []):
        d = wm(f"{item['lang']}.wikipedia.org", {"action": "parse", "page": item["title"], "prop": "wikitext", "redirects": "1"})
        wt = ((d or {}).get("parse") or {}).get("wikitext") or ""
        out.append(f"== {item.get('id','')} {item['lang']}:{item['title']} (len {len(wt)})")
        x = infobox_capacity(wt)
        out.append(f"  infobox [{x['kind']}] {x['raw'][:300]} ref {x['refurl'][:150]}")
        pat = re.compile(item.get("grep") or "capacit", re.I)
        shown = 0
        for m in pat.finditer(wt):
            out.append("  «" + re.sub(r"\s+", " ", wt[max(0, m.start() - 150):m.end() + 220]) + "»")
            shown += 1
            if shown >= int(item.get("max", 4)):
                break
    post_chunks(f"### run {RUN} FOLLOW-UP", out, limit=52000)
    post(f"### run {RUN} LOG\nrequests: " + ", ".join(f"{k} {v}" for k, v in sorted(NREQ.items())) + "\n```\n" + "\n".join(LOG)[-15000:] + "\n```\nDONE run " + RUN)


if __name__ == "__main__":
    if MODE == "followup":
        main_followup()
    else:
        main_compare()
