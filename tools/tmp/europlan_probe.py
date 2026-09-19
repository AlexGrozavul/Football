#!/usr/bin/env python3
"""THROWAWAY probe, phase 4: the seven the league pages did not hold.

Thirteen league pages settled 14 of the 22. Seven are left, and all of
them look like clubs that have simply dropped below tier 5 since
Wikidata last tagged them Regionalliga: Eutin 08, FC Kray, Lupo Martini
Wolfsburg, Torgelower FC Greif, VfB Hüls, VfR Garching, and Viktoria
1889 Berlin, whose best league-page candidate was a different Berlin
club matched on the word Berlin.

Guessing at more league pages is how a targeted lookup turns into a
scan, so this asks the site's own search instead - if it has one.
index.php?s=search came back in phase 1 as a distinct 46KB page rather
than the homepage the site serves for an unknown ?s=, so there is
something there.

FSV Optik Rathenow is the control. It is one of the 14 already settled,
so a search that cannot find it is broken rather than telling us these
seven are absent.
"""
import json, os, re, subprocess, time

BASE = "https://www.europlan-online.de"
UA = ("FootballFixturePlanner/1.0 (personal, non-commercial; "
      "resolving 22 missing German ground coordinates)")
OUT, PAUSE, MAXTIME = "tmp-europlan", 1.2, 40
os.makedirs(OUT, exist_ok=True)

MISSING = ["Eutin 08", "Kray", "Lupo Martini", "Torgelower", "Hüls",
           "Garching", "Viktoria 1889 Berlin"]
CONTROL = "Optik Rathenow"


def say(s): print(s, flush=True)


def get(path, label, post=None):
    url = path if path.startswith("http") else BASE + "/" + path.lstrip("/")
    cmd = ["curl", "-sSL", "--max-time", str(MAXTIME), "--compressed", "-A", UA,
           "-H", "Accept-Language: de,en", "-w", "\n__M__%{http_code}"]
    if post:
        cmd += ["--data-urlencode", post]
    cmd.append(url)
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=MAXTIME + 10)
    except subprocess.TimeoutExpired:
        say(f"  {label}: TIMEOUT"); return None
    raw = p.stdout.decode("utf-8", "replace")
    if "__M__" not in raw:
        say(f"  {label}: NO RESPONSE"); return None
    body, meta = raw.rsplit("\n__M__", 1)
    say(f"  {label}: {meta.strip()} {len(body)}B")
    time.sleep(PAUSE)
    return body


ENT = {"&nbsp;": " ", "&amp;": "&", "&uuml;": "ü", "&auml;": "ä",
       "&ouml;": "ö", "&szlig;": "ß", "&Uuml;": "Ü", "&Ouml;": "Ö"}

def txt(h):
    t = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", h)
    t = re.sub(r"<[^>]+>", " ", t)
    for k, v in ENT.items(): t = t.replace(k, v)
    return re.sub(r"\s+", " ", t).strip()


out = {}

# ------------------------------------------------- what is the search page
say("[1] the search page and its form")
h = get("index.php?s=search", "s=search")
if h:
    open(f"{OUT}/search-page.html", "w").write(h)
    forms = re.findall(r"(?is)<form[^>]*>.*?</form>", h)
    out["forms"] = [re.sub(r"\s+", " ", f)[:900] for f in forms[:4]]
    out["inputs"] = re.findall(r"(?is)<(?:input|select)[^>]*>", h)[:25]
    out["action_hints"] = sorted(set(re.findall(r'action=["\']([^"\']*)["\']', h)))[:8]
    say(f"  forms: {len(forms)}  inputs: {len(out['inputs'])}")
    for i in out["inputs"][:12]:
        say("    " + re.sub(r"\s+", " ", i)[:150])

json.dump(out, open(f"{OUT}/search-probe.json", "w"), ensure_ascii=False, indent=1)

# --------------------------------------- try query shapes with the control
say(f"[2] control search for {CONTROL!r}")
SHAPES = ["index.php?s=search&q={q}", "index.php?s=search&suche={q}",
          "index.php?s=search&begriff={q}", "index.php?s=search&name={q}",
          "index.php?s=search&t=verein&q={q}"]
import urllib.parse as up
working = None
tries = {}
for sh in SHAPES:
    u = sh.format(q=up.quote(CONTROL))
    b = get(u, sh.split("&", 1)[1].split("=")[0])
    if not b:
        continue
    hit = bool(re.search(r"stadion-\d+\.html", b)) and "Rathenow" in b
    tries[sh] = {"bytes": len(b), "found_control": hit}
    if hit and not working:
        working = sh
        open(f"{OUT}/search-hit.html", "w").write(b)
out["control_tries"] = tries
out["working_shape"] = working
say(f"  working shape: {working}")
json.dump(out, open(f"{OUT}/search-probe.json", "w"), ensure_ascii=False, indent=1)

# ------------------------------------------------------ the seven, if we can
results = {}
if working:
    say("[3] the seven")
    for name in MISSING:
        b = get(working.format(q=up.quote(name)), name)
        if not b:
            continue
        rows = []
        for m in re.finditer(
                r'(?is)<a href="([^"]*stadion-(\d+)\.html)"[^>]*>(.*?)</a>', b):
            rows.append({"href": m.group(1), "id": m.group(2),
                         "ground": txt(m.group(3))})
        seen, ded = set(), []
        for r in rows:
            if r["id"] not in seen:
                seen.add(r["id"]); ded.append(r)
        results[name] = {"hits": ded[:8], "text": txt(b)[:1200]}
        say(f"    {name}: {len(ded)} distinct ground links")
else:
    say("[3] skipped - no working search shape, so the seven cannot be asked for")

out["missing_results"] = results
json.dump(out, open(f"{OUT}/search-probe.json", "w"), ensure_ascii=False, indent=1)
say("done")
