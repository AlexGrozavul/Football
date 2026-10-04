#!/usr/bin/env python3
"""
check_holidays.py -- read-back and checks for data/holidays-manual.csv.

data/holidays-manual.csv is hand-written: one row per school holiday
block, movable school day or school start, from Alexandru's school
calendar and the Baden-Württemberg education ministry
(km.baden-wuerttemberg.de/de/service/ferien). The Bucket list tab's
calendar reads it to shade the days. Nothing writes to it.

This tool never writes to it either. It reads it, prints back every row
exactly as understood, and complains. A rejected row is named with its
line number and left alone, because the fix belongs in the file. It
exits 1 when a row was rejected, so a workflow step shows red rather
than a green tick over a broken file.

Usage:  python3 tools/check_holidays.py [--full]

        --full prints every note in full. Without it a long note is shown
        as its start and end plus a length.


WHAT REJECTS A ROW
------------------
- a required cell left empty: name, start, end, kind, dateSource, source.
  A holiday with no source is a guess, and this file holds none.
- a start or end that is not a real date written YYYY-MM-DD
  ("2027-02-30" and "YYYY-MM-DD" are both rejected)
- an end before its start
- a dateSource that is not confirmed, inferred or disputed (the closed
  list every hand-written file in this repo uses)
- a row with more values than the header has columns (an unquoted comma)

WHAT IS REPORTED, AND NOT ACCEPTED
----------------------------------
- a kind other than school-holiday, school-holiday-movable and
  school-start. The calendar does not draw it: a kind it does not know
  could mean anything, and shading a day on a guess is what rule 2
  forbids. Add the kind to KINDS here and to the page deliberately.

WHAT IS REPORTED AND KEPT
-------------------------
- two rows whose days overlap
- a school-start row that spans more than one day
- a row that is not confirmed: the calendar shades confirmed rows only
- no school-holiday-movable row at all: the movable days are then not
  entered, and a day without shading may still be one
"""

import csv
import datetime
import os
import sys

HOLIDAYS_FILE = "data/holidays-manual.csv"
REQUIRED = ["name", "start", "end", "kind", "dateSource", "source"]
OPTIONAL = ["note"]
KINDS = ["school-holiday", "school-holiday-movable", "school-start"]
DATE_SOURCES = ["confirmed", "inferred", "disputed"]

# Same guard as every other reader in tools/: a value past the last
# column is a comma that was meant to be inside a cell.
OVERFLOW = object()


def _s(v):
    return (v or "").strip()


def parse_day(v):
    """A real calendar date written YYYY-MM-DD, or None. A plain date:
    no time, no time zone, nothing converted."""
    if len(v) != 10 or v[4] != "-" or v[7] != "-":
        return None
    try:
        return datetime.date.fromisoformat(v)
    except ValueError:
        return None


def fmt(d):
    return d.strftime("%a %d %b %Y")


def note_text(v, full):
    if full or len(v) <= 110:
        return v
    return f"{v[:60]} … {v[-40:]} ({len(v)} characters)"


def main():
    full = "--full" in sys.argv[1:]
    problems, notices, unknown, rows = [], [], [], []

    print("=" * 70)
    print(f"{HOLIDAYS_FILE} - read back exactly as understood")
    print("=" * 70)

    if not os.path.exists(HOLIDAYS_FILE):
        print(f"  ! {HOLIDAYS_FILE}: file not found")
        return 1

    with open(HOLIDAYS_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh, restkey=OVERFLOW)
        headers = [_s(h) for h in (reader.fieldnames or [])]
        missing = [h for h in REQUIRED if h not in headers]
        if missing:
            print(f"  ! {HOLIDAYS_FILE} line 1: missing required column(s) "
                  f"{', '.join(missing)}. Nothing in this file was read.")
            return 1
        for h in headers:
            if h and h not in REQUIRED + OPTIONAL:
                notices.append(f"line 1: column {h!r} is not one this tool "
                               f"knows. It is ignored.")

        for raw in reader:
            line = reader.line_num
            extra = raw.pop(OVERFLOW, None)
            if extra:
                problems.append(
                    f"line {line}: {len(extra)} more value(s) than the header "
                    f"has columns, starting {extra[0]!r}. A comma inside a "
                    f'cell splits it in two - quote the whole cell ("a, b"). '
                    f"Row ignored.")
                continue
            row = {_s(k): _s(v) for k, v in raw.items() if k is not None}
            if not any(row.values()):
                continue
            label = row.get("name") or "(no name)"

            empty = [f for f in REQUIRED if not row.get(f)]
            if empty:
                why = (" A holiday without a source is a guess, and this file "
                       "holds none." if "source" in empty else "")
                problems.append(f"line {line} ({label}): {', '.join(empty)} "
                                f"empty.{why} Row ignored.")
                continue

            start, end = parse_day(row["start"]), parse_day(row["end"])
            bad = [f"{k} {row[k]!r}" for k, d in (("start", start), ("end", end)) if d is None]
            if bad:
                problems.append(f"line {line} ({label}): {' and '.join(bad)} "
                                f"{'are' if len(bad) > 1 else 'is'} not a real date written "
                                f"YYYY-MM-DD. Row ignored.")
                continue
            if end < start:
                problems.append(f"line {line} ({label}): ends {row['end']}, "
                                f"before it starts {row['start']}. Row ignored.")
                continue
            if row["dateSource"] not in DATE_SOURCES:
                problems.append(f"line {line} ({label}): dateSource "
                                f"{row['dateSource']!r} is not one of "
                                f"{', '.join(DATE_SOURCES)}. Row ignored.")
                continue

            row.update(_line=line, _start=start, _end=end)
            if row["kind"] not in KINDS:
                unknown.append(row)
                continue
            if row["kind"] == "school-start" and start != end:
                notices.append(f"line {line} ({label}): a school start that "
                               f"spans {(end - start).days + 1} days. Kept.")
            if row["dateSource"] != "confirmed":
                notices.append(f"line {line} ({label}): dateSource is "
                               f"{row['dateSource']}. Kept, but the calendar "
                               f"shades confirmed rows only.")
            rows.append(row)

    for r in rows:
        days = (r["_end"] - r["_start"]).days + 1
        span = fmt(r["_start"]) if days == 1 else f"{fmt(r['_start'])} to {fmt(r['_end'])}"
        print(f"\n  line {r['_line']}: {r['name']}")
        print(f"      {span}  ({days} day{'s' if days != 1 else ''})")
        print(f"      kind: {r['kind']} · dateSource: {r['dateSource']} · source: {r['source']}")
        if r.get("note"):
            print(f"      note: {note_text(r['note'], full)}")

    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            if a["_start"] <= b["_end"] and b["_start"] <= a["_end"]:
                notices.append(f"lines {a['_line']} and {b['_line']}: "
                               f"{a['name']} and {b['name']} overlap. Kept.")

    print("\n" + "-" * 70)
    blocks = [r for r in rows if r["kind"] in ("school-holiday", "school-holiday-movable")]
    if rows:
        first = min(r["_start"] for r in rows)
        last = max(r["_end"] for r in rows)
        print(f"Entered from {fmt(first)} to {fmt(last)}. Outside that the "
              f"calendar says school holidays are not entered - it never "
              f"says there are none.")
    by_kind = {k: sum(1 for r in rows if r["kind"] == k) for k in KINDS}
    print("Rows: " + ", ".join(f"{n} {k}" for k, n in by_kind.items()) +
          f"; {sum((r['_end'] - r['_start']).days + 1 for r in blocks)} holiday days in all.")
    if not by_kind["school-holiday-movable"]:
        notices.append("no school-holiday-movable row: the movable school days "
                       "(bewegliche Ferientage) are not entered, so a day "
                       "without shading may still be one. The calendar says so.")

    if unknown:
        print(f"\nNOT ACCEPTED - {len(unknown)} row(s) with a kind this tool "
              f"does not know. The calendar does not draw them:")
        for r in unknown:
            print(f"  line {r['_line']} ({r['name']}): kind {r['kind']!r}, not "
                  f"one of {', '.join(KINDS)}. If it is real, add it to KINDS "
                  f"here and to the page.")
    if notices:
        print(f"\nREPORTED - {len(notices)}:")
        for n in notices:
            print(f"  {n}")
    if problems:
        print(f"\nREJECTED - {len(problems)}:")
        for p in problems:
            print(f"  ! {p}")
        return 1
    print("\nNo row rejected." + (" Rows with an unknown kind are listed above."
                                 if unknown else " Every row was read."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
