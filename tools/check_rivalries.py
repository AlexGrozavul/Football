#!/usr/bin/env python3
"""
check_rivalries.py -- read-back and checks for data/club-rivalries.csv and
data/rivalry-sources.csv.

Both files are hand-written and nothing writes to them. This tool reads
them, prints every row as understood and exits 1 on a problem.

data/club-rivalries.csv: clubQ, rivalQ (blank when the rival is not on the
map), rivalName, class (main, local, other), sourceId, checkedOn. One row
per club per rival, stored separately for each club, because the same
rivalry can have a different class for each of the two clubs. The class
comes only from the wording of the source; where the wording does not say
how big the rivalry is, it is `other`.

EXITS 1 on: a clubQ or rivalQ that is on no data/clubs/*.json, a sourceId
not in rivalry-sources.csv, a class outside main/local/other, a missing
rivalName, a club with more than 5 rows, a repeated row (same club, same
rival), a row with more values than the header has columns.
WARNS (exit stays 0) on a row with no checkedOn, a checkedOn that is not
an ISO date or lies in the future, a source with no retrievedOn, and a
source no row uses.

Usage:  python3 tools/check_rivalries.py
"""
import csv, glob, json, os, re, sys
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
RIV = os.path.join(ROOT, 'data', 'club-rivalries.csv')
SRC = os.path.join(ROOT, 'data', 'rivalry-sources.csv')
CLASSES = ('main', 'local', 'other')
MAX_PER_CLUB = 5
QID = re.compile(r'^Q[1-9]\d*$')

problems, warnings = [], []


def read(path, required):
    """Rows as (line, dict). A row with more values than the header has
    columns is a problem: an unquoted comma."""
    if not os.path.exists(path):
        problems.append(f'{os.path.relpath(path, ROOT)} does not exist')
        return []
    out = []
    with open(path, newline='', encoding='utf-8') as f:
        rd = csv.reader(f)
        header = next(rd, [])
        missing = [c for c in required if c not in header]
        if missing:
            problems.append(f'{os.path.basename(path)}: header lacks {", ".join(missing)}')
            return []
        for row in rd:
            line = rd.line_num
            if not any(c.strip() for c in row):
                continue
            if len(row) > len(header):
                problems.append(f'{os.path.basename(path)} line {line}: {len(row)} values for '
                                f'{len(header)} columns (an unquoted comma?)')
                continue
            row += [''] * (len(header) - len(row))
            out.append((line, {h: v.strip() for h, v in zip(header, row)}))
    return out


def iso(s):
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


clubs = {}
for p in glob.glob(os.path.join(ROOT, 'data', 'clubs', '??.json')):
    for c in json.load(open(p, encoding='utf-8')).get('clubs', []):
        clubs[c['id']] = c.get('name') or c['id']

sources = {}
for line, r in read(SRC, ['sourceId', 'url', 'title', 'retrievedOn']):
    if not r['sourceId'] or not r['url'].startswith('http'):
        problems.append(f'rivalry-sources.csv line {line}: needs a sourceId and a URL')
        continue
    if r['sourceId'] in sources:
        problems.append(f'rivalry-sources.csv line {line}: sourceId {r["sourceId"]} repeated')
        continue
    if not r['retrievedOn']:
        warnings.append(f'rivalry-sources.csv line {line}: {r["sourceId"]} has no retrievedOn')
    elif not iso(r['retrievedOn']):
        problems.append(f'rivalry-sources.csv line {line}: retrievedOn "{r["retrievedOn"]}" is not an ISO date')
    sources[r['sourceId']] = r

rows = read(RIV, ['clubQ', 'rivalQ', 'rivalName', 'class', 'sourceId', 'checkedOn'])
seen, per_club, used = set(), {}, set()
today = date.today()
for line, r in rows:
    at = f'club-rivalries.csv line {line}'
    ok = True
    if r['clubQ'] not in clubs:
        problems.append(f'{at}: clubQ "{r["clubQ"]}" is on no club file'); ok = False
    if r['rivalQ'] and r['rivalQ'] not in clubs:
        problems.append(f'{at}: rivalQ "{r["rivalQ"]}" is on no club file '
                        f'(leave it blank if the rival is not on the map)'); ok = False
    if r['rivalQ'] and r['rivalQ'] == r['clubQ']:
        problems.append(f'{at}: a club cannot be its own rival'); ok = False
    if not r['rivalName']:
        problems.append(f'{at}: rivalName is empty'); ok = False
    if r['class'] not in CLASSES:
        problems.append(f'{at}: class "{r["class"]}" is not one of {", ".join(CLASSES)}'); ok = False
    if r['sourceId'] not in sources:
        problems.append(f'{at}: sourceId "{r["sourceId"]}" is not in rivalry-sources.csv'); ok = False
    else:
        used.add(r['sourceId'])
    if not r['checkedOn']:
        warnings.append(f'{at}: no checkedOn')
    else:
        d = iso(r['checkedOn'])
        if not d:
            warnings.append(f'{at}: checkedOn "{r["checkedOn"]}" is not an ISO date')
        elif d > today:
            warnings.append(f'{at}: checkedOn {r["checkedOn"]} is in the future')
    key = (r['clubQ'], r['rivalQ'] or r['rivalName'].casefold())
    if key in seen:
        problems.append(f'{at}: {clubs.get(r["clubQ"], r["clubQ"])} / {r["rivalName"]} is entered twice')
        ok = False
    seen.add(key)
    if ok:
        per_club.setdefault(r['clubQ'], []).append(r)

for q, rs in per_club.items():
    if len(rs) > MAX_PER_CLUB:
        problems.append(f'{clubs[q]} ({q}) has {len(rs)} rows; the limit is {MAX_PER_CLUB}')
for sid in sources:
    if sid not in used:
        warnings.append(f'source {sid} is used by no row')

print(f'{len(sources)} sources, {sum(len(v) for v in per_club.values())} accepted rows, {len(per_club)} clubs')
for q in sorted(per_club, key=lambda q: clubs[q]):
    print(f'  {clubs[q]} ({q})')
    for r in sorted(per_club[q], key=lambda r: r['rivalName']):
        print(f'    {r["class"]:5}  {r["rivalName"]}  {r["rivalQ"] or "(not on the map)"}  '
              f'{r["sourceId"]}  checked {r["checkedOn"] or "-"}')
counts = {c: sum(1 for v in per_club.values() for r in v if r['class'] == c) for c in CLASSES}
print('rows by class: ' + ', '.join(f'{c} {n}' for c, n in counts.items()))
for w in warnings:
    print('WARNING:', w)
for p in problems:
    print('PROBLEM:', p)
if problems:
    print(f'{len(problems)} problem(s).'); sys.exit(1)
print('No problems.' + (f' {len(warnings)} warning(s).' if warnings else ''))
