# German competitions queue

Created 2026-11-19 (first session of the German competitions job, PR #232).
One batch per session: up to 4 national competitions, or up to 6 regional
cups, or up to 8 "follow only" rows. Men's football only. Every row is
researched under the "Competition research procedure" of
`docs/claude/conventions.md`.

- **status**: `researched` = the competition has info rows from a research
  pass of its own under the procedure (PR #158 DFB-Pokal, PR #159 Bundesliga,
  PR #232 batch 1); `pending` = it has none. The three play-offs have rows
  from the phase 4a fact check (PR #224) only, not from a research pass, so
  they are `pending`; their rows are kept and corrected under the procedure
  when their turn comes. `blocked` = the association's own site is closed, so
  the cup has no name from its own site and is not in `data/competitions.csv`.
- **follow**: `done` = the competition has a "where to follow it" row (topic
  `tracking`); `missing` = it has none.
- **Order**: pending national competitions (as in `data/competitions.csv`),
  then the regional cups (the three Baden-Württemberg associations first, then
  the rest alphabetically by association), then researched competitions whose
  "follow" is missing.

**The DFB's own sites are closed** (found in run 1 of PR #232): the DFB's terms
of use for all its portals and apps (`https://www.dfb.de/nutzungsbedingungen`,
where fussball.de's terms link leads) forbid automated crawling and scraping
and the scripts for it, and reserve commercial text and data mining under
§ 44b UrhG. So dfb.de, fussball.de, datencenter.dfb.de and assets.dfb.de are
never read. On Alexandru's decision of 2026-11-19, Wikipedia (de) is the
entry point that names the associations and their sites; each association's
own site is then the source. The list of the 5 regional and 21 state
associations is from Wikipedia's DFB article (source C60), not from a DFB
page, as the job prompt asked; that could not be done.

## National competitions

| # | id | status | follow | batch / PR / date |
|---|---|---|---|---|
| 1 | de-2-bundesliga | researched | done (unverified: no open organiser page) | batch 1, PR #232, 2026-11-19 |
| 2 | de-3-liga | researched | done (unverified: no open organiser page) | batch 1, PR #232, 2026-11-19 |
| 3 | de-regionalliga-bayern | researched | done (confirmed) | batch 1, PR #232, 2026-11-19 |
| 4 | de-regionalliga-nord | researched | done (unverified: organiser pages show no season) | batch 1, PR #232, 2026-11-19 |
| 5 | de-regionalliga-nordost | researched | done (confirmed) | batch 2, PR #233, 2026-11-19 |
| 6 | de-regionalliga-suedwest | researched | done (confirmed) | batch 2, PR #233, 2026-11-19 |
| 7 | de-regionalliga-west | researched | done (confirmed) | batch 2, PR #233, 2026-11-19 |
| 8 | de-dfl-supercup | researched | done (unverified: the DFL's sites are closed) | batch 2, PR #233, 2026-11-19 |
| 9 | de-2-bundesliga-relegation-play-off | researched | done (unverified: no open organiser or broadcaster page) | batch 3, PR #234, 2026-11-19 |
| 10 | de-aufstiegsspiele-zur-3-liga | researched | done (unverified: the feeding leagues' channels; the DFB is closed) | batch 3, PR #234, 2026-11-19 |
| 11 | de-bundesliga-relegation-play-off | researched | done (unverified: no open organiser or broadcaster page) | batch 3, PR #234, 2026-11-19 |

## Regional cups (Verbandspokal / Landespokal)

Added to `data/competitions.csv` in batch 1 (PR #232), 20 rows, id
`de-verbandspokal-<association>` (not the sponsor's name, which changes),
name as the association's own site writes it, country `DE`, type `cup`,
`officialUrl` only where the cup page itself was opened. The file has no
organiser column; the organiser is the association named here and goes into
an `other` row when the cup is researched. Niedersachsen runs two cups, both
sending a team to the DFB-Pokal (NFV page), so it has two rows.

| # | id | association (site) | name on its own site | status | follow |
|---|---|---|---|---|---|
| 12 | de-verbandspokal-baden | Badischer FV (badfv.de) | Volksbanken Raiffeisenbanken bfv-Pokal | pending | missing |
| 13 | de-verbandspokal-suedbaden | Südbadischer FV (sbfv.de) | Volksbanken Raiffeisenbanken SBFV-Pokal | pending | missing |
| 14 | de-verbandspokal-wuerttemberg | Württembergischer FV (wuerttfv.de) | Volksbanken Raiffeisenbanken WFV-Pokal | pending | missing |
| 15 | de-verbandspokal-bayern | Bayerischer FV (bfv.de) | Bayerischer Toto-Pokal (page title "Der bayerische Toto-Pokal-Wettbewerb", menu "TOTO-POKAL") | pending | missing |
| 16 | de-verbandspokal-berlin | Berliner FV (berliner-fussball.de) | COSY-WASCH Landespokal | pending | missing |
| 17 | de-verbandspokal-brandenburg | FLB Brandenburg (flb.de) | Herren-Landespokal Brandenburg | pending | missing |
| 18 | de-verbandspokal-bremen | Bremer FV (bremerfv.de) | LOTTO-Pokal | pending | missing |
| 19 | de-verbandspokal-hamburg | Hamburger FV (hfv.de) | LOTTO Hamburg-Pokal (the site writes "den LOTTO Hamburg- und HOLSTEN-Pokal"; which of the two sends the DFB-Pokal team is to be checked) | pending | missing |
| 20 | — | Hessischer FV (hfv-online.de) | not read: bot challenge (HTTP 403) | blocked | missing |
| 21 | de-verbandspokal-mecklenburg-vorpommern | LFV Mecklenburg-Vorpommern (lfvm-v.de) | Lübzer Pils Landespokal | pending | missing |
| 22 | de-verbandspokal-mittelrhein | FV Mittelrhein (fvm.de) | Bitburger-Pokal | pending | missing |
| 23 | de-verbandspokal-niederrhein | FV Niederrhein (fvn.de) | Niederrheinpokal | pending | missing |
| 24 | de-verbandspokal-niedersachsen | Niedersächsischer FV (nfv.de) | Niedersachsenpokal 3. Liga und Regionalliga Nord | pending | missing |
| 25 | de-verbandspokal-niedersachsen-amateure | Niedersächsischer FV (nfv.de) | Krombacher-Niedersachsenpokal der Amateure | pending | missing |
| 26 | de-verbandspokal-rheinland | FV Rheinland (fv-rheinland.de) | Rheinlandpokal | pending | missing |
| 27 | de-verbandspokal-saarland | Saarländischer FV (saar-fv.de) | Sparkassen-Pokal Saar | pending | missing |
| 28 | de-verbandspokal-sachsen | Sächsischer FV (sfv-online.de) | Wernesgrüner Sachsenpokal | pending | missing |
| 29 | de-verbandspokal-sachsen-anhalt | FV Sachsen-Anhalt (fsa-online.de) | dachbleche24-Landespokal | pending | missing |
| 30 | de-verbandspokal-schleswig-holstein | Schleswig-Holsteinischer FV (shfv-kiel.de) | LOTTO Pokal | pending | missing |
| 31 | de-verbandspokal-suedwest | Südwestdeutscher FV (swfv.de) | Bitburger Verbandspokal | pending | missing |
| 32 | de-verbandspokal-thueringen | Thüringer FV (thueringerfv.de; tfv-erfurt.de forwards there) | Thüringen Pokal | pending | missing |
| 33 | — | FLVW Westfalen (flvw.de) | not read: "Bot/Crawler detected", HTTP 400 | blocked | missing |

Next batch: the regional cups, rows 12 to 17 (Baden, Südbaden, Württemberg,
then Bayern, Berlin, Brandenburg).

## Researched competitions

`de-dfb-pokal` (follow `done`), `de-bundesliga` (follow `done`). No
researched German competition has "follow" missing.

## Batch 1 (2026-11-19, PR #232)

Rows 1 to 4: 2. Bundesliga, 3. Liga, Regionalliga Bayern, Regionalliga Nord.
Written before any page was read. 8 probe runs of 8 used.

| id | rows | confirmed | inferred | unverified | follow |
|---|---|---|---|---|---|
| de-2-bundesliga | 5 | 0 | 0 | 5 | done |
| de-3-liga | 6 | 0 | 0 | 6 | done |
| de-regionalliga-bayern | 8 | 6 | 1 | 1 | done |
| de-regionalliga-nord | 5 | 4 | 0 | 1 | done |

Left: 7 national competitions, 20 regional cups (2 more blocked), 0 "follow
only" rows: 27 rows to research, plus the 2 blocked cups.

## Batch 2 (2026-11-19)

Rows 5 to 8: Regionalliga Nordost, Regionalliga Südwest, Regionalliga West,
Franz Beckenbauer Supercup. Written before any page was read. 6 probe runs of 8
used.

| id | rows | confirmed | inferred | unverified | follow |
|---|---|---|---|---|---|
| de-regionalliga-nordost | 6 | 5 | 1 | 0 | done |
| de-regionalliga-suedwest | 6 | 5 | 1 | 0 | done |
| de-regionalliga-west | 6 | 5 | 1 | 0 | done |
| de-dfl-supercup | 4 | 0 | 0 | 4 | done (Wikipedia only) |

Left: 3 national competitions (the play-offs), 20 regional cups (2 more
blocked), 0 "follow only" rows: 23 rows to research, plus the 2 blocked cups.

## Batch 3 (2026-11-19)

Rows 9 to 11 (PR #234): 2. Bundesliga relegation play-off, Aufstiegsspiele zur 3. Liga,
Bundesliga relegation play-off (the last three national competitions; no
regional cup is mixed into a national batch). Written before any page was
read. Their phase 4a rows (PR #224) have a basis other than search-result
summaries, so under the procedure they are not edited: only blank cells and
missing topics are filled, and a difference with what is read goes to the
report as a conflict.
6 probe runs of 8 used (run 5 and 6 only to settle sat1.de, which forwards to
joyn.de, closed by a § 44b UrhG reservation).

| id | new rows | confirmed | inferred | unverified | rows in all | follow |
|---|---|---|---|---|---|---|
| de-bundesliga-relegation-play-off | 4 | 0 | 1 | 3 | 6 | done (Wikipedia only) |
| de-2-bundesliga-relegation-play-off | 4 | 0 | 1 | 3 | 6 | done (Wikipedia, BFV results pages) |
| de-aufstiegsspiele-zur-3-liga | 5 | 2 | 2 | 1 | 6 | done (BFV and NFV channels) |

The phase 4a rows were not edited (their basis is not search summaries);
differences are in open-problems.md. Left: 0 national competitions, 20
regional cups (2 more blocked), 0 "follow only" rows: 20 rows to research,
plus the 2 blocked cups.
