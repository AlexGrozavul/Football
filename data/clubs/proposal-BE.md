# Proposal for BE (Belgium)

Generated 2026-10-21 17:06 UTC by `tools/propose_country.py`. **Read-only evidence, not decisions**: nothing here was written to a hand-written file or a club file; a gap is a gap.

## Summary

| kind | rows |
|---|---|
| roster-ok | 20 |
| roster-untagged | 7 |
| roster-wrong-tier | 2 |
| roster-unread | 4 |
| extra-tagged | 6 |
| not-a-club | 2 |
| duplicate | 6 |
| two-grounds | 1 |
| ground-proposal | 29 |
| capacity-proposal | 29 |

Tagged but dissolved (not drawn by the build, no row): 15; tagged extras whose tag is not truthy (not drawn, no row): 1; women's football items pointing at a club, carrying neither tag: 0 (other-sport items ignored: 1).

**Reader gaps: 4 roster row(s) the reader cannot read** (kind roster-unread).

Step durations (s): 1 rosters 2.5, 2 leagues 5.8, 3 items 3.2, 4 rank cross-check 1.1, 5 evidence for extras 4.9, 6 candidates 0.0, 6b grounds and capacities 1076.5, 7 wiring patch 0.5

## Leagues

| tier | article | league item | label | found via | P3983 | P17 | women-word check |
|---|---|---|---|---|---|---|---|
| 1 | 2026–27 Belgian Pro League | Q216022 | Belgian Pro League | season item Q138716967 -> P3450 | none | Q31 Belgium | none |
| 2 | 2026–27 Challenger Pro League | Q23925620 | Challenger Pro League | season item Q140073407 -> P3450 | none | Q31 Belgium | none |

P3983 and P17 are printed, not used: the country Q-id given on the command line is `Q31`.

### Items labelled like a tier, or succeeded by it (the 'old Second Division' trap)

| item | label | description | clubs carrying it (any rank) | dissolved | succeeded by |
|---|---|---|---|---|---|
| Q233199 | Belgian First Division B | defunct second level of men's association football in Belgium | 34 | 2016-01-01 | Q23925620 |

Rows with clubs > 0 and a dissolution or successor are the trap: not to be mapped.

## Wiring patch (printed, not applied)

### data/league-tiers.csv — append

```
Q216022,1,Belgian Pro League,BE
Q23925620,2,Challenger Pro League,BE
```

### data/league-rosters.csv — append

```
Q216022,BE,1,2026-27,2026–27 Belgian Pro League,
Q23925620,BE,2,2026-27,2026–27 Challenger Pro League,
```

### COUNTRY_BOX (tools/fetch_clubs.py)

- north: (51.50508, 4.77392) normal
- south: (49.49699, 5.47248) normal
- east: (50.3358193, 6.40743256) normal
- west: (51.089449723913674, 2.5452695664522746) normal
- proposal from best rank: `"BE": {"lat": (49.35, 51.66), "lon": (2.4, 6.56)},`
- proposal from normal rank only: `"BE": {"lat": (49.35, 51.66), "lon": (2.4, 6.56)},`

### football-data.org code (candidates only)

- none found in the free-tier list or data/fixtures/index.json

### Places to touch (with line numbers)

(template country: Portugal PT Q45; edit beside its lines)
- data/league-tiers.csv: append the league-tiers rows printed above
- data/league-rosters.csv: append the league-rosters rows printed above
- tools/fetch_clubs.py: COUNTRIES (code, P17 Q-id, name), COUNTRY_BOX and its comment, COUNTRY_NAMES, the label languages in the build loop
    tools/fetch_clubs.py:112: # Portugal, P17 Q45 (checked by probe 2026-10-20, see the Portugal entry).
    tools/fetch_clubs.py:113: ("PT", "Q45", "Portugal"),
    tools/fetch_clubs.py:1209: #       Portugal, Andorra, Gibraltar, northern Morocco and a strip of
    tools/fetch_clubs.py:1218: #   PT  Wikidata's own P1332-P1335 on Q45, read by probe on a runner
    tools/fetch_clubs.py:1281: "PT": {"lat": (32.35, 42.25), "lon": (-31.35, -6.10)},
    tools/fetch_clubs.py:1291: "Q31": "Belgium", "Q45": "Portugal", "Q55": "Netherlands", "Q36": "Poland",
    tools/fetch_clubs.py:1692: "RS": "en,sr-el", "GR": "en,el", "ES": "en,es", "NL": "en,nl", "BE": "en,nl,fr", "PT": "en,pt"}.get(code, "en"
- tools/diagnose_p118_rank.py: COUNTRIES (P17 Q-id to code)
    tools/diagnose_p118_rank.py:86: # Portugal: P17 Q45 on both leagues and the club items (probe 2026-10-20).
    tools/diagnose_p118_rank.py:87: "Q45": "PT"}
- tools/crosscheck_stadiumdb.py: COUNTRY_PAGES (the slug, found by probe); EXTRA_PAGES if the pyramid crosses a border
    tools/crosscheck_stadiumdb.py:171: # Portugal's "por" on 2026-10-20: /stadiums/por answers 200 on a runner
    tools/crosscheck_stadiumdb.py:174: # with Liga Portugal 2 clubs (Benfica B's Seixal campus among them), then 16
    tools/crosscheck_stadiumdb.py:190: "PT": ("por", "Portugal"),
- tools/link_fixtures.py: CLUB_FILES; FD_COUNTRY if football-data carries a league
    tools/link_fixtures.py:133: "data/clubs/NL.json", "data/clubs/BE.json", "data/clubs/PT.json"]
    tools/link_fixtures.py:149: "DED": "NL", "PPL": "PT", "BSA": "BR",
- tools/build_calendars.py: time zone (usually already there)
    tools/build_calendars.py:74: "PT": "Europe/Lisbon",
- index.html: COUNTRY_FILES; cn.XX in en and ro and COUNTRY_NAME; adj.XX and COUNTRY_ADJ for a country with no fixtures; noFixturesReason() top map; fx.coverage and LEAGUE_CODES if football-data carries a league
    index.html:1441: "cn.PT": "Portugal",
    index.html:1564: "cnm.Portugal": "Portugal",
    index.html:1656: "iso.PT": "Portugal",
    index.html:2689: "cn.PT": "Portugalia",
    index.html:2812: "cnm.Portugal": "Portugalia",
    index.html:2904: "iso.PT": "Portugalia",
    index.html:3591: const COUNTRY_FILES = ['data/clubs/DE.json','data/clubs/RO.json','data/clubs/FR.json','data/clubs/IT.json','da
    index.html:4469: NL:[t('fx.no.eredivisie'),t('fx.no.eerste')], PT:['Primeira Liga','Liga Portugal 2']}[club.country];
    index.html:6419: const COUNTRY_NAME = labelsOf('cn.', ['AT', 'BE', 'CH', 'DE', 'ES', 'FR', 'GB', 'GR', 'IT', 'NL', 'PT', 'RO', 
    index.html:7222: const ISO_KEYS = ['AR','AT','BA','BE','BG','BR','CH','CL','CO','CY','CZ','DE','DK','EG','ES','FR','GB','GR','H
- tools/test_nearme.js: the printed count ("of N country files")
    tools/test_nearme.js:376: console.log(`    the panel opened with ${early} of 13 country files read`);
- docs/ro-review.md: rows for the new keys (regenerate after the dictionary change)
- sw.js: SHELL_VERSION bump (any change to index.html's shell), history line in CLAUDE.md
    sw.js:17: remembered to change SHELL_VERSION.
    sw.js:26: SHELL_VERSION names the shell cache. Change it whenever this file
    sw.js:31: const SHELL_VERSION = 'v40';
    sw.js:32: const SHELL_CACHE = 'football-shell-' + SHELL_VERSION;

### Stays manual

- data/clubs-manual.csv: every skip, tier, ground, capacity, hand-named row (decisions)
- data/roster-links-manual.csv: identity links for rows the reader refuses
- data/fixture-links-manual.csv: abbreviations the fixture matcher refuses
- data/coordinate-reviews.csv: open/rejected rows for clubs left unplaced
- the pass over the proposals: each skip needs two complete division articles agreeing on the absence AND an independent statement of the reason (the Hermannstadt standard)
- the CLAUDE.md entry for the country, the roster-check, rank-diagnostic, StadiumDB and capacity dispatches on the branch, and the merge

## Grounds and capacities

- Wikidata name search for 11 ground(s) with no other position: 0 found an item with a position
- OpenStreetMap: queried; 373 named stadium / sports centre / soccer pitch elements within 3000 m of 25 club position(s) [Overpass requests this run: 5 of the cap 60]
- https://stadiumdb.com/robots.txt read (1 disallow rule(s)); /stadiums/ is allowed
- StadiumDB slug 'bel' answered a table of 37 grounds (37 with a capacity); tried: bel: answered (configured in crosscheck_stadiumdb.COUNTRY_PAGES)

12 ground(s) agree everywhere and need nothing; 17 need a look:

| verdict | club | table's ground | flags |
|---|---|---|---|
| attention | Antwerp | Bosuilstadion | Wikidata names 'Stadion Broodstraat', the table 'Bosuilstadion' |
| attention | Cercle Brugge | Jan Breydel Stadium | P115 shared with Club Brugge |
| attention | Club Brugge | Jan Breydel Stadium | P115 shared with Cercle Brugge |
| attention | Gent | Planet Group Arena | Wikidata names 'Jules Ottenstadion', the table 'Planet Group Arena' \| THE MAP WOULD BE 2807 m FROM THE PROPOSAL |
| unplaced | La Louvière | Easi Arena | UNPLACED by the build |
| unplaced | Lommel SK | Soevereinstadion | UNPLACED by the build |
| attention | Beerschot |  | NO ground-specific position found |
| attention | Dender EH |  | NO ground-specific position found |
| attention | Eupen |  | NO ground-specific position found |
| unplaced | Francs Borains |  | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| unplaced | Hasselt |  | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| attention | Virton |  | NO ground-specific position found |
| unplaced | Lokeren |  | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| attention | Lierse |  | NO ground-specific position found |
| attention | Patro Eisden Maasmechelen |  | the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| unplaced | RFC Liège |  | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| unplaced | Seraing |  | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |


## Candidates

### roster-ok (20)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q187528 | Anderlecht | table row 'Anderlecht' in 2026–27 Belgian Pro League | team=Anderlecht; ground=Constant Vanden Stock Stadium; capacity=21500; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 1935-) |
| 1 | Q732002 | Antwerp | table row 'Antwerp' in 2026–27 Belgian Pro League | team=Antwerp; ground=Bosuilstadion; capacity=21000; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2017-) |
| 1 | Q509170 | Beveren | table row 'Beveren' in 2026–27 Belgian Pro League | team=Beveren; ground=Freethiel Stadion; capacity=8190; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2012-2021) \| Belgian First Division B (normal, 2021-2026) \| Belgian Pro League (preferred, 2026-) |
| 1 | Q364698 | Cercle Brugge | table row 'Cercle Brugge' in 2026–27 Belgian Pro League | team=Cercle Brugge; ground=Jan Breydel Stadium; capacity=29042; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2018-) |
| 1 | Q19585 | Charleroi | table row 'Charleroi' in 2026–27 Belgian Pro League | team=Charleroi; ground=Stade du Pays de Charleroi; capacity=14000; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2012-) |
| 1 | Q190916 | Club Brugge | table row 'Club Brugge' in 2026–27 Belgian Pro League | team=Club Brugge; ground=Jan Breydel Stadium; capacity=29042; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 1959-) |
| 1 | Q216032 | Genk | table row 'Genk' in 2026–27 Belgian Pro League | team=Genk; ground=Cegeka Arena; capacity=24956; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 1996-) |
| 1 | Q18232 | Gent | table row 'Gent' in 2026–27 Belgian Pro League | team=Gent; ground=Planet Group Arena; capacity=20000; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 1989-) |
| 1 | Q618620 | Kortrijk | table row 'Kortrijk' in 2026–27 Belgian Pro League | team=Kortrijk; ground=Guldensporen Stadion; capacity=9399; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2008-2025) \| Challenger Pro League (normal, 2025-2026) \| Belgian Pro League (preferred, 2026-) |
| 1 | Q536651 | La Louvière | table row 'La Louvière' in 2026–27 Belgian Pro League | team=La Louvière; ground=Easi Arena; capacity=8050; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2025-) |
| 1 | Q113000 | Mechelen | table row 'Mechelen' in 2026–27 Belgian Pro League | team=Mechelen; ground=AFAS-stadion Achter de Kazerne; capacity=16700; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2019-) |
| 1 | Q916199 | OH Leuven | table row 'OH Leuven' in 2026–27 Belgian Pro League | team=OH Leuven; ground=Den Dreef; capacity=10000; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2020-) |
| 1 | Q138248 | Sint-Truiden | table row 'Sint-Truiden' in 2026–27 Belgian Pro League | team=Sint-Truiden; ground=Stayen; capacity=14600; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2015-) |
| 1 | Q190561 | Standard Liège | table row 'Standard Liège' in 2026–27 Belgian Pro League | team=Standard Liège; ground=Stade Maurice Dufrasne; capacity=30023; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 1921-) |
| 1 | Q196160 | Union SG | table row 'Union SG' in 2026–27 Belgian Pro League | team=Union SG; ground=Stade Joseph Marien; article=2026–27 Belgian Pro League; tags=Belgian First Division B (normal, 2015-2021) \| Belgian Pro League (preferred, 2021-) |
| 1 | Q849544 | Westerlo | table row 'Westerlo' in 2026–27 Belgian Pro League | team=Westerlo; ground=Het Kuipje; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2014-2017) \| Challenger Pro League (normal, 2017-07-01-2022) \| Belgian Pro League (preferred, 2022-) |
| 1 | Q376635 | Zulte Waregem | table row 'Zulte Waregem' in 2026–27 Belgian Pro League | team=Zulte Waregem; ground=Regenboogstadion; capacity=12500; article=2026–27 Belgian Pro League; tags=Belgian Pro League (normal, 2005-2023) \| Challenger Pro League (normal, 2023-2025) \| Belgian Pro League (preferred, 2025-) |
| 2 | Q2268833 | Beerschot | table row 'Beerschot' in 2026–27 Challenger Pro League | team=Beerschot; article=2026–27 Challenger Pro League; tags=Challenger Pro League (normal, 2017-2020) \| Belgian Pro League (normal, 2020-2022-06-30) \| Challenger Pro League (normal, 2022-07-01-2024) \| Belgian Pro League (normal, 2024-2025) \| Challenger Pro Lea |
| 2 | Q1423718 | Eupen | table row 'Eupen' in 2026–27 Challenger Pro League | team=Eupen; article=2026–27 Challenger Pro League; tags=Belgian Pro League (normal, 2016-2024) \| Challenger Pro League (preferred, 2024-) |
| 2 | Q925973 | Seraing | table row 'Seraing' in 2026–27 Challenger Pro League | team=Seraing; article=2026–27 Challenger Pro League; tags=Belgian Pro League (normal, 2021-2023) \| Challenger Pro League (preferred, 2023-) |

### roster-untagged (7)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q18001655 | Francs Borains | table row 'Francs Borains' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Francs Borains; article=2026–27 Challenger Pro League; fallback=hand-named fallback candidate; tags=no P118 |
| 2 | Q2456491 | Hasselt | table row 'Hasselt' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Hasselt; article=2026–27 Challenger Pro League; other_leagues=Belgian Third Division; named_in_team_changes=2026–27 Challenger Pro League: Virton and Hasselt were promoted from the 2025–26 Belgian Division 1 , respectively as FFA (Francophone) and VV (Fle |
| 2 | Q2313985 | Lierse | table row 'Lierse' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Lierse; article=2026–27 Challenger Pro League; other_leagues=Belgian Third Division \| Belgian First Division B; fallback=hand-named fallback candidate; tags=Belgian Third Division (normal, ?-2020-06-30) \| Belgian First Division B (preferred, 2020-07-01-) |
| 2 | Q95183770 | Lokeren | table row 'Lokeren' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Lokeren; article=2026–27 Challenger Pro League; fallback=hand-named fallback candidate; tags=no P118 |
| 2 | Q2308515 | Patro Eisden Maasmechelen | table row 'Patro Eisden Maasmechelen' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Patro Eisden Maasmechelen; article=2026–27 Challenger Pro League; other_leagues=Belgian Division 1; fallback=hand-named fallback candidate; tags=Belgian Division 1 (normal, 2019-) |
| 2 | Q1347229 | RFC Liège | table row 'RFC Liège' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=RFC Liège; article=2026–27 Challenger Pro League; other_leagues=Belgian Promotion; fallback=hand-named fallback candidate; tags=Belgian Promotion (normal) |
| 2 | Q650917 | Virton | table row 'Virton' in 2026–27 Challenger Pro League; carries no tag of the tracked leagues | team=Virton; article=2026–27 Challenger Pro League; other_leagues=Belgian First Division B; named_in_team_changes=2026–27 Challenger Pro League: Virton and Hasselt were promoted from the 2025–26 Belgian Division 1 , respectively as FFA (Francophone) and VV (Fl |

### roster-wrong-tier (2)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q1668203 | Lommel SK | table row 'Lommel SK' in 2026–27 Belgian Pro League; Wikidata tags it at tier 2 | team=Lommel SK; ground=Soevereinstadion; capacity=8000; article=2026–27 Belgian Pro League; roster_tier=1; tagged_tier=2; named_in_team_changes=2026–27 Challenger Pro League: Beveren , Kortrijk and Lommel were promoted to the 2026–27 Belgian Pro League , respe |
| 2 | Q1065328 | Dender EH | table row 'Dender EH' in 2026–27 Challenger Pro League; Wikidata tags it at tier 1 | team=Dender EH; article=2026–27 Challenger Pro League; roster_tier=2; tagged_tier=1; named_in_team_changes=2026–27 Challenger Pro League: Dender EH was relegated from the 2025–26 Belgian Pro League , returning after playing two seasons at the top level.; tags= |

### roster-unread (4)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 |  | Club NXT U23 [ a ] | 'Club NXT U23 [ a ]' in 2026–27 Challenger Pro League: a reserve side linked to 'Club NXT' - the reserve marker does not agree, so it is not read as that club | needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map |
| 2 |  | Jong KAA Gent U23 [ a ] | 'Jong KAA Gent U23 [ a ]' in 2026–27 Challenger Pro League: a reserve side linked to 'KAA Gent' - the reserve marker does not agree, so it is not read as that c | needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map |
| 2 |  | Jong Genk U23 [ a ] | 'Jong Genk U23 [ a ]' in 2026–27 Challenger Pro League: a reserve side linked to 'KRC Genk' - the reserve marker does not agree, so it is not read as that club | needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map |
| 2 |  | RSCA Futures U23 [ a ] | 'RSCA Futures U23 [ a ]' in 2026–27 Challenger Pro League: a reserve side linked to 'RSCA Futures' - the reserve marker does not agree, so it is not read as tha | needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map |

### extra-tagged (6)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q101625593 | Club NXT | The most senior team of Club NXT acts as Club Brugge's reserve team, and competes in the Challenger Pro League, the second flight of Belgian football. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; intro_mentions_a_tracked_league=Challenger Pro League (read the sentence: a past season or now?); absent_from |
| 2 | Q113884742 | Jong Genk | [nl] Jong Genk is de beloftenploeg van KRC Genk en speelt sinds het seizoen 2022-2023 in de Challenger Pro League, het tweede hoogste niveau van België. | drawn_by_build=yes: has a position; intro_mentions_a_tracked_league=Challenger Pro League (read the sentence: a past season or now?); absent_from=2026–27 Belgian Pro League (18 clubs resolved, 0 unread rows); 2026–27 Challenger Pro League (11 clubs resolved, 4 |
| 2 | Q1053917 | K.S.V. Roeselare | It last played at the highest level of Belgian football from 2005–06 until 2009–10, but finally folded in 2020 after having relegated to the third level and goi | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); absent_from=2026–27 Belgian Pro League (18 clubs resolved, 0 unread rows); 2026–27 Challenger Pro League (11 clubs resolved, 4 unread rows); tags=Challenger Pro L |
| 2 | Q20979061 | RWDM Brussels | The team last played in the Belgian Division 1, the third tier of the Belgian football league system. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); absent_from=2026–27 Belgian Pro League (18 club |
| 2 | Q291937 | Royale Union Tubize-Braine | The team is set to play in Belgian National Division 1 from 2024–25, third tier of Belgian football after promotion from Belgian Division 2 in 2023–24. | drawn_by_build=yes: has a position; absent_from=2026–27 Belgian Pro League (18 clubs resolved, 0 unread rows); 2026–27 Challenger Pro League (11 clubs resolved, 4 unread rows); tags=Challenger Pro League (normal); p576=none; tag_dates=?-; named_in_team_changes |
| 2 | Q115476719 | SL16 FC | They are one of the most successful clubs in Belgium, having won the Belgian league on ten occasions, most recently in 2007–08 and 2008–09. | drawn_by_build=yes: has a position; absent_from=2026–27 Belgian Pro League (18 clubs resolved, 0 unread rows); 2026–27 Challenger Pro League (11 clubs resolved, 4 unread rows); tags=Challenger Pro League (normal); p576=none; tag_dates=?-; named_in_team_changes |

### not-a-club (2)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q3906017 | 1991–92 R.S.C. Anderlecht season | Wikidata says it is a 'association football team season', which is a list, a season, a match, a history or a fiction, not a club | types=association football team season; tags=Belgian Pro League (normal) |
| 1 | Q4535270 | 1996–97 R.S.C. Anderlecht season | Wikidata says it is a 'association football team season', which is a list, a season, a match, a history or a fiction, not a club | types=association football team season; tags=Belgian Pro League (normal) |

### duplicate (6)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q190916 | Club Brugge K.V. | group D1: 2 items share ground 'Jan Breydel Stadium' | group=D1; basis=ground; members: Q190916 Club Brugge K.V. [association football club, association football team; sitelinks 69; tier 1; roster yes; P831 -; P576 -] \|\| Q364698 Cercle Brugge K.S.V. [association football club; sitelinks 46; tier 1; roster yes; P83 |
| 1 | Q364698 | Cercle Brugge K.S.V. | group D1: 2 items share ground 'Jan Breydel Stadium' | group=D1; basis=ground; members: Q190916 Club Brugge K.V. [association football club, association football team; sitelinks 69; tier 1; roster yes; P831 -; P576 -] \|\| Q364698 Cercle Brugge K.S.V. [association football club; sitelinks 46; tier 1; roster yes; P83 |
| 2 | Q113884742 | Jong Genk | group D2: 2 items share ground 'Cegeka Arena' | group=D2; basis=ground; members: Q113884742 Jong Genk [association football club, reserve team; sitelinks 2; tier 2; roster no; P831 -; P576 -] \|\| Q216032 K.R.C. Genk [association football club; sitelinks 58; tier 1; roster yes; P831 -; P576 -] |
| 1 | Q216032 | K.R.C. Genk | group D2: 2 items share ground 'Cegeka Arena' | group=D2; basis=ground; members: Q113884742 Jong Genk [association football club, reserve team; sitelinks 2; tier 2; roster no; P831 -; P576 -] \|\| Q216032 K.R.C. Genk [association football club; sitelinks 58; tier 1; roster yes; P831 -; P576 -] |
| 2 | Q115476719 | SL16 FC | group D3: 2 items share ground 'Stade Maurice Dufrasne' | group=D3; basis=ground; members: Q115476719 SL16 FC [association football club, reserve team; sitelinks 4; tier 2; roster no; P831 -; P576 -] \|\| Q190561 Standard Liège [association football club; sitelinks 65; tier 1; roster yes; P831 -; P576 -] |
| 1 | Q190561 | Standard Liège | group D3: 2 items share ground 'Stade Maurice Dufrasne' | group=D3; basis=ground; members: Q115476719 SL16 FC [association football club, reserve team; sitelinks 4; tier 2; roster no; P831 -; P576 -] \|\| Q190561 Standard Liège [association football club; sitelinks 65; tier 1; roster yes; P831 -; P576 -] |

### two-grounds (1)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q115476719 | SL16 FC | 2 truthy P115 at best rank: Stade Maurice Dufrasne Q959934 \| SL16 Football Campus Q17620899 | the club query keeps whichever row arrives first (the SC Freiburg shape); a hand row pins one |

### ground-proposal (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q187528 | Anderlecht | Anderlecht: ground 'Constant Vanden Stock Stadium' - ok | verdict=ok; ground_table=Constant Vanden Stock Stadium; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=[[Constant Vanden Stock Stadium; Wikidata P115=Lotto Park / Constant Vanden Stock Stadium; proposed_venue= |
| 1 | Q732002 | Antwerp | Antwerp: ground 'Bosuilstadion' - attention | verdict=attention; flags=Wikidata names 'Stadion Broodstraat', the table 'Bosuilstadion'; ground_table=Bosuilstadion; named_by=3 place(s): table, StadiumDB, club article infobox; other_names=club article infobox=Bosuilstadion; Wikidata P115=Stadion Broodstraat |
| 1 | Q509170 | Beveren | Beveren: ground 'Freethiel Stadion' - ok | verdict=ok; ground_table=Freethiel Stadion; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Freethiel Stadion, Beveren; Wikidata P115=Freethiel Stadion / Freethielstadion; proposed_venue=Freethiel Stadion; prop |
| 1 | Q364698 | Cercle Brugge | Cercle Brugge: ground 'Jan Breydel Stadium' - attention | verdict=attention; flags=P115 shared with Club Brugge; ground_table=Jan Breydel Stadium; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Jan Breydel Stadium; Wikidata P115=Jan Breydel Stadium / Jan B |
| 1 | Q19585 | Charleroi | Charleroi: ground 'Stade du Pays de Charleroi' - ok | verdict=ok; ground_table=Stade du Pays de Charleroi; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Stade du Pays de Charleroi; Wikidata P115=Stade du Pays de Charleroi / stade du Pays de Charleroi; proposed_v |
| 1 | Q190916 | Club Brugge | Club Brugge: ground 'Jan Breydel Stadium' - attention | verdict=attention; flags=P115 shared with Cercle Brugge; ground_table=Jan Breydel Stadium; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Jan Breydel Stadium; Wikidata P115=Jan Breydel Stadium / Jan |
| 1 | Q216032 | Genk | Genk: ground 'Cegeka Arena' - ok | verdict=ok; ground_table=Cegeka Arena; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Cegeka Arena; Wikidata P115=Cegeka Arena / Cristal Arena; proposed_venue=Cegeka Arena; proposed_position=51.005000 / 5.5333 |
| 1 | Q18232 | Gent | Gent: ground 'Planet Group Arena' - attention | verdict=attention; flags=Wikidata names 'Jules Ottenstadion', the table 'Planet Group Arena' \| THE MAP WOULD BE 2807 m FROM THE PROPOSAL; ground_table=Planet Group Arena; named_by=3 place(s): table, StadiumDB, club article infobox; other_names=club article inf |
| 1 | Q618620 | Kortrijk | Kortrijk: ground 'Guldensporen Stadion' - ok | verdict=ok; ground_table=Guldensporen Stadion; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Guldensporenstadion, Kortrijk; Wikidata P115=Guldensporen Stadion / Guldensporenstadion; proposed_venue=Guldenspore |
| 1 | Q536651 | La Louvière | La Louvière: ground 'Easi Arena' - unplaced | verdict=unplaced; flags=UNPLACED by the build; notes=Wikidata names no ground; ground_table=Easi Arena; named_by=2 place(s): table, club article infobox; other_names=club article infobox=Easi Arena; proposed_venue=Easi Arena; proposed_position=50.477503 / 4.20 |
| 1 | Q1668203 | Lommel SK | Lommel SK: ground 'Soevereinstadion' - unplaced | verdict=unplaced; flags=UNPLACED by the build; notes=Wikidata names no ground; ground_table=Soevereinstadion; named_by=2 place(s): table, club article infobox; other_names=club article infobox=Soevereinstadion, Lommel; proposed_venue=Soevereinstadion; proposed |
| 1 | Q113000 | Mechelen | Mechelen: ground 'AFAS-stadion Achter de Kazerne' - ok | verdict=ok; ground_table=AFAS-stadion Achter de Kazerne; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Achter de Kazerne; Wikidata P115=AFAS Stadion KV Mechelen / Scarlet Stadion Achter De Kazerne; |
| 1 | Q916199 | OH Leuven | OH Leuven: ground 'Den Dreef' - ok | verdict=ok; ground_table=Den Dreef; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Den Dreef; Wikidata P115=Den Dreef / Stadion Den Dreef; proposed_venue=Den Dreef; proposed_position=50.868333 / 4.694167; posi |
| 1 | Q138248 | Sint-Truiden | Sint-Truiden: ground 'Stayen' - ok | verdict=ok; ground_table=Stayen; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Stayen; Wikidata P115=Stayen / Stayen (stadion); proposed_venue=Stayen; proposed_position=50.813611 / 5.165278; position_sources= |
| 1 | Q190561 | Standard Liège | Standard Liège: ground 'Stade Maurice Dufrasne' - ok | verdict=ok; ground_table=Stade Maurice Dufrasne; named_by=4 place(s): table, Wikidata P115, StadiumDB, club article infobox; other_names=club article infobox=Stade Maurice Dufrasne; Wikidata P115=Stade Maurice Dufrasne / stade Maurice-Dufrasne; StadiumDB=Stade |
| 1 | Q196160 | Union SG | Union SG: ground 'Stade Joseph Marien' - ok | verdict=ok; ground_table=Stade Joseph Marien; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Joseph Marien Stadium; Wikidata P115=Joseph Marien Stadium / Joseph Marien Stadion; proposed_venue=Stade Joseph Mari |
| 1 | Q849544 | Westerlo | Westerlo: ground 'Het Kuipje' - ok | verdict=ok; ground_table=Het Kuipje; named_by=4 place(s): table, Wikidata P115, StadiumDB, club article infobox; other_names=club article infobox=Het Kuipje; Wikidata P115=Het Kuipje / 't Kuipje; StadiumDB='t Kuipje; proposed_venue=Het Kuipje; proposed_positio |
| 1 | Q376635 | Zulte Waregem | Zulte Waregem: ground 'Regenboogstadion' - ok | verdict=ok; ground_table=Regenboogstadion; named_by=2 place(s): table, Wikidata P115; other_names=club article infobox=[[Elindus Arena; Wikidata P115=Regenboogstadion / stade Arc-en-ciel; StadiumDB=Elindus Arena; proposed_venue=Regenboogstadion; proposed_posit |
| 2 | Q2268833 | Beerschot | Beerschot: ground '' - attention | verdict=attention; flags=NO ground-specific position found; notes=Wikidata names 'Olympisch Stadion Antwerp', the table '' - the table is the odd one out (three places agree with each other); named_by=1 place(s): table; other_names=club article infobox=[[Olymp |
| 2 | Q1065328 | Dender EH | Dender EH: ground '' - attention | verdict=attention; flags=NO ground-specific position found; notes=Wikidata names 'Florent Beeckmanstadion', the table '' - the table is the odd one out (three places agree with each other); named_by=1 place(s): table; other_names=club article infobox=Florent B |
| 2 | Q1423718 | Eupen | Eupen: ground '' - attention | verdict=attention; flags=NO ground-specific position found; notes=Wikidata names 'Kehrweg Stadion', the table '' - the table is the odd one out (three places agree with each other); named_by=1 place(s): table; other_names=club article infobox=Kehrwegstadion; W |
| 2 | Q18001655 | Francs Borains | Francs Borains: ground '' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox=Stade Robert |
| 2 | Q2456491 | Hasselt | Hasselt: ground '' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox=Stedelijk Spo |
| 2 | Q650917 | Virton | Virton: ground '' - attention | verdict=attention; flags=NO ground-specific position found; notes=Wikidata names 'Stade Yvan Georges', the table '' - the table is the odd one out (three places agree with each other); named_by=1 place(s): table; other_names=club article infobox=Stade Yvan Geo |
| 2 | Q95183770 | Lokeren | Lokeren: ground '' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox=Daknamstadion |
| 2 | Q2313985 | Lierse | Lierse: ground '' - attention | verdict=attention; flags=NO ground-specific position found; notes=Wikidata names 'Herman Vanderpoortenstadion', the table '' - the table is the odd one out (three places agree with each other); named_by=1 place(s): table; other_names=club article infobox=Herma |
| 2 | Q2308515 | Patro Eisden Maasmechelen | Patro Eisden Maasmechelen: ground '' - attention | verdict=attention; flags=the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox=Gemeentelijk Sportparkstadion, {{cit |
| 2 | Q1347229 | RFC Liège | RFC Liège: ground '' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox={{ill; build_ |
| 2 | Q925973 | Seraing | Seraing: ground '' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; named_by=1 place(s): table; other_names=club article infobox=Stade du Pair |

### capacity-proposal (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q187528 | Anderlecht | Anderlecht: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 21500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 21500, wikidata 21500); the table and Wikidata are both Wikipedia's; |
| 1 | Q732002 | Antwerp | Antwerp: agreed, proposed 21000 | verdict=agreed; proposed=21000; action=REPLACE the map's 5350; rule=table 21000 agrees within 5% with stadiumdb 21000; figures=table 21000; Wikidata 5350 (map's figure); OpenStreetMap None; StadiumDB 21000; not_used=Wikidata's 5350 is the capacity of Stadion B |
| 1 | Q509170 | Beveren | Beveren: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 13290 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 8190, wikidata 13290); the table and Wikidata are both Wikipedia's; f |
| 1 | Q364698 | Cercle Brugge | Cercle Brugge: agreed, proposed 29042 | verdict=agreed; proposed=29042; action=keep (the map's figure is in the agreement); rule=table 29042 agrees within 5% with stadiumdb 29042, wikidata 29062; figures=table 29042; Wikidata 29062 (map's figure); OpenStreetMap None; StadiumDB 29042; stadiumdb=Jan B |
| 1 | Q19585 | Charleroi | Charleroi: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 14891 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 14000, wikidata 14891); the table and Wikidata are both Wikipedia's; |
| 1 | Q190916 | Club Brugge | Club Brugge: agreed, proposed 29042 | verdict=agreed; proposed=29042; action=keep (the map's figure is in the agreement); rule=table 29042 agrees within 5% with stadiumdb 29042, wikidata 29062; figures=table 29042; Wikidata 29062 (map's figure); OpenStreetMap None; StadiumDB 29042; stadiumdb=Jan B |
| 1 | Q216032 | Genk | Genk: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 25000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 24956, wikidata 25000); the table and Wikidata are both Wikipedia's; |
| 1 | Q18232 | Gent | Gent: agreed, proposed 20000 | verdict=agreed; proposed=20000; action=REPLACE the map's 12919; rule=table 20000 agrees within 5% with stadiumdb 19999; figures=table 20000; Wikidata 12919 (map's figure); OpenStreetMap None; StadiumDB 19999; not_used=Wikidata's 12919 is the capacity of Jules |
| 1 | Q618620 | Kortrijk | Kortrijk: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 9399 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 9399, wikidata 9399); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q536651 | La Louvière | La Louvière: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 8050); the table and Wikidata are both Wikipedia's; figures=table 8050; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 1 | Q1668203 | Lommel SK | Lommel SK: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 8000); the table and Wikidata are both Wikipedia's; figures=table 8000; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 1 | Q113000 | Mechelen | Mechelen: agreed, proposed 16700 | verdict=agreed; proposed=16700; action=REPLACE the map's 13213; rule=table 16700 agrees within 5% with stadiumdb 16672; figures=table 16700; Wikidata 13213 (map's figure); OpenStreetMap None; StadiumDB 16672; stadiumdb=AFAS Stadion (Mechelen) - name-exact via |
| 1 | Q916199 | OH Leuven | OH Leuven: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 9493 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 10000, wikidata 9493); the table and Wikidata are both Wikipedia's; fi |
| 1 | Q138248 | Sint-Truiden | Sint-Truiden: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 11250 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 14600, wikidata 11250); the table and Wikidata are both Wikipedia's; |
| 1 | Q190561 | Standard Liège | Standard Liège: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 30023 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 30023, wikidata 30023); the table and Wikidata are both Wikipedia's; |
| 1 | Q196160 | Union SG | Union SG: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5100 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 5100); the table and Wikidata are both Wikipedia's; figures=table N |
| 1 | Q849544 | Westerlo | Westerlo: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 7982 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 7982); the table and Wikidata are both Wikipedia's; figures=table N |
| 1 | Q376635 | Zulte Waregem | Zulte Waregem: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 10200 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 12500, wikidata 10200); the table and Wikidata are both Wikipedia's; |
| 2 | Q2268833 | Beerschot | Beerschot: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 12771 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 12771); the table and Wikidata are both Wikipedia's; figures=table |
| 2 | Q1065328 | Dender EH | Dender EH: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 12000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 12000); the table and Wikidata are both Wikipedia's; figures=table |
| 2 | Q1423718 | Eupen | Eupen: agreed, proposed 8400 | verdict=agreed; proposed=8400; action=keep (the map's figure is in the agreement); rule=stadiumdb 8400 agrees within 5% with wikidata 8000; figures=table None; Wikidata 8000 (map's figure); OpenStreetMap None; StadiumDB 8400; stadiumdb=Kehrwegstadion (Eupen) - |
| 2 | Q18001655 | Francs Borains | Francs Borains: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |
| 2 | Q2456491 | Hasselt | Hasselt: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |
| 2 | Q650917 | Virton | Virton: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 4000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 4000); the table and Wikidata are both Wikipedia's; figures=table N |
| 2 | Q95183770 | Lokeren | Lokeren: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |
| 2 | Q2313985 | Lierse | Lierse: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 14538 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (wikidata 14538); the table and Wikidata are both Wikipedia's; figures=table |
| 2 | Q2308515 | Patro Eisden Maasmechelen | Patro Eisden Maasmechelen: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |
| 2 | Q1347229 | RFC Liège | RFC Liège: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |
| 2 | Q925973 | Seraing | Seraing: none, blank | verdict=none; proposed=BLANK; rule=no source has a figure; figures=table None; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this club's name |

## Appendix: tagged but dissolved (not drawn)

- Q646079 Beerschot A.C. (P576 2013)
- Q1669847 K.F.C. Lommel S.K. (P576 2003)
- Q221940 K.S.C. Lokeren Oost-Vlaanderen (P576 2020)
- Q961309 K.S.V. Waregem (P576 2001)
- Q41478744 KFC Winterslag (P576 1988)
- Q2584486 Olympia Club de Bruxelles (P576 1909)
- Q490586 R.A.E.C. Mons (P576 2015)
- Q967104 R.F.C. Seraing (P576 1996)
- Q2312558 Racing White Daring Molenbeek (P576 2002)
- Q578104 Royal Daring Club Molenbeek (P576 1973)
- Q2195773 Royal Excel Mouscron (P576 2022)
- Q865735 Royal Excelsior Mouscron (P576 2009)
- Q3486282 Skill F.C. de Bruxelles (P576 1902)
- Q2272132 Sporting Club de Bruxelles (P576 1897)
- Q1901250 Union F.C. d'Ixelles (P576 1901)

## Appendix: tagged extras whose tag is not truthy (not drawn)

- Q370206 KV Oostende (shape A)
