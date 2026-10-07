#!/usr/bin/env python3
"""Offline check of the hand-written dated sale and deadline entries.

Reads data/football-rules.json (ticketEvents) and nothing else. No network,
no commits, nothing is written, and it ALWAYS exits 0 - it prints warnings
only, so it can never fail a build.

CLAUDE.md rule 8: a hand-written dated sale or deadline entry needs a
`source` URL and a `checkedOn` date, and nothing fetches or verifies them
automatically. This lists, per entry that carries a date:

  1. entries missing `source` or `checkedOn`;
  2. entries whose date passed more than 14 days ago;
  3. entries whose `checkedOn` is more than 30 days old while the date is
     still in the future.

The date of an entry is read the way the page reads it: an annual entry's
`nextEstimate`, otherwise `date`, otherwise `dateEstimate`. A month
(YYYY-MM) counts as its last day, a range (a/b) as its last day.
Usage: python3 tools/check_sale_dates.py [path-to-football-rules.json]
"""
import json
import re
import sys
from datetime import date, timedelta
from calendar import monthrange
from pathlib import Path

PASSED_DAYS = 14
STALE_DAYS = 30


def entry_date(ev):
    raw = ev.get("nextEstimate") if ev.get("recurring") == "annual" else (ev.get("date") or ev.get("dateEstimate"))
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.split("/")[-1].strip()
    m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$", raw)
    if not m:
        return None
    y, mo = int(m.group(1)), int(m.group(2))
    try:
        d = int(m.group(3)) if m.group(3) else monthrange(y, mo)[1]
        return date(y, mo, d)
    except ValueError:
        return None


def parse_iso(s):
    try:
        return date.fromisoformat(str(s).strip())
    except ValueError:
        return None


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/football-rules.json")
    today = date.today()
    try:
        events = json.loads(path.read_text(encoding="utf-8")).get("ticketEvents", [])
    except Exception as exc:  # warnings only: never fail the build
        print(f"WARNING: could not read {path}: {exc}")
        return
    missing, passed, stale, undated = [], [], [], 0
    for ev in events:
        d = entry_date(ev)
        if d is None:
            undated += 1
            continue
        name = ev.get("id", "?")
        gaps = [f for f in ("source", "checkedOn") if not str(ev.get(f) or "").strip()]
        if gaps:
            missing.append(f"{name} ({d}): missing {' and '.join(gaps)}")
        if d < today - timedelta(days=PASSED_DAYS):
            passed.append(f"{name}: date {d} passed {(today - d).days} days ago")
        checked = parse_iso(ev.get("checkedOn")) if ev.get("checkedOn") else None
        if d >= today and checked and (today - checked).days > STALE_DAYS:
            stale.append(f"{name}: checkedOn {checked} is {(today - checked).days} days old, date {d} is still ahead")
    print(f"Sale-date check, {today}: {len(events)} ticketEvents, {undated} with no date (not checked). Warnings only.")
    for title, rows in (("Dated entries missing source or checkedOn", missing),
                        (f"Date passed more than {PASSED_DAYS} days ago", passed),
                        (f"checkedOn older than {STALE_DAYS} days, date still ahead", stale)):
        print(f"\n{title}: {len(rows)}")
        for r in rows:
            print(f"  WARNING: {r}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # never fail the build
        print(f"WARNING: sale-date check stopped: {exc}")
    sys.exit(0)
