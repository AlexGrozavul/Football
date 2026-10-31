# Ticket queue

One table of every German club of tier 1 and tier 2 for 2026/27, in the order a session works through it. The queue only says which club is next; it holds no ticket rule, date or deadline (CLAUDE.md rules 1 and 2).

## How a session uses this file

- Take the first row whose status is `pending`, in the order of the table.
- When the club is finished, set its status to `done` and fill PR (the pull request number), date and the counts per tag (confirmed, unverified, inferred) in notes.
- If the club's own host stops the probe, set the status to `blocked: reason` and leave the row; do not retry in the same session.
- Run only one session at a time on this file.

## How this table was built (2026-10-28)

- League 2026/27: the 2026/27 fixtures in `data/fixtures/` (`BL1.json` from football-data.org for the Bundesliga, `openligadb-bl2.json` from OpenLigaDB for the 2. Bundesliga), joined to the club file through `data/clubs/fixture-links.json`. The club file's tier (`data/clubs/DE.json`) agreed for all 36 clubs.
- Club key: the Wikidata Q-id, the `id` in `data/clubs/DE.json` and `clubQid` in the ticket files.
- Status: `done` = ticket rows sourced from the club's own 2026/27 pages; `redo` = ticket rows from older research; `pending` = no ticket rows in any `data/club-ticket*.csv`; `blocked` = none yet. A `redo` row is not picked up by the rule above.
- Order: `done` and `redo` first, alphabetical by name; then `pending` by distance from Leonberg, nearest first.
- Distance: straight line from Leonberg (48.8014 N, 9.0131 E, `settings.home` in `data/football-rules.json`), rounded to km. For ordering only; it is never shown in the app.

## Queue

| order | club key | name | league 2026/27 | km from Leonberg | status | PR | date | notes |
|---|---|---|---|---|---|---|---|---|
| 1 | Q8466 | 1. FC Kaiserslautern | 2. Bundesliga | 114 | done |  |  | ticket rows checked up to 2026-10-26 |
| 2 | Q15786 | 1. FC Nürnberg | 2. Bundesliga | 169 | redo |  |  | ticket rows checked up to 2026-09-23 |
| 3 | Q105254 | 1. FSV Mainz 05 | Bundesliga | 143 | done |  |  | ticket rows checked up to 2026-10-27 |
| 4 | Q38245 | Eintracht Frankfurt | Bundesliga | 143 | done |  |  | ticket rows checked up to 2026-10-26 |
| 5 | Q97905916 | FC Augsburg | Bundesliga | 148 | done |  |  | ticket rows checked up to 2026-10-27 |
| 6 | Q15789 | FC Bayern München | Bundesliga | 203 | redo |  |  | ticket rows checked up to 2026-09-19 |
| 7 | Q105853 | Karlsruher SC | 2. Bundesliga | 50 | redo |  |  | ticket rows checked up to 2026-10-06 |
| 8 | Q106394 | SC Freiburg | Bundesliga | 123 | done |  |  | ticket rows checked up to 2026-10-27 |
| 9 | Q153539 | SpVgg Greuther Fürth | 2. Bundesliga | 163 | done |  |  | ticket rows checked up to 2026-10-26 |
| 10 | Q692691 | SV Elversberg | Bundesliga | 149 | done |  |  | ticket rows checked up to 2026-10-26 |
| 11 | Q4512 | VfB Stuttgart | Bundesliga | 16 | redo |  |  | ticket rows checked up to 2026-10-07 |
| 12 | Q22707 | TSG 1899 Hoffenheim | Bundesliga | 50 | blocked: robots.txt 403 | #173 | 2026-10-28 | robots.txt of tsg-hoffenheim.de and www.tsg-hoffenheim.de answered HTTP 403; no page read; 0 confirmed, 0 unverified, 0 inferred; see open-problems.md |
| 13 | Q162251 | 1. FC Heidenheim 1846 | 2. Bundesliga | 84 | done | #174 | 2026-10-28 | 33 confirmed (14 rules, 18 season-ticket prices, 1 demand), 12 unverified, 0 inferred; day-ticket prices only in a price-list rule (presale and box-office prices, schema gap); see open-problems.md |
| 14 | Q479351 | SV Darmstadt 98 | 2. Bundesliga | 120 | done | #175 | 2026-10-29 | 81 confirmed (20 rules, 32 day-ticket and 28 season-ticket prices, 1 demand), 13 unverified, 0 inferred; which home games carry the 5-euro top-game surcharge is not stated; see open-problems.md |
| 15 | Q104770 | 1. FC Köln | Bundesliga | 282 | done | #176 | 2026-10-29 | 13 confirmed (12 rules, 1 demand), 19 unverified (18 rules, 1 demand), 0 inferred; no price row: the 2026/27 price list is a picture; the day-ticket terms carry no printed date; see open-problems.md |
| 16 | Q104761 | Bayer 04 Leverkusen | Bundesliga | 287 | done | #177 | 2026-10-30 | 34 confirmed (11 rules, 23 day-ticket prices), 20 unverified (19 rules, 1 demand), 0 inferred; which home games use price set B beyond VfB and Paderborn is not stated; the ATGB carry no printed date; see open-problems.md |
| 17 | Q41420 | Borussia Dortmund | Bundesliga | 319 | done | #178 | 2026-10-31 | 49 confirmed (20 rules, 14 day-ticket and 15 season-ticket prices), 14 unverified (13 rules, 1 demand), 0 inferred; day-ticket prices written as Bundesliga (the price table names no competition for them); 21-game season ticket incl. Champions League only in a price-list rule (schema gap); guest allocation size not stated; see open-problems.md |
| 18 | Q101959 | Borussia Mönchengladbach | Bundesliga | 324 | pending |  |  |  |
| 19 | Q105861 | VfL Bochum | 2. Bundesliga | 325 | pending |  |  |  |
| 20 | Q160532 | SC Paderborn 07 | Bundesliga | 327 | pending |  |  |  |
| 21 | Q32494 | FC Schalke 04 | Bundesliga | 336 | pending |  |  |  |
| 22 | Q105844 | Arminia Bielefeld | 2. Bundesliga | 361 | pending |  |  |  |
| 23 | Q702455 | RB Leipzig | Bundesliga | 370 | pending |  |  |  |
| 24 | Q160530 | VfL Osnabrück | 2. Bundesliga | 393 | pending |  |  |  |
| 25 | Q33748 | Hannover 96 | 2. Bundesliga | 399 | pending |  |  |  |
| 26 | Q154053 | Eintracht Braunschweig | 2. Bundesliga | 402 | pending |  |  |  |
| 27 | Q155730 | 1. FC Magdeburg | 2. Bundesliga | 415 | pending |  |  |  |
| 28 | Q141931 | Dynamo Dresden | 2. Bundesliga | 420 | pending |  |  |  |
| 29 | Q101859 | VfL Wolfsburg | 2. Bundesliga | 423 | pending |  |  |  |
| 30 | Q51976 | Werder Bremen | Bundesliga | 474 | pending |  |  |  |
| 31 | Q107818 | Energie Cottbus | 2. Bundesliga | 501 | pending |  |  |  |
| 32 | Q102720 | Hertha BSC | 2. Bundesliga | 509 | pending |  |  |  |
| 33 | Q141971 | 1. FC Union Berlin | Bundesliga | 518 | pending |  |  |  |
| 34 | Q6463 | FC St. Pauli | 2. Bundesliga | 533 | pending |  |  |  |
| 35 | Q51974 | Hamburger SV | Bundesliga | 536 | pending |  |  |  |
| 36 | Q157828 | Holstein Kiel | 2. Bundesliga | 622 | pending |  |  |  |
