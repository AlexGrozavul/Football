#!/usr/bin/env python3
"""Fixture test of the aging-document warning in tools/check_tickets.py.

Added 14 Nov 2026 (ticket audit, phase 2b). A row tagged `confirmed`
whose newest dated document (a "Stand" or "valid from" date in its
source record or note) is more than 12 months old is warned about; one
11 months old is not. Runs on fixtures only and reads no data file.
Exits 1 on a failure.
"""
import datetime
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location(
    "check_tickets", os.path.join(HERE, "check_tickets.py"))
ct = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ct)

TODAY = datetime.date(2026, 11, 14)
SOURCES = {
    "S11": {"sourceId": "S11", "published": "Stand: 14.12.2025"},   # 11 months
    "S13": {"sourceId": "S13", "published": "Stand 14.10.2025"},    # 13 months
    "MON": {"sourceId": "MON", "published": "Stand: Dezember 2025"},  # month level
    "UND": {"sourceId": "UND", "published": "current (read 7 Oct 2026)"},
    "NEW": {"sourceId": "NEW", "published": "18.10.2026; read 6 Nov 2026"},
    "OLDREAD": {"sourceId": "OLDREAD", "published": "undated, read 1 Jan 2024"},
    "KOE": {"sourceId": "KOE",
            "published": '"Die Stadionordnung gilt ab dem 19.11.2025", read'},
}


def row(line, refs, confidence="confirmed", note=""):
    return {"_line": line, "club": f"Club {line}", "confidence": confidence,
            "sourceRefs": refs, "note": note}


ROWS = {ct.RULES_FILE: [
    row(2, "S11"),                         # 11 months old: no warning
    row(3, "S13"),                         # 13 months old: warning
    row(4, "S13", confidence="unverified"),  # not confirmed: no warning
    row(5, "S13;NEW"),                     # a newer dated notice: no warning
    row(6, "UND"),                         # no document date: no warning
    row(7, "OLDREAD"),                     # a read date never counts
    row(8, "MON"),                         # month level: counts as 31 Dec 2025
    row(9, "UND", note="terms (Stand 1 Feb 2023) as quoted"),  # note: warning
    row(10, "KOE"),                        # Köln shape: gilt ab dem 19.11.2025
]}

failures = []


def expect(name, today, lines):
    got = sorted(line for _p, line, *_ in
                 ct.aging_documents(ROWS, SOURCES, today))
    ok = got == sorted(lines)
    print(("ok   " if ok else "FAIL ") + f"{name}: warned {got}, "
          f"expected {sorted(lines)}")
    if not ok:
        failures.append(name)


expect("11 months no warning, 13 months warning (14 Nov 2026)",
       TODAY, [3, 9])
expect("Köln shape still inside 12 months on 19 Nov 2026",
       datetime.date(2026, 11, 19), [3, 9])
expect("Köln shape warns from 20 Nov 2026",
       datetime.date(2026, 11, 20), [3, 9, 10])
expect("month-level Stand does not warn early (31 Dec 2026)",
       datetime.date(2026, 12, 31), [2, 3, 9, 10])
expect("month-level Stand warns once past (1 Jan 2027)",
       datetime.date(2027, 1, 1), [2, 3, 8, 9, 10])

dates = ct.document_dates("Stand: Juni 2025; read 7 Oct 2026")
if dates != [(datetime.date(2025, 6, 30), "Stand: Juni 2025")]:
    failures.append("document_dates")
    print(f"FAIL document_dates: {dates}")
else:
    print("ok   document_dates reads 'Stand: Juni 2025' as 30 Jun 2025 "
          "and ignores the read date")

if ct.twelve_months_before(datetime.date(2028, 2, 29)) != \
        datetime.date(2027, 2, 28):
    failures.append("leap day")
    print("FAIL twelve_months_before on 29 Feb")
else:
    print("ok   twelve_months_before handles 29 Feb")

print()
print(f"{len(failures)} failure(s)" if failures else "All aging checks pass.")
sys.exit(1 if failures else 0)
