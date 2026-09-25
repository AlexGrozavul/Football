"""TEMPORARY probe 3 for the Italy tier 1/2 pass. Removed in the same branch."""
import json, re, sys, urllib.parse
sys.path.insert(0, "tools")
import check_rosters as cr
q = urllib.parse.urlencode({"action": "wbgetentities", "ids": "Q3626037",
    "props": "sitelinks", "format": "json"})
data, err = cr.get_json_with_retry("https://www.wikidata.org/w/api.php?" + q, "entity")
links = {k: v.get("title") for k, v in ((data or {}).get("entities", {}).get("Q3626037", {}).get("sitelinks") or {}).items()}
print("SITELINKS", err, links, flush=True)
title = links.get("itwiki")
if title:
    q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "text",
        "format": "json", "formatversion": "2", "redirects": "1"})
    d, err = cr.get_json_with_retry("https://it.wikipedia.org/w/api.php?" + q, title)
    html = (d or {}).get("parse", {}).get("text", "")
    m = re.search(r'<table class="sinottico.*?</table>', html, re.S)
    print("INFOBOX", err, cr.text_of(m.group(0))[:1500] if m else "no infobox table", flush=True)
    body = cr.text_of(html)
    print("LEAD", body[:1200], flush=True)
print("=== END OF PROBE 3 ===")
