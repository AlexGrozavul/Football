#!/usr/bin/env python3
"""THROWAWAY probe. Phase 1: learn europlan-online.de's structure.

Not a fetcher and not a crawler. It reads a handful of pages to answer
three questions before any club lookup is attempted:

  1. Is the /<ground>/verein/<clubId> URL shape real, or was it an
     artefact of a search engine's index? CLAUDE.md says unverified.
  2. How do you get from a club name to its page at all?
  3. Are a ground page's coordinates and capacity laid out precisely
     and consistently? (go/no-go criterion 3, never checked)

Every request goes through curl with a hard --max-time, because the
first attempt at this hung for 13 minutes on urllib: urlopen's timeout
is a per-socket-operation one, so a slow but never-idle response can
take arbitrarily long. Findings are written to tmp-europlan/ as they
are learned, not at the end, so a hang still leaves the answers behind.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT = "tmp-europlan"
PAUSE = 1.5
MAXTIME = 40

os.makedirs(OUT, exist_ok=True)
findings = {}


def say(s):
    print(s, flush=True)


def save():
    with open(f"{OUT}/findings.json", "w") as f:
        json.dump(findings, f, ensure_ascii=False, indent=1)


def get(path, label):
    """Fetch one page. Returns None rather than raising, and never
    blocks longer than MAXTIME."""
    url = path if path.startswith("http") else BASE + path
    cmd = ["curl", "-sSL", "--max-time", str(MAXTIME), "--compressed",
           "-A", UA, "-H", "Accept-Language: de,en",
           "-w", "\n__META__%{http_code} %{url_effective}", url]
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=MAXTIME + 10)
    except subprocess.TimeoutExpired:
        say(f"  {label}: TIMEOUT")
        return None
    dt = time.time() - t0
    raw = p.stdout.decode("utf-8", "replace")
    if "__META__" not in raw:
        say(f"  {label}: NO RESPONSE ({p.returncode}) {dt:.1f}s")
        return None
    body, meta = raw.rsplit("\n__META__", 1)
    code, _, final = meta.partition(" ")
    h = hashlib.sha256(body.encode()).hexdigest()[:12]
    say(f"  {label}: {code} {len(body)}B {dt:.1f}s {h}")
    time.sleep(PAUSE)
    return {"url": url, "final": final.strip(), "code": code,
            "body": body, "hash": h}


ENT = {"&nbsp;": " ", "&amp;": "&", "&quot;": '"', "&#039;": "'",
       "&uuml;": "ü", "&auml;": "ä", "&ouml;": "ö", "&szlig;": "ß",
       "&Uuml;": "Ü", "&Auml;": "Ä", "&Ouml;": "Ö", "&eacute;": "é"}


def text_of(html):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?i)<br\s*/?>", "\n", t)
    t = re.sub(r"(?i)</(tr|p|div|h[1-6]|li|table)>", "\n", t)
    t = re.sub(r"(?i)</t[dh]>", " | ", t)
    t = re.sub(r"<[^>]+>", " ", t)
    for k, v in ENT.items():
        t = t.replace(k, v)
    t = re.sub(r"[ \t]+", " ", t)
    return re.sub(r"\n\s*\n+", "\n", t).strip()


def links(html):
    return re.findall(r'href=["\']([^"\']+)["\']', html, re.I)


def write(name, s):
    with open(f"{OUT}/{name}", "w") as f:
        f.write(s)


# ---------------------------------------------------------------- home
say("[1] homepage")
home = get("/", "home")
if not home:
    write("probe.log", "homepage unreachable")
    sys.exit("homepage unreachable - nothing else can be trusted")
HOME_HASH = home["hash"]
findings["homepage"] = {"bytes": len(home["body"]), "hash": HOME_HASH}
write("home-links.txt", "\n".join(sorted(set(links(home["body"])))))
save()

# ------------------------------------------------- does a search exist
# The site answers 200 with the homepage for any unknown ?s= value, so
# "does this page exist" is decided by comparing against the homepage.
say("[2] search endpoints")
sr = {}
for p in ["/index.php?s=suche", "/index.php?s=search", "/index.php?s=verein",
          "/index.php?s=vereine", "/index.php?s=suche&q=Kray",
          "/index.php?s=thisdefinitelydoesnotexist"]:
    r = get(p, p.split("?")[-1])
    if r:
        sr[p] = {"code": r["code"], "bytes": len(r["body"]),
                 "is_homepage": r["hash"] == HOME_HASH}
findings["search_probes"] = sr
save()

# --------------------------------------- the known-good ground page
say("[3] known ground page")
g = get("/stadion-gladbeck-vestische-kampfbahn/stadion-5093.html", "gladbeck")
if g:
    gt = text_of(g["body"])
    write("ground-sample.txt", g["url"] + "\n\n" + gt)
    write("ground-sample.html", g["body"])
    write("ground-links.txt", "\n".join(sorted(set(links(g["body"])))))
    findings["ground_sample"] = {
        "text_chars": len(gt),
        "verein_links": [l for l in set(links(g["body"])) if "/verein/" in l][:8],
        "coord_like": re.findall(r"\d{1,2}[.,]\d{3,}\s*[,/ ]\s*\d{1,2}[.,]\d{3,}", gt)[:5],
        "capacity_words": re.findall(r"(?i)(kapazit\w*|plätze|zuschauer|fassung\w*)", gt)[:8],
    }
save()

# --------------------------------------------- Germany's country page
say("[4] country page Germany (504KB, the big one)")
liga = []
c = get("/index.php?s=land&id=1", "land1")
if c:
    ls = links(c["body"])
    seen = set()
    for m in re.finditer(r'href=["\']([^"\']*s=liga[^"\']*)["\'][^>]*>(.*?)</a>',
                         c["body"], re.I | re.S):
        href, label = m.group(1), text_of(m.group(2))
        if href not in seen:
            seen.add(href)
            liga.append({"href": href, "label": label})
    write("de-leagues.json", json.dumps(liga, ensure_ascii=False, indent=1))
    findings["land1"] = {
        "bytes": len(c["body"]), "total_links": len(ls), "liga_links": len(liga),
        "stadion_links": len([l for l in ls if "stadion-" in l]),
        "verein_links": len([l for l in ls if "/verein/" in l]),
        "first_leagues": [x["label"] for x in liga[:15]],
        "regionalliga": [x["label"] for x in liga
                         if re.search(r"(?i)regionalliga", x["label"])][:10],
    }
save()

# ------------------------------------------------------- a league page
say("[5] one league page")
lg = None
cand = [x for x in liga if re.search(r"(?i)regionalliga", x["label"])] or liga
if cand:
    t = cand[0]["href"]
    lg = get(t if t.startswith("http") else "/" + t.lstrip("/"), "league")
if lg:
    ll = links(lg["body"])
    write("league-sample.txt", lg["url"] + "\n\n" + text_of(lg["body"])[:20000])
    write("league-links.txt", "\n".join(sorted(set(ll))))
    findings["league_sample"] = {
        "url": lg["url"], "bytes": len(lg["body"]),
        "is_homepage": lg["hash"] == HOME_HASH,
        "verein_links": len([l for l in ll if "/verein/" in l]),
        "stadion_links": len([l for l in ll if "stadion-" in l]),
        "sample_verein": sorted({l for l in ll if "/verein/" in l})[:6],
        "sample_stadion": sorted({l for l in ll if "stadion-" in l})[:6],
    }
save()

# ----------------------------------------------- follow one club link
say("[6] one club page, to test /<ground>/verein/<id>")
vl = sorted({l for l in links(lg["body"]) if "/verein/" in l}) if lg else []
if vl:
    v = get(vl[0] if vl[0].startswith("http") else "/" + vl[0].lstrip("/"),
            "verein")
    if v:
        write("club-sample.txt", v["url"] + "\n\n" + text_of(v["body"])[:20000])
        findings["club_sample"] = {
            "url": v["url"], "final": v["final"],
            "is_homepage": v["hash"] == HOME_HASH,
            "stadion_links": sorted({l for l in links(v["body"])
                                     if "stadion-" in l})[:8]}
save()

say("")
say("=== SUMMARY (detail committed under tmp-europlan/) ===")
say(json.dumps(findings, ensure_ascii=False)[:2000])
