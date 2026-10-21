# Proposal for PT (Portugal)

Generated 2026-10-21 15:59 UTC by `tools/propose_country.py`. **Read-only evidence, not decisions**: nothing here was written to a hand-written file or a club file; a gap is a gap.

## Summary

| kind | rows |
|---|---|
| roster-ok | 29 |
| roster-untagged | 3 |
| roster-wrong-tier | 4 |
| extra-tagged | 21 |
| duplicate | 2 |
| women-candidate | 5 |
| ground-proposal | 36 |
| capacity-proposal | 36 |

Tagged but dissolved (not drawn by the build, no row): 0; tagged extras whose tag is not truthy (not drawn, no row): 3; women's football items pointing at a club, carrying neither tag: 5 (other-sport items ignored: 20).

Step durations (s): 1 rosters 2.9, 2 leagues 6.3, 3 items 4.3, 4 rank cross-check 1.3, 5 evidence for extras 2.8, 6 candidates 0.0, 6b grounds and capacities 101.0, 7 wiring patch 0.5

## Leagues

| tier | article | league item | label | found via | P3983 | P17 | women-word check |
|---|---|---|---|---|---|---|---|
| 1 | 2026–27 Primeira Liga | Q182994 | Primeira Liga | season item Q139820318 -> P3450 | none | Q45 Portugal | none |
| 2 | 2026–27 Liga Portugal 2 | Q754488 | Liga Portugal 2 | season item Q140026835 -> P3450 | none | Q45 Portugal | none |

P3983 and P17 are printed, not used: the country Q-id given on the command line is `Q45`.

### Items labelled like a tier, or succeeded by it (the 'old Second Division' trap)

| item | label | description | clubs carrying it (any rank) | dissolved | succeeded by |
|---|---|---|---|---|---|
| Q21929716 | Primeira Liga | Brazilian football tournament | 1 |  |  |

Rows with clubs > 0 and a dissolution or successor are the trap: not to be mapped.

## Wiring patch (printed, not applied)

### data/league-tiers.csv — append

```
Q182994,1,Primeira Liga,PT
Q754488,2,Liga Portugal 2,PT
```

### data/league-rosters.csv — append

```
Q182994,PT,1,2026-27,2026–27 Primeira Liga,
Q754488,PT,2,2026-27,2026–27 Liga Portugal 2,
```

### COUNTRY_BOX (tools/fetch_clubs.py)

- north: (42.15416666666667, -8.198888888888888) normal
- south: (36.96024856, -7.88698196) normal
- east: (41.57488702, -6.19021386) normal
- west: (38.78099411, -9.50053453) normal
- proposal from best rank: `"PT": {"lat": (36.81, 42.3), "lon": (-9.65, -6.04)},`
- proposal from normal rank only: `"PT": {"lat": (36.81, 42.3), "lon": (-9.65, -6.04)},`
- NOTE: clubs outside the best-rank proposal (island/overseas?): C.D. Nacional (32.67, -16.88), C.S. Marítimo (32.65, -16.93), C.D. Santa Clara (37.76, -25.62)

### football-data.org code (candidates only)

- PPL — Primeira Liga (football-data free tier list (tools/fetch_fixtures.py))

### Places to touch (with line numbers)

(template country: Belgium BE Q31; edit beside its lines)
- data/league-tiers.csv: append the league-tiers rows printed above
- data/league-rosters.csv: append the league-rosters rows printed above
- tools/fetch_clubs.py: COUNTRIES (code, P17 Q-id, name), COUNTRY_BOX and its comment, COUNTRY_NAMES, the label languages in the build loop
    tools/fetch_clubs.py:109: # Belgium, P17 Q31 on both leagues and on every club item read on
    tools/fetch_clubs.py:111: ("BE", "Q31", "Belgium"),
    tools/fetch_clubs.py:232: #   The UNION on `?sup` - the suppression must actually BE a preferred
    tools/fetch_clubs.py:671: # Belgium (2026-10-01) is the first country whose labels can fall back to
    tools/fetch_clubs.py:1152: #       of Belgium, so it catches nothing near a border - Wikidata's P17
    tools/fetch_clubs.py:1260: #   BE  north 51.50508 (Zondereigen, P1332), south 49.49699 (Torgny,
    tools/fetch_clubs.py:1262: #       Q31's own normal-rank extreme points, read on a runner 2026-10-01,
    tools/fetch_clubs.py:1265: #       Limburg, and Aachen, so for BE as for NL both signals are weak at
    tools/fetch_clubs.py:1280: "BE": {"lat": (49.45, 51.55), "lon": (2.50, 6.45)},
    tools/fetch_clubs.py:1291: "Q31": "Belgium", "Q45": "Portugal", "Q55": "Netherlands", "Q36": "Poland",
    tools/fetch_clubs.py:1692: "RS": "en,sr-el", "GR": "en,el", "ES": "en,es", "NL": "en,nl", "BE": "en,nl,fr", "PT": "en,pt"}.get(code, "en"
- tools/diagnose_p118_rank.py: COUNTRIES (P17 Q-id to code)
    tools/diagnose_p118_rank.py:84: # Belgium: both leagues and every club item read on 2026-10-01 carry P17 Q31.
    tools/diagnose_p118_rank.py:85: "Q31": "BE",
- tools/crosscheck_stadiumdb.py: COUNTRY_PAGES (the slug, found by probe); EXTRA_PAGES if the pyramid crosses a border
    tools/crosscheck_stadiumdb.py:166: # Belgium's "bel" on 2026-10-01: /stadiums/bel answers 200, read on a
    tools/crosscheck_stadiumdb.py:189: "BE": ("bel", "Belgium"),
- tools/link_fixtures.py: CLUB_FILES; FD_COUNTRY if football-data carries a league
    tools/link_fixtures.py:40: 3. LEGAL FORMS AND YEARS MAY BE ABSENT, NOT DIFFERENT. "TSG Hoffenheim"
    tools/link_fixtures.py:133: "data/clubs/NL.json", "data/clubs/BE.json", "data/clubs/PT.json"]
- tools/build_calendars.py: time zone (usually already there)
    tools/build_calendars.py:72: "BE": "Europe/Brussels",
- index.html: COUNTRY_FILES; cn.XX in en and ro and COUNTRY_NAME; adj.XX and COUNTRY_ADJ for a country with no fixtures; noFixturesReason() top map; fx.coverage and LEAGUE_CODES if football-data carries a league
    index.html:1092: "adj.BE": "Belgian",
    index.html:1440: "cn.BE": "Belgium",
    index.html:1579: "cnm.Belgium": "Belgium",
    index.html:1633: "iso.BE": "Belgium",
    index.html:2340: "adj.BE": "belgiene",
    index.html:2688: "cn.BE": "Belgia",
    index.html:2827: "cnm.Belgium": "Belgia",
    index.html:2881: "iso.BE": "Belgia",
    index.html:3591: const COUNTRY_FILES = ['data/clubs/DE.json','data/clubs/RO.json','data/clubs/FR.json','data/clubs/IT.json','da
    index.html:4460: const COUNTRY_ADJ = labelsOf('adj.', ['RO', 'CH', 'AT', 'RS', 'GR', 'BE']);
    index.html:4467: (club.country === 'BE' ? ' ' + t('fx.no.be') : '')];
    index.html:6419: const COUNTRY_NAME = labelsOf('cn.', ['AT', 'BE', 'CH', 'DE', 'ES', 'FR', 'GB', 'GR', 'IT', 'NL', 'PT', 'RO', 
    ... and 1 more lines
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

- Wikidata name search for 4 ground(s) with no other position: 1 found an item with a position
- **WARNING: OpenStreetMap (Overpass) did not answer (HTTP 502). The grounds below were proposed WITHOUT it; run the tool again to ask it.**
- OpenStreetMap: asked and failed: HTTP 502 [Overpass requests this run: 4 of the cap 60]
- https://stadiumdb.com/robots.txt read (1 disallow rule(s)); /stadiums/ is allowed
- StadiumDB slug 'por' answered a table of 39 grounds (39 with a capacity); tried: por: answered (configured in crosscheck_stadiumdb.COUNTRY_PAGES)

28 ground(s) agree everywhere and need nothing; 8 need a look:

| verdict | club | table's ground | flags |
|---|---|---|---|
| unplaced | Alverca | Complexo Desportivo FC Alverca | UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places) |
| unplaced | Casa Pia | Estádio Municipal de Rio Maior | UNPLACED by the build |
| unplaced | AFS | Estádio do Clube Desportivo das Aves | UNPLACED by the build |
| attention | Benfica B | Benfica Campus - Campo n.° 1 | P115 is the first team's ground (Benfica) - copied onto a reserve side unless the table agrees \| Wikidata names 'Estádio da Luz', the table 'Benfica Campus - Campo n.° 1' \| THE MAP WOULD BE 14851 m FROM THE PROPOSAL |
| attention | Farense | Estádio de São Luís | Wikidata names 'Estádio Algarve', the table 'Estádio de São Luís' \| THE MAP WOULD BE 8359 m FROM THE PROPOSAL |
| unplaced | Lusitânia Lourosa | Estádio do Lusitânia de Lourosa FC | UNPLACED by the build \| NO ground-specific position found (OpenStreetMap was not queried) |
| attention | Porto B | Estádio Luís Filipe Menezes | Wikidata names 'Estádio Municipal Jorge Sampaio', the table 'Estádio Luís Filipe Menezes' \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found (OpenStreetMap was not queried) |
| attention | Sporting CP B | Estádio Aurélio Pereira | P115 is the first team's ground (Sporting CP) - copied onto a reserve side unless the table agrees \| Wikidata names 'Estádio José Alvalade', the table 'Estádio Aurélio Pereira' \| NO ground-specific position found (OpenStreetMap was not queried) |


## Candidates

### roster-ok (29)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q1386850 | Alverca | table row 'Alverca' in 2026–27 Primeira Liga | team=Alverca; ground=Complexo Desportivo FC Alverca; capacity=6932; article=2026–27 Primeira Liga; tags=Campeonato de Portugal (normal, 2020-2021) \| Liga 3 (normal, 2021-2024) \| Liga Portugal 2 (normal, 2024-2025) \| Primeira Liga (preferred, 2025-) |
| 1 | Q1386869 | Arouca | table row 'Arouca' in 2026–27 Primeira Liga | team=Arouca; ground=Estádio Municipal de Arouca; capacity=5000; article=2026–27 Primeira Liga; tags=Liga Portugal 2 (normal, 2020-2021) \| Primeira Liga (preferred, 2021-) |
| 1 | Q131499 | Benfica | table row 'Benfica' in 2026–27 Primeira Liga | team=Benfica; ground=Estádio da Luz; capacity=68100; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 1934-) |
| 1 | Q75684 | Braga | table row 'Braga' in 2026–27 Primeira Liga | team=Braga; ground=Estádio Municipal de Braga; capacity=30286; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 1975-) |
| 1 | Q1046440 | Casa Pia | table row 'Casa Pia' in 2026–27 Primeira Liga | team=Casa Pia; ground=Estádio Municipal de Rio Maior , at Rio Maior; capacity=7000; article=2026–27 Primeira Liga; tags=Terceira Divisão (normal, 2018-2019) \| Liga Portugal 2 (normal, 2019-2022) \| Primeira Liga (preferred, 2022-) |
| 1 | Q634829 | Estoril Praia | table row 'Estoril Praia' in 2026–27 Primeira Liga | team=Estoril Praia; ground=Estádio António Coimbra da Mota; capacity=5094; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 2012-2018) \| Liga Portugal 2 (normal, 2018-2021) \| Primeira Liga (preferred, 2021-) |
| 1 | Q838134 | Estrela da Amadora | table row 'Estrela da Amadora' in 2026–27 Primeira Liga | team=Estrela da Amadora; ground=Estádio José Gomes; capacity=9288; article=2026–27 Primeira Liga; tags=Liga Portugal 2 (normal, 2021-2023) \| Primeira Liga (preferred, 2023-) |
| 1 | Q1387105 | Famalicão | table row 'Famalicão' in 2026–27 Primeira Liga | team=Famalicão; ground=Estádio Municipal de Famalicão; capacity=5186; article=2026–27 Primeira Liga; tags=Liga Portugal 2 (normal, ?-2019) \| Primeira Liga (preferred, 2019-) |
| 1 | Q926438 | Gil Vicente | table row 'Gil Vicente' in 2026–27 Primeira Liga | team=Gil Vicente; ground=Estádio Cidade de Barcelos; capacity=12046; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 2019-) |
| 1 | Q216503 | Marítimo | table row 'Marítimo' in 2026–27 Primeira Liga | team=Marítimo; ground=Estádio do Marítimo; capacity=10600; article=2026–27 Primeira Liga; table_mark=promoted (up arrow); tags=Primeira Liga (normal, 1985-2023) \| Liga Portugal 2 (normal, 2023-2026) \| Primeira Liga (preferred, 2026-) |
| 1 | Q1346314 | Moreirense | table row 'Moreirense' in 2026–27 Primeira Liga | team=Moreirense; ground=Estádio Comendador Joaquim de Almeida Freitas; capacity=6150; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 2014-2022) \| Liga Portugal 2 (normal, 2022-2023) \| Primeira Liga (preferred, 2023-) |
| 1 | Q216459 | Nacional | table row 'Nacional' in 2026–27 Primeira Liga | team=Nacional; ground=Estádio da Madeira; capacity=5200; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, ?-2019) \| Liga Portugal 2 (normal, 2019-2020) \| Primeira Liga (normal, 2020-2021) \| Liga Portugal 2 (normal, 2021-2024) \| Primeira Liga (preferr |
| 1 | Q128446 | Porto | table row 'Porto' in 2026–27 Primeira Liga | team=Porto; ground=Estádio do Dragão; capacity=50033; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 1934-) |
| 1 | Q622432 | Rio Ave | table row 'Rio Ave' in 2026–27 Primeira Liga | team=Rio Ave; ground=Estadio dos Arcos; capacity=5300; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 2008-2021) \| Liga Portugal 2 (normal, 2021-2022) \| Primeira Liga (preferred, 2022-) |
| 1 | Q740637 | Santa Clara | table row 'Santa Clara' in 2026–27 Primeira Liga | team=Santa Clara; ground=Estádio de São Miguel; capacity=12500; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 2024-) |
| 1 | Q75729 | Sporting CP | table row 'Sporting CP' in 2026–27 Primeira Liga | team=Sporting CP; ground=Estádio José Alvalade; capacity=52095; article=2026–27 Primeira Liga; tags=Primeira Liga (normal, 1934-) |
| 1 | Q223450 | Vitória de Guimarães | table row 'Vitória de Guimarães' in 2026–27 Primeira Liga | team=Vitória de Guimarães; ground=Estádio D. Afonso Henriques; capacity=30029; article=2026–27 Primeira Liga; tags=Primeira Liga (preferred, 2007-) \| Taça de Portugal (normal) |
| 2 | Q243235 | Académica | table row 'Académica' in 2026–27 Liga Portugal 2 | team=Académica; ground=Estádio Cidade de Coimbra; capacity=29622; article=2026–27 Liga Portugal 2; table_mark=promoted (up arrow); tags=Primeira Liga (normal, 2002-2016) \| Liga Portugal 2 (preferred) |
| 2 | Q7387221 | Benfica B | table row 'Benfica B' in 2026–27 Liga Portugal 2 | team=Benfica B; ground=Benfica Campus - Campo n.° 1; capacity=2644; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal) |
| 2 | Q543467 | Chaves | table row 'Chaves' in 2026–27 Liga Portugal 2 | team=Chaves; ground=Estádio Municipal Eng.° Manuel Branco Teixeira; capacity=8400; article=2026–27 Liga Portugal 2; tags=Primeira Liga (normal, ?-2019) \| Liga Portugal 2 (normal, 2019-2022) \| Primeira Liga (normal, 2022-2024) \| Liga Portugal 2 (preferred, 2024 |
| 2 | Q744353 | Farense | table row 'Farense' in 2026–27 Liga Portugal 2 | team=Farense; ground=Estádio de São Luís; capacity=7000; article=2026–27 Liga Portugal 2; tags=Segunda Divisão (normal, 2012-2013) \| Liga Portugal 2 (normal, 2013-2016) \| Campeonato de Portugal (normal, 2016-2018) \| Liga Portugal 2 (normal, 2018-2020) \| Primei |
| 2 | Q671042 | Feirense | table row 'Feirense' in 2026–27 Liga Portugal 2 | team=Feirense; ground=Estádio Marcolino Castro; capacity=5401; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal, 2019-) |
| 2 | Q623730 | Leixões | table row 'Leixões' in 2026–27 Liga Portugal 2 | team=Leixões; ground=Estádio do Mar; capacity=6000; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal) |
| 2 | Q621120 | Portimonense | table row 'Portimonense' in 2026–27 Liga Portugal 2 | team=Portimonense; ground=Estádio Municipal de Portimão; capacity=4961; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal, ?-2017) \| Primeira Liga (normal, 2017-2024) \| Liga Portugal 2 (preferred, 2024-) |
| 2 | Q5423714 | Porto B | table row 'Porto B' in 2026–27 Liga Portugal 2 | team=Porto B; ground=Estádio Luís Filipe Menezes; capacity=3800; article=2026–27 Liga Portugal 2; dissolved=2006; tags=Liga Portugal 2 (normal) |
| 2 | Q3494112 | Sporting CP B | table row 'Sporting CP B' in 2026–27 Liga Portugal 2 | team=Sporting CP B; ground=Estádio Aurélio Pereira; capacity=1180; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal) |
| 2 | Q1853273 | Torreense | table row 'Torreense' in 2026–27 Liga Portugal 2 | team=Torreense; ground=Estádio Manuel Marques; capacity=2431; article=2026–27 Liga Portugal 2; tags=Liga Portugal 2 (normal, 2022-) |
| 2 | Q211401 | União de Leiria | table row 'União de Leiria' in 2026–27 Liga Portugal 2 | team=União de Leiria; ground=Estádio Dr. Magalhães Pessoa; capacity=23888; article=2026–27 Liga Portugal 2; tags=Segunda Divisão (normal) \| Terceira Divisão (normal) \| Liga Portugal 2 (preferred) |
| 2 | Q1387855 | Vizela | table row 'Vizela' in 2026–27 Liga Portugal 2 | team=Vizela; ground=Estádio do Futebol Clube de Vizela; capacity=6000; article=2026–27 Liga Portugal 2; tags=Segunda Divisão (normal, 1998-2005) \| Primeira Liga (normal, 2021-2024) \| Liga Portugal 2 (preferred, 2024-) |

### roster-untagged (3)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q2841205 | Amarante | table row 'Amarante' in 2026–27 Liga Portugal 2; carries no tag of the tracked leagues | team=Amarante; ground=Estádio Municipal de Amarante; capacity=5000; article=2026–27 Liga Portugal 2; table_mark=promoted (up arrow); other_leagues=Segunda Divisão; named_in_team_changes=2026–27 Liga Portugal 2: Amarante; fallback=hand-named fallback candidate; |
| 2 | Q17505449 | Felgueiras | table row 'Felgueiras' in 2026–27 Liga Portugal 2; carries no tag of the tracked leagues | team=Felgueiras; ground=Estádio Dr. Machado de Matos; capacity=7540; article=2026–27 Liga Portugal 2; other_leagues=Campeonato de Portugal; fallback=hand-named fallback candidate; tags=Campeonato de Portugal (normal) |
| 2 | Q6705180 | Lusitânia Lourosa | table row 'Lusitânia Lourosa' in 2026–27 Liga Portugal 2; carries no tag of the tracked leagues | team=Lusitânia Lourosa; ground=Estádio do Lusitânia de Lourosa FC; capacity=4900; article=2026–27 Liga Portugal 2; other_leagues=Segunda Divisão; fallback=hand-named fallback candidate; tags=Segunda Divisão (normal) |

### roster-wrong-tier (4)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q2410944 | Académico de Viseu | table row 'Académico de Viseu' in 2026–27 Primeira Liga; Wikidata tags it at tier 2 | team=Académico de Viseu; ground=Estádio Municipal do Fontelo; capacity=6912; article=2026–27 Primeira Liga; table_mark=promoted (up arrow); roster_tier=1; tagged_tier=2; named_in_team_changes=2026–27 Primeira Liga: Marítimo Académico de Viseu AVS Tondela; 2026 |
| 2 | Q120775987 | AFS | table row 'AFS' in 2026–27 Liga Portugal 2; Wikidata tags it at tier 1 | team=AFS; ground=Estádio do Clube Desportivo das Aves; capacity=6230; article=2026–27 Liga Portugal 2; table_mark=relegated (down arrow); roster_tier=2; tagged_tier=1; named_in_team_changes=2026–27 Primeira Liga: Marítimo Académico de Viseu AVS Tondela; 2026–2 |
| 2 | Q1387471 | Penafiel | table row 'Penafiel' in 2026–27 Liga Portugal 2; Wikidata tags it at tier 1 | team=Penafiel; ground=Estádio Municipal 25 de Abril; capacity=5230; article=2026–27 Liga Portugal 2; roster_tier=2; tagged_tier=1; tags=Primeira Liga (normal, 2014-2015) |
| 2 | Q1023227 | Tondela | table row 'Tondela' in 2026–27 Liga Portugal 2; Wikidata tags it at tier 1 | team=Tondela; ground=Estádio João Cardoso; capacity=5000; article=2026–27 Liga Portugal 2; table_mark=relegated (down arrow); roster_tier=2; tagged_tier=1; named_in_team_changes=2026–27 Primeira Liga: Marítimo Académico de Viseu AVS Tondela; 2026–27 Primeira L |

### extra-tagged (21)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 2 | Q290884 | A.D. Ovarense | The club currently competes in the AF Aveiro Second Division following a seventh-place finish in the 2011–12 AF Aveiro Second Division season. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal, 2000-2006); p576=none; tag_dates=2000-2006; named_in_team_change |
| 2 | Q846008 | Associação Naval 1º de Maio | Founded on 1 May 1893, it last played in the Division of Honour in the Coimbra Football Association, holding home games at the Estádio Municipal José Bento Pess | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p |
| 2 | Q59212899 | B-SAD | Competing initially under the name Belenenses SAD, the club played four seasons in the Primeira Liga between 2018 and 2022, before successive relegations to Lig | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); intro_mentions_a_tracked_league=Primeira Liga, Liga Portugal 2 (read the sentence: a past season or now?); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 |
| 2 | Q17524289 | C.D. Cova da Piedade | The club merged with B-SAD, in an attempt of the former to retain their position currently in Liga 3, the third tier of Portuguese football, but they weren't gr | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resol |
| 2 | Q176099 | C.D. Fátima | Centro Desportivo de Fátima, simply known as Fátima, is a Portuguese football club based in Fátima, in the municipality of Ourém. [no sentence of the intro name | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 2 | Q1023233 | C.D. Trofense | Founded in 1930, it plays in Liga 3, holding home games at Estádio do Clube Desportivo Trofense, with a capacity of 5,017 spectators. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 2 | Q216510 | C.F. Os Belenenses | ... Os Belenenses or simply Belenenses, is a Portuguese sports club best known for its football team, which currently competes in Liga 3, the third tier of the | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, 2013-2018) \| Liga Portugal 2 (preferred); p576=none; tag_dates=201 |
| 2 | Q1762119 | C.F. União | ... a Portuguese football club based in Funchal, Madeira, notable for its six seasons in the Portuguese top-flight Primeira Liga, between the 1989–90 and 1991–9 | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); intro_mentions_a_tracked_league=Primeira Liga (read the sentence: a past season or now?); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 20 |
| 2 | Q5006215 | C.S. Marítimo B | Club Sport Marítimo B is a Portuguese football club that currently plays in the AF Madeira 1ª Divisão. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 1 | Q1023163 | Clube Desportivo das Aves | ... commonly known as Desportivo das Aves, or simply as Aves, was a Portuguese football club based in Vila das Aves, Santo Tirso. [no sentence of the intro name | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal, ?- |
| 1 | Q1387110 | F.C. Felgueiras | Futebol Clube de Felgueiras was a Portuguese football club from Felgueiras. [no sentence of the intro names a league] | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, 1995 |
| 2 | Q371136 | F.C. Paços de Ferreira | Founded in 1950, the club competes in Liga 3, holding home games at the 9,076 seat Estádio Capital do Móvel The club's colours are yellow and green. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, 2019-2023) \| Liga Portugal 2 (preferred, 2023-); p576=none; tag_da |
| 2 | Q1256652 | Gondomar S.C. | Founded on 1 May 1921, it currently plays in the fourth-tier Campeonato de Portugal, holding home games at Estádio de São Miguel, with a capacity of 2.450 spect | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 1 | Q688300 | S.C. Beira-Mar | Its football team currently plays in the Campeonato de Portugal, the fourth national level, having gained promotion by winning the Aveiro FA First Division 2018 | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, 2010-2013); p576=none; tag_dates=2010-2013; named_in_team_changes= |
| 2 | Q7387158 | S.C. Braga B | Reserve teams in Portugal play in the same league system as the senior team, rather than in a reserve team league. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resol |
| 2 | Q1891367 | S.C. Covilhã | Covilhã, is a Portuguese football club from the city of Covilhã that plays in the third-tier Liga 3. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 2 | Q1031307 | S.C. Freamunde | Founded on 19 March 1933, it currently plays in the Campeonato de Portugal, holding home matches at the 3,919-capacity Complexo Desportivo do SC Freamunde. | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p576=none; tag_dates=?-; named_in_team_changes=no; types=associ |
| 2 | Q2061414 | U.D. Oliveirense | The main football team currently plays at the Estádio Carlos Osório which holds a seating capacity of 1,750 and plays in Liga Portugal 2. | drawn_by_build=yes: has a position; intro_mentions_a_tracked_league=Liga Portugal 2 (read the sentence: a past season or now?); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); ta |
| 2 | Q3551877 | UD Vilafranquense | The team currently compete in the 3rd division of Lisbon Football Association, equivalent to the 7th Portuguese division. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resol |
| 2 | Q1429473 | Varzim S.C. | The club plays in Liga 3, following relegation in the 2021–22 Liga Portugal 2. | drawn_by_build=yes: has a position; intro_mentions_a_tracked_league=Liga Portugal 2 (read the sentence: a past season or now?); absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); ta |
| 2 | Q17518847 | Vitória S.C. B | They compete in the Campeonato de Portugal, the fourth division of Portuguese football, and play their home matches at the club's 2,500-capacity Academia do Vit | drawn_by_build=yes: has a position; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal) \| Liga 3 (normal); p576=none; tag_dates=?-; named_in_team_change |

### duplicate (2)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q1387110 | F.C. Felgueiras | group D1: 2 items share ground 'Estádio Dr. Machado de Matos' | group=D1; basis=ground; members: Q1387110 F.C. Felgueiras [association football club; sitelinks 11; tier 1; roster no; P831 -; P576 -] \|\| Q17505449 F.C. Felgueiras 1932 [association football club; sitelinks 6; tier None; roster yes; P831 -; P576 -] |
|  | Q17505449 | F.C. Felgueiras 1932 | group D1: 2 items share ground 'Estádio Dr. Machado de Matos' | group=D1; basis=ground; members: Q1387110 F.C. Felgueiras [association football club; sitelinks 11; tier 1; roster no; P831 -; P576 -] \|\| Q17505449 F.C. Felgueiras 1932 [association football club; sitelinks 6; tier None; roster yes; P831 -; P576 -] |

### women-candidate (5)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
|  | Q106311156 | C.S. Marítimo (women) | angle 4: a women's item points at a roster/tagged club | reaches_the_map=no (carries neither tag); points=P361->C.S. Marítimo; types=women's association football club |
|  | Q132158652 | Vitória S.C. (women) | angle 4: a women's item points at a roster/tagged club | reaches_the_map=no (carries neither tag); points=P361->Vitória S.C., P749->Vitória S.C.; types=women's association football club; classes=women's association football |
|  | Q134697928 | Q134697928 | angle 4: a women's item points at a roster/tagged club | reaches_the_map=no (carries neither tag); points=P361->S.C.U. Torreense; types=sports club; classes=women's association football |
|  | Q136320163 | Rio Ave F.C. (women) | angle 4: a women's item points at a roster/tagged club | reaches_the_map=no (carries neither tag); points=P361->Rio Ave F.C., P749->Rio Ave F.C.; types=women's association football club; classes=women's association football |
|  | Q25238645 | Sporting CP (women) | angle 4: a women's item points at a roster/tagged club | reaches_the_map=no (carries neither tag); points=P749->Sporting CP; types=women's association football team; classes=women's association football |

### ground-proposal (36)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q2410944 | Académico de Viseu | Académico de Viseu: ground 'Estádio Municipal do Fontelo' - ok | verdict=ok; ground_table=Estádio Municipal do Fontelo; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio do Fontelo; Wikidata P115=Estádio do Fontelo / Estadio do Fontelo; proposed_venue=Estádio Municipal |
| 1 | Q1386850 | Alverca | Alverca: ground 'Complexo Desportivo FC Alverca' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| the ground is named by ONE place only (rule: two independent places); notes=Wikidata names no ground; ground_table=Complexo Desportivo FC Alverca; named_by=1 place(s): table; other_names=club article infobox=Comp |
| 1 | Q1386869 | Arouca | Arouca: ground 'Estádio Municipal de Arouca' - ok | verdict=ok; ground_table=Estádio Municipal de Arouca; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Municipal de Arouca; Wikidata P115=Estádio Municipal de Arouca / Estadio Municipal de Aro |
| 1 | Q131499 | Benfica | Benfica: ground 'Estádio da Luz' - ok | verdict=ok; notes=its P115 is also its reserve side's (Benfica B); ground_table=Estádio da Luz; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio da Luz; Wikidata P115=Estádio da Luz / Estádio |
| 1 | Q75684 | Braga | Braga: ground 'Estádio Municipal de Braga' - ok | verdict=ok; ground_table=Estádio Municipal de Braga; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Municipal de Braga; Wikidata P115=Estádio Municipal de Braga / Estádio Municipal de Braga; |
| 1 | Q1046440 | Casa Pia | Casa Pia: ground 'Estádio Municipal de Rio Maior' - unplaced | verdict=unplaced; flags=UNPLACED by the build; notes=Wikidata names no ground; ground_table=Estádio Municipal de Rio Maior; named_by=1 place(s): table; other_names=club article infobox=Estádio Pina Manique, Lisbon; StadiumDB=Estádio Pina Manique; proposed_venu |
| 1 | Q634829 | Estoril Praia | Estoril Praia: ground 'Estádio António Coimbra da Mota' - ok | verdict=ok; ground_table=Estádio António Coimbra da Mota; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio António Coimbra da Mota; Wikidata P115=Estádio António Coimbra da Mota / Estadio Anto |
| 1 | Q838134 | Estrela da Amadora | Estrela da Amadora: ground 'Estádio José Gomes' - ok | verdict=ok; ground_table=Estádio José Gomes; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio José Gomes; Wikidata P115=Estádio José Gomes / Estadio Jose Gomes; proposed_venue=Estádio José Gomes; propose |
| 1 | Q1387105 | Famalicão | Famalicão: ground 'Estádio Municipal de Famalicão' - ok | verdict=ok; notes=Wikidata names 'Estádio Municipal 22 de Junho', the table 'Estádio Municipal de Famalicão' - the table is the odd one out (three places agree with each other); ground_table=Estádio Municipal de Famalicão; named_by=1 place(s): table; other_nam |
| 1 | Q926438 | Gil Vicente | Gil Vicente: ground 'Estádio Cidade de Barcelos' - ok | verdict=ok; ground_table=Estádio Cidade de Barcelos; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Cidade de Barcelos; Wikidata P115=Estádio Cidade de Barcelos / Estadio Cidade de Barcelos; |
| 1 | Q216503 | Marítimo | Marítimo: ground 'Estádio do Marítimo' - ok | verdict=ok; ground_table=Estádio do Marítimo; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio do Marítimo; Wikidata P115=Estádio do Marítimo / Estadio dos Barreiros; StadiumDB=Estádio do Mari |
| 1 | Q1346314 | Moreirense | Moreirense: ground 'Estádio Comendador Joaquim de Almeida Freitas' - ok | verdict=ok; ground_table=Estádio Comendador Joaquim de Almeida Freitas; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Parque de Jogos Comendador Joaquim de Almeida Freitas; Wikidata P115=Parque de Jogos Comen |
| 1 | Q216459 | Nacional | Nacional: ground 'Estádio da Madeira' - ok | verdict=ok; ground_table=Estádio da Madeira; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio da Madeira; Wikidata P115=Estádio da Madeira / Estadio da Madeira; proposed_venue=Estádio da Madeira; propose |
| 1 | Q128446 | Porto | Porto: ground 'Estádio do Dragão' - ok | verdict=ok; ground_table=Estádio do Dragão; named_by=3 place(s): table, StadiumDB, Wikidata P115; other_names=club article infobox={{lang; Wikidata P115=Estádio do Dragão / Estádio do Futebol Clube do Porto; StadiumDB=Estádio do Dragão; proposed_venue=Estádio |
| 1 | Q622432 | Rio Ave | Rio Ave: ground 'Estadio dos Arcos' - ok | verdict=ok; ground_table=Estadio dos Arcos; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio do Rio Ave FC; Wikidata P115=Estádio do Rio Ave FC / Estádio dos Arcos; StadiumDB=Estádio dos Arcos |
| 1 | Q740637 | Santa Clara | Santa Clara: ground 'Estádio de São Miguel' - ok | verdict=ok; ground_table=Estádio de São Miguel; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=[[Estádio de São Miguel (Ponta Delgada); Wikidata P115=Estádio de São Miguel / Estádio do Santa Clara; proposed_ve |
| 1 | Q75729 | Sporting CP | Sporting CP: ground 'Estádio José Alvalade' - ok | verdict=ok; notes=its P115 is also its reserve side's (Sporting CP B); ground_table=Estádio José Alvalade; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio José Alvalade; Wikidata P115=Estádio |
| 1 | Q223450 | Vitória de Guimarães | Vitória de Guimarães: ground 'Estádio D. Afonso Henriques' - ok | verdict=ok; ground_table=Estádio D. Afonso Henriques; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio D. Afonso Henriques; Wikidata P115=Estádio D. Afonso Henriques / D. Afonso Henriques Stadium; propos |
| 2 | Q243235 | Académica | Académica: ground 'Estádio Cidade de Coimbra' - ok | verdict=ok; ground_table=Estádio Cidade de Coimbra; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Cidade de Coimbra; Wikidata P115=Estádio Cidade de Coimbra / Estádio EFAPEL Cidade de Coimb |
| 2 | Q120775987 | AFS | AFS: ground 'Estádio do Clube Desportivo das Aves' - unplaced | verdict=unplaced; flags=UNPLACED by the build; notes=Wikidata names no ground; ground_table=Estádio do Clube Desportivo das Aves; named_by=3 place(s): table, StadiumDB, club article infobox; other_names=club article infobox=Estádio do CD Aves, [[Aves (Santo Ti |
| 2 | Q2841205 | Amarante | Amarante: ground 'Estádio Municipal de Amarante' - ok | verdict=ok; ground_table=Estádio Municipal de Amarante; named_by=2 place(s): table, Wikidata P115; other_names=club article infobox={{lang; Wikidata P115=Estádio Municipal de Amarante; proposed_venue=Estádio Municipal de Amarante; proposed_position=41.282090 / |
| 2 | Q7387221 | Benfica B | Benfica B: ground 'Benfica Campus - Campo n.° 1' - attention | verdict=attention; flags=P115 is the first team's ground (Benfica) - copied onto a reserve side unless the table agrees \| Wikidata names 'Estádio da Luz', the table 'Benfica Campus - Campo n.° 1' \| THE MAP WOULD BE 14851 m FROM THE PROPOSAL; ground_table=Benfi |
| 2 | Q543467 | Chaves | Chaves: ground 'Estádio Municipal Eng.° Manuel Branco Teixeira' - ok | verdict=ok; ground_table=Estádio Municipal Eng.° Manuel Branco Teixeira; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Municipal Eng. Manuel Branco Teixeira; Wikidata P115=Estádio Municipal |
| 2 | Q744353 | Farense | Farense: ground 'Estádio de São Luís' - attention | verdict=attention; flags=Wikidata names 'Estádio Algarve', the table 'Estádio de São Luís' \| THE MAP WOULD BE 8359 m FROM THE PROPOSAL; ground_table=Estádio de São Luís; named_by=3 place(s): table, StadiumDB, club article infobox; other_names=club article info |
| 2 | Q671042 | Feirense | Feirense: ground 'Estádio Marcolino Castro' - ok | verdict=ok; ground_table=Estádio Marcolino Castro; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Marcolino de Castro; Wikidata P115=Estádio Marcolino de Castro / Estadio Marcolino de Castro; proposed_ |
| 2 | Q17505449 | Felgueiras | Felgueiras: ground 'Estádio Dr. Machado de Matos' - ok | verdict=ok; ground_table=Estádio Dr. Machado de Matos; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Dr. Machado de Matos; Wikidata P115=Estádio Dr. Machado de Matos; proposed_venue=Estádio Dr. Machad |
| 2 | Q623730 | Leixões | Leixões: ground 'Estádio do Mar' - ok | verdict=ok; ground_table=Estádio do Mar; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio do Mar; Wikidata P115=Estádio do Mar / Estadio do Mar; StadiumDB=Estádio do Mar; proposed_venue=Estádi |
| 2 | Q6705180 | Lusitânia Lourosa | Lusitânia Lourosa: ground 'Estádio do Lusitânia de Lourosa FC' - unplaced | verdict=unplaced; flags=UNPLACED by the build \| NO ground-specific position found (OpenStreetMap was not queried); notes=Wikidata names no ground; ground_table=Estádio do Lusitânia de Lourosa FC; named_by=2 place(s): table, club article infobox; other_names=cl |
| 2 | Q1387471 | Penafiel | Penafiel: ground 'Estádio Municipal 25 de Abril' - ok | verdict=ok; ground_table=Estádio Municipal 25 de Abril; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Municipal 25 de Abril, [[Penafiel, Portugal; Wikidata P115=Estádio Municipal 25 de Abril; proposed |
| 2 | Q621120 | Portimonense | Portimonense: ground 'Estádio Municipal de Portimão' - ok | verdict=ok; ground_table=Estádio Municipal de Portimão; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=[[Estádio Municipal de Portimão; Wikidata P115=Estádio Municipal de Portimão; StadiumDB=Estádio |
| 2 | Q5423714 | Porto B | Porto B: ground 'Estádio Luís Filipe Menezes' - attention | verdict=attention; flags=Wikidata names 'Estádio Municipal Jorge Sampaio', the table 'Estádio Luís Filipe Menezes' \| the ground is named by ONE place only (rule: two independent places) \| NO ground-specific position found (OpenStreetMap was not queried); groun |
| 2 | Q3494112 | Sporting CP B | Sporting CP B: ground 'Estádio Aurélio Pereira' - attention | verdict=attention; flags=P115 is the first team's ground (Sporting CP) - copied onto a reserve side unless the table agrees \| Wikidata names 'Estádio José Alvalade', the table 'Estádio Aurélio Pereira' \| NO ground-specific position found (OpenStreetMap was not |
| 2 | Q1023227 | Tondela | Tondela: ground 'Estádio João Cardoso' - ok | verdict=ok; ground_table=Estádio João Cardoso; named_by=4 place(s): table, StadiumDB, Wikidata P115, club article infobox; other_names=club article infobox=Estádio João Cardoso, Tondela; Wikidata P115=Estádio João Cardoso; StadiumDB=Estádio João Cardoso; propo |
| 2 | Q1853273 | Torreense | Torreense: ground 'Estádio Manuel Marques' - ok | verdict=ok; ground_table=Estádio Manuel Marques; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Manuel Marques; Wikidata P115=Estádio Manuel Marques / Estádio manuel marques; proposed_venue=Estádio Man |
| 2 | Q211401 | União de Leiria | União de Leiria: ground 'Estádio Dr. Magalhães Pessoa' - ok | verdict=ok; ground_table=Estádio Dr. Magalhães Pessoa; named_by=3 place(s): table, Wikidata P115, club article infobox; other_names=club article infobox=Estádio Dr. Magalhães Pessoa; Wikidata P115=Estádio Dr. Magalhães Pessoa / Estádio municipal de leiria; pro |
| 2 | Q1387855 | Vizela | Vizela: ground 'Estádio do Futebol Clube de Vizela' - ok | verdict=ok; ground_table=Estádio do Futebol Clube de Vizela; named_by=3 place(s): table, StadiumDB, Wikidata P115; other_names=club article infobox=Estádio do Futebol Clube de Vizela, Vizela, Portugal; Wikidata P115=Estádio do Futebol Clube de Vizela / Estadio |

### capacity-proposal (36)

| tier | club | label | evidence | detail |
|---|---|---|---|---|
| 1 | Q2410944 | Académico de Viseu | Académico de Viseu: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 6912 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6912, wikidata 6912); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q1386850 | Alverca | Alverca: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 6932); the table and Wikidata are both Wikipedia's; figures=table 6932; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 1 | Q1386869 | Arouca | Arouca: agreed, proposed 5000 | verdict=agreed; proposed=5000; action=REPLACE the map's 5600; rule=table 5000 agrees within 5% with stadiumdb 5000; figures=table 5000; Wikidata 5600 (map's figure); OpenStreetMap None; StadiumDB 5000; stadiumdb=Estádio Municipal de Arouca (Arouca) - name-exac |
| 1 | Q131499 | Benfica | Benfica: agreed, proposed 68100 | verdict=agreed; proposed=68100; action=keep (the map's figure is in the agreement); rule=table 68100 agrees within 5% with stadiumdb 68100, wikidata 68100; figures=table 68100; Wikidata 68100 (map's figure); OpenStreetMap None; StadiumDB 68100; stadiumdb=Estád |
| 1 | Q75684 | Braga | Braga: agreed, proposed 30286 | verdict=agreed; proposed=30286; action=keep (the map's figure is in the agreement); rule=table 30286 agrees within 5% with stadiumdb 30154, wikidata 30286; figures=table 30286; Wikidata 30286 (map's figure); OpenStreetMap None; StadiumDB 30154; stadiumdb=Estád |
| 1 | Q1046440 | Casa Pia | Casa Pia: contested, blank | verdict=contested; proposed=BLANK; rule=no two independent sources agree within 5%; figures=table 7000; Wikidata None (map's figure); OpenStreetMap None; StadiumDB 2574; stadiumdb=Estádio Pina Manique (Lisbon) - name-contained via 'Casa Pia' |
| 1 | Q634829 | Estoril Praia | Estoril Praia: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 5094 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 5094; Wikidata 5094 (map's figure); OpenStreetMap N |
| 1 | Q838134 | Estrela da Amadora | Estrela da Amadora: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 9288 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 9288, wikidata 9288); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q1387105 | Famalicão | Famalicão: agreed, proposed 5186 | verdict=agreed; proposed=5186; action=keep (the map's figure is in the agreement); rule=table 5186 agrees within 5% with stadiumdb 5186, wikidata 5186; figures=table 5186; Wikidata 5186 (map's figure); OpenStreetMap None; StadiumDB 5186; stadiumdb=Estádio Muni |
| 1 | Q926438 | Gil Vicente | Gil Vicente: agreed, proposed 12046 | verdict=agreed; proposed=12046; action=keep (the map's figure is in the agreement); rule=table 12046 agrees within 5% with stadiumdb 12504, wikidata 12046; figures=table 12046; Wikidata 12046 (map's figure); OpenStreetMap None; StadiumDB 12504; stadiumdb=Compl |
| 1 | Q216503 | Marítimo | Marítimo: agreed, proposed 10600 | verdict=agreed; proposed=10600; action=keep (the map's figure is in the agreement); rule=table 10600 agrees within 5% with stadiumdb 10932, wikidata 10600; figures=table 10600; Wikidata 10600 (map's figure); OpenStreetMap None; StadiumDB 10932; stadiumdb=Estád |
| 1 | Q1346314 | Moreirense | Moreirense: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 6150 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 6150, wikidata 6150); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q216459 | Nacional | Nacional: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5200 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 5200, wikidata 5200); the table and Wikidata are both Wikipedia's; fig |
| 1 | Q128446 | Porto | Porto: agreed, proposed 50033 | verdict=agreed; proposed=50033; action=keep (the map's figure is in the agreement); rule=table 50033 agrees within 5% with stadiumdb 50033, wikidata 50033; figures=table 50033; Wikidata 50033 (map's figure); OpenStreetMap None; StadiumDB 50033; stadiumdb=Estád |
| 1 | Q622432 | Rio Ave | Rio Ave: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 5300 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 5300; Wikidata 5300 (map's figure); OpenStreetMap N |
| 1 | Q740637 | Santa Clara | Santa Clara: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 12500 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 12500, wikidata 12500); the table and Wikidata are both Wikipedia's; |
| 1 | Q75729 | Sporting CP | Sporting CP: agreed, proposed 52095 | verdict=agreed; proposed=52095; action=keep (the map's figure is in the agreement); rule=table 52095 agrees within 5% with stadiumdb 50095, wikidata 52095; figures=table 52095; Wikidata 52095 (map's figure); OpenStreetMap None; StadiumDB 50095; stadiumdb=Estád |
| 1 | Q223450 | Vitória de Guimarães | Vitória de Guimarães: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 30029 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 30029, wikidata 30029); the table and Wikidata are both Wikipedia's; |
| 2 | Q243235 | Académica | Académica: agreed, proposed 29622 | verdict=agreed; proposed=29622; action=keep (the map's figure is in the agreement); rule=table 29622 agrees within 5% with stadiumdb 30210, wikidata 29622; figures=table 29622; Wikidata 29622 (map's figure); OpenStreetMap None; StadiumDB 30210; stadiumdb=Estád |
| 2 | Q120775987 | AFS | AFS: contested, blank | verdict=contested; proposed=BLANK; rule=no two independent sources agree within 5%; figures=table 6230; Wikidata None (map's figure); OpenStreetMap None; StadiumDB 5441; stadiumdb=Estádio do CD das Aves (Aves) - name-contained via 'AVS' |
| 2 | Q2841205 | Amarante | Amarante: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 5000, wikidata 5000); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q7387221 | Benfica B | Benfica B: agreed, proposed 2644 | verdict=agreed; proposed=2644; action=REPLACE the map's 68100; rule=table 2644 agrees within 5% with stadiumdb 2708; figures=table 2644; Wikidata 68100 (map's figure); OpenStreetMap None; StadiumDB 2708; not_used=Wikidata's 68100 is the capacity of Estádio da |
| 2 | Q543467 | Chaves | Chaves: agreed, proposed 8400 | verdict=agreed; proposed=8400; action=keep (the map's figure is in the agreement); rule=table 8400 agrees within 5% with stadiumdb 8400, wikidata 8400; figures=table 8400; Wikidata 8400 (map's figure); OpenStreetMap None; StadiumDB 8400; stadiumdb=Estádio Muni |
| 2 | Q744353 | Farense | Farense: agreed, proposed 7000 | verdict=agreed; proposed=7000; action=REPLACE the map's 30305; rule=table 7000 agrees within 5% with stadiumdb 7000; figures=table 7000; Wikidata 30305 (map's figure); OpenStreetMap None; StadiumDB 7000; not_used=Wikidata's 30305 is the capacity of Estádio Alg |
| 2 | Q671042 | Feirense | Feirense: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5401 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 5401, wikidata 5401); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q17505449 | Felgueiras | Felgueiras: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 7540 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 7540, wikidata 7540); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q623730 | Leixões | Leixões: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 6000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 6000; Wikidata 6000 (map's figure); OpenStreetMap N |
| 2 | Q6705180 | Lusitânia Lourosa | Lusitânia Lourosa: single-source, blank | verdict=single-source; proposed=BLANK; rule=one independent source only (table 4900); the table and Wikidata are both Wikipedia's; figures=table 4900; Wikidata None (map's figure); OpenStreetMap None; StadiumDB None; stadiumdb=no StadiumDB ground carries this |
| 2 | Q1387471 | Penafiel | Penafiel: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 5230 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 5230, wikidata 5230); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q621120 | Portimonense | Portimonense: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 4961 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 4961; Wikidata 4961 (map's figure); OpenStreetMap N |
| 2 | Q5423714 | Porto B | Porto B: single-source, blank | verdict=single-source; proposed=BLANK; action=CLEAR the map's 8500: it is the capacity of another ground (Estádio Municipal Jorge Sampaio), unless the two names are one ground; rule=one independent source only (table 3800); the table and Wikidata are both Wiki |
| 2 | Q3494112 | Sporting CP B | Sporting CP B: single-source, blank | verdict=single-source; proposed=BLANK; action=CLEAR the map's 52095: it is the capacity of another ground (Estádio José Alvalade), unless the two names are one ground; rule=one independent source only (table 1180); the table and Wikidata are both Wikipedia's; |
| 2 | Q1023227 | Tondela | Tondela: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 5000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 5000; Wikidata 5000 (map's figure); OpenStreetMap N |
| 2 | Q1853273 | Torreense | Torreense: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 2431 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 2431, wikidata 2431); the table and Wikidata are both Wikipedia's; fig |
| 2 | Q211401 | União de Leiria | União de Leiria: single-source, blank | verdict=single-source; proposed=BLANK; action=no change proposed: the map's 23888 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=one independent source only (table 23888, wikidata 23888); the table and Wikidata are both Wikipedia's; |
| 2 | Q1387855 | Vizela | Vizela: contested, blank | verdict=contested; proposed=BLANK; action=no change proposed: the map's 6000 has no independent agreement (it rests on Wikipedia/Wikidata alone); rule=no two independent sources agree within 5%; figures=table 6000; Wikidata 6000 (map's figure); OpenStreetMap N |

## Appendix: tagged but dissolved (not drawn)

- none

## Appendix: tagged extras whose tag is not truthy (not drawn)

- Q757422 Atlético Clube de Portugal (shape C)
- Q219703 Boavista F.C. (shape C)
- Q208585 Vitória F.C. (shape C)
