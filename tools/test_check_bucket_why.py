#!/usr/bin/env python3
"""Fixture test of tools/check_bucket_why.py.

Added 15 Nov 2026 (fact check, phase 3c). Runs on fixtures only and reads
no data file. Exits 1 on a failure.
"""
import datetime
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("check_bucket_why", os.path.join(HERE, "check_bucket_why.py"))
cb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cb)

TODAY = datetime.date(2026, 11, 15)
SRC = ["https://en.wikipedia.org/wiki/Ruhr"]
CASES = [
    # (name, entry, expected error count, expected warning count)
    ("checked with a source and a past date passes",
     {"id": "a", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whySources": SRC}, 0, 0),
    ("checked with no factual claim and no source passes",
     {"id": "b", "whyStatus": "checked", "whyCheckedOn": "2026-11-14", "whyBasis": "no factual claim"}, 0, 0),
    ("unverified as it is passes, with or without sources",
     {"id": "c", "whyStatus": "unverified", "whySources": SRC}, 0, 0),
    ("no whyStatus at all passes (older hand-written entries)", {"id": "d"}, 0, 0),
    ("checked without a date is rejected",
     {"id": "e", "whyStatus": "checked", "whySources": SRC}, 1, 0),
    ("checked without a source and without the no-claim basis is rejected",
     {"id": "f", "whyStatus": "checked", "whyCheckedOn": "2026-11-15"}, 1, 0),
    ("checked with an empty source list is rejected",
     {"id": "f2", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whySources": []}, 1, 0),
    ("checked with a future date is rejected",
     {"id": "g", "whyStatus": "checked", "whyCheckedOn": "2026-11-16", "whySources": SRC}, 1, 0),
    ("checked with a malformed date is rejected",
     {"id": "h", "whyStatus": "checked", "whyCheckedOn": "15.11.2026", "whySources": SRC}, 1, 0),
    ("checked with an impossible date is rejected",
     {"id": "h2", "whyStatus": "checked", "whyCheckedOn": "2026-02-30", "whySources": SRC}, 1, 0),
    ("another basis wording does not stand in for a source",
     {"id": "i", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whyBasis": "opinion"}, 2, 0),
    ("the no-claim basis together with sources is rejected",
     {"id": "j", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whyBasis": "no factual claim", "whySources": SRC}, 1, 0),
    ("an unknown status is rejected", {"id": "k", "whyStatus": "verified"}, 1, 0),
    ("whyCheckedOn on an unverified entry is rejected",
     {"id": "l", "whyStatus": "unverified", "whyCheckedOn": "2026-11-15"}, 1, 0),
    ("a source that is not a URL is rejected",
     {"id": "m", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whySources": ["Wikipedia"]}, 1, 0),
    ("checked with an added note passes with a warning",
     {"id": "n", "whyStatus": "checked", "whyCheckedOn": "2026-11-15", "whySources": SRC, "whyAssistant": "x"}, 0, 1),
]

failed = 0
for name, entry, want_e, want_w in CASES:
    e, w, _ = cb.check([entry], TODAY)
    ok = len(e) == want_e and len(w) == want_w
    failed += not ok
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f" :: errors {e} warnings {w}"))
_, _, c = cb.check([x[1] for x in CASES[:4]], TODAY)
ok = c == {"checked-sources": 1, "checked-no-claim": 1, "unverified": 1, "none": 1}
failed += not ok
print(("PASS " if ok else "FAIL ") + "counts: one of each kind" + ("" if ok else f" :: {c}"))
print(f"\n{len(CASES) + 1 - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)
