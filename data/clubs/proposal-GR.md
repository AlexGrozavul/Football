# Proposal for GR (Greece)

Generated 2026-10-22 14:10 UTC by `tools/propose_country.py`. **Read-only evidence, not decisions**: nothing here was written to a hand-written file or a club file; a gap is a gap.

## Summary

| kind | rows |
|---|---|
| roster-ok | 29 |
| roster-unread | 1 |
| extra-tagged | 2 |
| not-a-club | 1 |
| duplicate | 2 |
| ground-proposal | 29 |
| capacity-proposal | 29 |

Tagged but dissolved (not drawn by the build, no row): 0; tagged extras whose tag is not truthy (not drawn, no row): 6; women's football items pointing at a club, carrying neither tag: 0 (other-sport items ignored: 1).

**Reader gaps: 1 roster row(s) the reader cannot read** (kind roster-unread).

Step durations (s): 1 rosters 2.4, 2 leagues 7.9, 3 items 2.3, 4 rank cross-check 1.1, 5 evidence for extras 1.3, 6 candidates 0.0, 6b grounds and capacities 698.2, 7 wiring patch 0.4

## Leagues

| tier | article | league item | label | found via | P3983 | P17 | women-word check |
|---|---|---|---|---|---|---|---|
| 1 | 2026–27 Super League Greece | Q235114 | Super League Greece | the article's title without the season, [[Super League Greece]] (a fallback: check the label and P17 in this table) | none | Q41 Greece | none |
| 2 | 2026–27 Super League Greece 2 | Q63980269 | Super League Greece 2 | the article's title without the season, [[Super League Greece 2]] (a fallback: check the label and P17 in this table) | none | Q41 Greece | none |

P3983 and P17 are printed, not used: the country Q-id given on the command line is `Q41`.

### Items labelled like a tier, or succeeded by it (the 'old Second Division' trap)

None found.


## Wiring patch (printed, not applied)

### data/league-tiers.csv — append

```
Q235114,1,Super League Greece,GR
Q63980269,2,Super League Greece 2,GR
```

### data/league-rosters.csv — append

```
Q235114,GR,1,2026-27,2026–27 Super League Greece,
Q63980269,GR,2,2026-27,2026–27 Super League Greece 2,
```

### COUNTRY_BOX (tools/fetch_clubs.py)

- north: (41.74886, 26.17267) normal
- south: (34.69698, 24.09585) normal
- east: (35.9229, 29.7291) normal
- west: (39.69181618, 20.0084424) normal
- proposal from best rank: `"GR": {"lat": (34.55, 41.9), "lon": (19.86, 29.88)},`
- proposal from normal rank only: `"GR": {"lat": (34.55, 41.9), "lon": (19.86, 29.88)},`

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

- Wikidata name search for 4 ground(s) with no other position: 0 found an item with a position
- OpenStreetMap: queried; 277 named stadium / sports centre / soccer pitch elements within 3000 m of 27 club position(s); 1 of 4 ground(s) with no other position found an element of exactly that name by a search of the whole country [Overpass requests this run: 8 of the cap 60]
- https://stadiumdb.com/robots.txt read (1 disallow rule(s)); /stadiums/ is allowed
- StadiumDB slug 'gre' answered a table of 29 grounds (29 with a capacity); tried: gre: answered (configured in crosscheck_stadiumdb.COUNTRY_PAGES)

24 ground(s) agree everywhere and need nothing; 5 need a look:

| verdict | club | table's ground | flags |
|---|---|---|---|
| attention | A.E. Kifisia | Leoforos Alexandras Stadium | P115 shared with Panathinaikos |
| attention | Panathinaikos | Athens Olympic Stadium | P115 shared with A.E. Kifisia \| Wikidata names 'Apostolos Nikolaidis Stadium', the table 'Athens Olympic Stadium' \| THE MAP WOULD BE 211586 m FROM THE PROPOSAL |
| unplaced | Hellas Syros | Ermoupoli Municipal Stadium | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |
| unplaced | Nestos Chrysoupoli | Chrysoupoli Municipal Stadium | UNPLACED by the build \| NO ground-specific position found |
| unplaced | Zakynthos | Zakynthos Municipal Stadium | Wikidata names 'Δημοτικό Στάδιο Ζακύνθου', the table 'Zakynthos Municipal Stadium' \| UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found |


## Candidates

### roster-ok (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q16245443 | A.E. Kifisia | table row 'A.E. Kifisia' in 2026–27 Super League Greece | team=A.E. Kifisia; ground=Leoforos Alexandras Stadium; capacity=16003; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2023-2024) \| Super League Greece 2 (normal, 2024-2025) \| Super League Greece (preferred, 2025-) |
| 1 | Q201584 | AEK Athens | table row 'AEK Athens' in 2026–27 Super League Greece | team=AEK Athens; ground=Agia Sophia Stadium; capacity=32500; article=2026–27 Super League Greece; tags=Super League Greece (preferred, 2015-) \| Super League Greece (normal, ?-2013) |
| 1 | Q219926 | Aris | table row 'Aris' in 2026–27 Super League Greece | team=Aris; ground=Kleanthis Vikelidis Stadium; capacity=22800; article=2026–27 Super League Greece; tags=Super League Greece (preferred, 2018-) \| Super League Greece (normal, ?-2014) |
| 1 | Q757320 | Asteras Tripolis | table row 'Asteras Tripolis' in 2026–27 Super League Greece | team=Asteras Tripolis; ground=Theodoros Kolokotronis Stadium; capacity=7423; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2007-) |
| 1 | Q757754 | Atromitos | table row 'Atromitos' in 2026–27 Super League Greece | team=Atromitos; ground=Peristeri Stadium; capacity=9050; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2009-) |
| 1 | Q592241 | Iraklis | table row 'Iraklis' in 2026–27 Super League Greece | team=Iraklis; ground=Kaftanzoglio Stadium; capacity=27560; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2026-) |
| 1 | Q2744247 | Kalamata | table row 'Kalamata' in 2026–27 Super League Greece | team=Kalamata; ground=Kalamata Municipal Stadium; capacity=4496; article=2026–27 Super League Greece; tags=Super League Greece (normal) |
| 1 | Q824450 | Levadiakos | table row 'Levadiakos' in 2026–27 Super League Greece | team=Levadiakos; ground=Levadia Municipal Stadium; capacity=5915; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2024-) |
| 1 | Q931704 | OFI | table row 'OFI' in 2026–27 Super League Greece | team=OFI; ground=Pankritio Stadium; capacity=26240; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2018-) |
| 1 | Q19628 | Olympiacos | table row 'Olympiacos' in 2026–27 Super League Greece | team=Olympiacos; ground=Karaiskakis Stadium; capacity=33334; article=2026–27 Super League Greece; tags=Super League Greece (normal, 1959-) |
| 1 | Q204888 | PAOK | table row 'PAOK' in 2026–27 Super League Greece | team=PAOK; ground=Toumba Stadium; capacity=28703; article=2026–27 Super League Greece; tags=Super League Greece (normal, 1959-) |
| 1 | Q4122219 | Panathinaikos | table row 'Panathinaikos' in 2026–27 Super League Greece | team=Panathinaikos; ground=Athens Olympic Stadium; capacity=69618; article=2026–27 Super League Greece; tags=Super League Greece (normal, 1959-) |
| 1 | Q1460053 | Panetolikos | table row 'Panetolikos' in 2026–27 Super League Greece | team=Panetolikos; ground=Panetolikos Stadium; capacity=7321; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2013-) |
| 1 | Q43375974 | Volos | table row 'Volos' in 2026–27 Super League Greece | team=Volos; ground=Panthessaliko Stadium; capacity=22700; article=2026–27 Super League Greece; tags=Super League Greece (normal, 2019-) |
| 2 | Q275626 | AEL | table row 'AEL' in 2026–27 Super League Greece 2 | team=AEL; ground=AEL FC Arena; capacity=16118; article=2026–27 Super League Greece 2; tags=Super League Greece (normal, 2016-2021) \| Super League Greece 2 (normal, 2021-2025) \| Super League Greece (normal, 2025-2026) \| Super League Greece 2 (preferred, 2026-) |
| 2 | Q123283162 | Anagennisi Karditsa | table row 'Anagennisi Karditsa' in 2026–27 Super League Greece 2 | team=Anagennisi Karditsa; ground=Karditsa Municipal Stadium; capacity=3500; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q619215 | Apollon Kalamaria | table row 'Apollon Kalamaria' in 2026–27 Super League Greece 2 | team=Apollon Kalamaria; ground=Kalamaria Stadium; capacity=6500; article=2026–27 Super League Greece 2; tags=Gamma Ethniki (normal, 2024-2026) \| Super League Greece 2 (preferred, 2026-) |
| 2 | Q1547133 | Athens Kallithea | table row 'Athens Kallithea' in 2026–27 Super League Greece 2 | team=Athens Kallithea; ground=Grigoris Lamprakis Stadium; capacity=6300; article=2026–27 Super League Greece 2; tags=Super League Greece (normal, 2024-2025) \| Super League Greece 2 (preferred, 2025-) |
| 2 | Q12872753 | Hellas Syros | table row 'Hellas Syros' in 2026–27 Super League Greece 2 | team=Hellas Syros; ground=Ermoupoli Municipal Stadium; capacity=2500; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q15309584 | Marko | table row 'Marko' in 2026–27 Super League Greece 2 | team=Marko; ground=Municipal Stadium of Markopoulo; capacity=3000; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q16845757 | Nestos Chrysoupoli | table row 'Nestos Chrysoupoli' in 2026–27 Super League Greece 2 | team=Nestos Chrysoupoli; ground=Chrysoupoli Municipal Stadium; capacity=5000; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q3180055 | Niki Volos | table row 'Niki Volos' in 2026–27 Super League Greece 2 | team=Niki Volos; ground=Pantelis Magoulas Stadium; capacity=2500; article=2026–27 Super League Greece 2; tags=Football League (normal, 1960-1961) \| Super League Greece (normal, 1961-1966) \| Football League (normal, 1966-1975) \| Football League (normal, 1976-19 |
| 2 | Q107410262 | Olympiacos B | table row 'Olympiacos B' in 2026–27 Super League Greece 2 | team=Olympiacos B; ground=Rentis Training Centre; capacity=3000; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q107849577 | PAOK B | table row 'PAOK B' in 2026–27 Super League Greece 2 | team=PAOK B; ground=Kalamaria Stadium; capacity=6500; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q25535620 | PAS Pyrgos | table row 'PAS Pyrgos' in 2026–27 Super League Greece 2 | team=PAS Pyrgos; ground=Pyrgos Municipal Stadium; capacity=6750; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q460494 | Panionios | table row 'Panionios' in 2026–27 Super League Greece 2 | team=Panionios; ground=Nea Smyrni Stadium; capacity=11700; article=2026–27 Super League Greece 2; tags=Gamma Ethniki (normal, 2020-2024) \| Super League Greece 2 (preferred, 2024-) |
| 2 | Q1417287 | Panserraikos | table row 'Panserraikos' in 2026–27 Super League Greece 2 | team=Panserraikos; ground=Serres Municipal Stadium; capacity=9500; article=2026–27 Super League Greece 2; tags=Super League Greece (normal, 2023-2026) \| Super League Greece 2 (preferred, 2026-) |
| 2 | Q433230 | Panthrakikos | table row 'Panthrakikos' in 2026–27 Super League Greece 2 | team=Panthrakikos; ground=Komotini Municipal Stadium; capacity=6198; article=2026–27 Super League Greece 2; tags=Super League Greece 2 (normal) |
| 2 | Q3292651 | Zakynthos | table row 'Zakynthos' in 2026–27 Super League Greece 2 | team=Zakynthos; ground=Zakynthos Municipal Stadium; capacity=5000; article=2026–27 Super League Greece 2; tags=Gamma Ethniki (normal, 2022-2026) \| Super League Greece 2 (preferred, 2026-) |

### roster-unread (1)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 |  | Asteras Tripolis B | 'Asteras Tripolis B' in 2026–27 Super League Greece 2: a reserve side linked to 'Asteras Tripolis F.C.' - the reserve marker does not agree, so it is not read a | needs a hand link in data/roster-links-manual.csv, or the row is not a club on the map |

### extra-tagged (2)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q3292636 | F.S. Kozani | The club plays in Kozani FCA First Division, the fourth tier of Greek football. | drawn_by_build=yes: has a position; absent_from=2026–27 Super League Greece (14 clubs resolved, 0 unread rows); 2026–27 Super League Greece 2 (15 clubs resolved, 1 unread rows); tags=Super League Greece 2 (normal, 2023-2024) \| Gamma Ethniki (normal, 2024-2026) |
| 2 | Q16842502 | Kampaniakos F.C. | Kampaniakos F.C. is a Greek football club, based in Chalastra, Thessaloniki. [no sentence of the intro names a league] | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; absent_from=2026–27 Super League Greece (14 clubs resolved, 0 unread rows); 2026–27 Super League Greece 2 (15 |

### not-a-club (1)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q30646111 | 2016–17 Panionios G.S.S. season | Wikidata says it is a 'association football team season', which is a list, a season, a match, a history or a fiction, not a club | types=association football team season; tags=Super League Greece (normal) |

### duplicate (2)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q16245443 | A.E. Kifisia F.C. | group D1: 2 items share ground 'Apostolos Nikolaidis Stadium' | group=D1; basis=ground; members: Q16245443 A.E. Kifisia F.C. [men's association football club, association football club; sitelinks 16; tier 1; roster yes; P831 -; P576 -] \|\| Q4122219 Panathinaikos F.C. [association football club; sitelinks 70; tier 1; roster |
| 1 | Q4122219 | Panathinaikos F.C. | group D1: 2 items share ground 'Apostolos Nikolaidis Stadium' | group=D1; basis=ground; members: Q16245443 A.E. Kifisia F.C. [men's association football club, association football club; sitelinks 16; tier 1; roster yes; P831 -; P576 -] \|\| Q4122219 Panathinaikos F.C. [association football club; sitelinks 70; tier 1; roster |

### ground-proposal (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q201584 | AEK Athens | AEK Athens: ground 'Agia Sophia Stadium' - ok | verdict=ok; ground_table=Agia Sophia Stadium; ground_read_from=table; named_by=4 place(s): table, Wikidata P115, StadiumDB, club article infobox; other_names=club article infobox=Agia Sophia Stadium; Wikidata P115=Agia Sophia Stadium / Γήπεδο «Αγιά Σοφιά»; Sta |
| 1 | Q16245443 | A.E. Kifisia | A.E. Kifisia: ground 'Leoforos Alexandras Stadium' - attention | verdict=attention; flags=P115 shared with Panathinaikos; notes=Wikidata's ground 'Apostolos Nikolaidis Stadium' is the table's ground under another name: its position is 6 m from the ground's English article; ground_table=Leoforos Alexandras Stadium; ground_re |
| 1 | Q219926 | Aris | Aris: ground 'Kleanthis Vikelidis Stadium' - ok | verdict=ok; ground_table=Kleanthis Vikelidis Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Kleanthis Vikelidis Stadium; Wikidata P115=Kleanthis Vikelidis Stadium / |
| 1 | Q757320 | Asteras Tripolis | Asteras Tripolis: ground 'Theodoros Kolokotronis Stadium' - ok | verdict=ok; ground_table=Theodoros Kolokotronis Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Theodoros Kolokotronis Stadium; Wikidata P115=Theodoros Kolokotronis S |
| 1 | Q757754 | Atromitos | Atromitos: ground 'Peristeri Stadium' - ok | verdict=ok; ground_table=Peristeri Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Peristeri Stadium; Wikidata P115=Peristeri Stadium / Δημοτικό Στάδιο Περιστερίου; StadiumDB=St |
| 1 | Q592241 | Iraklis | Iraklis: ground 'Kaftanzoglio Stadium' - ok | verdict=ok; ground_table=Kaftanzoglio Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Kaftanzoglio Stadium; Wikidata P115=Kaftanzoglio National Stadium / Καυτανζόγλει |
| 1 | Q2744247 | Kalamata | Kalamata: ground 'Kalamata Municipal Stadium' - ok | verdict=ok; ground_table=Kalamata Municipal Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Kalamata Municipal Stadium; Wikidata P115=Kalamata Municipal Stadium / Δημοτικό Στάδι |
| 1 | Q824450 | Levadiakos | Levadiakos: ground 'Levadia Municipal Stadium' - ok | verdict=ok; ground_table=Levadia Municipal Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Levadia Municipal Stadium; Wikidata P115=Levadia Municipal Stadium / Δημοτικό Στάδιο Λ |
| 1 | Q931704 | OFI | OFI: ground 'Pankritio Stadium' - ok | verdict=ok; ground_table=Pankritio Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Pankritio Stadium; Wikidata P115=Pankritio Stadium / Παγκρήτιο Στάδιο; proposed_venue=Pankriti |
| 1 | Q19628 | Olympiacos | Olympiacos: ground 'Karaiskakis Stadium' - ok | verdict=ok; ground_table=Karaiskakis Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Georgios Karaiskakis Stadium; Wikidata P115=Karaiskakis Stadium / Στάδιο «Γεώργιος Καραϊσκάκ |
| 1 | Q4122219 | Panathinaikos | Panathinaikos: ground 'Athens Olympic Stadium' - attention | verdict=attention; flags=P115 shared with A.E. Kifisia \| Wikidata names 'Apostolos Nikolaidis Stadium', the table 'Athens Olympic Stadium' \| THE MAP WOULD BE 211586 m FROM THE PROPOSAL; ground_table=Athens Olympic Stadium; ground_read_from=table; named_by=2 pl |
| 1 | Q1460053 | Panetolikos | Panetolikos: ground 'Panetolikos Stadium' - ok | verdict=ok; ground_table=Panetolikos Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Panetolikos Stadium; Wikidata P115=Panetolikos Stadium / Γήπεδο Παναιτωλικού; proposed_venue |
| 1 | Q204888 | PAOK | PAOK: ground 'Toumba Stadium' - ok | verdict=ok; ground_table=Toumba Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Toumba Stadium; Wikidata P115=Toumba Stadium / Γήπεδο Τούμπας; StadiumDB=Stádio Toumba |
| 1 | Q43375974 | Volos | Volos: ground 'Panthessaliko Stadium' - ok | verdict=ok; ground_table=Panthessaliko Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Panthessaliko Stadium; Wikidata P115=Panthessaliko Stadium / Πανθεσσαλικό Στάδιο; proposed |
| 2 | Q275626 | AEL | AEL: ground 'AEL FC Arena' - ok | verdict=ok; ground_table=AEL FC Arena; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=AEL FC Arena; Wikidata P115=AEL FC Arena; proposed_venue=AEL FC Arena; proposed_position=39.615610 |
| 2 | Q123283162 | Anagennisi Karditsa | Anagennisi Karditsa: ground 'Karditsa Municipal Stadium' - ok | verdict=ok; ground_table=Karditsa Municipal Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Municipal Stadium of Karditsa; Wikidata P115=Municipal Stadium of Karditsa / Δημοτικό |
| 2 | Q619215 | Apollon Kalamaria | Apollon Kalamaria: ground 'Kalamaria Stadium' - ok | verdict=ok; notes=its P115 is shared with PAOK B; the table / club article names the same ground for them too (a genuinely shared ground); ground_table=Kalamaria Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; |
| 2 | Q1547133 | Athens Kallithea | Athens Kallithea: ground 'Grigoris Lamprakis Stadium' - ok | verdict=ok; notes=Wikidata's ground 'Municipal Stadium of Kallithea "Grigoris Lambrakis"' is the table's ground under another name: its position is 0 m from the ground's English article; ground_table=Grigoris Lamprakis Stadium; ground_read_from=table; named_by |
| 2 | Q12872753 | Hellas Syros | Hellas Syros: ground 'Ermoupoli Municipal Stadium' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; notes=Wikidata names no ground; ground_table=Ermoupoli Municipal Stadium; ground_read_from=table; named_by |
| 2 | Q15309584 | Marko | Marko: ground 'Municipal Stadium of Markopoulo' - ok | verdict=ok; ground_table=Municipal Stadium of Markopoulo; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Municipal Stadium of Markopoulo; Wikidata P115=Municipal Stadium of Markopoulo / |
| 2 | Q16845757 | Nestos Chrysoupoli | Nestos Chrysoupoli: ground 'Chrysoupoli Municipal Stadium' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| NO ground-specific position found; notes=Wikidata names no ground; ground_table=Chrysoupoli Municipal Stadium; ground_read_from=table; named_by=2 place(s): table, club article infobox; other_names=club article in |
| 2 | Q3180055 | Niki Volos | Niki Volos: ground 'Pantelis Magoulas Stadium' - ok | verdict=ok; ground_table=Pantelis Magoulas Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Pantelis Magoulas Stadium; Wikidata P115=Pantelis Magoulas Stadium / Γήπεδο Νίκης Βόλο |
| 2 | Q107410262 | Olympiacos B | Olympiacos B: ground 'Rentis Training Centre' - ok | verdict=ok; ground_table=Rentis Training Centre; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Rentis Training Centre; Wikidata P115=Rentis Training Center / Προπονητικό Κέντρο Ρέντη; |
| 2 | Q460494 | Panionios | Panionios: ground 'Nea Smyrni Stadium' - ok | verdict=ok; ground_table=Nea Smyrni Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Nea Smyrni Stadium; Wikidata P115=Nea Smyrni Stadium / Στάδιο Νέας Σμύρνης; Stadiu |
| 2 | Q1417287 | Panserraikos | Panserraikos: ground 'Serres Municipal Stadium' - ok | verdict=ok; ground_table=Serres Municipal Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Serres Municipal Stadium; Wikidata P115=Serres Municipal Stadium / Δημοτικό Γήπεδο Σερρ |
| 2 | Q433230 | Panthrakikos | Panthrakikos: ground 'Komotini Municipal Stadium' - ok | verdict=ok; ground_table=Komotini Municipal Stadium; ground_read_from=table; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Komotini Municipal Stadium; Wikidata P115=Komotini Municipal Stadium / Δημ |
| 2 | Q107849577 | PAOK B | PAOK B: ground 'Kalamaria Stadium' - ok | verdict=ok; notes=its P115 is shared with Apollon Kalamaria; the table / club article names the same ground for them too (a genuinely shared ground); ground_table=Kalamaria Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club articl |
| 2 | Q25535620 | PAS Pyrgos | PAS Pyrgos: ground 'Pyrgos Municipal Stadium' - ok | verdict=ok; ground_table=Pyrgos Municipal Stadium; ground_read_from=table; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Pyrgos Stadium; Wikidata P115=Pyrgos Stadium / Δημοτικό Στάδιο Πύργου «Χαράλαμπος Βιλαέ |
| 2 | Q3292651 | Zakynthos | Zakynthos: ground 'Zakynthos Municipal Stadium' - unplaced | verdict=unplaced; flags=Wikidata names 'Δημοτικό Στάδιο Ζακύνθου', the table 'Zakynthos Municipal Stadium' \| UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found; ground_table=Zakyntho |

### capacity-proposal (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q201584 | AEK Athens | AEK Athens: agreed, proposed 32500 | verdict=agreed; proposed=32500; action=keep (the map's figure is in the agreement); rule=table 32500 agrees within 5% with stadiumdb 32500, wikidata 31100; figures=table 32500; Wikidata 31100 (map's figure); OpenStreetMap None; StadiumDB 32500; stadiumdb=Allwy |
| 1 | Q16245443 | A.E. Kifisia | A.E. Kifisia: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 16003 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 16003, wikidata 16003); the table and Wikidata are both Wikipedia's; |
| 1 | Q219926 | Aris | Aris: agreed, proposed 22800 | verdict=agreed; proposed=22800; action=keep (the map's figure is in the agreement); rule=table 22800 agrees within 5% with stadiumdb 23220, wikidata 22800; figures=table 22800; Wikidata 22800 (map's figure); OpenStreetMap None; StadiumDB 23220; stadiumdb=Stádi |
| 1 | Q757320 | Asteras Tripolis | Asteras Tripolis: agreed, proposed 7423 | verdict=agreed; proposed=7423; action=keep (the map's figure is in the agreement); rule=table 7423 agrees within 5% with stadiumdb 7423, wikidata 7616; figures=table 7423; Wikidata 7616 (map's figure); OpenStreetMap None; StadiumDB 7423; stadiumdb=Gípedo Theód |
| 1 | Q757754 | Atromitos | Atromitos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 10200 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 9050, wikidata 10200); the table and Wikidata are both Wikipedia's; f |
| 1 | Q592241 | Iraklis | Iraklis: agreed, proposed 27560 | verdict=agreed; proposed=27560; action=keep (the map's figure is in the agreement); rule=table 27560 agrees within 5% with stadiumdb 28028, wikidata 27560; figures=table 27560; Wikidata 27560 (map's figure); OpenStreetMap None; StadiumDB 28028; stadiumdb=Stádi |
| 1 | Q2744247 | Kalamata | Kalamata: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 4496 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 4496, wikidata 4496); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q824450 | Levadiakos | Levadiakos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5915 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 5915, wikidata 5915); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q931704 | OFI | OFI: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 26240 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 26240, wikidata 26240); the table and Wikidata are both Wikipedia's; |
| 1 | Q19628 | Olympiacos | Olympiacos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 33334 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 33334, wikidata 33334); the table and Wikidata are both Wikipedia's; |
| 1 | Q4122219 | Panathinaikos | Panathinaikos: single-source, blank | verdict=single-source; proposed=BLANK; action=CLEAR the map's 16003: it is the capacity of another ground (Apostolos Nikolaidis Stadium), unless the two names are one ground; rule=one independent source only (table 69618); the table and Wikidata are both Wikip |
| 1 | Q1460053 | Panetolikos | Panetolikos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 7500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 7321, wikidata 7500); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q204888 | PAOK | PAOK: agreed, proposed 28703 | verdict=agreed; proposed=28703; action=keep (the map's figure is in the agreement); rule=table 28703 agrees within 5% with stadiumdb 28701, wikidata 28703; figures=table 28703; Wikidata 28703 (map's figure); OpenStreetMap None; StadiumDB 28701; stadiumdb=Stádi |
| 1 | Q43375974 | Volos | Volos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 22700 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 22700, wikidata 22700); the table and Wikidata are both Wikipedia's; |
| 2 | Q275626 | AEL | AEL: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 17118 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 16118, wikidata 17118); the table and Wikidata are both Wikipedia's; |
| 2 | Q123283162 | Anagennisi Karditsa | Anagennisi Karditsa: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 13000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 3500, wikidata 13000); the table and Wikidata are both Wikipedia's; f |
| 2 | Q619215 | Apollon Kalamaria | Apollon Kalamaria: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 6500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6500, wikidata 6500); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q1547133 | Athens Kallithea | Athens Kallithea: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 4200 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6300, wikidata 4200); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q12872753 | Hellas Syros | Hellas Syros: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 2500); the table and Wikidata are both Wikipedia's; figures=table 2500; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 2 | Q15309584 | Marko | Marko: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 3000); the table and Wikidata are both Wikipedia's; figures=table 3000; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 2 | Q16845757 | Nestos Chrysoupoli | Nestos Chrysoupoli: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 5000); the table and Wikidata are both Wikipedia's; figures=table 5000; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 2 | Q3180055 | Niki Volos | Niki Volos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 2500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 2500, wikidata 2500); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q107410262 | Olympiacos B | Olympiacos B: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 3000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 3000, wikidata 3000); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q460494 | Panionios | Panionios: agreed, proposed 11700 | verdict=agreed; proposed=11700; action=keep (the map's figure is in the agreement); rule=table 11700 agrees within 5% with stadiumdb 11115, wikidata 11115; figures=table 11700; Wikidata 11115 (map's figure); OpenStreetMap None; StadiumDB 11115; stadiumdb=Stádi |
| 2 | Q1417287 | Panserraikos | Panserraikos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 9500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 9500, wikidata 9500); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q433230 | Panthrakikos | Panthrakikos: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 6198 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 6198; Wikidata 6198 (map's figure); OpenStreetMap N |
| 2 | Q107849577 | PAOK B | PAOK B: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 6500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6500, wikidata 6500); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q25535620 | PAS Pyrgos | PAS Pyrgos: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 6750 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6750, wikidata 6750); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q3292651 | Zakynthos | Zakynthos: single-source, blank | verdict=single-source; proposed=BLANK; action=CLEAR the map's 2500: it is the capacity of another ground (Δημοτικό Στάδιο Ζακύνθου), unless the two names are one ground; rule=one independent source only (table 5000); the table and Wikidata are both Wikipedia's |

## Appendix: tagged but dissolved (not drawn)

- none

## Appendix: tagged extras whose tag is not truthy (not drawn)

- Q7802151 A.O. Tilikratis Lefkadas (shape C)
- Q2001271 Apollon Smyrnis F.C. (shape C)
- Q137826389 Makedonikos F.C. (shape C)
- Q6481836 P.A.S. Lamia 1964 (shape C)
- Q280679 PAS Giannina F.C. (shape C)
- Q7130058 Panargiakos F.C. (shape C)
