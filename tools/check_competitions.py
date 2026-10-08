#!/usr/bin/env python3
"""Read-back and checks for the three hand-written competition files:

  data/competitions.csv         id, name, country, level, type, wikidataQ, officialUrl
  data/competition-info.csv     competitionId, topic, text, status, basis, sourceId, checkedOn
  data/competition-sources.csv  sourceId, url, title, retrievedOn, note

Reads, never writes. Prints what it understood, and every problem with its
line number.

FAILS (exit 1): a malformed row (more values than columns), an invalid
topic, status or competition type, a duplicate id, an unknown
competitionId or sourceId, a bad date, and a day-level FUTURE date in a
text cell (rule 1: a schedule is month level here, never a day).

WARNS only (exit 0): an info row with no source or no checkedOn, a row
whose checkedOn is over 365 days old (rules change between seasons), and
a competition with no info rows at all (the app says "Not researched yet").

Nothing here is ever filled from fetched data.
"""
import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TOPICS = ["format", "qualification", "promotion-relegation", "season-window",
          "schedule-announcement", "tracking", "other"]
STATUSES = ["confirmed", "inferred", "unverified"]
TYPES = ["league", "cup", "supercup", "playoff", "international", "tournament"]
STALE_DAYS = 365

MONTHS = ("jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
          "sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?")
MONTH_NO = {m[:3]: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}

ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
DOTTED = re.compile(r"\b(\d{1,2})\.\s?(\d{1,2})\.\s?(\d{4})\b")
DAY_MONTH = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?(?:\s?[-–]\s?\d{1,2}(?:st|nd|rd|th)?)?\.?\s+(?:of\s+)?(" + MONTHS +
                       r")\b\.?(?:,?\s+(\d{4}))?", re.I)
MONTH_DAY = re.compile(r"\b(" + MONTHS + r")\b\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?!\d)(?:,?\s+(\d{4}))?", re.I)

problems, warnings = [], []


def read(name):
    path = DATA / name
    if not path.exists():
        problems.append(f"{name}: file is missing")
        return [], []
    with open(path, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f)
        head = rd.fieldnames or []
        rows = []
        for r in rd:
            line = rd.line_num
            if None in r:
                problems.append(f"{name} line {line}: more values than the header has columns "
                                f"(an unquoted comma in a cell?)")
                continue
            r["_line"] = line
            rows.append(r)
    return head, rows


def need(name, head, cols):
    miss = [c for c in cols if c not in head]
    if miss:
        problems.append(f"{name}: header lacks {', '.join(miss)}")
    return not miss


def day_level_dates(text, today):
    """Day-level dates in a text that are after today."""
    found = []
    for m in ISO.finditer(text):
        try:
            d = date(int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            found.append((m[0], True)); continue
        found.append((m[0], d > today))
    for m in DOTTED.finditer(text):
        try:
            d = date(int(m[3]), int(m[2]), int(m[1]))
        except ValueError:
            found.append((m[0], True)); continue
        found.append((m[0], d > today))
    for rx, order in ((DAY_MONTH, "dm"), (MONTH_DAY, "md")):
        for m in rx.finditer(text):
            if order == "dm":
                day, mon, year = int(m[1]), MONTH_NO[m[2][:3].lower()], m[3]
            else:
                mon, day, year = MONTH_NO[m[1][:3].lower()], int(m[2]), m[3]
            try:
                d = date(int(year), mon, day) if year else date(today.year, mon, day)
            except ValueError:
                found.append((m[0], True)); continue
            found.append((m[0], d > today))
    return [t for t, future in found if future]


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None


def main():
    today = date.today()
    ch, comps = read("competitions.csv")
    ih, info = read("competition-info.csv")
    sh, srcs = read("competition-sources.csv")

    ok_c = need("competitions.csv", ch, ["id", "name", "country", "level", "type", "wikidataQ", "officialUrl"])
    ok_i = need("competition-info.csv", ih, ["competitionId", "topic", "text", "status", "basis", "sourceId", "checkedOn"])
    ok_s = need("competition-sources.csv", sh, ["sourceId", "url", "title", "retrievedOn", "note"])

    ids, names = {}, {}
    if ok_c:
        for r in comps:
            ln = r["_line"]
            if not r["id"].strip() or not r["name"].strip():
                problems.append(f"competitions.csv line {ln}: id and name are required"); continue
            if r["id"] in ids:
                problems.append(f"competitions.csv line {ln}: id {r['id']} repeated (first on line {ids[r['id']]['_line']})")
            ids[r["id"]] = r
            k = (r["name"].strip().lower(), r["country"].strip())
            if k in names:
                problems.append(f"competitions.csv line {ln}: {r['name']} ({r['country'] or 'international'}) repeated (line {names[k]})")
            names[k] = ln
            if r["type"] not in TYPES:
                problems.append(f"competitions.csv line {ln}: type '{r['type']}' is not one of {', '.join(TYPES)}")
            if r["level"].strip() and not r["level"].strip().isdigit():
                problems.append(f"competitions.csv line {ln}: level '{r['level']}' is not a whole number")
            if r["country"].strip() and not re.fullmatch(r"[A-Z]{2}", r["country"].strip()):
                problems.append(f"competitions.csv line {ln}: country '{r['country']}' is not an ISO-2 code (blank = international)")
            if r["wikidataQ"].strip() and not re.fullmatch(r"Q\d+", r["wikidataQ"].strip()):
                problems.append(f"competitions.csv line {ln}: wikidataQ '{r['wikidataQ']}' is not a Q-id")
            if r["officialUrl"].strip() and not r["officialUrl"].startswith("http"):
                problems.append(f"competitions.csv line {ln}: officialUrl is not a link")

    sids = {}
    if ok_s:
        for r in srcs:
            ln = r["_line"]
            if not r["sourceId"].strip():
                problems.append(f"competition-sources.csv line {ln}: sourceId is required"); continue
            if r["sourceId"] in sids:
                problems.append(f"competition-sources.csv line {ln}: sourceId {r['sourceId']} repeated")
            sids[r["sourceId"]] = r
            if not r["url"].startswith("http"):
                problems.append(f"competition-sources.csv line {ln}: url is not a link")
            if r["retrievedOn"].strip() and not parse_date(r["retrievedOn"].strip()):
                problems.append(f"competition-sources.csv line {ln}: retrievedOn '{r['retrievedOn']}' is not YYYY-MM-DD")

    researched = set()
    if ok_i:
        seen = {}
        for r in info:
            ln = r["_line"]
            cid = r["competitionId"]
            if ok_c and cid not in ids:
                problems.append(f"competition-info.csv line {ln}: unknown competitionId '{cid}'")
            else:
                researched.add(cid)
            if r["topic"] not in TOPICS:
                problems.append(f"competition-info.csv line {ln}: topic '{r['topic']}' is not one of {', '.join(TOPICS)}")
            if r["status"] not in STATUSES:
                problems.append(f"competition-info.csv line {ln}: status '{r['status']}' is not one of {', '.join(STATUSES)}")
            if not r["text"].strip():
                problems.append(f"competition-info.csv line {ln}: text is empty (a missing fact is a missing row, not a blank one)")
            k = (cid, r["topic"])
            if k in seen and r["topic"] != "other":
                problems.append(f"competition-info.csv line {ln}: {cid} / {r['topic']} repeated (line {seen[k]})")
            seen[k] = ln
            refs = [s.strip() for s in r["sourceId"].split(";") if s.strip()]
            if not refs:
                warnings.append(f"competition-info.csv line {ln}: {cid} / {r['topic']} has no sourceId")
            for s in refs:
                if ok_s and s not in sids:
                    problems.append(f"competition-info.csv line {ln}: unknown sourceId '{s}'")
            ck = r["checkedOn"].strip()
            if not ck:
                warnings.append(f"competition-info.csv line {ln}: {cid} / {r['topic']} has no checkedOn")
            else:
                d = parse_date(ck)
                if not d:
                    problems.append(f"competition-info.csv line {ln}: checkedOn '{ck}' is not YYYY-MM-DD")
                elif d > today:
                    problems.append(f"competition-info.csv line {ln}: checkedOn {ck} is in the future")
                elif (today - d).days > STALE_DAYS:
                    warnings.append(f"competition-info.csv line {ln}: {cid} / {r['topic']} was checked {(today - d).days} days ago "
                                    f"(over {STALE_DAYS}); rules change between seasons")
            for col in ("text", "basis"):
                for hit in day_level_dates(r[col], today):
                    problems.append(f"competition-info.csv line {ln}: day-level date '{hit}' in {col} "
                                    f"(competition info is month level; rule 1)")

    # read-back
    print("== competitions.csv ==")
    by = {}
    for r in comps:
        by.setdefault((r["country"] or "international", r["type"]), []).append(r)
    for (c, t), rs in sorted(by.items()):
        print(f"  {c:14s} {t:14s} {len(rs)}")
    print(f"  total {len(comps)} competitions")
    print("== competition-info.csv ==")
    for cid in ids:
        rows = [r for r in info if r["competitionId"] == cid]
        if not rows:
            continue
        print(f"  {cid}")
        for r in sorted(rows, key=lambda r: TOPICS.index(r["topic"]) if r["topic"] in TOPICS else 99):
            print(f"    {r['topic']:22s} {r['status']:10s} sources={r['sourceId'] or '-'} checked={r['checkedOn'] or '-'}")
    none = [c for c in ids if c not in researched]
    print(f"  {len(researched)} competitions with info rows; {len(none)} show 'Not researched yet'")
    print(f"== competition-sources.csv ==\n  {len(srcs)} sources")

    for w in warnings:
        print("WARNING:", w)
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        print(f"\n{len(problems)} problem(s). Exit 1.")
        return 1
    print(f"\nNo problems. {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
