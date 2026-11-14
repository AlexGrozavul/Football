# Ticket data audit, phase 2a (November 2026)

A seeded sample of the ticket files, checked against pages opened in the
audit session itself. Part 1 of this file (method, seed, sample) was
written and committed **before any page was read**; the results follow
further down.

## 1. Method

- **What is audited:** `data/club-ticket-rules.csv`, `club-ticket-phases.csv`,
  `club-ticket-demand.csv` (one pool of 930 rows) and
  `club-ticket-prices.csv` (983 rows), as they stand at commit `6380d2c`.
- **Seed:** `20261114`, Python `random.Random(seed)`. The script is printed
  in full at the end of this section, so the draw can be repeated.
- **Rules, phases, demand: 60 rows** = 45 tagged `confirmed` + 15 tagged
  `unverified` (the 11 `inferred` rows are not in the pool). 15 clubs are
  drawn for one `unverified` row each; every club with a `confirmed` row
  gets one, and the remaining confirmed rows go to clubs drawn at random
  that still have fewer than 3 rows. No club has more than 3 rows.
- **Prices: 20 rows**, one each from 20 of the 21 clubs that have prices.
- **Row id** = file and line number in the file at `6380d2c` (line 1 is
  the header), for example `rules:703`.
- **Groups.** `R` = the club's research was reported in the coordinator
  chat (Elversberg, Frankfurt, Napoli, Kaiserslautern, Fürth, Freiburg,
  Mainz, Augsburg, Strasbourg, Bayern, Nürnberg, Inter, KSC, VfB).
  `Q` = researched in the ticket queue, PRs #172 to #189. **`Q+`** = six
  clubs the brief's two lists do not name (VfL Wolfsburg, Energie Cottbus,
  Hertha BSC, 1. FC Union Berlin, Hamburger SV, Holstein Kiel): they were
  researched in the queue after PR #189 and were not reviewed either.
  They are counted with group Q and also shown on their own, so the
  figure can be read both ways.
- **What is opened.** For each row, the page of the **first** entry of its
  `sourceRefs` (the row's first source record in `ticket-sources.csv`); a
  later entry of the same row only when the first page does not hold the
  statement, or its host is closed. `prices:8` (Bayern) has no source
  record; its `source` column names the page. Other club pages are opened
  only from link lists posted by the probe.
- **Hosts.** robots.txt and the legal notice or terms of every host are
  read before any content page of that host. A Disallow for the path, a
  robots group naming Anthropic's agents, HTTP 403/429/503, a challenge
  page, or a notice that bans automated access closes the host; a closed
  host is not read and not routed around, and its rows get "cannot
  verify".
- **Shops.** No shop listing, seat map, cart, login or queue page is
  opened, and nothing new is opened on a ticket-shop host. Seven sampled
  rows name a terms or information page that sits on a ticket host
  (`tickets.schalke04.de/agb`, `ticketing.schalke04.de/.../preise-kategorien`,
  `shop.fck.de/Informationen/ATGB/`, `stores.eintracht.de/rechtliches/atgb-maenner/`,
  the Strasbourg terms PDF on `billetterie.rcstrasbourgalsace.fr`). These
  exact pages were read in the clubs' research passes; the audit re-reads
  only these exact addresses, after the host's own robots and notice
  check. **This is the auditor's reading of the shop rule and is flagged
  for Alexandru**; the rows are marked in the results.
- **Verdicts.** `correct`; `wrong` (the page states something else: the
  row is fixed from the page); `stale` (the page changed: the row and its
  checked date are updated); `tag too strong` (downgraded to `unverified`,
  reason noted); `tag too weak` (a page opened now shows 2026/27 or a
  dated document: upgraded to `confirmed`); `cannot verify` (host closed,
  page gone, picture only). The tag is judged against the tag policy of
  2026-10-28 in `docs/claude/conventions.md`.
- **Errors** = wrong, stale, tag too strong. `tag too weak` and `cannot
  verify` are counted but are not errors. **Pass rule:** 0 or 1 errors in
  a stratum passes; 2 or more means a full check of that stratum later.
- **Prices** are also checked for whether any page of the club states that
  its prices include booking fees or VAT; `priceBasis` is set only from
  such a statement, never inferred.
- The audit's knowledge of football only produces leads. Every verdict
  and every fix rests on a page opened in this session.

### The draw script

```python
import csv, random, json, sys
SEED = 20261114
R = {'Q692691','Q38245','Q2641','Q8466','Q153539','Q106394','Q105254','Q97905916','Q126334','Q15789','Q15786','Q631','Q105853','Q4512'}
Q172 = {'Q162251','Q479351','Q104770','Q104761','Q41420','Q101959','Q105861','Q160532','Q32494','Q105844','Q160530','Q33748','Q154053','Q155730','Q141931'}
def load(name):
    out = []
    with open(f'data/club-ticket-{name}.csv', encoding='utf-8', newline='') as f:
        for i, r in enumerate(csv.DictReader(f), start=2):   # i = line number in the file
            r['_id'] = f'{name}:{i}'; r['_file'] = name
            out.append(r)
    return out
pool = [r for n in ('rules', 'phases', 'demand') for r in load(n)]
rng = random.Random(SEED)
clubs = sorted({r['clubQid'] for r in pool})
taken = {c: [] for c in clubs}
def rows(c, tag): return [r for r in pool if r['clubQid'] == c and r['confidence'] == tag and r not in taken[c]]
# 15 unverified: 15 clubs drawn from those that have an unverified row, one row each
uc = rng.sample([c for c in clubs if rows(c, 'unverified')], 15)
for c in uc: taken[c].append(rng.choice(rows(c, 'unverified')))
# 45 confirmed: one per club that has a confirmed row, then the rest from clubs with fewer than 3 rows
n = 0
for c in clubs:
    if rows(c, 'confirmed'): taken[c].append(rng.choice(rows(c, 'confirmed'))); n += 1
while n < 45:
    c = rng.choice([c for c in clubs if len(taken[c]) < 3 and rows(c, 'confirmed')])
    taken[c].append(rng.choice(rows(c, 'confirmed'))); n += 1
prices = load('prices')
pclubs = sorted({r['clubQid'] for r in prices})
psel = [rng.choice([r for r in prices if r['clubQid'] == c]) for c in rng.sample(pclubs, 20)]
sample = [r for c in clubs for r in taken[c]] + psel
for r in sample:
    r['_group'] = 'R' if r['clubQid'] in R else ('Q' if r['clubQid'] in Q172 else 'Q+')
json.dump(sample, open(sys.argv[1], 'w'), ensure_ascii=False, indent=0)
```

## 2. The sample

80 rows, 35 clubs. Tag = the row's `confidence` at `6380d2c`.

### Rules, phases, demand (60 rows: 45 confirmed, 15 unverified)

| row | group | club | tag | what | first source |
|---|---|---|---|---|---|
| `rules:703` | Q+ | VfL Wolfsburg | unverified | general / price-list | WOB3 |
| `rules:698` | Q+ | VfL Wolfsburg | confirmed | general / membership | WOB6 |
| `rules:440` | Q | Borussia Mönchengladbach | confirmed | general / away-allocation | BMG19 |
| `rules:767` | Q+ | Hertha BSC | confirmed | general / transfer | BSC8 |
| `rules:369` | Q | Bayer 04 Leverkusen | confirmed | general / presale-rights | LEV5 |
| `rules:366` | Q | 1. FC Köln | unverified | general / sales-channel | KOE1 |
| `rules:347` | Q | 1. FC Köln | confirmed | general / sector-rules | KOE8 |
| `rules:218` | R | 1. FSV Mainz 05 | confirmed | general / personalisation | MZ7 |
| `rules:570` | Q | Arminia Bielefeld | confirmed | general / membership | DSC5 |
| `rules:563` | Q | Arminia Bielefeld | confirmed | general / entrances | DSC9 |
| `demand:8` | R | Karlsruher SC | unverified | derby-home / sold-out / 2022-23 | K18 |
| `demand:10` | R | Karlsruher SC | confirmed | derby-home / sold-out / 2025-26 | K8 |
| `rules:472` | Q | VfL Bochum | confirmed | general / price-list | BOC3 |
| `rules:192` | R | SC Freiburg | confirmed | general / sales-channel | SC1 |
| `rules:205` | R | SC Freiburg | confirmed | general / access | SC1 |
| `rules:201` | R | SC Freiburg | confirmed | general / personalisation | SC7 |
| `rules:727` | Q+ | Energie Cottbus | confirmed | general / ticket-types | FCE1 |
| `rules:270` | R | RC Strasbourg Alsace | confirmed | general / access | RCS8 |
| `rules:257` | R | RC Strasbourg Alsace | confirmed | general / personalisation | RCS8 |
| `rules:674` | Q | Dynamo Dresden | confirmed | general / presale-rights | SGD6 |
| `rules:785` | Q+ | 1. FC Union Berlin | unverified | general / away-end | FCU7 |
| `rules:781` | Q+ | 1. FC Union Berlin | confirmed | general / sales-channel | FCU19 |
| `rules:180` | R | SpVgg Greuther Fürth | unverified | general / membership | GF1 |
| `rules:177` | R | SpVgg Greuther Fürth | confirmed | general / sales-channel | GF3 |
| `rules:640` | Q | Eintracht Braunschweig | unverified | general / ticket-types | EBS8 |
| `rules:631` | Q | Eintracht Braunschweig | confirmed | general / unofficial-resale | EBS11 |
| `rules:663` | Q | 1. FC Magdeburg | unverified | general / sector-separation | FCM12 |
| `rules:653` | Q | 1. FC Magdeburg | confirmed | general / ticket-types | FCM1 |
| `demand:39` | Q | 1. FC Magdeburg | confirmed | general / seats-left / 2026-27 | FCM27 |
| `rules:821` | Q+ | Holstein Kiel | confirmed | general / purchase-limit | KIEL7 |
| `rules:19` | R | 1. FC Nürnberg | confirmed | general / resale-price-cap | N7 |
| `rules:595` | Q | VfL Osnabrück | unverified | general / sales-channel | OSN4 |
| `rules:597` | Q | VfL Osnabrück | confirmed | general / presale-rights | OSN1 |
| `rules:495` | Q | SC Paderborn 07 | confirmed | general / purchase-limit | SCP2 |
| `rules:294` | Q | 1. FC Heidenheim 1846 | confirmed | general / minors | FCH5 |
| `rules:138` | R | SSC Napoli | confirmed | general / presale-rights | SN1 |
| `rules:538` | Q | FC Schalke 04 | unverified | general / away-end | FCS18 |
| `rules:545` | Q | FC Schalke 04 | confirmed | general / update-tracking | FCS15 |
| `rules:543` | Q | FC Schalke 04 | confirmed | general / ticket-types | FCS1 |
| `rules:619` | Q | Hannover 96 | unverified | general / sales-channel | HAN13 |
| `rules:605` | Q | Hannover 96 | confirmed | general / ticket-format | HAN2 |
| `rules:106` | R | Eintracht Frankfurt | confirmed | general / personalisation | F11 |
| `rules:109` | R | Eintracht Frankfurt | confirmed | general / unofficial-resale | F11 |
| `demand:28` | Q | Borussia Dortmund | unverified | general / sold-out / 2026-27 | BVB4 |
| `rules:409` | Q | Borussia Dortmund | confirmed | general / ticket-format | BVB15 |
| `rules:413` | Q | Borussia Dortmund | confirmed | general / minors | BVB3 |
| `rules:76` | R | VfB Stuttgart | confirmed | general / price-list | V8 |
| `rules:84` | R | VfB Stuttgart | confirmed | general / update-tracking | V2 |
| `rules:320` | Q | SV Darmstadt 98 | unverified | general / unofficial-resale | SVD31 |
| `rules:309` | Q | SV Darmstadt 98 | confirmed | general / purchase-limit | SVD13 |
| `rules:332` | Q | SV Darmstadt 98 | confirmed | general / access | SVD7 |
| `rules:809` | Q+ | Hamburger SV | confirmed | general / away-allocation | HSV18 |
| `rules:41` | R | FC Internazionale Milano | unverified | derby-home / resale-prices | I16 |
| `phases:16` | R | FC Internazionale Milano | confirmed | window derby-home / phase 6 | I2 |
| `rules:40` | R | FC Internazionale Milano | confirmed | general / unofficial-resale | I2 |
| `rules:128` | R | SV Elversberg | confirmed | general / capacity | E12 |
| `rules:162` | R | 1. FC Kaiserslautern | unverified | general / access | FK1 |
| `rules:150` | R | 1. FC Kaiserslautern | confirmed | general / ticket-format | FK5 |
| `rules:247` | R | FC Augsburg | unverified | general / minors | FCA11 |
| `rules:237` | R | FC Augsburg | confirmed | general / purchase-limit | FCA3 |

### Prices (20 rows)

| row | group | club | tag | season / competition / kind / category / place / price | first source |
|---|---|---|---|---|---|
| `prices:82` | R | Karlsruher SC | confirmed | 2026-27 / 2-bundesliga / face-value / west-w2-w3 / seat / 70.50 EUR | K2 |
| `prices:8` | R | FC Bayern München | unverified | 2026-27 / dfb-pokal / face-value / 4 / seat / 40 EUR | source column |
| `prices:641` | Q | Borussia Dortmund | confirmed | 2026-27 / bundesliga / face-value / stehplatz / standing / 120.40 EUR | BVB1 |
| `prices:277` | R | 1. FSV Mainz 05 | confirmed | 2026-27 / bundesliga / face-value / 2 / - / 37.00 EUR | MZ2 |
| `prices:153` | R | VfB Stuttgart | confirmed | 2026-27 / bundesliga / face-value / kat-6-kurve-sitz-2 / seat / 395.00 EUR | V14 |
| `prices:754` | Q | Hannover 96 | unverified | 2026-27 / 2-bundesliga / face-value / 3 / seat / 15.00 EUR | HAN5 |
| `prices:539` | Q | SV Darmstadt 98 | confirmed | 2026-27 / 2-bundesliga / face-value / gegengerade-stehplatz-g1-g3 / standing / 270.00 EUR | SVD3 |
| `prices:216` | R | SSC Napoli | confirmed | 2026-27 / serie-a / face-value / italia-tribuna-nisida / seat / 900.00 EUR | SN1 |
| `prices:968` | Q+ | 1. FC Union Berlin | confirmed | 2026-27 / bundesliga / face-value / 3 / seat / 19.00 EUR | FCU1 |
| `prices:897` | Q | 1. FC Magdeburg | confirmed | 2026-27 / 2-bundesliga / face-value / block-8 / - / 300.00 EUR | FCM9 |
| `prices:695` | Q | VfL Bochum | confirmed | 2026-27 / 2-bundesliga / face-value / west-e1-gaesteblock-stehplatz / standing / 17.00 EUR | BOC3 |
| `prices:411` | R | FC Augsburg | confirmed | 2026-27 / bundesliga / face-value / kat-2-sichteingeschraenkt / seat / 17.00 EUR | FCA1 |
| `prices:55` | R | FC Internazionale Milano | unverified | 2023-24 / serie-a / face-value / secondo-verde / - / 49 EUR | I12 |
| `prices:710` | Q | FC Schalke 04 | confirmed | 2026-27 / bundesliga / face-value / 1 / seat / 58.00 EUR | FCS2 |
| `prices:512` | Q | 1. FC Heidenheim 1846 | confirmed | 2026-27 / 2-bundesliga / face-value / stehplatz / standing / 180.00 EUR | FCH4 |
| `prices:26` | R | 1. FC Nürnberg | unverified | 2026-27 / 2-bundesliga / face-value / haupttribuene-kat-2 / seat / 54.50 EUR | N7 |
| `prices:959` | Q+ | Hertha BSC | confirmed | 2026-27 / 2-bundesliga / face-value / ostkurve-q-t-34-41 / - / 210.00 EUR | BSC14 |
| `prices:642` | Q | Borussia Mönchengladbach | confirmed | 2026-27 / bundesliga / face-value / stehplatz / standing / 17.00 EUR | BMG12 |
| `prices:611` | Q | Bayer 04 Leverkusen | confirmed | 2026-27 / bundesliga / face-value / 6 / - / 14.00 EUR | LEV10 |
| `prices:174` | R | SV Elversberg | confirmed | 2026-27 / bundesliga / face-value / stehplatz / standing / 84.00 EUR | E1 |

### Counts

- By file: rules 55 (42 confirmed, 13 unverified), phases 1 (1 confirmed), demand 4 (2 confirmed, 2 unverified), prices 20 (16 confirmed, 4 unverified).
- By group, rules/phases/demand: R 24, Q 28, Q+ 8. Prices: R 9, Q 9, Q+ 2.
- Distinct first-source pages: 73, on 49 hosts.
