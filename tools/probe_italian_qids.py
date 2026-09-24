#!/usr/bin/env python3
"""TEMPORARY probe, removed in the same branch. Reads Q631 and Q1543 from
Wikidata and prints label, description, P31, P17, P118 (with rank),
P115, enwiki/itwiki sitelinks, and whether P31 says men's team or club.
Also resolves enwiki titles "Inter Milan" and "AC Milan" to Q-ids, so the
answer does not depend on the ids being right in the first place."""
import json, urllib.request, urllib.parse, sys
UA = {"User-Agent": "football-planner-probe/1.0 (github.com/AlexGrozavul/football)"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)
API = "https://www.wikidata.org/w/api.php?"
def ents(**kw):
    kw.update(action="wbgetentities", format="json")
    return get(API + urllib.parse.urlencode(kw))
def label_of(qids):
    if not qids: return {}
    d = ents(ids="|".join(qids), props="labels", languages="en")
    return {q: e.get("labels", {}).get("en", {}).get("value", "?") for q, e in d.get("entities", {}).items()}
print("=== ANSWER FIRST: enwiki title -> Q-id ===")
for title in ("Inter Milan", "AC Milan"):
    d = ents(sites="enwiki", titles=title, props="info", normalize="1")
    if "error" in d: print("ERROR", d["error"]); continue
    print(f"  {title!r} -> {list(d.get('entities', {}).keys())}")
for q in ("Q631", "Q1543"):
    d = ents(ids=q, props="labels|descriptions|claims|sitelinks", languages="en|it")
    if "error" in d: print("ERROR", q, d["error"]); continue
    e = d["entities"][q]
    c = e.get("claims", {})
    def vals(p):
        out = []
        for s in c.get(p, []):
            dv = s["mainsnak"].get("datavalue")
            v = dv["value"]["id"] if dv and isinstance(dv["value"], dict) and "id" in dv["value"] else s["mainsnak"]["snaktype"]
            out.append((v, s["rank"]))
        return out
    p31, p17, p118, p115 = vals("P31"), vals("P17"), vals("P118"), vals("P115")
    names = label_of(sorted({v for v, _ in p31 + p17 + p118 + p115 if v.startswith("Q")}))
    print(f"=== {q} ===")
    print("  label en:", e.get("labels", {}).get("en", {}).get("value"), "| it:", e.get("labels", {}).get("it", {}).get("value"))
    print("  desc en:", e.get("descriptions", {}).get("en", {}).get("value"))
    for p, vs in (("P31", p31), ("P17", p17), ("P118", p118), ("P115", p115)):
        print(f"  {p}:", "; ".join(f"{v} {names.get(v, '')} [{r}]" for v, r in vs))
    sl = e.get("sitelinks", {})
    print("  sitelinks:", len(sl), "| enwiki:", sl.get("enwiki", {}).get("title"), "| itwiki:", sl.get("itwiki", {}).get("title"))
print("=== ANSWER AGAIN ===")
for title in ("Inter Milan", "AC Milan"):
    d = ents(sites="enwiki", titles=title, props="info", normalize="1")
    print(f"  {title!r} -> {list(d.get('entities', {}).keys())}")
