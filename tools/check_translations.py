#!/usr/bin/env python3
"""
Read-back and checks for the Romanian translations of data-file text
(data/ro/<source>.json). CLAUDE.md, "Romanian translations of data texts".

A translation is DERIVED data: the English data file is the original and is
never touched. An entry of data/ro/<source>.json is keyed by
"<rowKey>#<field>" and holds
    en      the fingerprint of the English text it was made from
    ro      the Romanian
    status  "machine-unchecked" (written by an assistant, not read by you)
The page shows the Romanian only while the fingerprint still matches the
English in the data file; edit the English and the entry is STALE, and the
page shows the English again until somebody retranslates it.

Fingerprint: 32-bit FNV-1a over the UTF-8 bytes of the text with leading and
trailing " \\t\\n\\r\\f\\v\\u00a0" removed, as 8 lower-case hex digits. index.html
has the same function; tools/translation-fingerprints.json is the fixture
both are tested against (this file by --self-test, the page by test_me.js).

Exit 1 (a problem):
  - a file that is not JSON, not an object, or has no registered source;
  - a malformed entry (not an object, wrong keys, `en` not 8 hex digits,
    `ro` not a string, `status` not a known value);
  - a duplicate key (JSON keeps the last one silently, so it is caught while
    parsing);
  - an empty `ro`;
  - an unknown row key: no such row in the data file, or a field that is not
    one of the translated fields of that source;
  - a `ro` that lacks a number group, an ISO date or a URL/domain that the
    English has. Digit groups are compared with thousands and decimal
    separators removed ("135,000" and "135.000" are the same group).
Warnings (exit 0): a stale entry (fingerprint no longer matches), a
translation that does not use a term of data/ro-glossary.csv that its English
has, and the coverage line per source.

    python3 tools/check_translations.py [--root DIR] [--registry] [--self-test]
"""
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATUSES = {"machine-unchecked", "checked"}
TRIM = " \t\n\r\f\v "


def fingerprint(text):
    h = 0x811C9DC5
    for b in text.strip(TRIM).encode("utf-8"):
        h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF
    return format(h, "08x")


# ---------------------------------------------------------------- registry
# What the page translates, per source: the visible prose of a data file.
# Names, source titles, URLs, original-language quotes, ids and codes are
# KEPT and are not here. Fields the page does not draw at all are not here
# either (club-ticket-prices `note`, every `note` of the ticket files, ...).

# football-rules.json: the normalised path of a string leaf (list indices
# written as []), per section. A prefix ending in "." covers everything under it.
BUCKET_PATHS = {
    "why", "whyAssistant", "warning", "blockedReason", "unblockCondition",
    "deferReason", "alternative", "fallback", "conflict", "note", "practical",
    "related", "relatedNear", "target", "ticketNote", "ticketRoutes.awayEnd",
    "trigger.action", "trigger.playedMonth", "trigger.playedMonthStatus",
    "trigger.playedPeriod", "trigger.drawMonth", "trigger.anchor",
    "nextFixture.derivation", "nextFixture.missed", "fixtures[].saleRoute",
}
CLUB_PATHS = {
    "ageRules.accountHolder", "ageRules.idAtGate", "ageRules.note",
    "ageRules.standingRestriction", "bonus", "caveat", "context", "demandNote",
    "memberStatus", "openQuestion", "realism", "role", "stadiumNote", "travel",
    "travelNote", "warning", "procedure.",
}


def norm_path(p):
    return re.sub(r"\[\d+\]", "[]", p)


def path_ok(path, allowed):
    n = norm_path(path)
    return any(n == a or (a.endswith(".") and n.startswith(a)) for a in allowed)


def leaves(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from leaves(v, p + ("." if p else "") + k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from leaves(v, f"{p}[{i}]")
    else:
        yield p, o


def rules_json(root):
    d = json.loads((root / "data/football-rules.json").read_text(encoding="utf-8"))
    out = {}
    for section, allowed in (("bucketList", BUCKET_PATHS), ("clubs", CLUB_PATHS)):
        for item in d.get(section, []):
            for p, v in leaves(item):
                if isinstance(v, str) and v.strip() and path_ok(p, allowed):
                    out[(f"{section}:{item['id']}", p)] = v
    return out


def csv_source(file, key_cols, fields):
    def read(root):
        path = root / "data" / file
        out = {}
        for r in csv.DictReader(path.open(encoding="utf-8", newline="")):
            key = "|".join((r.get(c) or "") for c in key_cols)
            for f in fields:
                v = r.get(f) or ""
                if v.strip():
                    out[(key, f)] = v
        return out
    return read


SOURCES = {
    "football-rules": rules_json,
    "derbies": csv_source("derbies.csv", ["clubA", "clubB"], ["note"]),
    "club-ticket-windows": csv_source("club-ticket-windows.csv", ["clubQid", "team", "window"],
                                      ["label", "opensEstimate", "pastCycle"]),
    "club-ticket-phases": csv_source("club-ticket-phases.csv", ["clubQid", "team", "window", "phase"],
                                     ["buyers", "opensRelative", "pastCycle"]),
    "club-ticket-rules": csv_source("club-ticket-rules.csv",
                                    ["clubQid", "team", "scope", "opponentQid", "topic", "season"], ["rule"]),
    "club-ticket-demand": csv_source("club-ticket-demand.csv",
                                     ["clubQid", "team", "scope", "opponentQid", "season"], ["timing"]),
    "country-ticket-rules": csv_source("country-ticket-rules.csv",
                                       ["country", "topic", "appliesTo", "condition"], ["rule"]),
    "event-ticket-rules": csv_source("event-ticket-rules.csv",
                                     ["bucketId", "scope", "opponentQid", "topic", "season"], ["rule"]),
    "competition-info": csv_source("competition-info.csv", ["competitionId", "topic", "sourceId"],
                                   ["text", "basis"]),
}

# ------------------------------------------------------------ what must survive
NUM_RE = re.compile(r"\d[\d.,]*\d|\d")
URL_RE = re.compile(r"https?://[^\s\"'<>)\]]+", re.I)
DOMAIN_RE = re.compile(
    r"\b(?:[a-z0-9-]+\.)+(?:com|org|net|de|ro|it|fr|uk|eu|info|at|ch|es|nl|be|gr|rs|pt|tv|io)\b(?:/[^\s\"'<>)\]]*)?", re.I)
ISO_RE = re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b")


def number_groups(s):
    return {re.sub(r"[.,]", "", m) for m in NUM_RE.findall(s)}


def urls_of(s):
    found = {u.rstrip(".,;:").lower() for u in URL_RE.findall(s)}
    for m in DOMAIN_RE.findall(s):
        found.add(m.rstrip(".,;:").lower())
    return found


def missing_from(en, ro):
    """What the English has and the Romanian lacks."""
    out = []
    ro_low = ro.lower()
    ro_nums = number_groups(ro)
    for g in sorted(number_groups(en)):
        if g not in ro_nums:
            out.append(f"number {g}")
    for d in sorted(set(ISO_RE.findall(en))):
        if d not in ro:
            out.append(f"date {d}")
    for u in sorted(urls_of(en)):
        if u not in ro_low:
            out.append(f"URL {u}")
    return out


def fold(s):
    """Lower case, diacritics removed (so 'găzduit' contains 'gazd')."""
    s = s.lower().replace("ș", "s").replace("ş", "s").replace("ț", "t").replace("ţ", "t")
    return unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()


def term_in(term, text):
    """Every word of a glossary term (its stem, so 'finală' also matches 'finalei')."""
    t = fold(text)
    for w in fold(term).split():
        if len(w) < 3:
            continue
        stem = w[:-1] if len(w) > 3 and w[-1] in "aeiu" else w
        if stem not in t:
            return False
    return True


def glossary(root):
    p = root / "data/ro-glossary.csv"
    if not p.exists():
        return []
    return [(r["english"].strip().lower(), r["romanian"].strip().lower())
            for r in csv.DictReader(p.open(encoding="utf-8", newline="")) if r.get("english") and r.get("romanian")]


def unique_pairs(pairs):
    seen, out = set(), []
    for k, v in pairs:
        if k in seen:
            raise ValueError(f"duplicate key {k!r}")
        seen.add(k)
        out.append((k, v))
    return dict(out)


def load_ro(path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def main(argv):
    root = ROOT
    if "--root" in argv:
        root = Path(argv[argv.index("--root") + 1]).resolve()
    if "--self-test" in argv:
        return self_test()
    if "--registry" in argv:
        reg = {s: [{"row": r, "field": f, "chars": len(v)} for (r, f), v in sorted(fn(root).items())]
               for s, fn in SOURCES.items()}
        json.dump(reg, sys.stdout, ensure_ascii=False)
        print()
        return 0

    problems, warnings = [], []
    gloss = glossary(root)
    print("Romanian translations of data texts - read back\n")
    rodir = root / "data/ro"
    files = sorted(rodir.glob("*.json")) if rodir.exists() else []
    for f in files:
        if f.stem not in SOURCES:
            problems.append(f"{f.relative_to(root)}: no registered source called '{f.stem}'")
    fp_fixture_ok = fixture_ok()
    if not fp_fixture_ok:
        problems.append("tools/translation-fingerprints.json: the fingerprint function does not reproduce the fixture")

    for name, reader in SOURCES.items():
        english = reader(root)
        path = rodir / f"{name}.json"
        total, chars = len(english), sum(len(v) for v in english.values())
        done = done_chars = stale = 0
        if not path.exists():
            problems.append(f"data/ro/{name}.json is missing")
            print(f"  {name:22s} no file; {total} strings, {chars} characters")
            continue
        try:
            entries = load_ro(path)
        except ValueError as e:
            problems.append(f"{path.relative_to(root)}: {e}")
            continue
        if not isinstance(entries, dict):
            problems.append(f"{path.relative_to(root)}: the top level is not an object")
            continue
        for key, e in entries.items():
            where = f"data/ro/{name}.json '{key}'"
            if "#" not in key:
                problems.append(f"{where}: key is not <rowKey>#<field>")
                continue
            if not isinstance(e, dict) or set(e) != {"en", "ro", "status"}:
                problems.append(f"{where}: malformed entry (needs exactly en, ro, status)")
                continue
            if not (isinstance(e["en"], str) and re.fullmatch(r"[0-9a-f]{8}", e["en"])):
                problems.append(f"{where}: 'en' is not an 8-digit hex fingerprint")
                continue
            if not isinstance(e["ro"], str):
                problems.append(f"{where}: 'ro' is not a string")
                continue
            if e["status"] not in STATUSES:
                problems.append(f"{where}: unknown status {e['status']!r}")
                continue
            if not e["ro"].strip():
                problems.append(f"{where}: empty 'ro'")
                continue
            row, field = key.rsplit("#", 1)
            # the data file keeps list indices out of the registry; compare as written
            en = english.get((row, field))
            if en is None:
                problems.append(f"{where}: unknown row key (no such row/field among the translated fields of {name})")
                continue
            if fingerprint(en) != e["en"]:
                stale += 1
                warnings.append(f"{where}: STALE - the English changed since this was translated")
                continue
            done += 1
            done_chars += len(en)
            for lack in missing_from(en, e["ro"]):
                problems.append(f"{where}: the Romanian lacks {lack}")
            for g_en, g_ro in gloss:
                if re.search(r"\b" + re.escape(g_en) + r"\b", en.lower()) and not term_in(g_ro, e["ro"]):
                    warnings.append(f"{where}: English has '{g_en}', the Romanian does not use '{g_ro}' (glossary)")
        print(f"  {name:22s} {done:4d} of {total:4d} strings translated "
              f"({100 * done / total if total else 0:5.1f}%), {done_chars} of {chars} characters"
              + (f", {stale} stale" if stale else ""))
    print()
    for w in warnings:
        print("WARNING:", w)
    for p in problems:
        print("PROBLEM:", p)
    print(f"\n{len(problems)} problem(s), {len(warnings)} warning(s).")
    return 1 if problems else 0


def fixture_ok():
    p = HERE / "translation-fingerprints.json"
    return all(fingerprint(c["text"]) == c["fp"] for c in json.loads(p.read_text(encoding="utf-8")))


def self_test():
    ok = fixture_ok()
    print("fingerprint fixture:", "ok" if ok else "MISMATCH")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
