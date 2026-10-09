#!/usr/bin/env python3
"""
check_club_culture.py -- read-back and checks for data/club-rivalries.csv,
data/club-atmosphere.csv and data/club-culture-sources.csv.

All three are hand-written and nothing writes to them. This tool reads them,
prints every accepted row as understood and exits 1 on a problem.

club-rivalries.csv: clubQ, rivalQ (blank when the rival is not on the map),
rivalName, class (main, local, other), sourceId, checkedOn. The class comes
only from the wording of the source. There is no row limit and no target.
club-atmosphere.csv: clubQ, situation, opponentQ, opponentName, where,
whenText, what, attribution, basis, sourceId, checkedOn. Every row is an
attributed claim, never our own statement.

EXITS 1 on: a clubQ, rivalQ or opponentQ on no data/clubs/*.json, a sourceId
not in club-culture-sources.csv, a class, situation, basis or source kind
outside its list, a duplicate row, a missing rivalName / what / attribution,
a day-level date in the future in a text cell, a row with more values than
the header has columns.
WARNS (exit stays 0) on a missing or malformed checkedOn, a club with more
than 12 rows in either file (so they can be reviewed for padding), a `what`
that uses "best", "loudest" or "most intense" outside quotation marks, and a
source no row uses.

Usage:  python3 tools/check_club_culture.py
"""
import csv, glob, json, os, re, sys
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
D = os.path.join(ROOT, 'data')
CLASSES = ('main', 'local', 'other')
SITUATIONS = ('derby', 'european', 'cup', 'big-occasion', 'regular-home', 'other')
BASES = ('documented', 'reported')
KINDS = ('wikipedia', 'club', 'press', 'fan-media')
REVIEW_OVER = 12
MONTHS = 'january|february|march|april|may|june|july|august|september|october|november|december'
ISO_DAY = re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b')
DMY = re.compile(r'\b(\d{1,2})\.?\s+(' + MONTHS + r')\s+(\d{4})\b', re.I)
MDY = re.compile(r'\b(' + MONTHS + r')\s+(\d{1,2}),?\s+(\d{4})\b', re.I)
SUPERLATIVE = re.compile(r'\b(best|loudest|most intense)\b', re.I)

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


def outside_quotes(text):
    return re.sub(r'"[^"]*"|“[^”]*”|‘[^’]*’', '', text)


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


riv, atm = {}, {}
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

for line, r in read('club-atmosphere.csv', ['clubQ', 'situation', 'opponentQ', 'opponentName', 'where', 'whenText',
                                            'what', 'attribution', 'basis', 'sourceId', 'checkedOn']):
    at = f'club-atmosphere.csv line {line}'
    ok = common(at, r, True)
    if r['situation'] not in SITUATIONS:
        problems.append(f'{at}: situation "{r["situation"]}" is not one of {", ".join(SITUATIONS)}'); ok = False
    if r['basis'] not in BASES:
        problems.append(f'{at}: basis "{r["basis"]}" is not one of {", ".join(BASES)}'); ok = False
    if r['opponentQ'] and r['opponentQ'] not in clubs:
        problems.append(f'{at}: opponentQ "{r["opponentQ"]}" is on no club file (leave it blank if the opponent is not on the map)'); ok = False
    for col in ('what', 'attribution'):
        if not r[col]:
            problems.append(f'{at}: {col} is empty'); ok = False
    for col in ('where', 'whenText', 'what', 'attribution', 'opponentName'):
        if future_days(r[col]):
            problems.append(f'{at}: {col} holds a future day-level date'); ok = False
    if SUPERLATIVE.search(outside_quotes(r['what'])):
        warnings.append(f'{at}: "what" uses best / loudest / most intense outside quotation marks; that must be the source\'s word, not ours')
    key = ('atm', r['clubQ'], r['situation'], r['opponentQ'] or r['opponentName'].casefold(), r['where'].casefold(),
           r['whenText'].casefold(), r['sourceId'], r['what'].casefold())
    if key in seen:
        problems.append(f'{at}: the same row is entered twice'); ok = False
    seen.add(key)
    if ok: atm.setdefault(r['clubQ'], []).append(r)

for label, d in (('club-rivalries.csv', riv), ('club-atmosphere.csv', atm)):
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
print(f'club-atmosphere.csv: {sum(len(v) for v in atm.values())} accepted rows, {len(atm)} clubs')
for q in sorted(atm, key=lambda q: clubs[q]):
    print(f'  {clubs[q]} ({q})')
    for r in atm[q]:
        print(f'    {r["situation"]:12} {r["basis"]:10} vs {r["opponentName"] or "any opponent"}  {r["sourceId"]}  checked {r["checkedOn"] or "-"}')
print('  rows by situation: ' + ', '.join(f'{s} {sum(1 for v in atm.values() for r in v if r["situation"] == s)}' for s in SITUATIONS))
print('  rows by basis: ' + ', '.join(f'{b} {sum(1 for v in atm.values() for r in v if r["basis"] == b)}' for b in BASES))
for w in warnings: print('WARNING:', w)
for p in problems: print('PROBLEM:', p)
if problems:
    print(f'{len(problems)} problem(s).'); sys.exit(1)
print('No problems.' + (f' {len(warnings)} warning(s).' if warnings else ''))
