# Founding queue

One table of the clubs whose founding date and main supporters group a session researches, in the order a session works through it. The queue only says which club is next; the data itself is in `data/club-founding.csv` (hand-written, conventions in `docs/claude/conventions.md` under "Founding data").

## How a session uses this file

- Take the next 6 rows whose status is `pending`, in the order of the table.
- When finished, set each of the six to `done` (or `blocked: reason`) with the PR number and the date; notes say what was written (club row, supporters row, tags) and what was not found.
- Run only one session at a time on this file.

## How this table was built (2026-11-06)

- Clubs: every German club of tier 1, 2 and 3 for 2026/27, and RC Strasbourg Alsace. The two reserve sides on the map (VfB Stuttgart II, TSG 1899 Hoffenheim II) are not in the queue (no rows for them, conventions "Founding data").
- League and order for tiers 1 and 2: copied from `docs/claude/ticket-queue.md` (2026/27 fixtures joined through `data/clubs/fixture-links.json`), rows 1 to 36 in that table's order.
- 3. Liga: the 2026/27 teams of `data/fixtures/openligadb-bl3.json`, joined through `data/clubs/fixture-links.json` (20 clubs; tier 3 in `data/clubs/DE.json` for all 20; the two reserve sides removed). They are not in the ticket queue, so they come after rows 1 to 36, by straight-line distance from Leonberg (48.8014 N, 9.0131 E), nearest first, coordinates from `data/clubs/DE.json`.
- Strasbourg is not in the ticket queue either, so it was placed with the 3. Liga clubs by the same distance rule (96 km, coordinates from `data/clubs/FR.json`). Distances were used for ordering only and are not stored.
- Club key: the Wikidata Q-id, the `id` in the club files and `clubQ` in `data/club-founding.csv`.

## Queue

| order | club key | name | league | status | PR | date | notes |
|---|---|---|---|---|---|---|---|
| 1 | Q8466 | 1. FC Kaiserslautern | 2. Bundesliga | done | #192 | 2026-11-06 | club row confirmed (statutes PDF); main group Generation Luzifer, founding year only (1998) |
| 2 | Q15786 | 1. FC Nürnberg | 2. Bundesliga | done | #192 | 2026-11-06 | club row unverified (Wikipedia only; fcn.de robots.txt bars Claude bots, treated as a stop); no main group named |
| 3 | Q105254 | 1. FSV Mainz 05 | Bundesliga | done | #192 | 2026-11-06 | club row confirmed (club chronicle); no main group named |
| 4 | Q38245 | Eintracht Frankfurt | Bundesliga | done | #192 | 2026-11-06 | club row confirmed (e.V. club page); no main group named |
| 5 | Q97905916 | FC Augsburg | Bundesliga | done | #192 | 2026-11-06 | club row confirmed (club history page); main group Legio Augusta, founding year only (2007) |
| 6 | Q15789 | FC Bayern München | Bundesliga | done | #192 | 2026-11-06 | club row unverified (Wikipedia only; fcbayern.com robots.txt no answer twice); no main group named |
| 7 | Q105853 | Karlsruher SC | 2. Bundesliga | pending |  |  |  |
| 8 | Q106394 | SC Freiburg | Bundesliga | pending |  |  |  |
| 9 | Q153539 | SpVgg Greuther Fürth | 2. Bundesliga | pending |  |  |  |
| 10 | Q692691 | SV Elversberg | Bundesliga | pending |  |  |  |
| 11 | Q4512 | VfB Stuttgart | Bundesliga | pending |  |  |  |
| 12 | Q22707 | TSG 1899 Hoffenheim | Bundesliga | pending |  |  |  |
| 13 | Q162251 | 1. FC Heidenheim 1846 | 2. Bundesliga | pending |  |  |  |
| 14 | Q479351 | SV Darmstadt 98 | 2. Bundesliga | pending |  |  |  |
| 15 | Q104770 | 1. FC Köln | Bundesliga | pending |  |  |  |
| 16 | Q104761 | Bayer 04 Leverkusen | Bundesliga | pending |  |  |  |
| 17 | Q41420 | Borussia Dortmund | Bundesliga | pending |  |  |  |
| 18 | Q101959 | Borussia Mönchengladbach | Bundesliga | pending |  |  |  |
| 19 | Q105861 | VfL Bochum | 2. Bundesliga | pending |  |  |  |
| 20 | Q160532 | SC Paderborn 07 | Bundesliga | pending |  |  |  |
| 21 | Q32494 | FC Schalke 04 | Bundesliga | pending |  |  |  |
| 22 | Q105844 | Arminia Bielefeld | 2. Bundesliga | pending |  |  |  |
| 23 | Q702455 | RB Leipzig | Bundesliga | pending |  |  |  |
| 24 | Q160530 | VfL Osnabrück | 2. Bundesliga | pending |  |  |  |
| 25 | Q33748 | Hannover 96 | 2. Bundesliga | pending |  |  |  |
| 26 | Q154053 | Eintracht Braunschweig | 2. Bundesliga | pending |  |  |  |
| 27 | Q155730 | 1. FC Magdeburg | 2. Bundesliga | pending |  |  |  |
| 28 | Q141931 | Dynamo Dresden | 2. Bundesliga | pending |  |  |  |
| 29 | Q101859 | VfL Wolfsburg | 2. Bundesliga | pending |  |  |  |
| 30 | Q51976 | Werder Bremen | Bundesliga | pending |  |  |  |
| 31 | Q107818 | Energie Cottbus | 2. Bundesliga | pending |  |  |  |
| 32 | Q102720 | Hertha BSC | 2. Bundesliga | pending |  |  |  |
| 33 | Q141971 | 1. FC Union Berlin | Bundesliga | pending |  |  |  |
| 34 | Q6463 | FC St. Pauli | 2. Bundesliga | pending |  |  |  |
| 35 | Q51974 | Hamburger SV | Bundesliga | pending |  |  |  |
| 36 | Q157828 | Holstein Kiel | 2. Bundesliga | pending |  |  |  |
| 37 | Q692755 | SG Sonnenhof Großaspach | 3. Liga | pending |  |  |  |
| 38 | Q170134 | SV Waldhof Mannheim | 3. Liga | pending |  |  |  |
| 39 | Q126334 | RC Strasbourg Alsace | Ligue 1 | pending |  |  |  |
| 40 | Q535785 | Würzburger Kickers | 3. Liga | pending |  |  |  |
| 41 | Q310621 | SV Wehen Wiesbaden | 3. Liga | pending |  |  |  |
| 42 | Q157463 | 1. FC Saarbrücken | 3. Liga | pending |  |  |  |
| 43 | Q170117 | FC Ingolstadt 04 | 3. Liga | pending |  |  |  |
| 44 | Q265570 | SSV Jahn Regensburg | 3. Liga | pending |  |  |  |
| 45 | Q695008 | FC Viktoria Köln | 3. Liga | pending |  |  |  |
| 46 | Q310608 | SC Fortuna Köln | 3. Liga | pending |  |  |  |
| 47 | Q153535 | Alemannia Aachen | 3. Liga | pending |  |  |  |
| 48 | Q151747 | Fortuna Düsseldorf | 3. Liga | pending |  |  |  |
| 49 | Q154293 | MSV Duisburg | 3. Liga | pending |  |  |  |
| 50 | Q155218 | Rot-Weiss Essen | 3. Liga | pending |  |  |  |
| 51 | Q666010 | SC Verl | 3. Liga | pending |  |  |  |
| 52 | Q316865 | Preußen Münster | 3. Liga | pending |  |  |  |
| 53 | Q537301 | TSV Havelse | 3. Liga | pending |  |  |  |
| 54 | Q819400 | SV Meppen | 3. Liga | pending |  |  |  |
| 55 | Q142005 | Hansa Rostock | 3. Liga | pending |  |  |  |
