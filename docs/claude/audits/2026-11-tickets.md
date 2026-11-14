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
  `unverified` (the 10 `inferred` rows are not in the pool). 15 clubs are
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

## 3. Results (written after the pages were read, 14 November 2026)

**No row was wrong, stale or tagged too strongly. 70 of the 80 rows match
their page; 10 could not be verified, and all 10 belong to group R. No
data row was changed.** Three probe runs were used out of eight; the page
extracts are the comments on PR #216.

### What "correct" means here

A row is `correct` when the page opened in this session states the row's
main statements: the figures, the named blocks, limits, channels and the
date or season mark the tag rests on were each looked up in the page
text. Long rows were **not** compared clause by clause, and a row that
covers several games was checked on the first source's game only (said
in the table). Whether a dated document is still linked from a current
page of the club was re-checked for Bielefeld's stadium rules and
Dortmund's terms; for the other dated documents the linking page is
taken from the row's note.

### Counts and rates

| stratum | rows | correct | wrong | stale | tag too strong | tag too weak | cannot verify | errors | verdict |
|---|---|---|---|---|---|---|---|---|---|
| rules, phases, demand tagged `confirmed` | 45 | 40 | 0 | 0 | 0 | 0 | 5 | 0 of 45 (0 %) | **pass** |
| rules, demand tagged `unverified` | 15 | 14 | 0 | 0 | 0 | 0 | 1 | 0 of 15 (0 %) | **pass** |
| prices | 20 | 16 | 0 | 0 | 0 | 0 | 4 | 0 of 20 (0 %) | **pass** |
| group R (rules 24 + prices 9) | 33 | 23 | 0 | 0 | 0 | 0 | 10 | 0 of 33 (0 %) | **pass, with the reservation below** |
| group Q, PRs #172 to #189 (rules 28 + prices 9) | 37 | 37 | 0 | 0 | 0 | 0 | 0 | 0 of 37 (0 %) | **pass** |
| group Q+, after PR #189 (rules 8 + prices 2) | 10 | 10 | 0 | 0 | 0 | 0 | 0 | 0 of 10 (0 %) | **pass** |

With no error in 80 rows the sample cannot say the files are free of
errors: zero in 45 confirmed rows is compatible with an error rate of up
to about 6 to 7 per cent in that stratum (95 per cent bound), about 18
per cent for the 15 unverified rows and about 14 per cent for the 20
prices.

**Reservation on group R.** The pass rule counts errors only, and group R
has none. But 10 of its 33 rows (30 per cent) could not be opened at all,
against none of 47 in the queue groups: R holds the clubs researched
first (Inter, Nürnberg, Bayern, KSC, VfB), whose rows rest on hosts that
are closed to this reader, on source records with a cut-off address, or
on ksc.de addresses that no longer exist. For R the result is "nothing
wrong found in the 23 rows that could be read", not "checked".

**No stratum reached 2 errors, so no full check is triggered.** For
reference, a full check would cover: 612 confirmed rows (rules 543,
phases 39, demand 30), 308 unverified rows (290, 4, 14), 983 price rows;
by group 334 rule-file rows and 510 prices in R, 436 and 431 in Q, 150
and 42 in Q+ (the 10 `inferred` rows are outside the audit).

### Verdict per row

Rows marked `[shop host]` were read on a ticket host at the exact address
of the source record (see "Shops" in the method).

| row | group | club | tag | verdict | page | what the page shows, or why not |
|---|---|---|---|---|---|---|
| `rules:703` | Q+ | VfL Wolfsburg | unverified | **correct** | WOB3 | 6, 9, 14 and 230 euro with companion and the AOK Stadion line are on the page; undated, so unverified fits |
| `rules:698` | Q+ | VfL Wolfsburg | confirmed | **correct** | WOB6 | "WölfeClub-AGB (Stand: 01.07.2026)": card not transferable, 30,00 euro a year, 12 euro for 14- and 15-year-olds |
| `rules:440` | Q | Borussia Mönchengladbach | confirmed | **correct** | BMG19 | notice of 19.10.2026: blocks 6A and 7A released, seats at 19 euro |
| `rules:767` | Q+ | Hertha BSC | confirmed | **correct** | BSC8, BSC14 | terms "Geltungszeitraum ab 20. Mai 2026"; the FAQ (2026/27) has the clearing-point upgrade and "Umschreibung nicht möglich" |
| `rules:369` | Q | Bayer 04 Leverkusen | confirmed | **correct** | LEV5 | the three member groups and their blocks, page shows 2026/27 |
| `rules:366` | Q | 1. FC Köln | unverified | **correct** | KOE1 | DERTOUR package and referee tickets through the FVM; undated page, unverified fits |
| `rules:347` | Q | 1. FC Köln | confirmed | **correct** | KOE8 | blocks as written; the text says "Die Stadionordnung gilt ab dem 19.11.2025" (inside 12 months, by five days) |
| `rules:218` | R | 1. FSV Mainz 05 | confirmed | **correct** | MZ7 | "15. Mai 2026" printed in the PDF; the text says "geeignetes amtliches Identifikationsdokument (z.B. Personalausweis oder Reisepass)", which the row calls a photo ID |
| `rules:570` | Q | Arminia Bielefeld | confirmed | **correct** | DSC5 | waiting list, membership needed, "am 19.06. geschlossen", reopened at the start of 26/27 |
| `rules:563` | Q | Arminia Bielefeld | confirmed | **correct** | DSC9, DSC19 | "tritt am 5. August 2026 in Kraft"; linked from the SchücoArena page |
| `demand:8` | R | Karlsruher SC | unverified | **correct** | K18 | "Bereits nach dem ersten Verkaufstag sind alle Tickets ... vergriffen" (article, Stand 29.04.2023); one press source, unverified fits |
| `demand:10` | R | Karlsruher SC | confirmed | **cannot verify** | K8, K22 | the match-report address now shows a general news page (ksc.de was relaunched); the second source meinka.de answered robots.txt with HTTP 508 and showed no notice, so it was not read |
| `rules:472` | Q | VfL Bochum | confirmed | **correct** | BOC3 | 2,50 euro for passive members, not block H2; categories may change with the stadium works; list headed 2026|27 |
| `rules:192` | R | SC Freiburg | confirmed | **correct** | SC1 | online shop, Reservix hotline 0761-888 499 96, no orders by e-mail, fax or letter; page shows 2026/27 |
| `rules:205` | R | SC Freiburg | confirmed | **correct** | SC1 | RVF-Kombi-Ticket, from five hours before kick-off, back until 3:00 |
| `rules:201` | R | SC Freiburg | confirmed | **correct** | SC7 | "Stand Juni 2026"; identifying features and the identification document as written (same wording note as rules:218) |
| `rules:727` | Q+ | Energie Cottbus | confirmed | **correct** | FCE1 | written application with a copy of the card, one companion; page headed 2026/2027 |
| `rules:270` | R | RC Strasbourg Alsace | confirmed | **correct** | RCS8, RCS6 | terms for 1 July 2026 to 30 June 2027: identity document, no screenshot, searches, exit is final, no entry after the second half starts; the gate-opening line is not in the terms (it comes from the later entries) `[shop host]` |
| `rules:257` | R | RC Strasbourg Alsace | confirmed | **correct** | RCS8 | "chaque Billet est nominatif", article R.332-20-3, bearer and attribution `[shop host]` |
| `rules:674` | Q | Dynamo Dresden | confirmed | **correct** | SGD6 | Ticket-Freunde, PIN under "Meine Freunde"; notice shows 2026/27 |
| `rules:785` | Q+ | 1. FC Union Berlin | unverified | **correct** | FCU7, FCU8, FCU1 | sector 5 and cash-desk area 4 on FCU7; Wuhlewanderweg and petrol station in the PDF FCU8; block Z on the price page; all undated, unverified fits |
| `rules:781` | Q+ | 1. FC Union Berlin | confirmed | **correct** | FCU19 | free sale online and in all Zeughaus shops, box offices on the day; dated preview |
| `rules:180` | R | SpVgg Greuther Fürth | unverified | **correct** | GF1 | admission fee 15 euro, Fanmitgliedschaft 50,00, Fördermitgliedschaft 80,00; undated page, unverified fits |
| `rules:177` | R | SpVgg Greuther Fürth | confirmed | **correct** | GF3 | notice of 07.10.2026: online shop, Sportheim and Franken Ticket |
| `rules:640` | Q | Eintracht Braunschweig | unverified | **correct** | EBS8 | five-euro social tickets and the list of proofs; undated page, unverified fits |
| `rules:631` | Q | Eintracht Braunschweig | confirmed | **correct** | EBS11 | "Stand: Mai 2026"; penalty up to 2.500 EUR and the other sanctions |
| `rules:663` | Q | 1. FC Magdeburg | unverified | **correct** | FCM12 | clause 11.6, blocks 1 to 7 and guest blocks 13, 14, 15; "Stand: Mai 2024" is older than 12 months, so unverified fits |
| `rules:653` | Q | 1. FC Magdeburg | confirmed | **correct** | FCM1 | reductions as written, page headed 2026/27 |
| `demand:39` | Q | 1. FC Magdeburg | confirmed | **correct** | FCM27 | preview of 09.10.2026: tickets still at the box office and outlets for the Hannover game |
| `rules:821` | Q+ | Holstein Kiel | confirmed | **correct** | KIEL7 | St. Pauli game: 1 ticket per member, reduced capacity and high demand; page shows 2026/27 (the other games are on later entries, not opened) |
| `rules:19` | R | 1. FC Nürnberg | confirmed | **cannot verify** | N7 | fcn.de: robots.txt bars ClaudeBot and anthropic-ai; host closed, not read |
| `rules:595` | Q | VfL Osnabrück | unverified | **correct** | OSN4 | form, number varies, no promise; undated page, unverified fits |
| `rules:597` | Q | VfL Osnabrück | confirmed | **correct** | OSN1 | hardcover tickets plus online sale, announced three to four weeks before; page shows 2026/27 |
| `rules:495` | Q | SC Paderborn 07 | confirmed | **correct** | SCP2 | up to two tickets, families up to four; page shows 2026/2027 |
| `rules:294` | Q | 1. FC Heidenheim 1846 | confirmed | **correct** | FCH5 | "Jedes Kind (ab Geburt)" needs a paid ticket; terms "Gültig ab 01. Juli 2026" |
| `rules:138` | R | SSC Napoli | confirmed | **correct** | SN1 | priority and discount for Champions League and Coppa Italia; page headed 2026/27 |
| `rules:538` | Q | FC Schalke 04 | unverified | **correct** | FCS18 | flags up to two metres, megaphones and drums in the standing blocks, 1.6 per mille; undated page, unverified fits |
| `rules:545` | Q | FC Schalke 04 | confirmed | **correct** | FCS15 | Ticket-News page with current 2026/27 fixtures |
| `rules:543` | Q | FC Schalke 04 | confirmed | **correct** | FCS1 | "Stand: 28. Mai 2026", clauses 6.4 and 6.5: subscription, chip card reloaded (terms page on the ticket host) `[shop host]` |
| `rules:619` | Q | Hannover 96 | unverified | **correct** | HAN13 | blocks O1, O8 and the south ramp, 13 euro with companion, 13 euro for blind fans; undated page, unverified fits |
| `rules:605` | Q | Hannover 96 | confirmed | **correct** | HAN2 | digital tickets in the account, wallet or PDF; page shows 2026/27 |
| `rules:106` | R | Eintracht Frankfurt | confirmed | **correct** | F11 | terms "Version September 2026", valid from 21 September 2026; photo ID with member and fan-club season tickets (terms page on the ticket host) `[shop host]` |
| `rules:109` | R | Eintracht Frankfurt | confirmed | **correct** | F11 | clause on eBay, Kleinanzeigen, Facebook, viagogo, StubHub, commercial resale and visiting fans `[shop host]` |
| `demand:28` | Q | Borussia Dortmund | unverified | **correct** | BVB4 | "bei fast allen Spielen frühzeitig ausverkauft"; undated general statement, unverified fits |
| `rules:409` | Q | Borussia Dortmund | confirmed | **correct** | BVB15 | news of 23.10.2026: NFC ticket, Google Wallet from the Frankfurt game |
| `rules:413` | Q | Borussia Dortmund | confirmed | **correct** | BVB3 and its linked PDF | the page only links the terms; the linked "ATGB_Saison_BVB_26-27" PDF ("Stand: Mai 2026") says "Jedes Kind (ab Geburt)" and no double reduction |
| `rules:76` | R | VfB Stuttgart | confirmed | **cannot verify** | V8 | the help page lists the question "Wo finde ich die Ticketpreise?" but its answer is not in the page until it is clicked and has no address of its own; not clicked. The tag itself is doubtful (an undated help page, season cell empty) and goes to the next check |
| `rules:84` | R | VfB Stuttgart | confirmed | **correct** | V2 | news of 25 August 2026: sale phases are announced in the ticket shop and by e-mail |
| `rules:320` | Q | SV Darmstadt 98 | unverified | **correct** | SVD31 | software scan, about 300 euro, "VB" counts too; undated help article, unverified fits |
| `rules:309` | Q | SV Darmstadt 98 | confirmed | **correct** | SVD13 | notice of 13.07.2026 for the Kiel game: at most four tickets per member (the other games are on later entries, not opened) |
| `rules:332` | Q | SV Darmstadt 98 | confirmed | **correct** | SVD7 | stadium rules "Stand: 08.07.2026": ticket shown unasked, search with technical means or a pyrotechnics search dog |
| `rules:809` | Q+ | Hamburger SV | confirmed | **correct** | HSV18 | members only, HSV-ID, all 17 away games, passed-on tickets do not count; page headed 2026/27 |
| `rules:41` | R | FC Internazionale Milano | unverified | **cannot verify** | I16 | the address in the source record is cut short ("…", urlComplete = truncated-in-pdf), so there is no page to open |
| `phases:16` | R | FC Internazionale Milano | confirmed | **cannot verify** | I2 | inter.it: the terms of use forbid "robot, crawler" and automated requests; host closed after its notice was read, page not opened |
| `rules:40` | R | FC Internazionale Milano | confirmed | **cannot verify** | I2 | inter.it closed by its terms of use, as above |
| `rules:128` | R | SV Elversberg | confirmed | **correct** | E12 | Wikipedia: about 10,000 places, 3,410 seats, 400 box seats, 800 business seats, 6,320 standing, DFL exemption (the 1,500 away seats are from the second source) |
| `rules:162` | R | 1. FC Kaiserslautern | unverified | **correct** | FK1 | "Stand: Juni 2023": ticket and an identity document suitable for identification, both shown on request; older than 12 months, unverified fits (terms page on the ticket host) `[shop host]` |
| `rules:150` | R | 1. FC Kaiserslautern | confirmed | **correct** | FK5 | fan information of 14.10.2026 for the Bochum game: print@home only printed, no wallet, FCK app |
| `rules:247` | R | FC Augsburg | unverified | **correct** | FCA11 | children up to five free on a lap ticket, entry alone from 14; the PDF prints no date, unverified fits |
| `rules:237` | R | FC Augsburg | confirmed | **correct** | FCA3 | Schalke game: up to four tickets per member, then the Bestandsfans phase; page shows 2026/27 |
| `prices:82` | R | Karlsruher SC | confirmed | **cannot verify** | K2, K1 | the price-list PDF answers HTTP 404 since the ksc.de relaunch; the new ticket page links its lists on a.storyblok.com, whose robots.txt answers HTTP 403, so they were not read |
| `prices:8` | R | FC Bayern München | unverified | **cannot verify** | source column | fcbayern.com: robots.txt did not answer (timeout); host closed, not read |
| `prices:641` | Q | Borussia Dortmund | confirmed | **correct** | BVB1 | "Stehplatz – Ermäßigt 11,00 / 120,40 / 148,90"; "Alle Preise inkl. 19 % MwSt." |
| `prices:277` | R | 1. FSV Mainz 05 | confirmed | **correct** | MZ2 | Preisliste 3, Kategorie 2: 41,00 / 37,00 (ermäßigt); list headed 2026/2027 |
| `prices:153` | R | VfB Stuttgart | confirmed | **correct** | V14 | "6 Kurve Sitzplatz 2": 428,00 / 395,00 (ermäßigt) / 285,00; list headed 2026/2027 |
| `prices:754` | Q | Hannover 96 | unverified | **correct** | HAN5 | Kategorie 3: 37 / 26 / 15 euro (KIND); the PDF prints no season, unverified fits |
| `prices:539` | Q | SV Darmstadt 98 | confirmed | **correct** | SVD3 | Stehplatz Gegengerade (G1 – G3), Mitglieder: 270 euro; table for 2026/27 |
| `prices:216` | R | SSC Napoli | confirmed | **correct** | SN1 | Nuovo Abbonato, Italia, 20 games, Tribuna Nisida: 1.200 / 900 / 600 euro |
| `prices:968` | Q+ | 1. FC Union Berlin | confirmed | **correct** | FCU1 | Bundesliga 2026/27 day tickets, Sek 1 Kat 3: 38,00 / 36,00 / 19,00 (Kind) |
| `prices:897` | Q | 1. FC Magdeburg | confirmed | **correct** | FCM9 | second block of the list (block 8): Jugendticket 15-17 Jahre 300,00; "Stand: 17.05.2026" |
| `prices:695` | Q | VfL Bochum | confirmed | **correct** | BOC3 | E1 Stehplatz: 17,00 EUR in the column Kategorie A |
| `prices:411` | R | FC Augsburg | confirmed | **correct** | FCA1 | B,C,P,Q "sichteingeschränkt Kind/ Teen": 23 / 17 (Topf B) / 14 / 10 euro; table for 2026/27 |
| `prices:55` | R | FC Internazionale Milano | unverified | **cannot verify** | I12 | the address in the source record is cut short ("…"), so there is no page to open |
| `prices:710` | Q | FC Schalke 04 | confirmed | **correct** | FCS2 | table "Tageskarten-Preise (Mitglieder) Saison 2026/2027": category 1, seat, Vollzahler 58,00 (information page on the ticket host) `[shop host]` |
| `prices:512` | Q | 1. FC Heidenheim 1846 | confirmed | **correct** | FCH4 | Stehplätze: 180 euro Vollzahler; page shows 2026/27 |
| `prices:26` | R | 1. FC Nürnberg | unverified | **cannot verify** | N7 | fcn.de closed by robots.txt, as rules:19 |
| `prices:959` | Q+ | Hertha BSC | confirmed | **correct** | BSC14 | blocks Q-T and 34-41 of the Ostkurve: single price 210 euro; FAQ for 2026/27 |
| `prices:642` | Q | Borussia Mönchengladbach | confirmed | **correct** | BMG12 | "Stehplatztickets kosten bei allen Heimspielen einheitlich 17 Euro"; notice for 2026/27 |
| `prices:611` | Q | Bayer 04 Leverkusen | confirmed | **correct** | LEV10 | PREISE (B), Kat. VI: 17 / 14 (ermäßigt) / 9; graphic headed 2026/27 |
| `prices:174` | R | SV Elversberg | confirmed | **correct** | E1 | "Preise Dauerkarten 1. Bundesliga 2026/2027", Stehplatz: 252,00 / 222,00 / 84,00 (Kind) |

### Fixes

None. No page stated something other than its row, no tag had to be
lowered or raised, and no checked date was changed (a checked date is
moved only for a stale row).

### Price basis

Asked for every club with a price row in the sample: does a page of the
club say whether its prices include VAT or booking fees? The price pages
themselves and, where a source record exists, the club's ticket terms
were searched for VAT and fee wording (the terms of Mainz, Heidenheim,
Bochum, Magdeburg, Leverkusen, Mönchengladbach, Schalke, Hertha and
Darmstadt in a run of their own).

- **Dortmund** is the only club whose page states VAT: "Alle Preise inkl.
  19 % MwSt." (BVB1). Its 29 rows already carry `incl-vat-excl-fees`;
  confirmed, nothing to change.
- **No other club got a basis; every other row stays `unknown`.** The
  basis values all need a statement on VAT, and none of these pages makes
  one. What they do say, for Alexandru to judge:
  - 1. FC Union Berlin (FCU1): "Alle Preise sind Endpreise. Tageskarten
    an der Tageskasse zzgl. 2,00€ pro Ticket Bearbeitungsgebühr"; for
    season tickets "ggf. zusätzlich 6,95 Euro Versand-/Hinterlegungs- und
    Bearbeitungsgebühr". "Endpreise" was **not** read as "includes VAT":
    that would be an inference.
  - SSC Napoli (SN1): "Al prezzo di vendita saranno applicate le
    commissioni di servizio" (fees come on top; VAT not stated).
  - SV Elversberg (E1): a system fee of 2 euro in the online shop (VAT
    not stated).
  - SV Darmstadt 98 (SVD3): a system and handling fee of 4,90 euro for a
    season-ticket renewal (VAT not stated).
  - The terms of Mainz, Heidenheim, Leverkusen and Hertha say only that
    the club may charge shipping and a service or presale fee, and name
    VAT only in the price-change clause; the terms of Bochum, Magdeburg,
    Mönchengladbach, Schalke and Darmstadt have no VAT wording at all.
  - Not readable: Bayern, Nürnberg (hosts closed), KSC (price lists gone),
    Inter (source address cut off).

### Hosts and pages that stopped the audit

- **fcn.de**: robots.txt has groups for ClaudeBot and anthropic-ai with
  `Disallow: /`. Closed; `rules:19`, `prices:26`.
- **fcbayern.com**: robots.txt did not answer (timeout). Closed, not
  retried; `prices:8`.
- **inter.it**: robots.txt is open, but the terms of use
  (`/it/termini-e-condizioni`) forbid "utilizzare robot, crawler e
  applicazioni simili per raccogliere e analizzare i Contenuti" and
  sending automated requests. Closed after the notice was read, no content
  page opened; `phases:16`, `rules:40`. **For Alexandru:** 7 source
  records point at inter.it, and under this wording none of them can be
  re-read by a probe.
- **ksc.de was relaunched.** The category-A price list
  (`/fileadmin/Ticketing/Preislisten_Tageskarten_26-27_KAT-A.pdf`, K2)
  answers HTTP 404; the day-ticket page (K1) and the ATGB page (K13) now
  both show one general ticket page; the match-report address K8 shows a
  news overview. The new page links its price lists on `a.storyblok.com`,
  whose robots.txt answers HTTP 403, so they were not read. `prices:82`
  and `demand:10` cannot be verified. **16 source records point at
  ksc.de** and were written before the relaunch; the 48 KSC price rows
  and the KSC rules need new addresses, by hand.
- **meinka.de** (second source of `demand:10`): robots.txt answered HTTP
  508 and the landing page showed no notice. Not read.
- **service.vfb.de** (`rules:76`): the help page lists questions whose
  answers appear only after a click and have no address; nothing was
  clicked.
- **calciomercato.com, goal.com** (`rules:41`, `prices:55`): the source
  records I16 and I12 hold an address cut short with "…"; nothing to
  open.

### Decisions the auditor took, for Alexandru to confirm or overturn

1. **Group Q+.** Wolfsburg, Cottbus, Hertha, Union, HSV and Kiel are in
   neither list of the brief; they are counted with the queue and shown
   separately.
2. **Terms and information pages on ticket hosts** were re-read at the
   exact address of the source record (7 rows, marked above): Schalke's
   terms and price page, Frankfurt's terms, Kaiserslautern's terms and
   the Strasbourg terms PDF. No shop listing, cart or login was opened.
   If "shops are not opened" is meant to cover these pages too, the 7
   rows become "cannot verify" and nothing else changes.
3. **Bot wording in ticket terms.** The terms of Schalke, Frankfurt and
   Kaiserslautern were held by the probe because they contain bot or
   "automatic" wording. Read by hand, the wording bans buying tickets
   with automated tools ("BOT-Käufe") and describes automatic renewal;
   it says nothing about reading the page. Judged open.
4. **heidelberg24.de** reserves "kommerzielles Text- und Data-Mining"
   under § 44b UrhG; its robots.txt allows Claude-User. One article was
   read for a private fact check and only its key-word paragraphs were
   posted, not the first 3000 characters.
5. **ticketing.schalke04.de** has no start page that is not the shop, so
   its notice links were taken from the price page itself, the notice
   was read, then the page.
6. **service.vfb.de and wirlilien.sv98.de** show no notice of their own;
   they were read under the notice of www.vfb.de and www.sv98.de.
7. **"Photo ID".** `rules:218` (Mainz) and `rules:201` (Freiburg) say an
   official photo ID must be carried; both terms say "geeignetes amtliches
   Identifikationsdokument (z.B. Personalausweis oder Reisepass)". Counted
   as correct, because both examples are photo documents; the terms do not
   use the word.
8. **`rules:347` (Köln)** is confirmed by a document dated 19 November
   2025. It falls out of the 12-month window on 19 November 2026, five
   days after this audit.
9. **`rules:76` (VfB)** is tagged `confirmed` with an empty season cell
   and rests on an undated help page. It could not be read, so it has no
   verdict, but under the tag policy of 28 October it looks too strong.
