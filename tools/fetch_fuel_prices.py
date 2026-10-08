#!/usr/bin/env python3
"""
fetch_fuel_prices.py -- diesel pump prices for the route cost estimate.

Source: the European Commission's Weekly Oil Bulletin, "Weekly prices with
Taxes" workbook (one sheet, one row per country, prices in EUR per 1000 l).
The page https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en
links the workbook; its file NAME carries a date that lags the sheet (the
2026-10-08 read: name 2026-09-21, sheet 2026-10-05), so the week date is
read from the sheet's own date cell, never from the name.

Keeps only diesel ("Gas oil automobile ... Dieselkraftstoff"), converted to
EUR per litre, for the countries the map covers that the bulletin lists.
A country the bulletin does not list (Switzerland, Serbia) is named under
"missing" and gets no price - nothing is filled from memory or from a
neighbour.

Writes data/fuel-prices.json. The file is fetched and never hand-edited.
If the workbook cannot be found or read, or Germany or Romania is absent,
NOTHING is written and the tool exits 1, so the last good file stays.
It rewrites the file only when a price or the week changed.

Stdlib only.  Usage:  python3 tools/fetch_fuel_prices.py [--dry-run]
"""

import datetime
import html
import io
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

PAGE = "https://energy.ec.europa.eu/data-and-analysis/weekly-oil-bulletin_en"
HOST = "https://energy.ec.europa.eu"
OUT = "data/fuel-prices.json"
ATTEMPTS = 3
UA = "Mozilla/5.0 (football-planner fuel price fetch; weekly)"

# The bulletin's English country names -> the ISO codes the club files use
# (England's pyramid is GB). Only countries the map covers.
COUNTRIES = {
    "Germany": "DE", "Romania": "RO", "France": "FR", "Italy": "IT",
    "Austria": "AT", "Greece": "GR", "Spain": "ES", "Netherlands": "NL",
    "Belgium": "BE", "United Kingdom": "GB", "Switzerland": "CH", "Serbia": "RS",
}
REQUIRED = ("DE", "RO")
# A sanity band for a pump price in EUR/L; outside it the cell is not read
# as a price (a unit change or a shifted column), and the run fails.
LOW, HIGH = 0.5, 4.0

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def get(url):
    last = None
    for n in range(1, ATTEMPTS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001 - reported, then retried
            last = e
            print(f"  attempt {n}/{ATTEMPTS} failed: {e}")
            time.sleep(5 * n)
    raise RuntimeError(f"could not fetch {url}: {last}")


def find_workbook(page_html):
    links = re.findall(r'href="(/document/download/[^"]+\.xlsx)"', page_html, re.I)
    want = [html.unescape(l) for l in links
            if re.search(r"prices(%20|\+| )with(%20|\+| )taxes", l, re.I)]
    if len(want) != 1:
        raise RuntimeError(
            f"expected exactly one 'prices with Taxes' workbook link, found {len(want)}: {want}")
    return HOST + want[0]


def read_sheet(data):
    """First sheet as rows of cell values (str / float / None), stdlib only."""
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    sheet = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))[0]
    rows = {}
    for c in ET.fromstring(z.read(sheet)).iter(f"{{{NS['m']}}}c"):
        ref = c.get("r")
        col = re.match(r"[A-Z]+", ref).group(0)
        row = int(ref[len(col):])
        v = c.find("m:v", NS)
        if c.get("t") == "inlineStr":
            val = "".join(t.text or "" for t in c.iter(f"{{{NS['m']}}}t"))
        elif v is None or v.text is None:
            val = None
        elif c.get("t") == "s":
            val = shared[int(v.text)]
        elif c.get("t") in ("str", "b", "e"):
            val = v.text
        else:
            val = float(v.text)
        rows.setdefault(row, {})[col] = val
    return rows


def excel_date(v):
    if isinstance(v, float):
        return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(v))).isoformat()
    m = re.match(r"(\d{4}-\d{2}-\d{2})", str(v or ""))
    return m.group(1) if m else None


def parse(rows):
    head = rows.get(1, {})
    diesel_cols = [c for c, t in head.items()
                   if isinstance(t, str) and re.search(r"diesel", t, re.I)]
    if len(diesel_cols) != 1:
        raise RuntimeError(f"expected one diesel column in row 1, found {diesel_cols}")
    col = diesel_cols[0]
    units = rows.get(2, {})
    if "1000 l" not in str(units.get(col, "")):
        raise RuntimeError(f"diesel column unit is {units.get(col)!r}, expected '1000 l'")
    week = excel_date(units.get("A"))
    if not week:
        raise RuntimeError(f"no week date in A2: {units.get('A')!r}")
    seen, prices = [], {}
    for r in sorted(rows):
        if r < 3:
            continue
        name = rows[r].get("A")
        if isinstance(name, str):
            seen.append(name.strip())
            iso = COUNTRIES.get(name.strip())
            val = rows[r].get(col)
            if iso and isinstance(val, float):
                eur_l = round(val / 1000, 4)
                if not LOW <= eur_l <= HIGH:
                    raise RuntimeError(f"{name}: {val} per 1000 l is outside {LOW}-{HIGH} EUR/L")
                prices[iso] = eur_l
    return week, prices, seen


def main():
    dry = "--dry-run" in sys.argv
    try:
        print(f"Reading {PAGE}")
        url = find_workbook(get(PAGE).decode("utf-8", "replace"))
        print(f"Workbook: {url}")
        week, prices, seen = parse(read_sheet(get(url)))
        absent = [r for r in REQUIRED if r not in prices]
        if absent:
            raise RuntimeError(f"required countries missing from the bulletin: {absent}")
    except Exception as e:  # noqa: BLE001
        print(f"FAILED, nothing written: {e}")
        return 1

    missing = {iso: "not listed in the bulletin" for iso in COUNTRIES.values() if iso not in prices}
    print(f"Bulletin week: {week}")
    print("Countries in the sheet:", ", ".join(seen))
    for iso in sorted(prices):
        print(f"  {iso}  diesel {prices[iso]:.3f} EUR/L")
    for iso in sorted(missing):
        print(f"  {iso}  no price: {missing[iso]}")

    doc = {"fuel": "diesel", "unit": "EUR per litre, pump price incl. taxes",
           "bulletinWeek": week, "sourceUrl": url, "sourcePage": PAGE,
           "prices": dict(sorted(prices.items())), "missing": dict(sorted(missing.items()))}
    try:
        old = json.load(open(OUT))
    except Exception:  # noqa: BLE001
        old = {}
    same = all(old.get(k) == doc[k] for k in ("bulletinWeek", "prices", "missing", "sourceUrl"))
    if same:
        print("Unchanged. File left as it is.")
        return 0
    if dry:
        print("Dry run: would write", OUT)
        return 0
    doc["fetchedOn"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("Wrote", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
