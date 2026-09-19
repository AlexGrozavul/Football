#!/usr/bin/env python3
"""THROWAWAY probe. Phase 1: learn europlan-online.de's structure.

Not a fetcher and not a crawler. It reads a handful of pages to answer
three questions before any club lookup is attempted:

  1. Is the /<ground>/verein/<clubId> URL shape real, or was it an
     artefact of a search engine's index? CLAUDE.md says unverified.
  2. How do you get from a club name to its page at all?
  3. Are a ground page's coordinates and capacity laid out precisely
     and consistently? (go/no-go criterion 3, never checked)

Writes its findings to tmp-europlan/ so the job log stays small.
Delete this file and its workflow step when the answers are in.
"""
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT = "tmp-europlan"
PAUSE = 2.0

os.makedirs(OUT, exist_ok=True)
_log = []


def say(line):
    _log.append(line)
    print(line, flush=True)


def get(path, label):
    url = path if path.startswith("http") else BASE + path
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept-Language": "de,en"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            body = r.read().decode("utf-8", "replace")
            code, final = r.status, r.geturl()
    except urllib.error.HTTPError as e:
        body, code, final = "", e.code, url
    except Exception as e:
        say(f"  {label}: FAILED {type(e).__name__}")
        return None
    dt = time.time() - t0
    h = hashlib.sha256(body.encode()).hexdigest()[:12]
    say(f"  {label}: {code} {len(body)}B {dt:.1f}s {h}")
    time.sleep(PAUSE)
    return {"url": url, "final": final, "code": code, "body": body, "hash": h}


def text_of(html):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</(tr|p|div|h[1-6]|li|table)>", "\n", t)
    t = re.sub(r"(?i)</t[dh]>", " | ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    t = (t.replace("&nbsp;", " ").replace("&amp;", "&")
          .replace("&quot;", '"').replace("&#039;", "'")
          .replace("&uuml;", "ü").replace("&auml;", "ä")
          .replace("&ouml;", "ö").replace("&szlig;", "ß")
          .replace("&Uuml;", "Ü").replace("&Auml;", "Ä").replace("&Ouml;", "Ö"))
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def links(html):
    return re.findall(r'href=["\']([^"\']+)["\']', html, re.I)


findings = {}

# ---------------------------------------------------------------- home
say("[1] homepage")
home = get("/", "home")
if not home:
    raise SystemExit("homepage unreachable - nothing else can be trusted")
HOME_HASH = home["hash"]
HOME_LEN = len(home["body"])

# The site answers 200 with the homepage for any unknown ?s= value, so
# every later "does this page exist" test compares against this.
findings["homepage"] = {"bytes": HOME_LEN, "hash": HOME_HASH}

# ------------------------------------------------- does a search exist
say("[2] search endpoints")
search_probes = ["/index.php?s=suche", "/index.php?s=search",
                 "/index.php?s=verein", "/index.php?s=vereine",
                 "/index.php?s=suche&q=Kray",
                 "/index.php?s=thisdefinitelydoesnotexist"]
sr = {}
for p in search_probes:
    r = get(p, p)
    if r:
        sr[p] = {"code": r["code"], "bytes": len(r["body"]),
                 "is_homepage": r["hash"] == HOME_HASH}
findings["search_probes"] = sr

# --------------------------------------- the known-good ground page
say("[3] known ground page (layout / precision)")
g = get("/stadion-gladbeck-vestische-kampfbahn/stadion-5093.html", "gladbeck")
if g:
    gt = text_of(g["body"])
    with open(f"{OUT}/ground-sample.txt", "w") as f:
        f.write(g["url"] + "\n\n" + gt)
    with open(f"{OUT}/ground-sample.html", "w") as f:
        f.write(g["body"])
    findings["ground_sample"] = {
        "text_chars": len(gt),
        "has_verein_links": len([l for l in links(g["body"]) if "/verein/" in l]),
        "coord_like": re.findall(r"\d{1,2}[.,]\d{3,}\s*[,/]\s*\d{1,2}[.,]\d{3,}", gt)[:5],
        "capacity_words": re.findall(r"(?i)(kapazit\w*|plätze|zuschauer|fassung\w*)", gt)[:8],
    }
    # every link off the ground page, so the /verein/ shape can be judged
    with open(f"{OUT}/ground-links.txt", "w") as f:
        f.write("\n".join(sorted(set(links(g["body"])))))

# --------------------------------------------- Germany's country page
say("[4] country page Germany")
c = get("/index.php?s=land&id=1", "land1")
if c:
    ls = links(c["body"])
    liga = []
    seen = set()
    for m in re.finditer(
            r'href=["\']([^"\']*s=liga[^"\']*)["\'][^>]*>(.*?)</a>',
            c["body"], re.I | re.S):
        href, label = m.group(1), text_of(m.group(2))
        if href in seen:
            continue
        seen.add(href)
        liga.append({"href": href, "label": label})
    with open(f"{OUT}/de-leagues.json", "w") as f:
        json.dump(liga, f, ensure_ascii=False, indent=1)
    findings["land1"] = {
        "bytes": len(c["body"]),
        "total_links": len(ls),
        "liga_links": len(liga),
        "stadion_links": len([l for l in ls if "stadion-" in l]),
        "verein_links": len([l for l in ls if "/verein/" in l]),
        "first_leagues": [x["label"] for x in liga[:12]],
    }

# ------------------------------------------------------- a league page
say("[5] one league page")
lg = None
try:
    cand = [x for x in liga if re.search(r"(?i)regionalliga", x["label"])]
    target = (cand or liga)[0]["href"] if liga else None
except Exception:
    target = None
if target:
    if target.startswith("index.php"):
        target = "/" + target
    lg = get(target, "league")
if lg:
    lt = text_of(lg["body"])
    ll = links(lg["body"])
    with open(f"{OUT}/league-sample.txt", "w") as f:
        f.write(lg["url"] + "\n\n" + lt[:20000])
    with open(f"{OUT}/league-links.txt", "w") as f:
        f.write("\n".join(sorted(set(ll))))
    findings["league_sample"] = {
        "url": lg["url"],
        "bytes": len(lg["body"]),
        "verein_links": len([l for l in ll if "/verein/" in l]),
        "stadion_links": len([l for l in ll if "stadion-" in l]),
        "sample_verein": sorted({l for l in ll if "/verein/" in l})[:6],
        "sample_stadion": sorted({l for l in ll if "stadion-" in l})[:6],
    }

# ----------------------------------------------- follow one club link
say("[6] one club page, to test /<ground>/verein/<id>")
vl = sorted({l for l in links(lg["body"])if "/verein/" in l}) if lg else []
if vl:
    v = get(vl[0] if vl[0].startswith("http") else "/" + vl[0].lstrip("/"),
            "verein")
    if v:
        vt = text_of(v["body"])
        with open(f"{OUT}/club-sample.txt", "w") as f:
            f.write(v["url"] + "\n\n" + vt[:20000])
        findings["club_sample"] = {
            "url": v["url"], "final": v["final"],
            "is_homepage": v["hash"] == HOME_HASH,
            "stadion_links": sorted({l for l in links(v["body"])
                                     if "stadion-" in l})[:8],
        }

with open(f"{OUT}/findings.json", "w") as f:
    json.dump(findings, f, ensure_ascii=False, indent=1)
with open(f"{OUT}/probe.log", "w") as f:
    f.write("\n".join(_log))

say("")
say("=== SUMMARY (full detail is committed under tmp-europlan/) ===")
say(json.dumps({k: v for k, v in findings.items()
                if k != "land1"}, ensure_ascii=False)[:1500])
say("land1: " + json.dumps(findings.get("land1", {}), ensure_ascii=False)[:800])
