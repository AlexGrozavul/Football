# Founding queue

One table of the clubs whose founding date and main supporters group a session researches, in the order a session works through it. The queue only says which club is next; the data itself is in `data/club-founding.csv` (hand-written, conventions in `docs/claude/conventions.md` under "Founding data research").

## How a session uses this file

- Take the next 6 rows whose status is `pending`, in the order of the table.
- When finished, set each of the six to `done` (or `blocked: reason`) with the PR number and the date; notes say what was written (club row, supporters row, tags) and what was not found.
- Run only one session at a time on this file.

## How this table was built (2026-11-06)

- Clubs: every German club of tier 1, 2 and 3 for 2026/27, and RC Strasbourg Alsace. The two reserve sides on the map (VfB Stuttgart II, TSG 1899 Hoffenheim II) are not in the queue (no rows for them, conventions "Founding data research").
- League and order for tiers 1 and 2: copied from `docs/claude/ticket-queue.md` (2026/27 fixtures joined through `data/clubs/fixture-links.json`), rows 1 to 36 in that table's order.
- 3. Liga: the 2026/27 teams of `data/fixtures/openligadb-bl3.json`, joined through `data/clubs/fixture-links.json` (20 clubs; tier 3 in `data/clubs/DE.json` for all 20; the two reserve sides removed). They are not in the ticket queue, so they come after rows 1 to 36, by straight-line distance from Leonberg (48.8014 N, 9.0131 E), nearest first, coordinates from `data/clubs/DE.json`.
- Strasbourg is not in the ticket queue either, so it was placed with the 3. Liga clubs by the same distance rule (96 km, coordinates from `data/clubs/FR.json`). Distances were used for ordering only and are not stored.
- **Re-ordered 2026-11-08 (batch 2)**: the order above was wrong for the queue's purpose. Copying the ticket queue's order brought along that table's own rule (its `done` and `redo` rows first, alphabetical by name), so rows 1 to 11 were alphabetical and batch 1 took six clubs that were not the nearest. **Order now: rows already `done` or `blocked` keep their place at the top; every `pending` row follows by straight-line distance from Leonberg (48.8014 N, 9.0131 E), nearest first, all leagues mixed**, coordinates from `data/clubs/DE.json` and `data/clubs/FR.json`, unrounded (Hoffenheim 49.5 km comes before Karlsruhe 50.1 km, Heidenheim 83.9 km before Waldhof Mannheim 84.0 km). A session keeps this rule when it re-numbers.
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
| 7 | Q4512 | VfB Stuttgart | Bundesliga | done | #200 | 2026-11-08 | club row confirmed (club anniversary page). Year only: Commando Cannstatt 1997, 1997, https://de.wikipedia.org/wiki/VfB_Stuttgart, called the main group: yes (Wikipedia "gilt als größte Ultras-Gruppierung in der Cannstatter Kurve"; 90min.de: "Gründung im März 1997", month only); no row |
| 8 | Q692755 | SG Sonnenhof Großaspach | 3. Liga | done | #200 | 2026-11-08 | club row confirmed (club history page). No main group: no group named; the club page names only its first fan club, "Projekt Waldameise" |
| 9 | Q22707 | TSG 1899 Hoffenheim | Bundesliga | done | #200 | 2026-11-08 | club row unverified (Wikipedia only; tsg-hoffenheim.de robots.txt HTTP 403; heidelberg24.de, bundesliga.com, worldfootball.net name Claude crawlers). No main group: Young Boyz 07 (Wikipedia: "Fangruppe", source of a fan friendship), Zwinger-Club (Wikipedia: "erster Fanclub"); none called the main one |
| 10 | Q105853 | Karlsruher SC | 2. Bundesliga | done | #200 | 2026-11-08 | club row confirmed: 16 October 1952, the merger date the club chronicle gives; predecessor KFC Phönix 6 June 1894 is in basis only (which date is the club's: Alexandru's call). No main group: ULTRA1894 (Wikipedia: alliance of four groups since 2009, "keine eigenständige Gruppe"), Phönix Sons 1999, Rheinfire 2002, Armata Fidelis 2003, Wild Boys 2004; Supporters Karlsruhe 1986 e. V. (fan project, about 2700 members) |
| 11 | Q162251 | 1. FC Heidenheim 1846 | 2. Bundesliga | done | #200 | 2026-11-08 | club row confirmed: 1 January 2007, the club page's founding of 1. FC Heidenheim 1846 (15 June 2007, effective 1 January; DFB agrees); 1846 is the tradition year, no day (which date is the club's: Alexandru's call). No main group: Unitas Aquileiae (Wikipedia: "Ultra-Gruppierung", 2014 merger), Fanatico Boys (Wikipedia: "die größte Ultra-Gruppierung neben Unitas Aquileiae"), Hellenstein Supporters 2004 ("Mutter der organisierten Heidenheimer Fanszene") |
| 12 | Q170134 | SV Waldhof Mannheim | 3. Liga | done | #200 | 2026-11-08 | club row unverified (DFB data center 11 April 1907, Wikipedia agrees; RSSSF 9 April 1907; club page year only). No main group: Pro Waldhof e. V. (club fan page: "Fan-Dachverband" of the official fan clubs); no ultra group named |
| 13 | Q126334 | RC Strasbourg Alsace | Ligue 1 | done | #201 | 2026-11-08 | no club row: club history page gives 1906 only (FC Neudorf); French Wikipedia infobox 1 January 1906, prose 1906, not written (1 January looks like a year-only placeholder: Alexandru's call); club site forbids reproduction. No main group: Ultra Boys 90 (fr Wikipedia: founded 1990, 450 members 2007-08), Kop Ciel et Blanc (2000; "le plus grand des cinq autres groupes"), Club Central des Supporters ("le plus ancien", winter 1953); ub90.com is now a parked domain behind a bot check (stop) |
| 14 | Q479351 | SV Darmstadt 98 | 2. Bundesliga | done | #201 | 2026-11-08 | club row confirmed (club history page: FK Olympia 1898 founded 22 May 1898, merger with SC Darmstadt 11 November 1919; site forbids copying, no quote). No main group: Block 1898 (Wikipedia: its ultras are "hauptverantwortlich" for the support; umbrella of Usual Suspects, Deliquents, Ultrà de Lis, Underdogs; formed season 2012/13), Die Siedler (Wikipedia: "Fanclub mit den meisten Mitgliedern", 120 members) |
| 15 | Q106394 | SC Freiburg | Bundesliga | done | #201 | 2026-11-08 | no club row: club history pages and statutes give 1904 only (two predecessors of 1904, Freiburger FV in March 1904; merger 1912); Wikipedia 1904; DFB club page HTTP 500. No main group: Corrillo, Immer wieder Freiburg, Synthesia Ultras (club fan page: the ultra movement "besteht aus" these three), SC Freiburg Fangemeinschaft e. V. ("Dachverband" of the fan clubs), Supporters Crew Freiburg (2005, "Interessengemeinschaft") |
| 16 | Q535785 | Würzburger Kickers | 3. Liga | done | #201 | 2026-11-08 | club row confirmed (e.V. history page: 17 November 1907; DFB data center and Wikipedia agree). No main group: Wikipedia names only the B-Block, "Kern der aktiven Fanszene" (a stand, not a group) |
| 17 | Q692691 | SV Elversberg | Bundesliga | done | #201 | 2026-11-08 | no club row: club history page gives 1907 only (FC Germania; dissolved 1914, refounded 1918, today's SV split off 1952); Wikipedia 1907; DFB data center 01.01.1907, not written (year-only placeholder: Alexandru's call). No group named: club pages list official fan clubs and fan officers only; Wikipedia names none |
| 18 | Q310621 | SV Wehen Wiesbaden | 3. Liga | done | #201 | 2026-11-08 | no club row: club history page and statutes (Stand 27.11.2023) give 1926 only; DFB data center 01.01.1926 and Wikipedia infobox 1 January 1926 agree but look like a year-only placeholder, not written (Alexandru's call). No main group: Herzenssache 1926 e.V. (club fan page: "Dachverband für alle Fans"), Halbergtramps e.V. (2000, "einer der ersten offiziellen Fanclubs") |
| 19 | Q157463 | 1. FC Saarbrücken | 3. Liga | pending |  |  |  |
| 20 | Q153539 | SpVgg Greuther Fürth | 2. Bundesliga | pending |  |  |  |
| 21 | Q170117 | FC Ingolstadt 04 | 3. Liga | pending |  |  |  |
| 22 | Q265570 | SSV Jahn Regensburg | 3. Liga | pending |  |  |  |
| 23 | Q695008 | FC Viktoria Köln | 3. Liga | pending |  |  |  |
| 24 | Q310608 | SC Fortuna Köln | 3. Liga | pending |  |  |  |
| 25 | Q104770 | 1. FC Köln | Bundesliga | pending |  |  |  |
| 26 | Q104761 | Bayer 04 Leverkusen | Bundesliga | pending |  |  |  |
| 27 | Q153535 | Alemannia Aachen | 3. Liga | pending |  |  |  |
| 28 | Q151747 | Fortuna Düsseldorf | 3. Liga | pending |  |  |  |
| 29 | Q41420 | Borussia Dortmund | Bundesliga | pending |  |  |  |
| 30 | Q101959 | Borussia Mönchengladbach | Bundesliga | pending |  |  |  |
| 31 | Q105861 | VfL Bochum | 2. Bundesliga | pending |  |  |  |
| 32 | Q160532 | SC Paderborn 07 | Bundesliga | pending |  |  |  |
| 33 | Q154293 | MSV Duisburg | 3. Liga | pending |  |  |  |
| 34 | Q155218 | Rot-Weiss Essen | 3. Liga | pending |  |  |  |
| 35 | Q32494 | FC Schalke 04 | Bundesliga | pending |  |  |  |
| 36 | Q666010 | SC Verl | 3. Liga | pending |  |  |  |
| 37 | Q105844 | Arminia Bielefeld | 2. Bundesliga | pending |  |  |  |
| 38 | Q316865 | Preußen Münster | 3. Liga | pending |  |  |  |
| 39 | Q702455 | RB Leipzig | Bundesliga | pending |  |  |  |
| 40 | Q160530 | VfL Osnabrück | 2. Bundesliga | pending |  |  |  |
| 41 | Q33748 | Hannover 96 | 2. Bundesliga | pending |  |  |  |
| 42 | Q154053 | Eintracht Braunschweig | 2. Bundesliga | pending |  |  |  |
| 43 | Q537301 | TSV Havelse | 3. Liga | pending |  |  |  |
| 44 | Q155730 | 1. FC Magdeburg | 2. Bundesliga | pending |  |  |  |
| 45 | Q141931 | Dynamo Dresden | 2. Bundesliga | pending |  |  |  |
| 46 | Q101859 | VfL Wolfsburg | 2. Bundesliga | pending |  |  |  |
| 47 | Q819400 | SV Meppen | 3. Liga | pending |  |  |  |
| 48 | Q51976 | Werder Bremen | Bundesliga | pending |  |  |  |
| 49 | Q107818 | Energie Cottbus | 2. Bundesliga | pending |  |  |  |
| 50 | Q102720 | Hertha BSC | 2. Bundesliga | pending |  |  |  |
| 51 | Q141971 | 1. FC Union Berlin | Bundesliga | pending |  |  |  |
| 52 | Q6463 | FC St. Pauli | 2. Bundesliga | pending |  |  |  |
| 53 | Q51974 | Hamburger SV | Bundesliga | pending |  |  |  |
| 54 | Q157828 | Holstein Kiel | 2. Bundesliga | pending |  |  |  |
| 55 | Q142005 | Hansa Rostock | 3. Liga | pending |  |  |  |
