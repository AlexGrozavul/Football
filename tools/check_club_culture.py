#!/usr/bin/env python3
"""
check_club_culture.py -- read-back and checks for data/club-rivalries.csv,
data/club-friendships.csv and data/club-culture-sources.csv.

All three are hand-written and nothing writes to them. This tool reads them,
prints every accepted row as understood and exits 1 on a problem.

club-rivalries.csv: clubQ, rivalQ (blank when the rival is not on the map),
rivalName, class (main, local, other), sourceId, checkedOn. The class comes
only from the wording of the source. There is no row limit and no target.
club-friendships.csv: clubQ, friendQ (blank when the friend is not on the map),
friendName, scope (fan-groups, clubs, unclear), status (active, ended, unclear),
groupsText (the fan groups the source names, blank if it names none), sourceId,
checkedOn. Scope and status come only from the wording of the source; nothing is
inferred from rivalries or shared enemies.

EXITS 1 on: a clubQ or rivalQ on no data/clubs/*.json, a sourceId
not in club-culture-sources.csv, a class or source kind
outside its list, a duplicate row, a missing rivalName,
a day-level date in the future in a text cell, a row with more values than
the header has columns; in club-friendships.csv also an unknown friendQ, a scope
or status outside its list, a club listed as its own friend, a duplicate row.
WARNS (exit stays 0) on a missing or malformed checkedOn, a club pair that is in
both the friendships file and the rivalries file (they should not contradict), a club with more
than 12 rows in either file (so they can be reviewed for padding), and a
source no row uses.

Usage:  python3 tools/check_club_culture.py
"""
import csv, glob, json, os, re, sys
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(ROOT, 'data')
CLASSES = ('main', 'local', 'other')
SCOPES = ('fan-groups', 'clubs', 'unclear')
STATUSES = ('active', 'ended', 'unclear')
ORDER_SHOWN = ('active', 'unclear', 'ended')   # the order the club sheet draws them
KINDS = ('wikipedia', 'club', 'press', 'fan-media')
REVIEW_OVER = 12
MONTHS = 'january|february|march|april|may|june|july|august|september|october|november|december'
ISO_DAY = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
DMY = re.compile(r'\b(\d{1,2})\.?\s+(' + MONTHS + r')\s+(\d{4})\b', re.I)
MDY = re.compile(r'\b(' + MONTHS + r')\s+(\d{1,2}),?\s+(\d{4})\b', re.I)

problems, warnings = [], []
today = date.today()


def read(name, required):
    path = os.path.join(D, name)
    if not os.path.exists(path):
        problems.append(f'{name} does not exist')
        return []
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        rd = csv.reader(f)
        header = next(rd, [])
        missing = [c for c in required if c not in header]
        if missing:
            problems.append(f'{name}: header lacks {", ".join(missing)}')
            return []
        for row in rd:
            if not any(c.strip() for c in row):
                continue
            if len(row) > len(header):
                problems.append(f'{name} line {rd.line_num}: {len(row)} values for {len(header)} columns (an unquoted comma?)')
                continue
            row += [''] * (len(header) - len(row))
            out.append((rd.line_num, {h: v.strip() for h, v in zip(header, row)}))
    return out


def iso(s):
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def future_days(text):
    """Day-level dates in a text cell that lie after today."""
    found = []
    for y, m, d in ISO_DAY.findall(text):
        try:
            found.append(date(int(y), int(m), int(d)))
        except ValueError:
            pass
    names = {n: i + 1 for i, n in enumerate(MONTHS.split('|'))}
    for d, m, y in DMY.findall(text):
        try: found.append(date(int(y), names[m.lower()], int(d)))
        except ValueError: pass
    for m, d, y in MDY.findall(text):
        try: found.append(date(int(y), names[m.lower()], int(d)))
        except ValueError: pass
    return [x for x in found if x > today]


clubs = {}
for p in glob.glob(os.path.join(D, 'clubs', '??.json')):
    for c in json.load(open(p, encoding='utf-8')).get('clubs', []):
        clubs[c['id']] = c.get('name') or c['id']

sources = {}
for line, r in read('club-culture-sources.csv', ['sourceId', 'url', 'title', 'retrievedOn', 'kind']):
    at = f'club-culture-sources.csv line {line}'
    if not r['sourceId'] or not r['url'].startswith('http'):
        problems.append(f'{at}: needs a sourceId and a URL'); continue
    if r['sourceId'] in sources:
        problems.append(f'{at}: sourceId {r["sourceId"]} repeated'); continue
    if r['kind'] not in KINDS:
        problems.append(f'{at}: kind "{r["kind"]}" is not one of {", ".join(KINDS)}')
    if not r['retrievedOn']:
        warnings.append(f'{at}: {r["sourceId"]} has no retrievedOn')
    elif not iso(r['retrievedOn']):
        problems.append(f'{at}: retrievedOn "{r["retrievedOn"]}" is not an ISO date')
    sources[r['sourceId']] = r
used = set()


def common(at, r, ok):
    if r['clubQ'] not in clubs:
        problems.append(f'{at}: clubQ "{r["clubQ"]}" is on no club file'); ok = False
    if r['sourceId'] not in sources:
        problems.append(f'{at}: sourceId "{r["sourceId"]}" is not in club-culture-sources.csv'); ok = False
    else:
        used.add(r['sourceId'])
    if not r['checkedOn']:
        warnings.append(f'{at}: no checkedOn')
    else:
        d = iso(r['checkedOn'])
        if not d: warnings.append(f'{at}: checkedOn "{r["checkedOn"]}" is not an ISO date')
        elif d > today: warnings.append(f'{at}: checkedOn {r["checkedOn"]} is in the future')
    return ok


riv, fri = {}, {}
seen = set()
for line, r in read('club-rivalries.csv', ['clubQ', 'rivalQ', 'rivalName', 'class', 'sourceId', 'checkedOn']):
    at = f'club-rivalries.csv line {line}'
    ok = common(at, r, True)
    if r['rivalQ'] and r['rivalQ'] not in clubs:
        problems.append(f'{at}: rivalQ "{r["rivalQ"]}" is on no club file (leave it blank if the rival is not on the map)'); ok = False
    if r['rivalQ'] and r['rivalQ'] == r['clubQ']:
        problems.append(f'{at}: a club cannot be its own rival'); ok = False
    if not r['rivalName']:
        problems.append(f'{at}: rivalName is empty'); ok = False
    if r['class'] not in CLASSES:
        problems.append(f'{at}: class "{r["class"]}" is not one of {", ".join(CLASSES)}'); ok = False
    for col in ('rivalName',):
        if future_days(r[col]):
            problems.append(f'{at}: {col} holds a future day-level date'); ok = False
    key = ('riv', r['clubQ'], r['rivalQ'] or r['rivalName'].casefold())
    if key in seen:
        problems.append(f'{at}: {clubs.get(r["clubQ"], r["clubQ"])} / {r["rivalName"]} is entered twice'); ok = False
    seen.add(key)
    if ok: riv.setdefault(r['clubQ'], []).append(r)

for line, r in read('club-friendships.csv', ['clubQ', 'friendQ', 'friendName', 'scope', 'status', 'groupsText', 'sourceId', 'checkedOn']):
    at = f'club-friendships.csv line {line}'
    ok = common(at, r, True)
    if r['friendQ'] and r['friendQ'] not in clubs:
        problems.append(f'{at}: friendQ "{r["friendQ"]}" is on no club file (leave it blank if the friend is not on the map)'); ok = False
    if r['friendQ'] and r['friendQ'] == r['clubQ']:
        problems.append(f'{at}: a club cannot be its own friend'); ok = False
    if not r['friendName']:
        problems.append(f'{at}: friendName is empty'); ok = False
    if r['scope'] not in SCOPES:
        problems.append(f'{at}: scope "{r["scope"]}" is not one of {", ".join(SCOPES)}'); ok = False
    if r['status'] not in STATUSES:
        problems.append(f'{at}: status "{r["status"]}" is not one of {", ".join(STATUSES)}'); ok = False
    for col in ('friendName', 'groupsText'):
        if future_days(r[col]):
            problems.append(f'{at}: {col} holds a future day-level date'); ok = False
    key = ('fri', r['clubQ'], r['friendQ'] or r['friendName'].casefold())
    if key in seen:
        problems.append(f'{at}: {clubs.get(r["clubQ"], r["clubQ"])} / {r["friendName"]} is entered twice'); ok = False
    seen.add(key)
    if ok: fri.setdefault(r['clubQ'], []).append(r)

# A friendship and a rivalry for the same two clubs should not both be on file: warn, keep both.
rival_pairs = {}
for q, rs in riv.items():
    for r in rs:
        rival_pairs[(q, r['rivalQ'] or r['rivalName'].casefold())] = r
        if r['rivalQ']:
            rival_pairs[(r['rivalQ'], q)] = r
for q, rs in fri.items():
    for r in rs:
        hit = rival_pairs.get((q, r['friendQ'] or r['friendName'].casefold()))
        if hit:
            warnings.append(f'{clubs[q]} / {r["friendName"]} is in club-friendships.csv ({r["status"]}) and in club-rivalries.csv ({hit["class"]}); the two should not contradict, check both sources')

for label, d in (('club-rivalries.csv', riv), ('club-friendships.csv', fri)):
    for q, rs in d.items():
        if len(rs) > REVIEW_OVER:
            warnings.append(f'{label}: {clubs[q]} ({q}) has {len(rs)} rows; review them for padding')
for sid in sources:
    if sid not in used:
        warnings.append(f'source {sid} is used by no row')

print(f'{len(sources)} sources')
print(f'club-rivalries.csv: {sum(len(v) for v in riv.values())} accepted rows, {len(riv)} clubs')
for q in sorted(riv, key=lambda q: clubs[q]):
    print(f'  {clubs[q]} ({q})')
    for r in sorted(riv[q], key=lambda r: (CLASSES.index(r['class']), r['rivalName'])):
        print(f'    {r["class"]:5}  {r["rivalName"]}  {r["rivalQ"] or "(not on the map)"}  {r["sourceId"]}  checked {r["checkedOn"] or "-"}')
print('  rows by class: ' + ', '.join(f'{c} {sum(1 for v in riv.values() for r in v if r["class"] == c)}' for c in CLASSES))
print(f'club-friendships.csv: {sum(len(v) for v in fri.values())} accepted rows, {len(fri)} clubs')
for q in sorted(fri, key=lambda q: clubs[q]):
    print(f'  {clubs[q]} ({q})')
    for r in sorted(fri[q], key=lambda r: (ORDER_SHOWN.index(r['status']), r['friendName'])):
        print(f'    {r["status"]:7} {r["scope"]:10} {r["friendName"]}  {r["friendQ"] or "(not on the map)"}  {r["sourceId"]}  checked {r["checkedOn"] or "-"}')
for w in warnings: print('WARNING:', w)
for p in problems: print('PROBLEM:', p)
if problems:
    print(f'{len(problems)} problem(s).'); sys.exit(1)
print('No problems.' + (f' {len(warnings)} warning(s).' if warnings else ''))
