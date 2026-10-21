# Proposal for PT (Portugal)

Generated 2026-10-21 14:47 UTC by `tools/propose_country.py`. **Read-only evidence, not decisions**: nothing here was written to a hand-written file or a club file; a gap is a gap.

## Summary

| kind | rows |
|---|---|
| roster-ok | 29 |
| roster-untagged | 3 |
| roster-wrong-tier | 4 |
| extra-tagged | 21 |
| duplicate | 2 |
| women-candidate | 5 |

Tagged but dissolved (not drawn by the build, no row): 0; tagged extras whose tag is not truthy (not drawn, no row): 3; women's football items pointing at a club, carrying neither tag: 5 (other-sport items ignored: 20).

Step durations (s): 1 rosters 2.6, 2 leagues 5.8, 3 items 4.2, 4 rank cross-check 1.2, 5 evidence for extras 8.5, 6 candidates 0.0, 7 wiring patch 0.3

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
| 2 | Q290884 | A.D. Ovarense | The club currently competes in the AF Aveiro Second Division following a seventh-place finish in the 2011–12 AF Aveiro Second Division season. | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Campeonato de Portugal: Ovarense; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal |
| 2 | Q846008 | Associação Naval 1º de Maio | Founded on 1 May 1893, it last played in the Division of Honour in the Coimbra Football Association, holding home games at the Estádio Municipal José Bento Pess | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (1 |
| 2 | Q59212899 | B-SAD | Competing initially under the name Belenenses SAD, the club played four seasons in the Primeira Liga between 2018 and 2022, before successive relegations to Lig | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); intro_mentions_a_tracked_league=Primeira Liga, Liga Portugal 2 (read the sentence: a past season or now?); listed_in_lower_article=not listed in the lower article |
| 2 | Q17524289 | C.D. Cova da Piedade | The club merged with B-SAD, in an attempt of the former to retain their position currently in Liga 3, the third tier of Portuguese football, but they weren't gr | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs |
| 2 | Q176099 | C.D. Fátima | Centro Desportivo de Fátima, simply known as Fátima, is a Portuguese football club based in Fátima, in the municipality of Ourém. [no sentence of the intro name | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Campeonato de Portugal: Fátima; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); |
| 2 | Q1023233 | C.D. Trofense | Founded in 1930, it plays in Liga 3, holding home games at Estádio do Clube Desportivo Trofense, with a capacity of 5,017 spectators. | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Liga 3 (Portugal): Trofense; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); p5 |
| 2 | Q216510 | C.F. Os Belenenses | ... Os Belenenses or simply Belenenses, is a Portuguese sports club best known for its football team, which currently competes in Liga 3, the third tier of the | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Liga 3 (Portugal): Belenenses; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, 201 |
| 2 | Q1762119 | C.F. União | ... a Portuguese football club based in Funchal, Madeira, notable for its six seasons in the Portuguese top-flight Primeira Liga, between the 1989–90 and 1991–9 | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); intro_mentions_a_tracked_league=Primeira Liga (read the sentence: a past season or now?); listed_in_lower_article=not listed in the lower article(s) given; absent |
| 2 | Q5006215 | C.S. Marítimo B | Club Sport Marítimo B is a Portuguese football club that currently plays in the AF Madeira 1ª Divisão. | drawn_by_build=yes: has a position; listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal |
| 1 | Q1023163 | Clube Desportivo das Aves | ... commonly known as Desportivo das Aves, or simply as Aves, was a Portuguese football club based in Vila das Aves, Santo Tirso. [no sentence of the intro name | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (1 |
| 1 | Q1387110 | F.C. Felgueiras | Futebol Clube de Felgueiras was a Portuguese football club from Felgueiras. [no sentence of the intro names a league] | drawn_by_build=yes: has a position; first_sentence_of_intro_is_past_tense=yes ("was a ... club"); listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (1 |
| 2 | Q371136 | F.C. Paços de Ferreira | Founded in 1950, the club competes in Liga 3, holding home games at the 9,076 seat Estádio Capital do Móvel The club's colours are yellow and green. | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Liga 3 (Portugal): Paços de Ferreira; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (norm |
| 2 | Q1256652 | Gondomar S.C. | Founded on 1 May 1921, it currently plays in the fourth-tier Campeonato de Portugal, holding home games at Estádio de São Miguel, with a capacity of 2.450 spect | drawn_by_build=yes: has a position; listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal |
| 1 | Q688300 | S.C. Beira-Mar | Its football team currently plays in the Campeonato de Portugal, the fourth national level, having gained promotion by winning the Aveiro FA First Division 2018 | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Campeonato de Portugal: Beira-Mar; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Primeira Liga (normal, |
| 2 | Q7387158 | S.C. Braga B | Reserve teams in Portugal play in the same league system as the senior team, rather than in a reserve team league. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; listed_in_lower_article=2026–27 Campeonato de Portugal: Braga B; absent_from=2026–27 Primeira Liga (18 clubs |
| 2 | Q1891367 | S.C. Covilhã | Covilhã, is a Portuguese football club from the city of Covilhã that plays in the third-tier Liga 3. | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Liga 3 (Portugal): Sp. Covilhã; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal); |
| 2 | Q1031307 | S.C. Freamunde | Founded on 19 March 1933, it currently plays in the Campeonato de Portugal, holding home matches at the 3,919-capacity Complexo Desportivo do SC Freamunde. | drawn_by_build=yes: has a position; listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal |
| 2 | Q2061414 | U.D. Oliveirense | The main football team currently plays at the Estádio Carlos Osório which holds a seating capacity of 1,750 and plays in Liga Portugal 2. | drawn_by_build=yes: has a position; intro_mentions_a_tracked_league=Liga Portugal 2 (read the sentence: a past season or now?); listed_in_lower_article=2026–27 Liga 3 (Portugal): Oliveirense; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows) |
| 2 | Q3551877 | UD Vilafranquense | The team currently compete in the 3rd division of Lisbon Football Association, equivalent to the 7th Portuguese division. | drawn_by_build=NO: no P625 on the club or on any P115 ground, so the build drops it at the coordinates gate, so there is nothing on the map to remove; listed_in_lower_article=not listed in the lower article(s) given; absent_from=2026–27 Primeira Liga (18 clubs |
| 2 | Q1429473 | Varzim S.C. | The club plays in Liga 3, following relegation in the 2021–22 Liga Portugal 2. | drawn_by_build=yes: has a position; intro_mentions_a_tracked_league=Liga Portugal 2 (read the sentence: a past season or now?); listed_in_lower_article=2026–27 Liga 3 (Portugal): Varzim; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 202 |
| 2 | Q17518847 | Vitória S.C. B | They compete in the Campeonato de Portugal, the fourth division of Portuguese football, and play their home matches at the club's 2,500-capacity Academia do Vit | drawn_by_build=yes: has a position; listed_in_lower_article=2026–27 Liga 3 (Portugal): Vitória SC B; absent_from=2026–27 Primeira Liga (18 clubs resolved, 0 unread rows); 2026–27 Liga Portugal 2 (18 clubs resolved, 0 unread rows); tags=Liga Portugal 2 (normal) |

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

## Appendix: tagged but dissolved (not drawn)

- none

## Appendix: tagged extras whose tag is not truthy (not drawn)

- Q757422 Atlético Clube de Portugal (shape C)
- Q219703 Boavista F.C. (shape C)
- Q208585 Vitória F.C. (shape C)
