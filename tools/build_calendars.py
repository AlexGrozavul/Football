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

import hashlib
import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone

# ---------------------------------------------------------------- config

DATA_FILE = "data/football-rules.json"
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

def build_event(uid, title, start, end, source, lead_days, action, detail_lines):
    """Assemble the dict an event is rendered from. All-day throughout."""
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
    if lead_days is None:
        lead_days = 0
        alarm += " (No leadTimeDays in the JSON - alarm set to the day itself.)"

    return {
        "uid": uid,
        "summary": display,
        "start": start,
        "end": end + timedelta(days=1),  # DTEND is exclusive for all-day
        "description": "\n".join(b for b in body if b is not None),
        "lead_days": int(lead_days),
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
        f"DTSTART;VALUE=DATE:{ymd(ev['start'])}",
        f"DTEND;VALUE=DATE:{ymd(ev['end'])}",
        f"SUMMARY:{esc(ev['summary'])}",
        f"DESCRIPTION:{esc(ev['description'])}",
        "TRANSP:TRANSPARENT",
        "BEGIN:VALARM",
        "ACTION:DISPLAY",
        f"TRIGGER;RELATED=START:-P{ev['lead_days']}D",
        f"DESCRIPTION:{esc(ev['alarm'] + ' ' + ev['summary'])}",
        "END:VALARM",
        "END:VEVENT",
    ]
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

    club_names = {c["id"]: c.get("name", c["id"]) for c in data.get("clubs", [])}

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


if __name__ == "__main__":
    main()
