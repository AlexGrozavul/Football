#!/usr/bin/env python3
"""Offline check of the "why" status of the bucket-list entries.

Reads data/football-rules.json (bucketList) and nothing else. No network,
nothing is written. Exits 1 on an error, 0 otherwise.

Added 15 Nov 2026 (fact check, phase 3c). `whyStatus` has two values:

  unverified  the text was written from memory and nobody has read it
              against a page; the List shows "Not yet verified".
  checked     a fact-check session found every factual claim of the
              entry's texts supported by a page (or corrected it from a
              page), or found no factual claim at all. Opinions are never
              checked.

Rules for `checked` (each break is an error):
  - `whyCheckedOn` is required: YYYY-MM-DD, a real date, not in the future.
    It is the day the session read the page, never the day it wrote the
    status.
  - at least one `whySources` entry (an http(s) URL) is required, UNLESS
    `whyBasis` is "no factual claim"; an entry with that basis carries no
    `whySources` (there is no claim for a page to support).
Also errors: a `whyStatus` other than the two values; `whyCheckedOn` or
`whyBasis` on an entry that is not `checked`; a `whyBasis` other than
"no factual claim"; a `whySources` that is not a list of http(s) URLs.
A warning only: a `checked` entry that carries an added note
(`whyAssistant`) - the status then covers that note too, so it must have
been checked as well. `unverified` entries are not otherwise checked.

Usage: python3 tools/check_bucket_why.py [path-to-football-rules.json]
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

STATUSES = ("unverified", "checked")
NO_CLAIM = "no factual claim"


def parse_day(s):
    if not isinstance(s, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def check(bucket, today):
    """Return (errors, warnings, counts) for a bucketList."""
    errors, warnings = [], []
    counts = {"checked-sources": 0, "checked-no-claim": 0, "unverified": 0, "none": 0}
    for i, b in enumerate(bucket):
        bid = b.get("id") or f"entry {i}"
        st = b.get("whyStatus")
        on, basis, srcs = b.get("whyCheckedOn"), b.get("whyBasis"), b.get("whySources")
        err = lambda why: errors.append(f"{bid}: {why}")
        if srcs is not None and (not isinstance(srcs, list) or
                                 not all(isinstance(u, str) and re.match(r"^https?://\S+$", u) for u in srcs)):
            err("whySources must be a list of http(s) URLs")
        if st is None:
            counts["none"] += 1
        elif st not in STATUSES:
            err(f"whyStatus {st!r} is not one of {', '.join(STATUSES)}")
        if st != "checked":
            if on is not None:
                err("whyCheckedOn is set but whyStatus is not 'checked'")
            if basis is not None:
                err("whyBasis is set but whyStatus is not 'checked'")
            if st == "unverified":
                counts["unverified"] += 1
            continue
        d = parse_day(on)
        if on is None:
            err("whyStatus 'checked' needs whyCheckedOn (YYYY-MM-DD)")
        elif d is None:
            err(f"whyCheckedOn {on!r} is not a real date written YYYY-MM-DD")
        elif d > today:
            err(f"whyCheckedOn {on} is in the future (today is {today.isoformat()})")
        if basis is not None and basis != NO_CLAIM:
            err(f"whyBasis {basis!r} is not {NO_CLAIM!r}")
        has_src = isinstance(srcs, list) and len(srcs) > 0
        if basis == NO_CLAIM:
            if has_src:
                err(f"whyBasis {NO_CLAIM!r} with whySources: a text with no claim has no source to cite")
            else:
                counts["checked-no-claim"] += 1
        elif not has_src:
            err(f"whyStatus 'checked' needs at least one whySources entry, or whyBasis {NO_CLAIM!r}")
        else:
            counts["checked-sources"] += 1
        if b.get("whyAssistant"):
            warnings.append(f"{bid}: 'checked' while it carries an added note (whyAssistant); "
                            "the status covers that note too")
    return errors, warnings, counts


def main(argv):
    path = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parent.parent / "data" / "football-rules.json"
    bucket = json.loads(path.read_text(encoding="utf-8")).get("bucketList", [])
    errors, warnings, c = check(bucket, date.today())
    print(f"{path.name}: {len(bucket)} bucketList entries - checked with sources {c['checked-sources']}, "
          f"checked with no factual claim {c['checked-no-claim']}, unverified {c['unverified']}, "
          f"no whyStatus {c['none']}")
    for w in warnings:
        print("WARNING " + w)
    for e in errors:
        print("ERROR " + e)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
