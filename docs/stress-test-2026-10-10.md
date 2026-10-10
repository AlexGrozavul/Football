# Stress test, 2026-10-10

Report only. No data file, app code or test was changed. Evidence comes from the repo's own files; nothing was fetched from the web. Full list: `docs/stress-test-findings.csv` (first 25 examples of every check, one row each, with a proposed fix; no fix applied).

## Summary: rows found (checks with a hit)

| Area | A | B | C |
|---|---|---|---|
| A Club layer | 1 (1) | 258 (12) | 883 (5) |
| B Leagues and tiers | 0 (0) | 8 (2) | 56 (3) |
| C Fixtures vs clubs | 1 (1) | 34 (4) | 1501 (3) |
| D Derbies, rivalries, friendships | 0 (0) | 7 (3) | 27 (3) |
| E Bucket list | 1 (1) | 13 (2) | 118 (3) |
| F football-rules.json | 0 (0) | 2 (1) | 0 (0) |
| G Attended matches | 3 (1) | 3 (2) | 14 (2) |
| H App wiring | 0 (0) | 0 (0) | 226 (3) |
| I Holidays and calendars | 0 (0) | 2 (2) | 0 (0) |
| **Total** | **6** | **327** | **2825** |

A = provably wrong or contradictory. B = suspicious, needs a source. C = cosmetic/housekeeping (large C counts are mostly by-design lists: 731 seed leagues, 1,452 placeholder kick-offs).

**Checks that ran and found nothing (64):** A1, A2, A3, A4, A6, A12, A19, A22, A24, A25, B1, B2b, B3b, B4, B6, C1, C2, C5, C7, C8, C12, D1, D2, D3, D4, D6, D7, D10, D14, E1, E3, E4, E5, E6, E7, E7b, E8, E9, E10, E12, F1, F2, F3, F4, G1, G2, G3, G4, G5, G6, G7, G9, G9b, H1, H1b, H2, H4, H4b, H4c, H5, H5b, I3, I4, A26 (titles are in the check list above and in the CSV `problem` column of any hit)

## Severity A

**A13 · 1 · roster-review.csv: wrong-tier where no other division confirms the club layer**  
_File: data/clubs/roster-review.csv_ · Fix: Hand tier row in clubs-manual.csv, or confirm the table is not a clean division list
- `line 494 Q99446805 CSM Olimpia Satu Mare (RO)` the league lists it at tier 2 and the map has it at tier 3 in RO - most likely a P118 left over from last season. Put 2 in the tier cell of  — our tier=3; article=2026–27 Liga II; also listed ok in: nothing else

**E11 · 1 · Dated bucket entries where the fixture files give a different date**  
_File: data/football-rules.json vs data/fixtures/*.json_ · Fix: Alexandru decides which is right (hand date wins in calendars, rule 3)
- `derby-madonnina` fixtures.date:milan=2026-11-01 differs from every fixture-file meeting of the two linked clubs — fixture dates [('SA.json', '2026-10-31', 'AC Milan', 'v', 'FC Internazionale Milano'), ('SA.json', '2027-02-14', 'FC Internazionale Milano', 'v', 'AC 

**G10 · 3 · My stats figures where the page's logic and an independent recompute disagree**  
_File: index.html attStats vs data/attended.json_ · Fix: Decide which definition is intended (e.g. count goals from the score, count second-yellow separately)
- `Goals (page counts entries in each goals list)` page 55 vs independent 68 — independent = sum of both score numbers; goals lists total 55
- `Goals per match` page 2.39 vs independent 2.96
- `Red cards (page: everything not yellow)` page 3 vs independent 1 — second-yellow cards in complete matches: 2 (page adds them to red)

**C13 · 1 · Fixture matches whose status and score contradict each other**  
_File: data/fixtures/*.json_ · Fix: Next fetch; otherwise upstream
- `PD.json match 564685` score present but status TIMED — Levante UD v Athletic Club

## My stats: page logic against an independent recompute

| figure | page | independent | result |
|---|---|---|---|
| Matches | 23 | 23 | agree |
| Goals (page counts entries in each goals list) | 55 | 68 | DISAGREE |
| Goals per match | 2.39 | 2.96 | DISAGREE |
| Penalties scored | 6 | 6 | agree |
| Stadiums (distinct) | 15 | 15 | agree |
| Cards complete for (matches) | 19 | 19 | agree |
| Yellow cards | 86 | 86 | agree |
| Red cards (page: everything not yellow) | 3 | 1 | DISAGREE |
| Cities (distinct) | 14 | 14 | agree |
| Countries (distinct) | 4 | 4 | agree |
| Competitions (distinct) | 12 | 12 | agree |
| Most-seen team | (['Germany'], 4) | (['Germany'], 4) | agree |
| Most-seen player | (['joshua kimmich'], 5) | (['joshua kimmich'], 5) | agree |
| Matches with line-ups | 21 | 21 | agree |
| Biggest crowd | (81365, ['2023-02-19-bvb-bsc']) | (81365, ['2023-02-19-bvb-bsc']) | agree |
| Smallest crowd | (300, ['2026-08-29-ucd-scm']) | (300, ['2026-08-29-ucd-scm']) | agree |

The goals gap (55 against 68) is exactly the one match with a 7-6 score and an empty goals list. The red-card gap is two `second-yellow` cards that the page counts as red. The record (W-D-L) could not be recomputed: it lives on the device.

## Severity B, by area

### A Club layer

**A5 · 2 · Identical coordinates on clubs whose venue names differ (no shared-grounds list exists in the repo; same coordinate AND same venue name is treated as a genuine shared ground)**  
_File: data/clubs/??.json_ · Fix: Confirm one ground, or correct the copied coordinate with <clear>/lat/lon · needs a source
- `(44.783333, 20.464722)` Same coordinate, different venue names — Q173009 FK Crvena zvezda (RS, tier 1) venue=Rajko Mitić Stadium; Q3063273 RFK Grafičar Beograd (RS, tier 2) venue=Rajko Mitić Stadium, auxiliary pitch
- `(43.583114, 21.338122)` Same coordinate, different venue names — Q2123289 FK Bor 1919 (RS, tier 2) venue=Stadion Mladost, Kruševac; Q843210 FK Napredak Kruševac (RS, tier 2) venue=Stadion Mladost

**A7 · 1 · Capacity under 500 or over 120,000**  
_File: data/clubs/??.json_ · Fix: Verify against a second source · needs a source
- `Q24068131 Jong FC Utrecht (NL, tier 2)` Implausible capacity per task thresholds — capacity=450 venue=Sportcomplex Zoudenbalch

**A8 · 31 · Capacity missing with no hand-row note explaining it**  
_File: data/clubs/??.json_ · Fix: Add a sourced capacity or a note-only row saying why it is blank · needs a source
- `Q15843660 SV Rödinghausen (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Häcker-Wiehenstadion
- `Q16645947 VfL Wolfsburg II (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=AOK Stadion
- `Q17321080 DJK Vilzing (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Manfred Zollner Stadion
- `Q2207914 SSV Jeddeloh (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Haskamp Arena
- `Q2208389 SV Eichede (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Ernst-Wagener-Stadion
- `Q479321 FV Illertissen (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Vöhlinstadion
- `Q479340 TSV 1896 Rain (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Georg-Weber-Stadion
- `Q479366 VfB Auerbach (DE, tier 4)` No capacity and no clubs-manual.csv note/clear for it — venue=Arena zur Vogtlandweide
- … 23 more (25 are in the CSV)

**A10 · 10 · capacity-review.csv: unresolved rows where Wikidata and OpenStreetMap figures differ (file has no decision column, so every row is unresolved)**  
_File: data/clubs/capacity-review.csv_ · Fix: Judge each: keep, or record a clubs-manual.csv row with every figure in the note · needs a source
- `line 22 Q5424829 FC Augsburg II (DE)` sources differ by 6% — Wikidata=26443 OSM=28000 venue=
- `line 23 Q153539 SpVgg Greuther Fürth (DE)` sources differ by 8% — Wikidata=16626 OSM=18000 venue=
- `line 24 Q170157 Wuppertaler SV (DE)` sources differ by 9% — Wikidata=23067 OSM=21000 venue=
- `line 26 Q460448 Cádiz Club de Fútbol (ES)` sources differ by 17% — Wikidata=20724 OSM=25033 venue=
- `line 27 Q7156 FC Barcelona (ES)` sources differ by 37% — Wikidata=62652 OSM=99354 venue=
- `line 29 Q126334 RC Strasbourg Alsace (FR)` sources differ by 10% — Wikidata=26109 OSM=29000 venue=
- `line 30 Q182876 AJ Auxerre (FR)` sources differ by 13% — Wikidata=18541 OSM=21379 venue=
- `line 31 Q192071 Football Club de Nantes (FR)` sources differ by 7% — Wikidata=35318 OSM=38004 venue=
- … 2 more (10 are in the CSV)

**A13b · 3 · roster-review.csv: wrong-tier where another division article lists the same club as ok (club appears in two rosters; probably a reserve side joined to its parent)**  
_File: data/clubs/roster-review.csv_ · Fix: Add a roster-links-manual.csv line for the reserve side · needs a source
- `line 168 Q155730 1. FC Magdeburg (DE)` the league lists it at tier 4 and the map has it at tier 2 in DE - most likely a P118 left over from last season. Put 4 in the tier cell of  — our tier=2; article=2026–27 Regionalliga; also listed ok in: ['2. Bundesliga']
- `line 169 Q6463 FC St. Pauli (DE)` the league lists it at tier 4 and the map has it at tier 2 in DE - most likely a P118 left over from last season. Put 4 in the tier cell of  — our tier=2; article=2026–27 Regionalliga; also listed ok in: ['2. Bundesliga']
- `line 170 Q160532 SC Paderborn 07 (DE)` the league lists it at tier 4 and the map has it at tier 1 in DE - most likely a P118 left over from last season. Put 4 in the tier cell of  — our tier=1; article=2026–27 Regionalliga; also listed ok in: ['Bundesliga']

**A14 · 44 · roster-review.csv: extra-not-in-roster (on the map, not in the current division)**  
_File: data/clubs/roster-review.csv_ · Fix: skip/rename/tier per the Hermannstadt standard (Alexandru decides) · needs a source
- `line 171 Q797022 BSV Rehden (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 172 Q176850 Bahlinger SC (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 173 Q16536906 Bayer 04 Leverkusen II (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 174 Q692704 Berliner AK 07 (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 175 Q16559523 Eintracht Braunschweig II (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 176 Q666000 FC Bayern Alzenau (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 177 Q5424977 FC Ingolstadt 04 II (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 178 Q831887 FC Ismaning (DE)` the map has this club at this tier and the league does not list it. Either its P118 is stale and it belongs at another tier, or the league article lin — tier=4 league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- … 36 more (25 are in the CSV)

**A15 · 42 · roster-review.csv: missing-from-wikidata (in the division, not on the map)**  
_File: data/clubs/roster-review.csv_ · Fix: Hand-named fallback row in clubs-manual.csv with country+tier · needs a source
- `line 141 Q162213 1. FC Bocholt (DE)` Wikidata gives it only leagues Q1476473, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 142 Q162366 1. FC Phönix Lübeck (DE)` Wikidata gives it no league at all, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 143 Q162394 1. FC Schweinfurt 05 (DE)` Wikidata gives it only leagues Q15735, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 144 Q666155 BFC Preussen (DE)` Wikidata gives it only leagues Q821097, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 145 Q479276 Bremer SV (DE)` Wikidata gives it only leagues Q475887, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 146 Q468738 Eimsbütteler TV (DE)` Wikidata gives it no league at all, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 147 Q14118284 Eintracht Frankfurt II (DE)` Wikidata marks this club dissolved (P576) and the club query excludes dissolved clubs, so it can never reach the map. Either Wikidata is wrong or the  — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- `line 148 Q325270 FC Astoria Walldorf (DE)` Wikidata gives it only leagues Q878642, none of them in data/league-tiers.csv, so the club query never sees it. Add a row to data/clubs-manual.csv — league=Regionalliga Suedwest, Regionalliga Nordost, Regionalliga West, Regionalliga Bayern, Regionalliga Nord
- … 34 more (25 are in the CSV)

**A16 · 35 · roster-review.csv: unplaced-no-coordinates**  
_File: data/clubs/roster-review.csv_ · Fix: Place via coordinate-review route · needs a source
- `line 395 Q3292651 A.P.S. Zakynthos (GR)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Super League 2 (Greece)
- `line 396 Q16845757 A.S. Nestos Chrysoupolis (GR)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Super League 2 (Greece)
- `line 397 Q12872753 Hellas Syros F.C. (GR)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Super League 2 (Greece)
- `line 432 Q650365 Carrarese Calcio (IT)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Serie B
- `line 490 Q39487082 CSA Steaua București (RO)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Liga a II-a
- `line 491 Q66424141 CSC 1599 Șelimbăr (RO)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Liga a II-a
- `line 492 Q18539440 CSL Ștefăneștii de Jos (RO)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Liga a II-a
- `line 493 Q55593565 SC Popești-Leordeni (RO)` the club query can see this club - its league is mapped - but neither it nor its ground has a position, so it is dropped at the coordinates gate. This — league=Liga a II-a
- … 27 more (25 are in the CSV)

**A20 · 79 · coordinate-review.csv: unresolved rows (no _reviewed stamp) and not yet on the map**  
_File: data/clubs/coordinate-review.csv_ · Fix: Judge and record in coordinate-reviews.csv · needs a source
- `line 2 Q461162 Brigittenauer AC (AT)` ambiguous - 5 grounds match equally well, nothing here can choose between them
- `line 3 Q683981 FC Wien (AT)` ambiguous - 4 grounds match equally well, nothing here can choose between them
- `line 4 Q684205 SC Wacker Wien (AT)` ambiguous - 4 grounds match equally well, nothing here can choose between them
- `line 5 Q459929 SK Admira Wien (AT)` ambiguous - 4 grounds match equally well, nothing here can choose between them
- `line 9 Q430940 Vienna Cricket and Football-Club (AT)` no match - nothing in the club's name is the name of a place OpenStreetMap knows, and no ground names the club
- `line 11 Q566179 Torgelower FC Greif (DE)` ambiguous - 3 grounds match equally well, nothing here can choose between them
- `line 12 Q7671747 TSV 1860 München II (DE)` ambiguous - reserve team, so the town in the name is the first team's town and says nothing about which of the
- `line 13 Q21175456 Teutonia Watzenborn-Steinberg (DE)` no match - every candidate is more than 30 km from Pohlheim, the club's town in Wikidata, so each one is some 
- … 71 more (25 are in the CSV)

**A21 · 7 · coordinate-review.csv rows still open although coordinate-reviews.csv holds a decision for the same club**  
_File: data/clubs/coordinate-review.csv_ · Fix: Next monthly run stamps it
- `line 2 Q461162 Brigittenauer AC` decision rejected 2026-09-27 — review row _reviewed blank
- `line 3 Q683981 FC Wien` decision rejected 2026-09-27 — review row _reviewed blank
- `line 4 Q684205 SC Wacker Wien` decision rejected 2026-09-27 — review row _reviewed blank
- `line 5 Q459929 SK Admira Wien` decision rejected 2026-09-27 — review row _reviewed blank
- `line 9 Q430940 Vienna Cricket and Football-Club` decision rejected 2026-09-27 — review row _reviewed blank
- `line 15 Q3590859 équipe fédérale Reims-Champagne` decision rejected 2026-09-29 — review row _reviewed blank
- `line 16 Q1514915 Sporting Club fivois` decision rejected 2026-09-29 — review row _reviewed blank

**A5b · 2 · Shared ground (same coordinate, same venue name) with different capacities on the clubs**  
_File: data/clubs/??.json_ · Fix: Give one figure to the ground (hand rows) · needs a source
- `(48.980485, 9.393005)` Clubs on the same coordinate and venue name carry different capacities — VfB Stuttgart II=10001; SG Sonnenhof Großaspach=10000
- `(51.345833, 12.348056)` Clubs on the same coordinate and venue name carry different capacities — RB Leipzig II=42000; RB Leipzig=47800

**A27 · 2 · clubs-manual.csv rows with data for a club that is not on the map (the row has no effect; the guard should have rejected or the fallback should have surfaced it)**  
_File: data/clubs-manual.csv_ · Fix: Check whether the roster/hand-named fallback failed on the last build
- `clubs-manual.csv line 21 Q7671747 TSV 1860 München II` Hand row names a club that is not in any club file (and is not a skip row) — country DE tier 5
- `clubs-manual.csv line 180 Q1323373 FK Zemun` Hand row names a club that is not in any club file (and is not a skip row) — country RS tier 1

### B Leagues and tiers

**B7 · 7 · Tier count on the map differs from the roster size of that division**  
_File: data/clubs/*.json vs roster-review.csv_ · Fix: Work the roster-review rows (see A13-A16) · needs a source
- `DE tier 4` 88 clubs on the map vs 87 in the roster — {'missing-from-wikidata': 27, 'wrong-tier': 3, 'extra-not-in-roster': 31, 'ok': 57}
- `GR tier 2` 13 clubs on the map vs 16 in the roster — {'unplaced-no-coordinates': 3, 'ok': 13}
- `IT tier 2` 18 clubs on the map vs 20 in the roster — {'missing-from-wikidata': 1, 'unplaced-no-coordinates': 1, 'ok': 18}
- `RO tier 2` 17 clubs on the map vs 22 in the roster — {'missing-from-wikidata': 1, 'unplaced-no-coordinates': 4, 'wrong-tier': 1, 'extra-not-in-roster': 1, 'ok': 16}
- `RO tier 3` 38 clubs on the map vs 64 in the roster — {'missing-from-wikidata': 13, 'unplaced-no-coordinates': 25, 'extra-not-in-roster': 12, 'ok': 26}
- `RS tier 1` 13 clubs on the map vs 14 in the roster — {'unplaced-no-coordinates': 1, 'ok': 13}
- `RS tier 2` 15 clubs on the map vs 16 in the roster — {'unplaced-no-coordinates': 1, 'ok': 15}

**B8 · 1 · league-tiers.csv and league-rosters.csv disagree or each lacks the other's league**  
_File: data/league-tiers.csv, data/league-rosters.csv_ · Fix: Align the two hand files
- `Q2188121` league-tiers.csv league Regionalliga (the generic fourth-division item) (DE tier 4) has no row in league-rosters.csv

### C Fixtures vs clubs

**C3 · 1 · Linked fixture team name materially different from the club name (automatic link)**  
_File: data/clubs/fixture-links.json_ · Fix: Check the link
- `Q191843 RC Lens (FR, tier 1)` linked team name differs materially (similarity 0.35, basis short-name) — club 'RC Lens' <-> football-data 546 'Racing Club de Lens'

**C6 · 17 · League fixture teams (in a country the map covers) linked to no club on the map**  
_File: data/clubs/fixture-links.json_ · Fix: Add a fixture-links-manual.csv row or a club row
- `rln SpVgg Drochtersen/Assel (openligadb 4341)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln 1. FC Phönix Lübeck (openligadb 6326)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln HSC Hannover (openligadb 8804)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln FSV Schöningen (openligadb 8802)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln Bremer SV (openligadb 2727)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln Eintracht Norderstedt (openligadb 4342)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln Atlas Delmenhorst (openligadb 5024)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- `rln SV Todesfelde (openligadb 5213)` Team in openligadb-rln.json (tier 4 DE) is linked to no club on the map — 18 teams in file vs 88 clubs at that tier on the map
- … 9 more (17 are in the CSV)

**C9 · 10 · OpenLigaDB matches dated before today with finished=false**  
_File: data/fixtures/openligadb-*.json_ · Fix: Result not entered upstream
- `openligadb-rln.json match 87129` Dated 2026-09-26T13:30:00Z (before 2026-10-10) but finished=false — 1. FC Phönix Lübeck v VfB Oldenburg round 11. Spieltag
- `openligadb-rln.json match 87132` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — SpVgg Drochtersen/Assel v SSV Jeddeloh II round 12. Spieltag
- `openligadb-rln.json match 87133` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — VfB Lübeck v Eimsbütteler TV round 12. Spieltag
- `openligadb-rln.json match 87134` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — Hamburger SV II v Werder Bremen II round 12. Spieltag
- `openligadb-rln.json match 87135` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — Kickers Emden v SV Todesfelde round 12. Spieltag
- `openligadb-rln.json match 87136` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — HSC Hannover v FSV Schöningen round 12. Spieltag
- `openligadb-rln.json match 87137` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — Eintracht Norderstedt v Bremer SV round 12. Spieltag
- `openligadb-rln.json match 87138` Dated 2026-10-04T13:00:00Z (before 2026-10-10) but finished=false — SC Weiche Flensburg 08 v VfB Oldenburg round 12. Spieltag
- … 2 more (10 are in the CSV)

**C11 · 6 · Kick-offs at 00:00 UTC with a status other than SCHEDULED (not a placeholder by the repo's own rule)**  
_File: data/fixtures/*.json_ · Fix: Check the source time · needs a source
- `WC.json match 537354` 00:00 UTC with status FINISHED — 2026-06-21T00:00:00Z Ecuador v Curaçao
- `WC.json match 537394` 00:00 UTC with status FINISHED — 2026-06-23T00:00:00Z Norway v Senegal
- `WC.json match 537373` 00:00 UTC with status FINISHED — 2026-06-27T00:00:00Z Uruguay v Spain
- `WC.json match 537374` 00:00 UTC with status FINISHED — 2026-06-27T00:00:00Z Cape Verde Islands v Saudi Arabia
- `WC.json match 537421` 00:00 UTC with status FINISHED — 2026-07-02T00:00:00Z United States v Bosnia-Herzegovina
- `WC.json match 537380` 00:00 UTC with status FINISHED — 2026-07-07T00:00:00Z United States v Belgium

### D Derbies, rivalries, friendships

**D8 · 5 · Rivalry/friendship/derby rows pointing to a club the repo itself marks stale or inactive (skip, whole-club rejection, or extra-not-in-roster)**  
_File: data/club-rivalries.csv, club-friendships.csv, derbies.csv_ · Fix: Review whether the row still stands · needs a source
- `club-friendships.csv line 56 Q170157 Wuppertaler SV` Points to a club marked stale/inactive; roster-review: extra-not-in-roster — other side ['Q32494']
- `derbies.csv line 17 Q584629 FCU Craiova` Points to a club marked stale/inactive; roster-review: extra-not-in-roster — other side ['Q204237']
- `derbies.csv line 19 Q584629 FCU Craiova` Points to a club marked stale/inactive; roster-review: extra-not-in-roster — other side ['Q16838020']
- `derbies.csv line 22 Q639046 Dacia Unirea Brăila` Points to a club marked stale/inactive; roster-review: extra-not-in-roster — other side ['Q220863']
- `derbies.csv line 24 Q1386940 Bihor Oradea` Points to a club marked stale/inactive; roster-review: extra-not-in-roster — other side ['Q680770']

**D9 · 1 · Rival/friend name differs from the club layer name for the same Q-id (the row's text and its id may name different clubs)**  
_File: data/club-rivalries.csv, club-friendships.csv_ · Fix: Check which club is meant
- `club-friendships.csv line 15 Q6703` Name 'Empoli' differs from the club layer name 'Empoli Football Club' (IT)

**D12 · 1 · Friendship rows with status active whose quote contains a past-tense marker**  
_File: data/club-friendships.csv_ · Fix: Re-read the quote: "was/war/bis" may be harmless ("bis heute"); otherwise set unclear/ended · needs a source
- `club-friendships.csv line 33 Q104770 Paris Saint-Germain` status=active but the quote contains past-tense marker(s): ['ehemaligen'] — «Auf Ultra-Ebene gibt es zudem noch eine gewachsene Freundschaft zu den ehemaligen Gruppen»

### E Bucket list

**E2 · 12 · Two-club titles with fewer than two links where BOTH clubs can be matched by exact name in the club layer (link could be written from repo data)**  
_File: data/bucket-links-manual.csv_ · Fix: Add a club line (identity claim: Alexandru decides)
- `ostderby [DE]` Title names two clubs but 0 linked — 'Dynamo Dresden' / 'Hansa Rostock'; resolvable by exact name in the layer: [True, True]
- `nice-v-monaco [FR]` Title names two clubs but 1 linked — 'Nice' / 'Monaco'; resolvable by exact name in the layer: [True, True]
- `napoli-v-roma-derby-del-sole [IT]` Title names two clubs but 1 linked — 'Napoli' / 'Roma'; resolvable by exact name in the layer: [True, True]
- `roma-v-lazio-derby-della-capitale [IT]` Title names two clubs but 1 linked — 'Roma' / 'Lazio'; resolvable by exact name in the layer: [True, True]
- `valencia-v-levante-valencian-derby [ES]` Title names two clubs but 1 linked — 'Valencia' / 'Levante'; resolvable by exact name in the layer: [True, True]
- `fc-heidenheim-v-ssv-ulm-1846 [DE]` Title names two clubs but 1 linked — 'FC Heidenheim' / 'SSV Ulm 1846'; resolvable by exact name in the layer: [True, True]
- `karlsruher-sc-v-waldhof-mannheim [DE]` Title names two clubs but 1 linked — 'Karlsruher SC' / 'Waldhof Mannheim'; resolvable by exact name in the layer: [True, True]
- `waldhof-mannheim-v-sv-sandhausen [DE]` Title names two clubs but 1 linked — 'Waldhof Mannheim' / 'SV Sandhausen'; resolvable by exact name in the layer: [True, True]
- … 4 more (12 are in the CSV)

**E13 · 1 · Bucket "why" texts that state a distance contradicted by the two linked clubs' coordinates**  
_File: data/football-rules.json vs club layer_ · Fix: Edit the why text (unverified hand/assistant text) or fix coordinates · needs a source
- `frankenderby` Text says 300 km but the two linked grounds are 11 km apart in the club layer — 1. FC Nürnberg / SpVgg Greuther Fürth; text: «...es regardless of division. Biggest occasion reachable within 300 km. Franconia's local derby between 

### F football-rules.json

**F5 · 2 · Hand-written distanceKm that disagrees with the distance computed from the club layer**  
_File: data/football-rules.json_ · Fix: Alexandru decides (hand value is "rough") · needs a source
- `fck` rules distanceKm 190 vs estimate from the club layer 143 km (straight line x 1.25) — 1. FC Kaiserslautern
- `rcsa` rules distanceKm 155 vs estimate from the club layer 120 km (straight line x 1.25) — RC Strasbourg Alsace

### G Attended matches

**G3b · 1 · attended.json: match with a score above 0-0 but an empty goals list**  
_File: data/attended.json_ · Fix: Goals not entered; Stats "goals" undercounts · needs a source
- `2019-05-18-sfr-sfb` score 7-6 but goals list gives 0-0 — 0 goals listed; after90=None scoreHT=None; Stelele Fotbalului Românesc v Stelele Fotbalului Bănățean

**G6b · 2 · attended.json: card type that the page would count as a red card although it is neither yellow nor red (page: anything not "yellow" is red)**  
_File: data/attended.json + index.html attStats_ · Fix: Page counts second-yellow as red; confirm intent
- `2024-07-05-esp-ger` card type 'second-yellow' is neither yellow nor red — Dani Carvajal
- `2024-11-26-fcb-psg` card type 'second-yellow' is neither yellow nor red — Ousmane Dembélé

### I Holidays and calendars

**I1 · 1 · Days still marked missing (check_holidays.py prints no MISSING marker; the open item it reports is the movable school days, none entered)**  
_File: data/holidays-manual.csv_ · Fix: Enter the four movable days from the school calendar (Alexandru) · needs a source
- `holidays-manual.csv` no school-holiday-movable row: bewegliche Ferientage not entered (ministry: 4 movable days in 2026/27 per CLAUDE.md) — REPORTED - 1:;   no school-holiday-movable row: the movable school days (bewegliche Ferientage) are not entered, so a day without shading may still be

**I2 · 1 · Calendar events outside the 2026-27 season window (1 July 2026 to 30 June 2027)**  
_File: calendars/*.ics_ · Fix: Expected for next-cycle sale reminders; otherwise fix the source date (hand-written)
- `bayern.ics fcb-away-window-2026@football.local` 2027-07-27 is outside the 2026-27 season window 2026-07-01..2027-06-30 (1 July to 30 June) — [?] Bayern away request window closes

## Severity C

### A Club layer

**A9 · 26 · Capacity missing but documented in clubs-manual.csv**  
_File: data/clubs-manual.csv_ · Fix: None - housekeeping count
- `Q297832 ASK Voitsberg (AT, tier 2)` Blank on purpose per hand row — manual line 159
- `Q98217947 SK Sturm Graz II (AT, tier 2)` Blank on purpose per hand row — manual line 162
- `Q101625593 Club NXT (BE, tier 2)` Blank on purpose per hand row — manual line 241
- … 23 more (25 are in the CSV)

**A11 · 57 · capacity-review.csv: unresolved rows with only one or no OpenStreetMap figure**  
_File: data/clubs/capacity-review.csv_ · Fix: Needs an independent source; no repo-only fix · needs a source
- `line 2 Q98217947 SK Sturm Graz II` neither source has a capacity — Wikidata= OSM=
- `line 3 Q297832 ASK Voitsberg` no stadium in OSM within 500m — Wikidata= OSM=
- `line 4 Q1668203 Lommel SK` neither source has a capacity — Wikidata= OSM=
- … 54 more (25 are in the CSV)

**A17 · 3 · country-review.csv rows (clubs possibly in the wrong country file)**  
_File: data/clubs/country-review.csv_ · Fix: Documented exception shape (Monaco/Vaduz); no change
- `Q180305 AS Monaco FC in FR` P17 on the item says Monaco (Q235), not France — hand-corrected=yes; manual note: yes
- `Q216773 FC Vaduz in CH` P17 on the item says Liechtenstein (Q347), not Switzerland — hand-corrected=yes; manual note: yes
- `Q1386854 FC Andorra in ES` P17 on the item says Andorra (Q228), not Spain — hand-corrected=yes; manual note: yes

**A18 · 731 · unmapped-leagues.csv: seed list rows (all have blank tier by design)**  
_File: data/clubs/unmapped-leagues.csv_ · Fix: Seed list for league-tiers.csv; map or ignore
- `Q749736 Tercera División (ES)` Unmapped league, 368 clubs seen
- `Q1141778 Serie D (IT)` Unmapped league, 260 clubs seen
- `Q2186316 Belgian Provincial leagues (BE)` Unmapped league, 157 clubs seen
- … 728 more (25 are in the CSV)

**A23 · 66 · stadiumdb-review.csv rows where StadiumDB differs (third opinion; no decision column)**  
_File: data/clubs/stadiumdb-review.csv_ · Fix: Needs an independent source · needs a source
- `line 2 Q698702 Admira Wacker (AT)` sources differ by 42% — ours=12000 stadiumdb=7010
- `line 3 Q699686 SC Schwarz-Weiß Bregenz (AT)` sources differ by 7% — ours=12000 stadiumdb=11112
- `line 4 Q686826 First Vienna FC 1894 (AT)` sources differ by 8% — ours=5500 stadiumdb=6000
- … 63 more (25 are in the CSV)

### B Leagues and tiers

**B2 · 9 · Club has no league id (tier rests on a documented hand row)**  
_File: data/clubs/??.json_ · Fix: None
- `Q63168427 FC Hertha Wels (AT, tier 2)` No league id on the club — manual rows: [160]; manual=True
- `Q98217947 SK Sturm Graz II (AT, tier 2)` No league id on the club — manual rows: [162]; manual=True
- `Q98228613 SK Rapid Wien II (AT, tier 2)` No league id on the club — manual rows: [161]; manual=True
- … 6 more (9 are in the CSV)

**B3 · 17 · League id not in league-tiers.csv, club has a hand row (hand-named fallback shape: tag names the lower league it left)**  
_File: data/league-tiers.csv_ · Fix: None - documented in CLAUDE.md
- `Q2206406 SKU Amstetten (AT, tier 2)` League id not in league-tiers.csv — Q683390
- `Q297832 ASK Voitsberg (AT, tier 2)` League id not in league-tiers.csv — Q4825490
- `Q696474 Floridsdorfer AC (AT, tier 2)` League id not in league-tiers.csv — Q683390
- … 14 more (17 are in the CSV)

**B5 · 30 · Club tier differs from its league tag but a hand tier row documents it**  
_File: data/clubs-manual.csv_ · Fix: None - hand data wins (rule 3)
- `Q696525 FC Blau-Weiß Linz (AT, tier 2)` Tier differs from the most senior mapped league tag — leagues=[('Q219592', '1')]; hand tier rows=[127]
- `Q1065328 FCV Dender EH (BE, tier 2)` Tier differs from the most senior mapped league tag — leagues=[('Q216022', '1')]; hand tier rows=[230]
- `Q1668203 Lommel SK (BE, tier 1)` Tier differs from the most senior mapped league tag — leagues=[('Q23925620', '2')]; hand tier rows=[231]
- … 27 more (25 are in the CSV)

### C Fixtures vs clubs

**C4 · 11 · Linked fixture team name materially different from the club name (hand link in fixture-links-manual.csv; hand data wins)**  
_File: data/fixture-links-manual.csv_ · Fix: None - abbreviations the matcher refuses by design
- `Q10286 Club Atlético Osasuna (ES, tier 1)` linked team name differs materially (similarity 0.50, basis manual) — club 'Club Atlético Osasuna' <-> football-data 79 'CA Osasuna'
- `Q8682 Real Madrid Club de Fútbol (ES, tier 1)` linked team name differs materially (similarity 0.59, basis manual) — club 'Real Madrid Club de Fútbol' <-> football-data 86 'Real Madrid CF'
- `Q210864 Le Mans Football Club (FR, tier 1)` linked team name differs materially (similarity 0.50, basis manual) — club 'Le Mans Football Club' <-> football-data 535 'Le Mans FC'
- … 8 more (11 are in the CSV)

**C6b · 38 · Brazil/Portugal league fixture teams (no club file for those countries; by design)**  
_File: data/fixtures/BSA.json, PPL.json_ · Fix: None
- `BSA CA Mineiro (football-data 1766)` Team in BSA.json (tier 1 BR) is linked to no club on the map — 20 teams in file vs 0 clubs at that tier on the map
- `BSA SE Palmeiras (football-data 1769)` Team in BSA.json (tier 1 BR) is linked to no club on the map — 20 teams in file vs 0 clubs at that tier on the map
- `BSA Coritiba FBC (football-data 4241)` Team in BSA.json (tier 1 BR) is linked to no club on the map — 20 teams in file vs 0 clubs at that tier on the map
- … 35 more (25 are in the CSV)

**C10 · 1452 · Kick-offs at 00:00 UTC with status SCHEDULED (known placeholder; the page says "time not set")**  
_File: data/fixtures/*.json_ · Fix: None
- `BL1.json match 565875` 00:00 UTC SCHEDULED — 2026-12-05T00:00:00Z 1. FC Union Berlin v Hamburger SV
- `BL1.json match 565876` 00:00 UTC SCHEDULED — 2026-12-05T00:00:00Z FC Schalke 04 v Borussia Dortmund
- `BL1.json match 565877` 00:00 UTC SCHEDULED — 2026-12-05T00:00:00Z Bayer 04 Leverkusen v Borussia Mönchengladbach
- … 1449 more (25 are in the CSV)

### D Derbies, rivalries, friendships

**D5 · 1 · derbies.csv: rows whose two clubs are in different country files (cross-border pairs)**  
_File: data/derbies.csv_ · Fix: Informational
- `line 107 European Clásico` DE v ES (kind historic) — FC Bayern München / Real Madrid Club de Fútbol

**D11 · 9 · Rivalry/friendship pairs across countries (not an error; informational)**  
_File: data/club-rivalries.csv, club-friendships.csv_ · Fix: None
- `club-rivalries.csv line 15 Q15789->Q8682` FC Bayern München (DE) and rival Real Madrid Club de Fútbol (ES) are in different countries — class other source R9
- `club-friendships.csv line 15 Q15789->Q6703` FC Bayern München (DE) and friend Empoli Football Club (IT) in different countries — scope fan-groups status active
- `club-friendships.csv line 24 Q126334->Q105853` RC Strasbourg Alsace (FR) and friend Karlsruher SC (DE) in different countries — scope unclear status active
- … 6 more (9 are in the CSV)

**D13 · 17 · Rivalry/friendship pair appearing in several rows (either direction; per-club storage means one row each side is by design)**  
_File: data/club-rivalries.csv, club-friendships.csv_ · Fix: Informational
- `club-rivalries.csv lines [2, 9]` Same pair stored more than once (either direction) — ['Q101959', 'Q104770']
- `club-rivalries.csv lines [6, 34]` Same pair stored more than once (either direction) — ['Q102720', 'Q141971']
- `club-rivalries.csv lines [7, 14]` Same pair stored more than once (either direction) — ['Q15789', 'Q41420']
- … 14 more (17 are in the CSV)

### E Bucket list

**E2b · 85 · Two-club titles with fewer than two links where a club is off the map or not matched by exact name**  
_File: data/bucket-links-manual.csv_ · Fix: Link when the club reaches the map
- `intercontinental-derby [TR]` Title names two clubs but 0 linked — 'Galatasaray' / 'Fenerbahçe'; resolvable by exact name in the layer: [False, False]
- `old-firm [GB]` Title names two clubs but 0 linked — 'Celtic' / 'Rangers'; resolvable by exact name in the layer: [False, False]
- `prague-derby [CZ]` Title names two clubs but 0 linked — 'Sparta' / 'Slavia'; resolvable by exact name in the layer: [False, False]
- … 82 more (25 are in the CSV)

**E4b · 4 · Bucket entries with whyAssistant only (no why)**  
_File: data/football-rules.json_ · Fix: Informational
- `zweite-liga-relegation` no "why" field; only "whyAssistant" (hand-written wins; page shows whyAssistant)
- `regionalliga-aufstiegsspiele` no "why" field; only "whyAssistant" (hand-written wins; page shows whyAssistant)
- `superliga-relegation-baraj` no "why" field; only "whyAssistant" (hand-written wins; page shows whyAssistant)
- … 1 more (4 are in the CSV)

**E12b · 29 · leagueCheck true and both linked clubs share a league (flag is satisfied; check not built)**  
_File: data/football-rules.json_ · Fix: Informational
- `frankenderby` leagueCheck true and both linked clubs sit in the same league (check would pass) — 1. FC Nürnberg / SpVgg Greuther Fürth: 2. Bundesliga tiers 2/2
- `sudwest-derby` leagueCheck true and both linked clubs sit in the same league (check would pass) — Karlsruher SC / 1. FC Kaiserslautern: 2. Bundesliga tiers 2/2
- `revierderby` leagueCheck true and both linked clubs sit in the same league (check would pass) — FC Schalke 04 / Borussia Dortmund: Bundesliga tiers 1/1
- … 26 more (25 are in the CSV)

### G Attended matches

**G6a · 7 · attended.json: cards without a minute (page lists them first, shown as a dash)**  
_File: data/attended.json_ · Fix: None
- `2024-11-26-fcb-psg` card has no minute (page shows a dash by design) — Kingsley Coman
- `2024-11-26-fcb-psg` card has no minute (page shows a dash by design) — Serge Gnabry
- `2024-11-26-fcb-psg` card has no minute (page shows a dash by design) — Michael Olise
- … 4 more (7 are in the CSV)

**G8 · 7 · attended.json: stadium not found by name among club-layer venues (expected for off-map grounds and demolished stadiums)**  
_File: data/attended.json vs data/clubs/*.json_ · Fix: None unless the club is on the map
- `2016-10-25-poli-pan` stadium 'Stadionul Dan Păltinișanu' is in no club's venue in the layer — Politehnica Timișoara v Pandurii Târgu Jiu, 2016-10-25
- `2019-05-18-sfr-sfb` stadium 'Stadionul Dan Păltinișanu' is in no club's venue in the layer — Stelele Fotbalului Românesc v Stelele Fotbalului Bănățean, 2019-05-18
- `2021-06-23-por-fra` stadium 'Puskás Aréna' is in no club's venue in the layer — Portugal v France, 2021-06-23
- … 4 more (7 are in the CSV)

### H App wiring

**H2b · 3 · Files in icons/ not referenced by the app (tooling sources such as draw-icon.js are expected)**  
_File: icons/_ · Fix: None
- `icons/icon-maskable.svg` file in icons/ not referenced by manifest, sw.js or index.html
- `icons/draw-icon.js` file in icons/ not referenced by manifest, sw.js or index.html
- `icons/icon.svg` file in icons/ not referenced by manifest, sw.js or index.html

**H3 · 4 · Files in data/ not referenced by the app, a tool or a workflow**  
_File: data/_ · Fix: Delete or document
- `data/fixtures/BSA.json` no reference by path or file name in index.html, sw.js, tools/ or workflows/
- `data/fixtures/EC.json` no reference by path or file name in index.html, sw.js, tools/ or workflows/
- `data/fixtures/PPL.json` no reference by path or file name in index.html, sw.js, tools/ or workflows/
- … 1 more (4 are in the CSV)

**H6 · 219 · en keys never referenced by a static t()/tn()/data-i18n call (may be reached dynamically)**  
_File: index.html I18N_ · Fix: Delete if dead
- `adj.AT` no static reference
- `adj.BE` no static reference
- `adj.CH` no static reference
- … 216 more (25 are in the CSV)

## Tables behind the checks

**A · Shared coordinate groups**

| measure | count |
|---|---|
| coordinate groups with >=2 clubs | 25 |
| of which same venue name (treated as genuine) | 23 |
| clubs involved | 50 |

**A · capacity-review.csv rows by verdict**

| verdict | rows |
|---|---|
| neither source has a capacity | 37 |
| no stadium in OSM within 500m | 17 |
| only OpenStreetMap has a figure | 3 |
| sources differ | 10 |

**A · roster-review.csv rows by verdict**

| verdict | rows |
|---|---|
| ok | 507 |
| missing-from-wikidata | 42 |
| wrong-tier | 4 |
| extra-not-in-roster | 44 |
| unplaced-no-coordinates | 35 |

**A · coordinate-review.csv rows by verdict class**

| class | rows |
|---|---|
| ambiguous | 39 |
| rejected | 10 |
| no match | 50 |
| held | 14 |

**B · Tier counts per country vs roster sizes (roster = review rows that are not extra-not-in-roster)**

| country | tier | on map | roster size | verdicts |
|---|---|---|---|---|
| AT | 1 | 12 | 12 | {'ok': 12} |
| AT | 2 | 16 | 16 | {'ok': 16} |
| BE | 1 | 18 | 18 | {'ok': 18} |
| BE | 2 | 15 | 15 | {'ok': 15} |
| CH | 1 | 12 | 12 | {'ok': 12} |
| CH | 2 | 10 | 10 | {'ok': 10} |
| DE | 1 | 18 | 18 | {'ok': 18} |
| DE | 2 | 18 | 18 | {'ok': 18} |
| DE | 3 | 20 | 20 | {'ok': 20} |
| DE | 4 | 88 | 87 | {'missing-from-wikidata': 27, 'wrong-tier': 3, 'extra-not-in-roster': 31, 'ok': 57} |
| DE | 6 | 3 | (no roster) |  |
| DE | 7 | 1 | (no roster) |  |
| DE | 8 | 1 | (no roster) |  |
| ES | 1 | 20 | 20 | {'ok': 20} |
| ES | 2 | 22 | 22 | {'ok': 22} |
| FR | 1 | 18 | 18 | {'ok': 18} |
| FR | 2 | 18 | 18 | {'ok': 18} |
| GB | 1 | 20 | 20 | {'ok': 20} |
| GB | 2 | 24 | 24 | {'ok': 24} |
| GR | 1 | 14 | 14 | {'ok': 14} |
| GR | 2 | 13 | 16 | {'unplaced-no-coordinates': 3, 'ok': 13} |
| IT | 1 | 20 | 20 | {'ok': 20} |
| IT | 2 | 18 | 20 | {'missing-from-wikidata': 1, 'unplaced-no-coordinates': 1, 'ok': 18} |
| NL | 1 | 18 | 18 | {'ok': 18} |
| NL | 2 | 20 | 20 | {'ok': 20} |
| RO | 1 | 16 | 16 | {'ok': 16} |
| RO | 2 | 17 | 22 | {'missing-from-wikidata': 1, 'unplaced-no-coordinates': 4, 'wrong-tier': 1, 'extra-not-in- |
| RO | 3 | 38 | 64 | {'missing-from-wikidata': 13, 'unplaced-no-coordinates': 25, 'extra-not-in-roster': 12, 'o |
| RS | 1 | 13 | 14 | {'unplaced-no-coordinates': 1, 'ok': 13} |
| RS | 2 | 15 | 16 | {'unplaced-no-coordinates': 1, 'ok': 15} |

**C · Fixture competitions and the tier this audit assigned them**

| file | code | name in file | audit tier |
|---|---|---|---|
| BL1.json | BL1 | Bundesliga | ('DE', 1) |
| BSA.json | BSA | Campeonato Brasileiro Série A | ('BR', 1) |
| CL.json | CL | UEFA Champions League | cup/other |
| DED.json | DED | Eredivisie | ('NL', 1) |
| EC.json | EC | European Championship | cup/other |
| ELC.json | ELC | Championship | ('GB', 2) |
| FL1.json | FL1 | Ligue 1 | ('FR', 1) |
| PD.json | PD | Primera Division | ('ES', 1) |
| PL.json | PL | Premier League | ('GB', 1) |
| PPL.json | PPL | Primeira Liga | ('PT', 1) |
| SA.json | SA | Serie A | ('IT', 1) |
| WC.json | WC | FIFA World Cup | cup/other |
| openligadb-bl2.json | bl2 | 2. Fußball-Bundesliga 2026/2027 | ('DE', 2) |
| openligadb-bl3.json | bl3 | 3. Liga 2026/2027 | ('DE', 3) |
| openligadb-dfb.json | dfb | DFB Pokal 2026/2027 | cup/other |
| openligadb-rln.json | rln | Fußball-Regionalliga Nord | ('DE', 4) |
| openligadb-rlno.json | rlno | NOFV Regionalliga NordOst | ('DE', 4) |

**C · Kick-offs at 00:00 UTC by file and status**

| file | status | matches |
|---|---|---|
| BL1.json | SCHEDULED | 198 |
| BSA.json | FINISHED | 13 |
| BSA.json | POSTPONED | 1 |
| BSA.json | SCHEDULED | 40 |
| BSA.json | TIMED | 3 |
| DED.json | SCHEDULED | 100 |
| ELC.json | SCHEDULED | 264 |
| FL1.json | SCHEDULED | 192 |
| PD.json | SCHEDULED | 270 |
| PPL.json | SCHEDULED | 198 |
| SA.json | SCHEDULED | 190 |
| WC.json | FINISHED | 6 |

**D · tools/check_derbies.py exit code**

| exit | last lines |
|---|---|
| 0 |  /   No problems. 248 row(s) read. / ===================================================== |

**D · tools/check_club_culture.py exit code**

| exit | last lines |
|---|---|
| 0 | WARNING: source C22 is used by no row / WARNING: source C23 is used by no row / No problem |

**E · Two-club bucket titles with fewer than two links, by countryCode**

| countryCode | all | both clubs matchable |
|---|---|---|
| DE | 19 | 8 |
| GB | 11 | 0 |
| FR | 6 | 1 |
| ES | 6 | 1 |
| IT | 5 | 2 |
| BR | 4 | 0 |
| PL | 4 | 0 |
| PT | 4 | 0 |
| - | 3 | 0 |
| AR | 3 | 0 |
| AT | 3 | 0 |
| TR | 2 | 0 |
| RO | 2 | 0 |
| HR | 2 | 0 |
| NL | 2 | 0 |
| US | 2 | 0 |
| CZ | 1 | 0 |
| BE | 1 | 0 |
| BA | 1 | 0 |
| BG | 1 | 0 |
| CL | 1 | 0 |
| CO | 1 | 0 |
| CY | 1 | 0 |
| DK | 1 | 0 |
| EG | 1 | 0 |
| GR | 1 | 0 |
| HU | 1 | 0 |
| JP | 1 | 0 |
| MX | 1 | 0 |
| MA | 1 | 0 |
| SK | 1 | 0 |
| SI | 1 | 0 |
| ZA | 1 | 0 |
| CH | 1 | 0 |
| UY | 1 | 0 |

**E · Dated bucket entries seen**

| id | field | value |
|---|---|---|
| el-final-2027 | date | 2027-05-26 |
| frankenderby | nextFixture.dateEstimate | 2027-01-30/2027-02-01 |
| sudwest-derby | nextFixture.dateEstimate | 2027-01-29/2027-01-31 |
| derby-madonnina | fixtures.date:milan | 2026-11-01 |
| derby-madonnina | fixtures.date:inter | 2027-02-14 |

**E · Dated entries compared with the fixture files**

| id | field | value | result |
|---|---|---|---|
| el-final-2027 | date | 2027-05-26 | not two linked clubs - could not compare |
| frankenderby | nextFixture.dateEstimate | 2027-01-30/2027-02-01 | fixture dates [('openligadb-bl2.json', '2026-08-15'), ('openligadb-bl2.json', '2027-01-31' |
| sudwest-derby | nextFixture.dateEstimate | 2027-01-29/2027-01-31 | fixture dates [('openligadb-bl2.json', '2026-08-15'), ('openligadb-bl2.json', '2027-01-31' |
| derby-madonnina | fixtures.date:milan | 2026-11-01 | fixture dates [('SA.json', '2026-10-31'), ('SA.json', '2027-02-14')]; match: False |
| derby-madonnina | fixtures.date:inter | 2027-02-14 | fixture dates [('SA.json', '2026-10-31'), ('SA.json', '2027-02-14')]; match: True |

**E · leagueCheck entries**

| measure | count |
|---|---|
| leagueCheck true | 102 |
| of which both clubs linked | 61 |
| not comparable (fewer than two linked) | 41 |

**G · Attendance spread**

| measure | value |
|---|---|
| matches with a figure | 21 |
| min | (300, '2026-08-29-ucd-scm') |
| max | (81365, '2023-02-19-bvb-bsc') |
| median | 29886 |

**H · Template (dynamic) paths in index.html/sw.js that cannot be checked statically**

| path |
|---|

**H · How data files are referenced**

| kind | files |
|---|---|
| index.html/sw.js path | 37 |
| tool/workflow path | 14 |
| tool/workflow by file name | 2 |
| fixture index/links | 12 |

**H · Dictionary facts**

| measure | count |
|---|---|
| en keys | 1124 |
| ro keys | 1124 |
| static t()/data-i18n keys used | 758 |
| static tn() keys | 19 |
| t()/tn() calls with a computed key (not statically checkable) | 43 |
| vocab() prefixes | ['bstatus.', 'btype.', 'cnm.', 'freq.', 'grp.', 'tstatus.'] |

**I · check_holidays.py**

| exit | summary |
|---|---|
| 0 | Entered from Thu 30 Jul 2026 to Mon 13 Sep 2027. Outside that the calendar says school hol |

**I · Events per calendar file**

| file | events |
|---|---|
| admin.ics | 1 |
| bayern.ics | 2 |
| bucket-list.ics | 5 |
| local.ics | 2 |
| uefa-finals.ics | 1 |

**I · fixtures-manual.csv**

| rows |
|---|
| 0 |

**Coverage · Rows each check actually evaluated (so a zero is not an empty loop)**

| check | rows evaluated |
|---|---|
| C1 club tier vs fixture competition tier (club-competition pairs) | 195 |
| B4 club tier vs league tag (clubs with a mapped league) | 530 |
| A3/A4 clubs with coordinates | 556 |
| A24 id/country cross-file rows | 880 |
| D1-D4 derby rows with both clubs on the map | 197 |
| E9 bucket entries with a countryCode and a linked club | 113 |
| E11 dated entries compared with a fixture file | 4 |
| E10 dated bucket entries | 5 |
| F2 id references checked | 380 |
| G stats matches | 23 |
| H5 static t()/data-i18n keys | 758 |

## Needs a source

Checks whose hits cannot be settled from the repo (flag `needsSource` = yes in the CSV):

- A5 (2) Identical coordinates on clubs whose venue names differ (no shared-grounds list exists in the repo; same coord
- A7 (1) Capacity under 500 or over 120,000
- A8 (31) Capacity missing with no hand-row note explaining it
- A10 (10) capacity-review.csv: unresolved rows where Wikidata and OpenStreetMap figures differ (file has no decision col
- A11 (57) capacity-review.csv: unresolved rows with only one or no OpenStreetMap figure
- A13b (3) roster-review.csv: wrong-tier where another division article lists the same club as ok (club appears in two ro
- A14 (44) roster-review.csv: extra-not-in-roster (on the map, not in the current division)
- A15 (42) roster-review.csv: missing-from-wikidata (in the division, not on the map)
- A16 (35) roster-review.csv: unplaced-no-coordinates
- A20 (79) coordinate-review.csv: unresolved rows (no _reviewed stamp) and not yet on the map
- A23 (66) stadiumdb-review.csv rows where StadiumDB differs (third opinion; no decision column)
- B7 (7) Tier count on the map differs from the roster size of that division
- C11 (6) Kick-offs at 00:00 UTC with a status other than SCHEDULED (not a placeholder by the repo's own rule)
- D8 (5) Rivalry/friendship/derby rows pointing to a club the repo itself marks stale or inactive (skip, whole-club rej
- D12 (1) Friendship rows with status active whose quote contains a past-tense marker
- G3b (1) attended.json: match with a score above 0-0 but an empty goals list
- I1 (1) Days still marked missing (check_holidays.py prints no MISSING marker; the open item it reports is the movable
- A5b (2) Shared ground (same coordinate, same venue name) with different capacities on the clubs
- E13 (1) Bucket "why" texts that state a distance contradicted by the two linked clubs' coordinates
- F5 (2) Hand-written distanceKm that disagrees with the distance computed from the club layer
- H: t()/tn() calls with a computed key: 43 call sites (e.g. !cc[0] && !cc[1] ? 'rt.cost.startEnd' : !cc[0] ? 'rt.cost.st; FILTERS.comp.empty; FILTERS[FP_FOR].noun; FILTERS[name].empty; FP_FOR === 'bucket' ? 'f.titleBucket' : 'f.titleComp') cannot be matched to the dictionary without running the page — run the page headless (test_me.js already does for the dictionary)

## Looks wrong, needs a source (unverified, capped at 30)

Plausibility flags only, not findings. Nothing here is evidence of an error.

- Q2744247 Kalamata F.C. (GR, tier 1): top-tier club with a small capacity: 4496 (Kalamata Municipal Stadium)
- Q370712 Excelsior Rotterdam (NL, tier 1): top-tier club with a small capacity: 4500 (Stadion Woudestein)
- Q213161 FK Čukarički (RS, tier 1): top-tier club with a small capacity: 4070 (Stadion Čukarički)
- Q5426356 FK Radnik Surdulica (RS, tier 1): top-tier club with a small capacity: 3312 (Surdulica City Stadium)
- Q142005 Hansa Rostock (DE, tier 3): tier 3 club with a large capacity: 29000 (Ostseestadion)
- Q151747 Fortuna Düsseldorf (DE, tier 3): tier 3 club with a large capacity: 54600 (Merkur Spiel-Arena)
- Q153535 Alemannia Aachen (DE, tier 3): tier 3 club with a large capacity: 32960 (Tivoli)
- Q154293 MSV Duisburg (DE, tier 3): tier 3 club with a large capacity: 31500 (Schauinsland-Reisen-Arena)
- Q16525407 1. FC Kaiserslautern II (DE, tier 4): tier 4 club with a large capacity: 49780 (Fritz-Walter-Stadion)
- Q16536906 Bayer 04 Leverkusen II (DE, tier 4): tier 4 club with a large capacity: 30210 (BayArena)
- Q170134 SV Waldhof Mannheim (DE, tier 3): tier 3 club with a large capacity: 27000 (Carl-Benz-Stadion)
- Q176168 TSG Neustrelitz (DE, tier 4): tier 4 club with a large capacity: 62008 (Parkstadion)
- Q20994272 RB Leipzig II (DE, tier 4): tier 4 club with a large capacity: 42000 (Red Bull Arena)
- Q5424829 FC Augsburg II (DE, tier 4): tier 4 club with a large capacity: 26443 (Rosenaustadion)
- Q826212 VfB Oldenburg (DE, tier 4): tier 4 club with a large capacity: 32000 (Marschweg-Stadion)
- Q584629 FCU Craiova (RO, tier 3): tier 3 club with a large capacity: 30944 (Stadionul Ion Oblemenco)

## Checks that could not run

- **My stats "Record" (W-D-L)**: Depends on the supported-team choice kept only on the device (football-attended-personal); not in the repo
- **Web checks**: Every capacity, ground, tier, roster, rivalry, friendship and attended-match fact that needs a second source is under "needs a source"; none was looked up.
- **"MISSING" days**: check_holidays.py prints no MISSING marker. The only open holiday item is the movable school days (I1).
- **Shared-grounds list**: No such list exists in the repo; the page groups clubs on exactly equal coordinates. Same coordinate plus same venue name was treated as a genuine shared ground (A5).
- **Club "country" field**: Club records carry none; the file name is the country. Country was cross-checked against clubs-manual, roster-review, capacity-review and stadiumdb-review (A24) and against league-tiers (B6).
- **Stale/inactive flag**: The club layer has no such flag. D8 uses the repo's own markers: a `skip` row, a whole-club rejection in coordinate-reviews.csv, or roster-review `extra-not-in-roster`.
- **Rival/friend country "in the text"**: Rows have names but no country text. D9 compares the row name with the club layer name for the same id; D11 lists cross-country pairs.
- **"Agreed order" of bucket groups**: No written order exists. Used the order the page's own sort produces: Tournaments, Finals and super cups, International fixtures, Germany, Romania, other countries (E6).
- **Page tests**: tools/test_*.js (Playwright) were not run; the page was not opened.
- **Network tools**: check_rosters.py, crosscheck_*.py, propose_coordinates.py, link_fixtures.py and diagnose_p118_rank.py need Wikidata/Overpass/StadiumDB and were not run.
- **Ticket data and competition info**: Out of scope by instruction.
