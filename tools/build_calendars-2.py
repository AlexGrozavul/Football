#!/usr/bin/env python3
"""
build_calendars.py -- step 1 of the football fixture/ticket planner.

Reads data/football-rules.json and emits one .ics file per feed, plus
bucket-list.ics, plus skipped.md explaining every entry that produced
no event.

Stdlib only. No network. No dependencies. Nothing here invents a date,
a deadline or a ticket rule: every date comes from the JSON, and an
entry whose date cannot be resolved is skipped and reported.

Usage:  python3 tools/build_calendars.py
"""

import csv
import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None

# ---------------------------------------------------------------- config

DATA_FILE = "data/football-rules.json"
FIXTURES_FILE = "data/fixtures-manual.csv"
OUT_DIR = "calendars"
STAMP_FILE = os.path.join(OUT_DIR, ".stamps.json")

# Used only to build UIDs. Must never change once you have subscribed,
# or every client treats every event as brand new.
UID_DOMAIN = "football.local"

# Every feed gets a file, even when it is empty. An empty but valid
# calendar is correct; a 404 makes subscribing clients drop the feed.
FEEDS = {
    "bayern":      "Bayern - tickets",
    "germany-nt":  "Germany NT - tickets",
    "local":       "Local (day trip) - tickets",
    "italy":       "Italy - tickets",
    "romania":     "Romania - tickets",
    "uefa-finals": "UEFA finals - tickets",
    "admin":       "Admin - verification tasks",
}
BUCKET_FEED = "bucket-list"
BUCKET_NAME = "Bucket list"

# Hand-entered fixtures are written to fixtures-<feed>.ics, kept apart
# from the ticket-window feeds. Put "manual" in every feed cell if you
# want them all in one file.
FIXTURE_PREFIX = "fixtures-"
FIXTURE_MATCH_HOURS = 2

# Kick-off times are local to the ground. Derived from the home club's
# country when the club id is known; overridden by a tz column.
COUNTRY_TZ = {
    "DE": "Europe/Berlin",
    "RO": "Europe/Bucharest",
    "IT": "Europe/Rome",
    "FR": "Europe/Paris",
    "AT": "Europe/Vienna",
    "CH": "Europe/Zurich",
    "NL": "Europe/Amsterdam",
    "BE": "Europe/Brussels",
    "ES": "Europe/Madrid",
    "PT": "Europe/Lisbon",
    "PL": "Europe/Warsaw",
    "CZ": "Europe/Prague",
    "HU": "Europe/Budapest",
    "GB": "Europe/London",
}
FALLBACK_TZ = "Europe/Berlin"

CSV_REQUIRED = ("date", "home", "away", "feed", "dateSource")
CSV_OPTIONAL = ("time", "venue", "competition", "leadTimeDays", "notes", "tz")

# dateSource values.
#   confirmed - from a published source. Normal event.
#   inferred  - reasoned from a known pattern. Emits, marked [?].
#   disputed  - may be the wrong year or the wrong event. Never emits.
EMITS = {"confirmed", "inferred"}
KNOWN_SOURCES = EMITS | {"disputed"}

UNCONFIRMED_PREFIX = "[?] "

ALARM_TEXT = {
    "confirmed": "Buy now.",
    "inferred": "Check whether this window has been announced. "
                "The date below is an estimate, not a published one.",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ------------------------------------------------------------ ics output

def esc(text):
    """Escape a value for an iCalendar property."""
    if text is None:
        return ""
    s = str(text)
    s = s.replace("\\", "\\\\")
    s = s.replace(";", "\\;")
    s = s.replace(",", "\\,")
    s = s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")
    return s


def fold(line):
    """Fold a content line to 75 octets, never splitting a UTF-8 char."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line
    out, start, limit = [], 0, 75
    while start < len(raw):
        end = min(start + limit, len(raw))
        # back off until we are on a character boundary
        while end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        out.append(raw[start:end].decode("utf-8"))
        start = end
        limit = 74  # continuation lines lose one octet to the leading space
    return "\r\n ".join(out)


def ymd(d):
    return d.strftime("%Y%m%d")


# ------------------------------------------------------------ date rules

def parse_date(value):
    """'YYYY-MM-DD' -> (d, d). 'YYYY-MM-DD/YYYY-MM-DD' -> (start, end)."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if "/" in value:
        a, b = value.split("/", 1)
        a, b = a.strip(), b.strip()
        if DATE_RE.match(a) and DATE_RE.match(b):
            da = date.fromisoformat(a)
            db = date.fromisoformat(b)
            if db >= da:
                return (da, db)
        return None
    if DATE_RE.match(value):
        d = date.fromisoformat(value)
        return (d, d)
    return None


def resolve_ticket_event(ev, today):
    """
    Return (start, end, source) or (None, None, reason_string).

    Recurring annual entries regenerate from nextEstimate and emit ONE
    future occurrence. Past occurrences stay in the JSON as history but
    never reach the calendar.
    """
    source = ev.get("dateSource")
    if source is None:
        return None, None, "no dateSource set - cannot classify the date, so it is not emitted"
    if source not in KNOWN_SOURCES:
        return None, None, f"unrecognised dateSource {source!r}"
    if source == "disputed":
        return None, None, "dateSource is disputed - the date may be from the wrong year or event"

    recurring = ev.get("recurring")
    if recurring == "per fixture":
        return None, None, ("recurring per fixture - needs the fixture list, "
                            "which does not exist until step 3")

    if recurring == "annual":
        raw = ev.get("nextEstimate")
        if not raw:
            return None, None, "recurring annual but no nextEstimate to regenerate from"
    else:
        raw = ev.get("date") or ev.get("dateEstimate")
        if not raw:
            return None, None, "no date or dateEstimate"

    span = parse_date(raw)
    if span is None:
        return None, None, f"unparseable date {raw!r}"

    start, end = span
    if end < today:
        return None, None, f"occurrence {raw} is in the past - history stays in the JSON only"
    return start, end, source


def resolve_bucket_dates(item, today):
    """
    Yield (suffix, start, end, source, extra_note) for each dated
    occurrence of a bucket-list item, or record why there is none.

    Trigger-only entries are skipped by design. They belong in the
    bucket-list tab, not in a calendar.
    """
    results, reasons = [], []

    fixtures = item.get("fixtures")
    if isinstance(fixtures, list) and fixtures:
        for i, fx in enumerate(fixtures):
            src = fx.get("dateSource")
            if src is None:
                reasons.append(f"fixtures[{i}] has no dateSource")
                continue
            if src == "disputed":
                reasons.append(f"fixtures[{i}] dateSource is disputed")
                continue
            if src not in EMITS:
                reasons.append(f"fixtures[{i}] unrecognised dateSource {src!r}")
                continue
            span = parse_date(fx.get("date"))
            if span is None:
                reasons.append(f"fixtures[{i}] has no usable date")
                continue
            if span[1] < today:
                reasons.append(f"fixtures[{i}] on {fx.get('date')} is in the past")
                continue
            note = fx.get("saleRoute")
            results.append((f"-{i}", span[0], span[1], src, note))
        return results, reasons

    nxt = item.get("nextFixture")
    if isinstance(nxt, dict):
        src = nxt.get("dateSource")
        raw = nxt.get("dateEstimate") or nxt.get("date")
        if src is None:
            reasons.append("nextFixture has no dateSource")
        elif src == "disputed":
            reasons.append("nextFixture dateSource is disputed")
        elif src not in EMITS:
            reasons.append(f"nextFixture unrecognised dateSource {src!r}")
        else:
            span = parse_date(raw)
            if span is None:
                reasons.append("nextFixture has no usable date")
            elif span[1] < today:
                reasons.append(f"nextFixture on {raw} is in the past")
            else:
                results.append(("", span[0], span[1], src, nxt.get("derivation")))
        return results, reasons

    src = item.get("dateSource")
    raw = item.get("date") or item.get("dateEstimate")
    if raw:
        if src is None:
            reasons.append("no dateSource set")
        elif src == "disputed":
            reasons.append("dateSource is disputed")
        elif src not in EMITS:
            reasons.append(f"unrecognised dateSource {src!r}")
        else:
            span = parse_date(raw)
            if span is None:
                reasons.append(f"unparseable date {raw!r}")
            elif span[1] < today:
                reasons.append(f"{raw} is in the past")
            else:
                results.append(("", span[0], span[1], src, None))
        return results, reasons

    if item.get("trigger"):
        reasons.append("trigger only, no date - belongs in the bucket-list tab, not a calendar")
    else:
        reasons.append("no date of any kind")
    return results, reasons


# ------------------------------------------------------------ event body

def build_event(uid, title, start, end, source, lead_days, action, detail_lines,
                start_utc=None, end_utc=None, location=None):
    """Assemble the dict an event is rendered from.

    All-day unless start_utc/end_utc are supplied, which is how a
    fixture with a known kick-off time is carried.
    """
    display = (UNCONFIRMED_PREFIX + title) if source == "inferred" else title

    body = list(detail_lines)
    if action:
        body.insert(0, action)
    body.append("")
    body.append(f"Date source: {source}.")
    if source == "inferred":
        body.append("This date was reasoned from a pattern, not published. Verify before acting.")
    body.append("Generated from football-rules.json. Edit the JSON, not the calendar.")

    alarm = ALARM_TEXT[source]

    return {
        "uid": uid,
        "summary": display,
        "start": start,
        "end": end + timedelta(days=1),  # DTEND is exclusive for all-day
        "start_utc": start_utc,
        "end_utc": end_utc,
        "location": location,
        "description": "\n".join(b for b in body if b is not None),
        "lead_days": None if lead_days is None else int(lead_days),
        "alarm": alarm,
    }


def event_hash(ev):
    payload = json.dumps(
        {k: (v.isoformat() if isinstance(v, date) else v)
         for k, v in ev.items() if k != "uid"},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def render_event(ev, dtstamp, sequence):
    lines = [
        "BEGIN:VEVENT",
        f"UID:{ev['uid']}",
        f"DTSTAMP:{dtstamp}",
        f"SEQUENCE:{sequence}",
    ]
    if ev.get("start_utc"):
        # Stored in UTC so the phone shows the correct local time
        # wherever it happens to be. No VTIMEZONE block needed.
        lines.append("DTSTART:" + ev["start_utc"].strftime("%Y%m%dT%H%M%SZ"))
        lines.append("DTEND:" + ev["end_utc"].strftime("%Y%m%dT%H%M%SZ"))
        lines.append("TRANSP:OPAQUE")
    else:
        lines.append(f"DTSTART;VALUE=DATE:{ymd(ev['start'])}")
        lines.append(f"DTEND;VALUE=DATE:{ymd(ev['end'])}")
        lines.append("TRANSP:TRANSPARENT")
    lines.append(f"SUMMARY:{esc(ev['summary'])}")
    if ev.get("location"):
        lines.append(f"LOCATION:{esc(ev['location'])}")
    lines.append(f"DESCRIPTION:{esc(ev['description'])}")
    if ev.get("lead_days") is not None:
        lines.extend([
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER;RELATED=START:-P{ev['lead_days']}D",
            f"DESCRIPTION:{esc(ev['alarm'] + ' ' + ev['summary'])}",
            "END:VALARM",
        ])
    lines.append("END:VEVENT")
    return lines


def render_calendar(name, events, stamps):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//football-rules//calendar generator//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{esc(name)}",
        "X-PUBLISHED-TTL:PT12H",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
    ]
    for ev in sorted(events, key=lambda e: (e["start"], e["uid"])):
        h = event_hash(ev)
        prev = stamps.get(ev["uid"])
        if prev and prev.get("hash") == h:
            dtstamp, sequence = prev["dtstamp"], prev["sequence"]
        else:
            dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            sequence = (prev["sequence"] + 1) if prev else 0
            stamps[ev["uid"]] = {"hash": h, "dtstamp": dtstamp, "sequence": sequence}
        lines.extend(render_event(ev, dtstamp, sequence))
    lines.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in lines) + "\r\n"



# --------------------------------------------------- hand-entered fixtures

def _clean(value):
    return (value or "").strip()


def read_manual_fixtures(clubs_by_id, today):
    """
    Parse data/fixtures-manual.csv.

    Header-driven: column order does not matter and unused optional
    columns may be left out entirely. Returns (events_by_feed, readback,
    problems) where readback is the plain list of rows as understood.
    """
    events, readback, problems = {}, [], []

    if not os.path.exists(FIXTURES_FILE):
        readback.append(f"{FIXTURES_FILE} not present - no hand-entered fixtures.")
        return events, readback, problems

    with open(FIXTURES_FILE, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            problems.append("line 1: the file is empty - it needs a header row")
            return events, readback, problems

        headers = [(_clean(h) or "") for h in reader.fieldnames]
        missing = [c for c in CSV_REQUIRED if c not in headers]
        if missing:
            problems.append(
                "line 1: header row is missing required column(s): " + ", ".join(missing))
            return events, readback, problems
        unknown = [h for h in headers if h and h not in CSV_REQUIRED + CSV_OPTIONAL]
        for h in unknown:
            problems.append(f"line 1: column {h!r} is not recognised and was ignored")

        for row in reader:
            line = reader.line_num
            row = {(_clean(k) or ""): _clean(v) for k, v in row.items() if k is not None}

            if not any(row.get(c) for c in CSV_REQUIRED) and not any(row.values()):
                continue  # blank line

            raw_date = row.get("date", "")
            span = parse_date(raw_date)
            if span is None or span[0] != span[1]:
                problems.append(f"line {line}: date {raw_date!r} is not a single YYYY-MM-DD")
                continue
            day = span[0]

            home_raw, away_raw = row.get("home", ""), row.get("away", "")
            if not home_raw or not away_raw:
                problems.append(f"line {line}: home and away are both required")
                continue

            feed = row.get("feed", "")
            if not feed:
                problems.append(f"line {line}: feed is required")
                continue
            feed = re.sub(r"[^a-z0-9-]+", "-", feed.lower()).strip("-")

            source = row.get("dateSource", "")
            if source not in KNOWN_SOURCES:
                problems.append(
                    f"line {line}: dateSource {source!r} must be confirmed, inferred or disputed")
                continue
            if source == "disputed":
                problems.append(f"line {line}: dateSource is disputed - not emitted")
                continue

            home_club = clubs_by_id.get(home_raw)
            away_club = clubs_by_id.get(away_raw)
            home_name = home_club["name"] if home_club else home_raw
            away_name = away_club["name"] if away_club else away_raw

            venue = row.get("venue", "")
            venue_note = ""
            if not venue:
                ground = (home_club or {}).get("ground")
                if not ground or ground.lower() == "unknown":
                    problems.append(
                        f"line {line}: venue is blank and no usable ground is on file for "
                        f"{home_raw!r} - fill in the venue column, or add the ground to "
                        f"football-rules.json")
                    continue
                venue = ground
            else:
                venue_note = " (moved)"

            tzname = row.get("tz", "")
            tz_guessed = False
            if not tzname:
                country = (home_club or {}).get("country")
                tzname = COUNTRY_TZ.get(country or "", "")
                if not tzname:
                    tzname, tz_guessed = FALLBACK_TZ, True

            raw_time = row.get("time", "")
            start_utc = end_utc = None
            when = "all-day"
            if raw_time:
                if not re.match(r"^\d{1,2}:\d{2}$", raw_time):
                    problems.append(f"line {line}: time {raw_time!r} is not HH:MM")
                    continue
                hh, mm = (int(p) for p in raw_time.split(":"))
                if hh > 23 or mm > 59:
                    problems.append(f"line {line}: time {raw_time!r} is not a real time")
                    continue
                if ZoneInfo is None:
                    problems.append(f"line {line}: no timezone database available")
                    continue
                local = datetime(day.year, day.month, day.day, hh, mm,
                                 tzinfo=ZoneInfo(tzname))
                start_utc = local.astimezone(timezone.utc)
                end_utc = start_utc + timedelta(hours=FIXTURE_MATCH_HOURS)
                when = f"{raw_time} {tzname}" + (" [assumed]" if tz_guessed else "")

            lead_raw = row.get("leadTimeDays", "")
            lead = None
            if lead_raw:
                if not lead_raw.isdigit():
                    problems.append(f"line {line}: leadTimeDays {lead_raw!r} is not a whole number")
                    continue
                lead = int(lead_raw)

            comp = row.get("competition", "")
            title = f"{home_name} v {away_name}"
            if comp:
                title += f" ({comp})"

            if day < today:
                problems.append(f"line {line}: {raw_date} has passed - not emitted")
                continue

            detail = [f"Venue: {venue}{venue_note}"]
            if comp:
                detail.append(f"Competition: {comp}")
            if row.get("notes"):
                detail.append(f"Notes: {row['notes']}")
            if tz_guessed and raw_time:
                detail.append(
                    f"Kick-off timezone was assumed to be {tzname} because "
                    f"{home_raw!r} is not a club id in football-rules.json.")

            uid_seed = f"{raw_date}|{home_raw.lower()}|{away_raw.lower()}"
            uid = hashlib.sha256(uid_seed.encode("utf-8")).hexdigest()[:12]

            events.setdefault(feed, []).append(build_event(
                uid=f"fx-{uid}@{UID_DOMAIN}",
                title=title,
                start=day, end=day, source=source,
                lead_days=lead,
                action=None,
                detail_lines=detail,
                start_utc=start_utc, end_utc=end_utc,
                location=venue,
            ))

            alarm_txt = f"alarm {lead}d before" if lead is not None else "no alarm"
            readback.append(
                f"line {line}: {raw_date}  {when}  |  {title}  |  {venue}{venue_note}"
                f"  |  feed={feed}  |  {alarm_txt}  |  {source}")

    return events, readback, problems


# ------------------------------------------------------------------ main

def main():
    if not os.path.exists(DATA_FILE):
        sys.exit(f"cannot find {DATA_FILE}")
    with open(DATA_FILE, encoding="utf-8") as fh:
        data = json.load(fh)

    today = date.today()
    feeds = {k: [] for k in FEEDS}
    bucket = []
    skipped = []

    clubs_by_id = {c["id"]: c for c in data.get("clubs", []) if c.get("id")}
    club_names = {cid: c.get("name", cid) for cid, c in clubs_by_id.items()}

    fixture_feeds, fixture_readback, fixture_problems = read_manual_fixtures(
        clubs_by_id, today)

    # ---- ticketEvents
    for ev in data.get("ticketEvents", []):
        eid = ev.get("id", "<no id>")
        title = ev.get("title", eid)

        feed = ev.get("feed")
        if feed is None:
            skipped.append((eid, title, "no feed field set"))
            continue
        if feed not in feeds:
            skipped.append((eid, title, f"unknown feed {feed!r}"))
            continue

        start, end, outcome = resolve_ticket_event(ev, today)
        if start is None:
            skipped.append((eid, title, outcome))
            continue

        detail = []
        club = club_names.get(ev.get("club"))
        if club:
            detail.append(f"Club: {club}")
        for key, label in (("derivation", "Derivation"), ("rule", "Rule"),
                           ("warning", "Warning"), ("dependsOn", "Depends on"),
                           ("status", "Status"), ("priority", "Priority")):
            if ev.get(key):
                detail.append(f"{label}: {ev[key]}")

        feeds[feed].append(build_event(
            uid=f"{eid}@{UID_DOMAIN}",
            title=title,
            start=start, end=end, source=outcome,
            lead_days=ev.get("leadTimeDays"),
            action=ev.get("action"),
            detail_lines=detail,
        ))

    # ---- bucketList
    for item in data.get("bucketList", []):
        iid = item.get("id", "<no id>")
        title = item.get("title", iid)
        occurrences, reasons = resolve_bucket_dates(item, today)
        if not occurrences:
            for r in reasons:
                skipped.append((iid, title, r))
            continue
        for r in reasons:
            skipped.append((iid, title, r))

        for suffix, start, end, source, note in occurrences:
            detail = []
            if item.get("venue"):
                detail.append(f"Venue: {item['venue']}")
            if item.get("kickoff"):
                detail.append(f"Kick-off: {item['kickoff']}")
            if item.get("distanceKm"):
                detail.append(f"Distance: ~{item['distanceKm']} km straight line")
            if item.get("status"):
                detail.append(f"Status: {item['status']}")
            if note:
                detail.append(f"Note: {note}")
            for key, label in (("ticketRoute", "Ticket route"),
                               ("ticketNote", "Ticket note"),
                               ("practical", "Practical"),
                               ("conflict", "Clashes with"),
                               ("fallback", "Fallback"),
                               ("warning", "Warning")):
                if item.get(key):
                    detail.append(f"{label}: {item[key]}")

            bucket.append(build_event(
                uid=f"{iid}{suffix}@{UID_DOMAIN}",
                title=title,
                start=start, end=end, source=source,
                lead_days=item.get("leadTimeDays"),
                action=item.get("why"),
                detail_lines=detail,
            ))

    # ---- write
    os.makedirs(OUT_DIR, exist_ok=True)
    stamps = {}
    if os.path.exists(STAMP_FILE):
        with open(STAMP_FILE, encoding="utf-8") as fh:
            stamps = json.load(fh)

    written = []
    for feed, name in FEEDS.items():
        path = os.path.join(OUT_DIR, f"{feed}.ics")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(render_calendar(name, feeds[feed], stamps))
        written.append((path, len(feeds[feed])))

    path = os.path.join(OUT_DIR, f"{BUCKET_FEED}.ics")
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(render_calendar(BUCKET_NAME, bucket, stamps))
    written.append((path, len(bucket)))

    for feed in sorted(fixture_feeds):
        label = FEEDS.get(feed, feed.replace("-", " ").title())
        path = os.path.join(OUT_DIR, f"{FIXTURE_PREFIX}{feed}.ics")
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(render_calendar(f"Fixtures - {label}", fixture_feeds[feed], stamps))
        written.append((path, len(fixture_feeds[feed])))

    with open(STAMP_FILE, "w", encoding="utf-8") as fh:
        json.dump(stamps, fh, indent=1, sort_keys=True)
        fh.write("\n")

    lines = [
        "# Entries that produced no calendar event",
        "",
        f"Generated {today.isoformat()} by tools/build_calendars.py.",
        "Nothing below is an error in the code. Each line is either a",
        "deliberate exclusion or a field you still need to fill in.",
        "",
    ]
    if skipped:
        for eid, title, reason in sorted(skipped):
            lines.append(f"- **{eid}** - {title}")
            lines.append(f"  - {reason}")
    else:
        lines.append("Nothing skipped.")
    lines.append("")
    with open(os.path.join(OUT_DIR, "skipped.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    total = sum(n for _, n in written)
    for path, n in written:
        print(f"{path:40s} {n} event(s)")
    print(f"{'calendars/skipped.md':40s} {len(skipped)} entr(ies) skipped")
    print(f"total emitted: {total}")

    print()
    print("=" * 68)
    print("HAND-ENTERED FIXTURES - read this back and check it says what")
    print("you meant. Every row below is what the file was understood to say.")
    print("=" * 68)
    if fixture_readback:
        for line in fixture_readback:
            print("  " + line)
    else:
        print("  (no rows read)")
    if fixture_problems:
        print()
        print("  ROWS NOT USED:")
        for p in fixture_problems:
            print("  ! " + p)
    print("=" * 68)


if __name__ == "__main__":
    main()
