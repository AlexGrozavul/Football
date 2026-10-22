# Files, hand-written, generated and code: the full entries

Moved byte for byte from CLAUDE.md (old lines 148-1007, 2026-10-22). Long new entries go here; CLAUDE.md keeps only rules and index lines. Grep this file for the name you need.

---

## Files

### Hand-written — never write to these from a script

- `data/football-rules.json` — ticket rules, bucket list, clubs, settings.
  The irreplaceable file. Structure is decided; do not redesign it.
- `data/fixtures-manual.csv` — fixtures Alexandru enters himself, mostly
  Romanian. Header-driven, so column order does not matter and unused
  optional columns may be omitted. Required: `date`, `home`, `away`,
  `feed`, `dateSource`.
- `data/clubs-manual.csv` — corrections and additions to the club layer.
  **Since 2026-10-18 an optional `allowDissolved` column** (value `yes`)
  lets the hand-named fallback accept a candidate that carries a `P576`,
  for that row only and only when a tracked roster names the club
  (Conventions, "The dissolution exception of the hand-named fallback").
  A row with a `clubQid` overrides only the cells that are filled in; a
  row without one adds a club; `skip` in the tier column removes one,
  which is how a duplicate Wikidata item is dropped, and also how a club
  that only reaches the map through a wrong league tag is removed — SC
  Veltheim is the second kind. A `skip` row needs a `clubQid`, because
  there has to be something already there to remove, and every other
  cell on it is ignored. A cell reading `<clear>` is the third thing a
  cell can say, and it is not the same as leaving it empty: empty means
  *leave the fetched value alone*, `<clear>` means *delete it and put
  nothing back*. See the convention below. Same column set as
  `capacity-review.csv`.
  **Since 2026-09-27 a row may name a club the club query does not
  return**, provided it carries the club's own `clubQid`, a `country`
  and a `tier`: the **hand-named fallback** brings the club in under
  its own Q-id when Wikidata has the item and a tracked 2026-27 roster
  names it (Conventions). That is how a promoted club whose league tag
  did not follow reaches the map now. A row with **no** `clubQid` still
  adds a club, under a made-up `MANUAL-` id the roster check cannot join
  to its division - one club read as two errors on every run, which is
  what the fallback was built to end. Prefer the Q-id.
- `data/league-tiers.csv` — maps a league's Wikidata Q-id to a tier.
  Tier comes from this file and never from a league name: Wikidata's
  league items are fragmented and undated, so names cannot be trusted.
  `skip` in the tier column excludes a league.
- `data/club-tickets.csv` — one row per club per team: who may buy, how
  the club allocates, whether there is a formal cutoff, whether the
  window can close before it, how demand behaves, and whether official
  resale exists. **No cell in this file ever holds a date.** `cutoff`
  says whether a stated deadline *exists*, not when it falls.
  Since 2026-09-24 it has an optional, hand-written `country` — the
  country of the club's ground — which is how the layered view knows
  which national rows apply. A blank is reported, never filled from
  `data/clubs/*.json`; where the club is in one of those files a
  disagreement is reported and the hand-written value wins.
- `data/club-ticket-windows.csv` — one row per club per team per sales
  window. This is where a pattern-based estimate of when a recurring
  window tends to open is allowed to live, and the only place it is.
  It carries its own `dateSource` and its own `basis`.
- `data/club-ticket-prices.csv` — one row per club per team per season
  per competition per stage per category per `kind` per `opponentTier`.
  Face values, and observed resale prices, which are marked as
  observations rather than policy. `kind` is part of that key because a
  face value and a price somebody saw are two different facts about the
  same seat and the file already holds both for one category.
  `opponentTier` is part of it because a club may publish two prices for
  the same seat in the same round depending on who is visiting, and
  Bayern does — see the Conventions entry.
- `data/club-ticket-phases.csv` — added 2026-09-23. One row per
  **phase** of a window in `club-ticket-windows.csv`, numbered in the
  order they open: who may buy, how the phase opens relative to
  something (`opensRelative`, loose text, never a date), the ticket cap,
  and — in `pastCycle`, with `pastCycleFor` — the dated **past** phase a
  source recorded. The only day-level date a phase row may hold is a
  past one with a source, which is what `pastCycle` already meant.
- `data/club-ticket-rules.csv` — added 2026-09-23. **One sourced fact
  per row**, each with its own `confidence`, `basis`, `ref` and
  `sourceRefs`, and a `scope`: `general`, or a derby override
  (`derby-home`, `derby-away`) naming the opponent in `opponentQid`.
  Sector separation, away-end restrictions, personalisation or its
  absence, resale platforms and price caps live here. See the
  Conventions entry on layering.
- `data/club-ticket-demand.csv` — added 2026-09-23. A sell-out **track
  record**: one row per club per fixture per season, with `outcome`,
  loose-text `timing`, `attendance` where a source gives it, and its own
  confidence. Several seasons side by side, not one estimate.
- `data/ticket-sources.csv` — added 2026-09-23. **Every citation as its
  own row**: publisher, whether it is the club or a third party
  (`publisherKind`), title, date, URL, and `urlComplete`, which records
  a URL the source document itself cut short rather than repairing it.
  The other ticket files point at it through `sourceRefs`. Since
  2026-09-24 it also has an optional `country` column, filled on a
  source a country row cites; a source cited by both files keeps one
  row and one id. Since 2026-10-06 `publisherKind` also takes
  `federation` (the DFB) and `wiki` (Wikipedia, a third party's record),
  and the KSC research added 34 rows (`K1`-`K34`) and Germany 4
  (`DE1`-`DE4`); the KSC ids are this project's own, not a source
  document's item numbers, so the KSC rows leave `ref` blank. Since
  2026-10-07 the VfB research added 31 more (`V1`-`V31`), its own ids in
  the same way, so the VfB rows leave `ref` blank too.
- `data/country-ticket-rules.csv` — added 2026-09-24. Rules **no club
  decides** — a country's law, ministry, police or league — held once
  and inherited by every club whose ground is in that country. Same
  shape as `club-ticket-rules.csv` plus `country`, `authority`,
  `authorityKind`, `appliesTo`, `condition` and `clubLatitude`.
  `appliesTo` and `condition` are required and **never blank**: a blank
  read as "all" or "always" is the default-fill rule 2 forbids.
  `clubLatitude` (`none`, `may-add`, `implements`) says how to read a
  club row on the same topic; a club row **never replaces** a country
  row. The design, including where a fact belongs when it could sit in
  either file, is `docs/country-ticket-rules-design.md`. Holds Italy's
  four rows, moved out of Inter's club rows rather than copied, and
  **since 2026-10-06 Germany's first three** - the DFB's away-ticket
  floor (§ 25), the DFB's rule on matches with increased risk (§ 32) and
  the DFL's fair-play cap on official resale - each from a source that
  speaks for the federation or the league (Conventions, "Karlsruher SC and
  Germany's first national rows"). They now show on **every German club
  sheet**, Bayern's and Nürnberg's included.
- `data/fixture-links-manual.csv` — added 2026-09-25. Hand corrections
  to which fixture-source team a map club is: `clubQid`, `source`
  (`football-data` or `openligadb`), `teamId`, `action` (`link` or
  `reject`), `note`. Wins over everything `link_fixtures.py` decides.
  The `link` rows for one club and one source are together that club's
  whole answer for that source, so two rows can link both of the ids
  OpenLigaDB sometimes gives one club. Empty at creation: every
  ambiguity it could settle is Alexandru's to settle. Since
  2026-09-25 it also holds Le Mans (`Q210864` → football-data 535),
  and Inter (`Q631` → 108), Atalanta (`Q1886` → 102) and Sassuolo
  (`Q8603` → 471), all added on his instruction; since 2026-09-30 Real
  Madrid, Atlético, Osasuna, Deportivo and Racing, and since 2026-10-01
  the five Dutch abbreviations - AZ (`Q191264` → 682), PSV (`Q11938` →
  674), Excelsior (`Q370712` → 670), Cambuur (`Q875120` → 1909) and
  Willem II (`Q332664` → 672) - also on his instruction; since
  2026-10-02 Club Brugge (`Q190916` → 851, Champions League), on his
  instruction too. Since 2026-10-20, in the Portugal pass and under the
  instruction to link only unambiguous abbreviations, S.C. Braga (`Q75684` → 5613).
- `data/league-rosters.csv` — one line per league, telling the roster
  check which Wikipedia season article holds that league's membership:
  `leagueQid`, `country`, `tier`, `season`, `article`, `note`. The
  article title is hand-written because deriving it is exactly what
  failed on two leagues in the design pass, and the **en dash is not
  optional** — `2026–27 Bundesliga` resolves and `2026-27 Bundesliga`
  does not. The checker rejects a row whose article starts with a
  hyphen and says why.
  `leagueQid` is documentation of which league the article is about;
  the comparison is driven by `country` and `tier`, because one article
  can cover a whole level. The Regionalliga's five divisions are a
  single page and `league-tiers.csv` maps all five to tier 4, so the
  five rows share one article and it is fetched once.
  A row whose country has no file in `data/clubs/`, or whose
  `leagueQid` is not in `league-tiers.csv`, is **read back and
  skipped** rather than compared against nothing. The Austrian 2. Liga
  row was that case until 2026-09-26, holding its corrected title
  against the day Austria was added; it is now a live row.
- `data/roster-links-manual.csv` — added 2026-09-27. **Which Q-id a
  season-table row is, where the table cannot say**: `article` (exactly
  as `league-rosters.csv` writes it, en dash included), `team` (the team
  as the row shows it; footnote marks like `[a]` and `(P)` are set
  aside, case and accents folded), `clubQid`, `note`. Read by
  `check_rosters.py` and, through `roster_qids()`, by the club builder.
  It exists for the rows the reader rightly refuses: a reserve side with
  no English article of its own links its **parent** ("SK Rapid II"
  linking SK Rapid Wien), and a team cell with no link has the city as
  its first link ("Austria Wien II" linking Vienna). It can re-point a
  row the reader did read, and the read-back then says what the article
  linked, so an override is never silent. A malformed row is rejected by
  line, and a link that matched no row once its article was read is a
  problem that turns the run red - a table edited under a link is the
  change a person should look at. Holds eight rows today: since
  2026-10-02 the four Challenger Pro League U23 rows (Club NXT, Jong Genk,
  Jong KAA Gent, RSCA Futures), on Alexandru's instruction; and three 2. Liga
  rows - Rapid II and Sturm II (added on Alexandru's instruction) and
  Austria Wien II - and, since 2026-09-30, the Super League Greece 2 row
  "Asteras Tripolis B" (also on his instruction). **Since 2026-10-18 it holds nine rows**: the ninth joins the 2026-27 Liga II row "FC Bihor Oradea" (the roster's own link is the 2022 item `Q113541238`, which has no league tag, ground or position and cannot be drawn) to `Q1386940`, the 1958 item the map draws at tier 2, **Alexandru's decision of 2026-10-18**; it settles which item the roster row is read as and nothing about whether the two items are one club. The roster check now reads Bihor as one club, `ok` (the two rows `missing-from-wikidata` and `extra-not-in-roster` became one). **A link is a hand-written identity claim** - the same kind of
  decision as a `fixture-links-manual.csv` row, and Alexandru's to make.
- `data/coordinate-reviews.csv` — added 2026-09-26. **What a person
  already decided about a row of `coordinate-review.csv`**, so the
  monthly run cannot offer it again as though it were new: `clubQid`,
  `name`, `country`, `decision`, `osmRef`, `reviewed`, `reason`.
  `decision` is closed: `rejected` with an `osmRef` (that ground is
  wrong for that club and is never proposed for it again), `rejected`
  without one (the club itself is not to be placed — dissolved, not a
  club, below every tracked tier), `held` (the ground looks right and is
  kept back on purpose; needs the `osmRef`), `open` (under
  investigation). `propose_coordinates.py` reads it, prints it back with
  line numbers, rejects a malformed row by line, and writes the decision
  into the review row's `_verdict` (`held`, `open`, `rejected`) and
  `_reviewed` columns, keeping the tool's own finding as evidence. A
  held row whose ground the tool no longer proposes stays as the tool
  says, with a note that the held ground was a different one. A row for
  a club that has since been placed is named in the summary as inert.
  Applying a proposal is still a `clubs-manual.csv` row; this file never
  places anything.
- `data/derbies.csv` — added 2026-10-03. **One row per derby**: `name`,
  `clubA`, `clubB` (Q-ids), `kind` (`city`, `regional`, `historic`),
  `source` (a URL that NAMES the rivalry), and optionally `clubAName`,
  `clubBName`, `offMap`, `rulesId`, `note`. Header-driven. Read by the
  Derbies panel and `tools/check_derbies.py`; nothing writes to it. A
  Q-id that is in no club file is rejected as a probable typo **unless**
  `offMap` names that side and says why (`B: League One; GB tracks
  tiers 1-2`) - Alexandru's decision of 2026-10-03, so a derby whose
  club is off the map waits in the file instead of being lost.
  `rulesId` is a hand-written join to a `football-rules.json` bucketList
  id, so the two files can be compared without matching names. How each
  row was sourced is the Conventions entry on derbies.

- `data/football-rules-links.csv` — added 2026-10-03, on Alexandru's
  instruction. **Which club on the map each `clubs` entry of
  `football-rules.json` is**: `rulesId` (the entry's `id`), `clubQid`,
  `note`. Header-driven. It exists because the entries carry no Q-id and
  `football-rules.json`'s structure is decided, so the join lives beside
  it rather than in it. The club sheet reads it to show an entry's notes
  on that club; `check_tickets.py` reads it back, line by line, and
  rejects a line whose `rulesId` is no entry, whose Q-id is on no map,
  or that links an entry twice. Written with a line **only where the
  match was certain from the club data** - eleven of the thirteen
  entries. `dfb` (the national team) and `uefa` (finals) are not clubs
  and have no line. **Poli's line is the one to look at**: the names
  differ (Politehnica Timișoara against Știința Poli Timișoara); it was
  linked because the ground, tier and country agree, it is the only club
  at Stadionul Electrica, and its own hand row in `clubs-manual.csv` says
  what `football-rules.json` says about the Dan Păltinișanu and Eroii
  Timișoarei. **A line is an identity claim**, like a
  `fixture-links-manual.csv` row; delete one and the notes leave that
  sheet.

- `data/event-ticket-rules.csv` — added 2026-10-04, on Alexandru's
  instruction. **Ticket rules for one bucket-list entry** - a final, one
  fixture - that belong to neither a club nor a country: the columns of
  `club-ticket-rules.csv` with `bucketId` (an id in `football-rules.json`'s
  `bucketList`) in place of the club key (`clubQid`, `club`, `team`):
  `bucketId,scope,opponentQid,topic,season,rule,confidence,basis,ref,
  sourceRefs,source,checked,note`. **Header only**: it landed with its
  checker so it is never unread, and every bucket entry says
  "Event-specific ticket rules not researched yet". `check_tickets.py`
  reads it like the club rules file (closed `confidence`, `basis`,
  `scope`; the shared `topic` list) and **refuses a day-level date in
  `rule` as well as `topic`** - stricter than the club rules file, as the
  brief asked - and rejects a `bucketId` that is no entry.
- `data/bucket-links-manual.csv` — added 2026-10-04, on Alexandru's
  instruction. **Which clubs a bucket entry names, and which entry a
  ticket event belongs to**, because neither the `bucketList` entries
  nor the `ticketEvents` carry a Q-id or a link of their own, and the
  structure of `football-rules.json` is decided. Header-driven:
  `bucketId,ticketEventId,hostQid,otherQids,leg,note`. Two kinds of line:
  a **club line** (`ticketEventId` empty) - `hostQid`, the club whose
  ground the match is at, where that is known, `otherQids`, a `;`-list of
  the rest, and `leg` (`first`, `second`, `single` or empty); an entry
  whose legs have different hosts has one line per leg (the Milan derby).
  An **event line** - `ticketEventId` and its `bucketId`, nothing else;
  an event belongs to one entry. Read back line by line by
  `check_tickets.py`. **Filled only where the match was certain from
  existing data**, each line's note saying how: 12 club lines for 11 (13 for 12 until 2026-10-08, when `vfb-regular` and its two lines went)
  entries (the venue equal to a club's ground on the map, the entry's own
  `clubs` through `football-rules-links.csv`, or the `derbies.csv` row
  whose `rulesId` is the entry), 8 event lines. **Not linked**: the
  `ostderby`, `old-firm`, `intercontinental-derby` and `prague-derby`
  entries (no row in `derbies.csv`, clubs off the map or not certain),
  and three events - `poli-rapid-cup`, `fcb-pokal-r2`, `rcsa-resale` -
  which show under Reminders. **A line is an identity claim**, like a
  `fixture-links-manual.csv` row; two are judgements worth a look:
  `fcb-away-window-2026` is linked to `klassiker-away`, whose
  `blockedReason` names that window and its date, and not to
  `away-end-first`; `pokal-draw-2027`, filed under club `fcb`, is linked
  to `pokal-first-round`.
- `data/holidays-manual.csv` — added 2026-10-04, on Alexandru's
  instruction. **School holidays for the Bucket list calendar**, from his
  school calendar and the Baden-Württemberg education ministry
  (`km.baden-wuerttemberg.de/de/service/ferien`). Header-driven:
  `name,start,end,kind,dateSource,source,note`. `kind` is
  `school-holiday`, `school-holiday-movable` or `school-start`. **The
  rows are exactly the ones he gave**: six holiday blocks from
  Sommerferien 2026 to Sommerferien 2027, and Schulstart 13 Sep 2027.
  **No movable day is entered**: the brief carried a placeholder line
  (`Beweglicher Ferientag,YYYY-MM-DD,...`) that was never filled in, so
  it was left out, not guessed (Known open problems). Read back by
  `tools/check_holidays.py`, which rejects a bad date, an end before a
  start, a missing source or an unknown `dateSource`, and reports a kind
  it does not know without accepting it. The calendar shades
  **confirmed** rows only. Nothing writes to it.

- `data/competitions.csv` — added 2026-10-08. **One row per competition**:
  `id` (`<country>-<slug>`, `int-<slug>` for international), `name`,
  `country` (ISO-2, blank = Europe and international), `level` (a whole
  number for a league, blank otherwise), `type` (`league`, `cup`,
  `supercup`, `playoff`, `international`, `tournament`), `wikidataQ` (only
  where `league-tiers.csv` already holds the Q-id), `officialUrl` (blank
  unless verified; none is). First filled once from `league-tiers.csv`
  (leagues with clubs on the map; the generic Regionalliga item
  `Q2188121` is not a competition and was left out), the football-data.org
  and OpenLigaDB competitions, and the cups, finals, super cups and
  play-offs of the bucket list, deduplicated by name and country: **64
  competitions**. Nothing refreshes it.
- `data/competition-info.csv` — added 2026-10-08. `competitionId`, `topic`
  (closed, in this order: `format`, `qualification`,
  `promotion-relegation`, `season-window`, `schedule-announcement`,
  `tracking`, `other`), `text`, `status` (closed: `confirmed`, `inferred`,
  `unverified`), `basis`, `sourceId` (a `;`-list), `checkedOn`. Seeded with
  the DFB-Pokal (5 rows, all `unverified`: dfb.de could not be opened, two
  tries, so everything is from search-result summaries; the schedule row is
  `inferred`) and five play-off competitions, whose formats and sources are
  copied from the PR #65 bucket entries, `unverified`. Nothing else is
  researched.
- `data/competition-sources.csv` — added 2026-10-08. `sourceId`, `url`,
  `title`, `retrievedOn` (blank where the page was not opened), `note`.

- `data/club-rivalries.csv` and `data/club-culture-sources.csv` — rivalries added 2026-10-08, the shared source file 2026-10-09. **Both are hand-written and no script ever writes to them; fetched data never overwrites them.** `club-rivalries.csv` (`clubQ,rivalQ,rivalName,class,sourceId,checkedOn,quote`): one row per club per rival, stored separately for each club; **the class (`main`, `local`, `other`) comes only from the wording of the row's source** (arch-rival or biggest rivalry = main, derby or nearby-city rivalry = local, anything else = other); where the source does not say a rivalry exists there is no row, and no ranking is invented. **Since 2026-10-17 the file has an optional `quote` column** (header-driven; the page's own words behind the class, in the original language, 15 words at most, one contiguous piece of the opened page's plain text, one cell): **a NEW row takes its class from the wording of its quote** (arch-rival or biggest rival = main, derby or nearby-city rivalry = local, anything else = other), and the club sheet shows the quote under the row as "Source says: «…»", marked `data-content` so it is never translated, with the same renderer and the same string (`fri.quote`) as the Fan friendships quote; a row without a quote looks as before. **All 348 rows existing on 2026-10-17 before the German tiers 1-3 batch have a blank quote and keep their class**: they were written without one (the 2026-10-08 rows from citations of `derbies.csv`, the 2026-10-17 rows from pages that were checked only for naming both clubs), and no quote was invented for them afterwards - a quote is added only from an opened page. `tools/check_club_culture.py` exits 1 on a rivalry quote of more than 15 words and warns once, with a count and without listing rows, about rows with no quote. **Mirrored rivalries and the empty line, 2026-10-18 (drawn by the page only; no file, no checker changed; the same mechanism as the friendship mirror).** For every row A to B with a non-blank `rivalQ`, if B has no row of its own with `rivalQ` = A, B's sheet also shows it, mirrored: the rival shown is A (its name from the club files, tappable to A's sheet like any rival), with A's quote ("Source says: «…»"), A's source line as on A's sheet, and the label "Stated on <A>'s page only" (`riv.mirror`, ro unchecked). **A mirrored row shows NO class tag** (a class is the stating club's view) and carries `data-mirror="1"` instead of `data-class`. A row with a blank `rivalQ` is never mirrored, and a mirror needs A on the map. Mirrored rows come after the club's own rows, alphabetical by the name shown, and count in the first 5 and in "Show all (n)"; a club with only mirrored rows gets the section; the bucket-list links on a mirrored row are found as for any row. **A club on the map with no own row and no mirrored row now shows, under the Rivalries heading, "No rivalry recorded for this club yet."** (`riv.none`, ro unchecked), so every club's sheet has the Rivalries heading; the line claims nothing about any page having been checked. On 2026-10-18, against the 791 rows then in the file: 198 rows are mirrored, 104 clubs that had rows gained mirrored ones, 25 clubs gained the section, 219 of 557 clubs show the neutral line (counts printed by `tools/test_sheet_tickets.js`). Tested there, with expected values worked out from the files and with injected rows (a club with only mirrored rows, a two-sided pair, a blank `rivalQ`, "Show all (6)", English and Romanian). **Atmosphere was removed on 2026-10-10: the club sheet has Rivalries and Fan friendships only, and atmosphere content was removed because it can't be sourced.** `data/club-atmosphere.csv`, the "When the atmosphere is best" section, its strings and its test assertions are gone, and so are the three sources only it used (`C10`-`C12`). `club-culture-sources.csv` (`sourceId,url,title,retrievedOn,kind`; kind `wikipedia`, `club`, `press`, `fan-media`) holds the citations of rivalries and fan friendships; the ids `R1`-`R17` are the old `rivalry-sources.csv`, moved here unchanged. **There is no row target and no row limit**: a row exists because a source supports it, never to fill a club; a club with no sourced rows and no mirrored row shows the Rivalries heading with "No rivalry recorded for this club yet." (since 2026-10-18). Read by the club sheet's **Rivalries** section (main, then local, then other, alphabetical within a class; the first 5 shown, the rest behind "Show all (n)") and by `tools/check_club_culture.py`, which replaced `check_rivalries.py` (and its limit of 5 rows a club). The rivalry rows from 2026-10-08 are unchanged (all `other` except three Strasbourg rows, from `derbies.csv` citations). **Since 2026-10-17 the scope includes the pairs of `data/derbies.csv`** (305 rows added, all class `other`, `checkedOn` 2026-10-17; after that pass the file held 348 rows, 40 + 305 `other` and 3 `local`): each of the 248 pairs was written only where its cited page, opened on a runner, names both clubs. A club's name matches when its name, with legal-form words (FC, SV, Calcio and the like) and founding years set aside, appears in the page text, or all its words do; **a page that holds many derbies (the lists of rivalries, a country's derbies, a regional article) must also name both clubs in one line of the cited section** (the line of the fragment where the row has one), so a list that merely mentions both clubs on different lines gave no row. 183 pairs passed (65 skipped: 37 where the page did not name both clubs, 28 where a list page named them on different lines). A pair with both clubs on the map gives two rows, one per side, with `rivalQ` and the other club's name exactly from `derbies.csv` and the club file; a pair with one club on the map (`offMap`) gives one row for the on-map club with a blank `rivalQ` and the rival's name from `clubAName` or `clubBName` (34 such rows; 38 blank `rivalQ` cells in all). A side that already had a row for that rival was not written again (26 sides, no difference of class), and no pair is also a friendship that has not ended. No row exists for a pair whose cited page could not be opened (none failed). The sources are one row per distinct cited URL in `club-culture-sources.csv` (117 new rows, `C63`-`C179`; a URL with a fragment keeps it, so the section is one click away), with `retrievedOn` 2026-10-17. Clubs with a Rivalries section went from 24 to 208. **German tiers 1-3 batch, 2026-10-17: 65 rows added for 17 of the 30 clubs of tiers 1-3 that had none** (the file now holds 413 rows for 225 clubs: 365 `other`, 38 `local`, 10 `main`; 48 with a blank `rivalQ`; 348 with a blank quote). Each row comes from the club's own German Wikipedia article only, read on 2026-10-17 from the sandbox with the Wikipedia API (no workflow probe was needed; User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second), and carries a `quote` (15 words at most, checked as one contiguous piece of the saved plain text). 10 `main` (wording Erzrivale, Hauptrivale, größte Rivalität, größter Rivale: Köln for Düsseldorf; Frankfurt and Kaiserslautern for Mainz; Stuttgart for Freiburg; Lübeck for Kiel; Dresden for Magdeburg; Kaiserslautern for Waldhof Mannheim; Burghausen for Regensburg; Osnabrück and Oldenburg for Meppen), 35 `local` (derby, Nachbar, Stadtrivale, Ortskonkurrent, Region or Ruhrgebiets-Rivalen wording), 20 `other`. 55 rows have a `rivalQ`, 10 do not (the page's link is not a map club; or the paragraph has no link for the rival, as for Mainz's Darmstadt and Wehen Wiesbaden). **Fix-up of the same day (a second PR):** the class of each of the 65 rows was re-derived from its quote's wording alone and one changed (Freiburg's Freiburger FC, `Ortskonkurrenten`, `other` to `local`); the two Augsburg rows (Mainz, Leipzig) carry `Q97905916`, the map's item, not the club item `Q15755` the page links; and three blanks were filled from a link in the rivalry statement's own paragraph (Paderborn's Sportfreunde Siegen `Q609926`, Magdeburg's Hallescher FC `Q316855`, Regensburg's FC Ingolstadt 04 `Q170117`). **19 rows have a quote that does not name the rival** (the page names several rivals in one sentence and no piece of 15 words holds both the wording and the name, so the row keeps the rivalry wording): Mainz (Darmstadt, Wehen Wiesbaden), Paderborn (Ahlen, Lippstadt, Osnabrück, Siegen), Cottbus (Hansa Rostock, Hertha BSC), Düsseldorf (Wuppertal), Duisburg (Oberhausen, Münster, Bochum, Schalke), Essen (Oberhausen, Wuppertal, Düsseldorf, Münster, Schwarz-Weiß Essen), Regensburg (Ingolstadt). No rival's side was written (a club gets its row only from its own page). Not written: a rival that is only named in a match account, a transfer or a season narrative ("Lokalrivale" inside a result), and wording such as Abneigung, Antipathie, unbeliebt or Brisanz; the 13 clubs left without a row are: five whose page has none of the rivalry wording (Aachen, Saarbrücken, Hoffenheim, Wehen Wiesbaden, Elversberg), six whose page has such wording that does not meet the rule (Ingolstadt: Antipathie only; Verl, Großaspach, Havelse and Würzburger Kickers: match accounts; Dynamo Dresden: the sentence names cities, not clubs), and VfB Stuttgart II and TSG Hoffenheim II, which have no article of their own (the title redirects to the parent club). The 30-club batch was found by comparing `data/clubs/*.json` with this file by `clubQ`. **Italy, Spain, France and England batch, 2026-10-17: 298 rows for 50 of the 66 clubs (tiers 1-2) of those countries that had none**, so the file held 711 rows for 275 clubs (after the fix-ups of the third PR below it holds 712 rows for 276 clubs: 595 `other`, 97 `local`, 20 `main`; 205 with a blank `rivalQ`; 348 with a blank quote, the older rows, unchanged). By country, with the classes as corrected by those fix-ups: Italy 24 clubs, 217 rows (2 `main`, 31 `local`, 184 `other`; 7/29/181 when written); Spain 12 clubs, 35 rows (3/16/16; 5/15/15 when written); France 11 clubs, 23 rows (1/11/11; 3/10/10); England 3 clubs (Wrexham, Bolton, Bournemouth), 23 rows (4/1/18; 5/1/17). Each row comes from the club's own Wikipedia article only, read on 2026-10-17 from the sandbox with the Wikipedia API (no workflow probe, no dispatch; User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second, waiting out every 429): English first for Italy, Spain and England, French first and then English for France, and the Italian or Spanish edition for a club whose English article states none. Each carries a `quote` (15 words at most, one contiguous piece of the saved plain text of the page, checked by the tool before writing) and the 50 pages are `C182`-`C231` in `club-culture-sources.csv` (16 English, 16 Italian, 11 French, 7 Spanish; a page that gave no row has no source row). The class comes from the wording of the quote: `main` for a superlative of the rivalry or a main rival (`main rivalry`, `biggest rival`, `most intense rivalry`, `principale rivale`, `rivalità più importante`, `rivalità più sentita`, `la più accesa`, `rivalidad más intensa`, `mayor rivalidad`, `gran rival`, `rivalité la plus forte`, `principal rival`), `local` for a derby by name (derby, derbi, `Derby della ...`), `other` for everything else, a plural list (`rivalità più sentite`, `main rivalries`) included; a derby label wins over `fierce rivalry` in the same sentence. Rows with a `rivalQ`: 133 when written, 139 after the fix-ups (taken from a link of the quote's sentence, else of its paragraph, whose Q-id is in `data/clubs/*.json` and whose title or text matches the rival's name word for word; the `rivalName` is then the map club's name); 159 without after them, 165 when written (the page's link is not a map club, or the paragraph has no link for the rival). 123 rows have a quote that does not name the rival (a long list of rivals of which the quote can hold the wording and only the first names, as for Cesena's 25 and Venezia's 14 rivals). Two `club-item shape?` blanks when written: Monza's Como (the page links the city `Q1308`, not the club `Q1120838`) and Valladolid's Burgos CF (the Spanish page has no Wikidata item, so no Q-id came from it); both were filled by exact name in the fix-ups below. No row for: a rival that is only named in a match account, a transfer or a season narrative (Mantova's Padova, Modena's Bologna, Cremonese's and Juve Stabia's derby wins, Troyes's `arch-rivals Sedan`, Sochaux's Valentigney, Dunkerque's Boulogne as `émulation`); antipathy or tension with no rivalry word (`rapporti tesi`, `pessimi rapporti`, `screzi`, `ostilità`, `hostility with Getafe`, Vicenza's Juventus, Rayo's problems with ultras); a rivalry the page says has ended or is not one (Montpellier's Sète, Laval's Beauregard, Castellón's Elche, Levante and Real Murcia, Eldense's Hércules, Eibar's Real Sociedad `siguió siendo amistosa`); the rivalry of a predecessor club (Celta Fortuna's Gran Peña, Red Star's Olympique). The 16 clubs left without a row, `none stated in the pages read`: Córdoba, Real Sociedad B, Girona, Andorra, Alavés, Celta Fortuna, Albacete, Ceuta and Burgos (English and Spanish; the Spanish article of Burgos has no Wikidata item and was not saved at the time, and was read in the fix-ups below), Dunkerque, Sochaux, Grenoble, Rodez, Boulogne, Troyes and Clermont (French and English). **Judgement calls, Alexandru's to overrule:** Frosinone-Latina, Bolton's `biggest rivals` survey (Manchester United and Oldham `main`; Blackburn and Bury are `other` in their own sentence) and Bournemouth's Southampton are `main` by wording (Frosinone-Latina and Bournemouth-Leeds were `main` when written and are `other` since the fix-ups below); Red Star's PSG rivalry is `éphémère` and Nantes's Bordeaux row has the quote of the rivalry without the name. `tools/check_club_culture.py` exits 0 and warns of padding for clubs with more than 10 rows (Como 15, Vicenza 13, Atalanta 16, Cesena 28 and others): each row is a rival the page names. **Fix-ups of 2026-10-17 (a third PR, after #106; Wikipedia en, de, fr, es, it answered from the sandbox, User-Agent `FootballPlannerBot/1.0`, one request a second, every 429 waited out, no workflow probe, no dispatch).** (1) **Class.** The 20 `main` rows of the Italy, Spain, France and England batch were re-read against the word list of `main` (arch-rival, main rival, biggest/greatest/fiercest rival; Erzrivale, Erzfeind, größter Rivale, Hauptrivale, größte Rivalität; rival principal, plus grand rival, ennemi juré; acerrimo rivale, principale rivale, rivale per eccellenza, più grande rivale; máximo rival, eterno rival, principal rival, acérrimo rival, gran rival; aartsrivaal, grootste rivaal, belangrijkste rivaal, hoofdrivaal). A quote with none of those words changed class by the same table (`local` for derby, nearby-city, regional or city-rival wording, else `other`), and **superlatives of intensity (most intense, più sentita, più accesa, mayor rivalidad, `la rivalità più importante`) are not `main`**: ten rows. Main to `other`: Entella-Sestri Levante, Sassuolo-Carpi, Frosinone-Latina, Valladolid-Salamanca, Pau-Bayonne, Bournemouth-Leeds. Main to `local`: Atalanta-Brescia (`nearby club`), Cesena-Bologna (`derby con la principale squadra rivale`; `principale rivale` is split by one word, so the row is `local` by `derby` and could be argued `main`), Rayo-Real Madrid (`rival de la ciudad`) and Nantes-Bordeaux (`Derby de l'Atlantique`). The ten that stay `main` hold a listed word (`main rivalry`, `fiercest rivalry`, `biggest rival`, `gran rival`, `principal rival`): Lecce-Bari, Monza-Como, Osasuna-Zaragoza, Racing-Athletic, Castellón-Villarreal, Brest-Guingamp, Bolton's three and Bournemouth-Southampton. The `main` rows of the German batch were not re-read. (2) **The 27 clubs without a row were re-read** (German pages for the 11 German clubs; English and Spanish pages for the 9 Spanish, among them the Spanish Burgos article not saved before and the Spanish Andorra article; French and English pages for the 7 French), with the earlier wording plus historic, traditional, fierce, bitter, enmity, acharn, ennemi, hostil, acérrimo, enemistad, Fangegnerschaft, Fanfeindschaft. **One row written: Dynamo Dresden's 1. FC Magdeburg** (`other`; the Fans section says `Rivalitäten bestehen mit den Fans der sächsischen Fußballvereine aus Leipzig, Chemnitz und Aue sowie weiterer ehemaliger DDR-Oberligavereine wie dem 1. FC Magdeburg`; 23 words, so the quote is the 13-word piece that names Magdeburg and holds no rivalry word, and the row is one whose quote does not name the rivalry; Leipzig, Chemnitz and Aue are cities, so they got no row). Not written, each only in a match account, a transfer, a season narrative or a past tense: Ingolstadt (`die größte Antipathie zum SSV Jahn Regensburg`, under the heading Rivalitäten, no rivalry word in the sentence), Verl (`Lokalrivalen FC Gütersloh`, a season account), Würzburger Kickers (`Stadtrivale FV 04 Würzburg`, club history), Havelse (a derby with Hannover 96 as an attendance record), Großaspach (`Ligarivalen TSG Balingen`, a cup final), Dunkerque (`émulation avec l'US Boulogne CO`; the English page says `their rivals US Boulogne` in the promotion account), Sochaux (`son vieux rival de l'AS Valentigney`, a final of the 1930s-40s), Burgos (`su máximo rival por aquel entonces, el Palencia` and `derbi provincial ante el CD Mirandés`, both in accounts), and **Troyes: `vers le rival historique du Stade de Reims` is on the French page, in the transfers of one season (the English page has `arch-rivals Sedan` in the 2011-12 promotion account)**. Córdoba's and Celta Fortuna's rivalries (Córdoba Sporting v Electro Mecánica, Turista v Gran Peña) are of predecessor clubs. Still no rivalry stated: Aachen, Saarbrücken, Hoffenheim, Wehen Wiesbaden, Elversberg, Córdoba, Real Sociedad B, Girona, Andorra, Alavés, Celta Fortuna, Albacete, Ceuta, Grenoble, Rodez, Boulogne and Clermont. (3) **Links.** Of the 175 blank `rivalQ` cells of the batches of #104 and #106, none had a qualifying link (a link of the quote's sentence, else of its paragraph, whose Q-id is a map club and whose text or title shares a folded word with the rival's name; a shared common word such as `Real` matched only a rival that already had a row). **Eight were filled by exact name**: the rival's name as the page writes it, with legal-form words and founding years set aside, equals the name (treated the same) of exactly one map club of the stating club's country, and the pair is neither a row yet nor an unended friendship; the `rivalName` is then the map club's name. They are Mainz's SV Darmstadt 98 and SV Wehen Wiesbaden, Monza's Como (Como 1907) and Pisa (Pisa Sporting Club), Valladolid's Burgos CF, Castellón's Villarreal CF, Laval's Le Mans (Le Mans Football Club) and Bournemouth's Leeds United (Leeds United F.C.). 167 blanks of those batches remain: 164 where the rival is a club not on the map (the page links an item that is no map club), none cross-border, and 3 unresolved (Entella's Sestri Levante, Castellón's Hércules and Pau's Aviron bayonnais FC: the sentence names the club without a link that identifies it). **Netherlands, Belgium, Switzerland and Austria batch, 2026-10-17 (a fourth PR): 27 rows for 15 of the 66 clubs (tiers 1-2) of those countries that had none**, so the file now holds 739 rows for 291 clubs: 609 `other`, 108 `local`, 22 `main`; 211 with a blank `rivalQ`; 348 with a blank quote (the older rows, unchanged). By country: Netherlands 5 clubs, 11 rows (2 `main`, 3 `local`, 6 `other`); Belgium 5 clubs, 8 rows (0/4/4); Switzerland 3 clubs, 6 rows (0/2/4); Austria 2 clubs, 2 rows (0/2/0). Each row comes from the club's own Wikipedia page only, read from the sandbox with the API (User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second, every 429 waited out; no workflow probe, no dispatch): English first, then Dutch for the Dutch and Flemish clubs, French for the Walloon, Brussels and Romandie clubs, German for the Swiss German clubs; for Austria German first, then English. Each carries a `quote` (15 words at most, one contiguous piece of the saved plain text, checked with `grep -F`) and the 15 pages are `C232`-`C246` (9 English, 2 German, 3 Dutch, 1 French). Classes follow the table of the fix-ups above; judgement calls, Alexandru's to overrule: `local` for `city neighbours` (Antwerp-Beerschot), `crosstown rival` (Charleroi), `principal city rivalry` (Union SG-RWD Molenbeek, not `main` because `principal rivalry` is not on the main list), `binnen de provincie ... de rivaal` (AZ-Ajax) and `Landeskonkurrenten` (Admira-SKN St. Pölten); Sparta's Excelsior row quotes the section heading `Rivaliteit met Excelsior`. `main`: Vitesse-N.E.C. (`archrivals`) and Sparta-Feyenoord (`aartsrivaal`). Rows with a `rivalQ`: 21 (19 from a link of the quote's sentence, one from the paragraph, Beerschot-Antwerp, one by exact name, Admira-SKN St. Pölten); 6 without: four where the rival is not on the map (ROC de Charleroi-Marchienne, RWD Molenbeek, FC Baden, Wiener Sport-Club) and two where it is, with no link to identify it (Excelsior's `Feyenoord`, whose map name is `Feyenoord Rotterdam`; Sparta's `Excelsior`, quoted from a heading). One row has a quote that does not name the rival (Beerschot-Antwerp: `sindsdien bestaat een grote rivaliteit tussen beide clubs`, the rival is in the sentence before). One `club-item shape?`: Antwerp's `Beerschot A.C.` links `Q646079`, the old club; the same sentence says `now known as K Beerschot VA` and links the map's `Q2268833`, which the row uses. No club has more than 10 rows. The 51 clubs without a row, `none stated in the pages read`: NL Utrecht, Telstar, Helmond Sport, Jong AZ, Jong Ajax, Jong FC Utrecht, Jong PSV, RKC Waalwijk; BE Westerlo, Genk, Lommel, OH Leuven, La Louvière, Sint-Truiden, Club NXT, Dender, Francs Borains, Lierse, Eupen, Patro Eisden, Seraing, RSCA Futures, Virton, Hasselt (Jong Genk and Jong KAA Gent have no article of their own: the title redirects to the parent club, so they were skipped; Virton has no English article); CH Sion, Vaduz, Rapperswil-Jona, Stade Lausanne-Ouchy, Stade Nyonnais, Winterthur, Neuchâtel Xamax, Yverdon-Sport, Étoile Carouge; AT Salzburg, Lustenau, Altach, Hartberg, WSG Tirol, Voitsberg, Hertha Wels, Liefering, Floridsdorf, Kapfenberg, Bregenz, Rapid Wien II, Sturm Graz II (the English titles of both redirect to the parent club, their German articles state none), SKN St. Pölten, Amstetten and Young Violets (Young Violets has no English article). Not written, only in a match account, a transfer, a season narrative, a past tense or a predecessor club: Utrecht's `belangrijkste opponent` Ajax (under the heading Rivaliteit, no rivalry word for Ajax), Genk's `derby rival Sint-Truiden`, Altach's `Lokalrivalen` Lustenau, Bregenz's Vorarlberg derby as an attendance record, First Vienna's `Erzrivalen` Vienna Cricket and Football-Club (1897, a club that no longer plays football), Telstar's `direct rival Volendam`, Winterthur's `cantonal rivals` Grasshopper (a coach move), Yverdon's `rival Lausannois` (a cup tie), Seraing's `voisin et rival du Standard` (an absorption), Hertha Wels's `Stadtrivalen FC Wels` (a merger), Westerlo's `rivalry between the teams` (two predecessors), Young Violets's and Rapid II's `Rivalen` in cup accounts, Charleroi's `Rivals from Olympic Charleroi` (1930s-40s), Leuven's derby with Daring (historic) and Sint-Truiden's Limburg derby (a match). **Fix-ups of 2026-10-18 (a sixth PR; Wikipedia en, de, fr, nl, es answered from the sandbox, User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second, every 429 waited out, no workflow probe, no dispatch).** (1) **The eight rows of PR #107 filled by exact name were re-checked** against the rule (only legal-form words such as FC, SV, AS, AC, US, CF, SSC, SC, and their spelled-out forms `Football Club` and `Sporting Club`, and founding years are set aside; `Leeds` and `Leeds United` are not equal): Mainz's SV Darmstadt 98 and SV Wehen Wiesbaden (the page writes the same names), Monza's Como (`Como` against `Como 1907`, year only) and Pisa (`Pisa` against `Pisa Sporting Club`, spelled-out SC only), Valladolid's Burgos (`Burgos C.F.` against `Burgos CF`), Laval's Le Mans (`le Mans` against `Le Mans Football Club`, spelled-out FC only) and Bournemouth's Leeds United (`Leeds United` against `Leeds United F.C.`) are equal, and no `rivalQ` was blanked for the name. **Castellón's Villarreal is the exception to the name rule and was kept on another basis**: the page writes `Villareal CF` (a typo), which is not equal to `Villarreal CF`, but the quote's own sentence links the page `Villareal CF`, which Wikipedia resolves to `Q12297` (checked with pageprops), so the cell rests on the page's link and not on the name. (2) **One row written: Troyes's Stade de Reims** (`other`, `C247`, quote `vers le rival historique du Stade de Reims`, `rivalQ` `Q208228` from the link in that sentence and the exact name). The sentence sits in the transfers of the 2018-19 pre-season and its grammar is loose (`le rival historique du Stade de Reims`), so it reads as Reims being Troyes's historic rival; the row is a judgement, Alexandru's to overrule. (3) **Dresden's Magdeburg row stays**: the sentence names the club `1. FC Magdeburg` (`... weiterer ehemaliger DDR-Oberligavereine wie dem 1. FC Magdeburg`), and the next sentence calls the match the `Elb-Clásico`; Leipzig, Chemnitz and Aue are cities and have no row. Cesena's Bologna row (`local`, `derby con la principale squadra rivale, il Bologna`) was read again and not changed. (4) **The NL, BE, CH and AT audit.** Of the 51 clubs without a row only **15** are tier 1 (NL 2, BE 6, CH 2, AT 5), not 24. For every one the club's English page and its own-language editions were read again (NL: en, nl; BE: en, nl, fr; CH: en, de, fr; AT: en, de), 145 pages opened with the 16 ES/FR clubs of the next paragraph, and each searched for the rivalry words of the table plus `historic`, `traditional`, `fierce`, `bitter`, `traditioneel`, `historisch`, `fel`, `traditionell`, `Fangegnerschaft`, `historique`, `traditionnel`, `acharn`, `hostil` within two lines of a rival or rivalry word. Pages opened: NL 15, BE 45, CH 27, AT 28; no page in any edition: none; one edition missing: Helmond Sport (nl), Club NXT (fr), Jong Genk (en, fr), Jong KAA Gent (en, fr), K. Lierse SK (nl, fr), RSCA Futures (fr), Sporting Hasselt (nl), SC Schwarz-Weiß Bregenz (de), SK Rapid Wien II (en), SK Sturm Graz II (en), Young Violets Austria Wien (en). Pages with no rivalry word: NL 12, BE 29, CH 22, AT 16. **Six rows written** (all from a sentence that states the rivalry by a rivalry word; a transfer or season paragraph was not a reason to skip it): KRC Genk's Standard and Sint-Truiden (`main`, Dutch page: `aartsrivaal`, the first in the sale of Defour), Westerlo's KFC Heultje (`local`, French page, `derbys`; Heultje is not on the map), Dender's Denderleeuw (`other`, French page, `son rival de Denderleeuw`; the page names the town, not the club, so `rivalQ` is blank), Lausanne-Ouchy's Lausanne-Sport (`local`, French page, `derbies lausannois avec son voisin`) and Winterthur's Grasshopper (`other`, English page, `cantonal rivals`, in a coach's move). **Borderline, not written** (a match account, a merger or predecessor club, a title race, a derby label for one game, or no club named): Telstar `Visserderby tegen lokale rivaal FC Volendam` and `direct rival Volendam`; Utrecht `ontbreekt het FC Utrecht aan een echte klassieke rivaal` (the page says it has none); Genk `fusionne avec son rival de Waterschei`; La Louvière `face au rival borain`, `face à leur rival carolo`; Seraing `voisin et rival du Standard de Liège absorber le club`; Virton `alors rival de l'Union Sportive Virtonaise` and `Luxemburgse derby ... RSC Habay-la-Neuve`; Eupen `main rivals for the championship, Alken`; Leuven `een derby met de stadsgenoot`; Yverdon `battre le rival Lausannois en demi-finale`; Xamax `Stadtrivalen FC Cantonal Neuchâtel`, `Lokalrivalen FC Serrières`; Salzburg `der Rivale aus Linz`; Young Violets `Rivalen SK Rapid Wien`; Rapid II `des Rivalen FK Austria Wien`; Wels `Stadtrivalen FC Wels`; Lustenau `Ortskonkurrenten FC Lustenau 07`; Bregenz `Vorarlberg derby against SC Austria Lustenau`; Floridsdorf `Bezirksrivalen SV Amateure Fiat Wien`. (5) **Sources.** 145 rows (`C247`-`C391`) were added for every page opened in this pass, in the edition read, `retrievedOn` 2026-10-18: the pages of the rows above, the 51 NL/BE/CH/AT clubs, and the 16 ES and FR clubs without a row since PR #106 (Spanish clubs: English and Spanish; French clubs: French and English; their pages were found again by `wikibase_item` and read now, not at the time of #106). A source used by no row is a warning of `check_club_culture.py` by design. **The file now holds 746 rows for 297 clubs: 612 `other`, 110 `local`, 24 `main`; 213 with a blank `rivalQ`; 348 with a blank quote.** **Romania batch, 2026-10-18 (a seventh PR): 25 rows for 9 of the 23 clubs (tiers 1-2: 7 at tier 1, 16 at tier 2) of Romania that had none**, so the file now holds 771 rows for 306 clubs: 626 `other`, 119 `local`, 26 `main`; 223 with a blank `rivalQ`; 348 with a blank quote (the older rows, unchanged). Each row comes from the club's own Romanian Wikipedia article first (written in Romanian) and the English article where the Romanian one states no rivalry by a rivalry word (Metalul Buzău, Cetatea Suceava) or does not exist (Farul), read from the sandbox with the API (User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second, every 429 waited out; no workflow probe, no dispatch); quotes are one contiguous piece of the saved plain text, 15 words at most, checked by the tool before writing. 41 pages were opened (sources `C392`-`C432`, in the edition read; 5 clubs have no Romanian article found by `wikibase_item` or search: CS Dinamo București, CSM Olimpia Satu Mare, FC Bacău, Farul, SCM Râmnicu Vâlcea, whose English articles were read), none failed after four tries. By class: 2 `main` (Argeș's Dinamo București, `principalul rival tradițional`; ASA Târgu Mureș's Universitatea Cluj, `Rivala principala`, written without the diacritic), 9 `local`, 14 `other`. Rows by club: Argeș 4 (Dinamo, Universității Craiova, FCSB for `galeria echipei Steaua București`, CS Mioveni), Corvinul Hunedoara 4 (Jiul Petroșani `Derby al Hunedoarei`; CSM Reșița, Mureșul Deva, Politehnica Timișoara in one `Alte rivalități sunt ...` sentence), ASA Târgu Mureș 2 (Universitatea Cluj, CFR Cluj), Csíkszereda 1 (AFC Odorheiu Secuiesc), Universitatea Craiova 4 (FC U Craiova 1948, Dinamo, FCSB, Pandurii Târgu Jiu), CSM Reșița 3 (Muncitorul Reșița, Gloria Reșița, Politehnica Timișoara), Metalul Buzău 1 (Gloria Buzău), Farul 5 (Rapid and Dinamo `traditional rivals`, and CS Năvodari, Săgeata Năvodari, Delta Tulcea `rivalries against teams from nearby cities`) and Cetatea Suceava 1 (Șoimii Gura Humorului, `local rivals`, in a season account). **`rivalQ`**: filled for 15 rows from the link of the quote's sentence (read in the page's wikitext, the link target resolved with pageprops), blank for 10: the rival is not a map club (CS Mioveni, AFC Odorheiu Secuiesc, Pandurii Târgu Jiu, Muncitorul Reșița, Gloria Reșița, Gloria Buzău, CS Năvodari, Săgeata Năvodari, Delta Tulcea, Șoimii Gura Humorului). **Judgement calls, Alexandru's to overrule:** `principalul rival` and `Rivala principala` are read as `main`, and `rivalii locali`, `una locală` and `rivalries against teams from nearby cities` as `local`, although none is a word of the list literally; two links name a different club from the page's words and the cell follows the link: Argeș's `Universității Craiova` links `FCU Craiova` (`Q584629`, tier 3; the club that claims the old Universitatea's history, so the Craiova row of Craiova's own page, `FC U Craiova`, is the same item) and Reșița's and Corvinul's `Politehnica Timișoara` link `Q4654417`, which the map holds as Știința Poli Timișoara (the page says the rivalry continues against `SSU Politehnica Timișoara`, the fans' team); Argeș's `Steaua București` links `FCSB` (`Q179658`) and the rival there is the club's ultras (`galeria`), as for the fan rows of the older batches. **Three quotes do not name the rival** (the rivalry word and the name are further apart than 15 words): Argeș-Universității Craiova, Craiova-FC U Craiova and Reșița-Politehnica. **Borderline, not written:** Chindia's `rivalitate locală efemeră` with Flacăra Moreni and its 2010-15 rivalry with FCM Târgoviște (both ended; the page says the club `nu are rivalități importante`); Corvinul's `adversitate tradițională față de ... Dinamo și Rapid` (no rivalry word); ASA's `marii rivale Anderlecht` (a play-off in 2009) and `confruntare directa cu Dinamo` (no rivalry word); Csíkszereda's `principalele rivale` (one season); Metalul's cup tie against `local rivals Gloria Buzău` (a match account). **The 14 clubs with none stated** (their pages hold no rivalry word, or no page was found): CS Dinamo București, CSM Olimpia Satu Mare, FC Bacău, SCM Râmnicu Vâlcea, AFC Unirea Slobozia, CS Afumați, CSC Dumbrăvița, Concordia Chiajna, Gloria Bistrița, Metaloglobus, FC Voluntari, Sepsi OSK, CSM Slatina and Chindia. **Fix-ups of 2026-10-18 (an eighth PR; Wikipedia en, nl, fr, de, it, ro answered from the sandbox, User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second, every 429 waited out, no workflow probe, no dispatch).** Only class, `rivalQ` and `rivalName` cells changed; no row was added or deleted, no source row was added, and the file holds 771 rows for 306 clubs: 625 `other`, 119 `local`, 27 `main`; 225 with a blank `rivalQ`; 348 with a blank quote. (1) **Cesena's Bologna row `local` to `main`**: the page says `si accende specialmente nei derby con la principale squadra rivale, il Bologna`, and `principale squadra rivale` is on the `main` list (a derby is the kind of match, the main word is about Cesena's rival). (2) **Winterthur's Grasshopper row `other` to `local`**: `cantonal rivals` is a regional rivalry (the sentence is a coach's move). (3) **Dender's row**: the sentence `son rival de Denderleeuw, tout juste relégué de Division 2` (and the one before, `le club rival de Denderleeuw remporte le titre`) names a club, so the row stays and `rivalName` is now `FC Denderleeuw`, `rivalQ` blank. **It is a judgement, Alexandru's to overrule**: FC Denderleeuw is a predecessor club that merged into Dender in 2005 (matricule 5647 struck off), and an earlier rule kept the rivalries of predecessor clubs out. (4) **Two `rivalQ` cells blanked as identity questions**, rows kept: Argeș's `FCU Craiova` (the page writes `[[FCU Craiova|Universității Craiova]]`; the link target is FCU Craiova `Q584629`, tier 3, the club that claims the old Universitatea's history, while the map's Universitatea Craiova is `Q16838020`) and Reșița's `Știința Poli Timișoara` (the page's sentence is about `FC Politehnica Timișoara`, bankrupt, and `SSU Politehnica Timișoara`, the fans' team; both redirect to `Q4654417`, the map's Știința Poli Timișoara). Their `rivalName` cells were left as they were, so they still carry the map names; Corvinul's Politehnica row (same `Q4654417`) was not part of the instruction and was not changed. (5) **Genk's two `main` rows stay**: `Genk zag zich genoodzaakt Defour te verkopen aan aartsrivaal Standard` and `...tegen aartsrivaal Sint-Truiden VV` call each the arch-rival of Genk (the second sits in a cup-final account). Westerlo-Heultje (`plusieurs derbys contre le KFC Heultje... une forte rivalité`) and Lausanne-Ouchy-Lausanne-Sport (`plusieurs derbies lausannois avec son voisin`) stay `local`. **Not written, borderline**: Telstar-Volendam (both editions: the final-day match against `direct rival Volendam` / `lokale rivaal FC Volendam`, a match account), Seraing (`le voisin et rival du Standard de Liège absorber le club` is about the old RFC Sérésien, matricule 17, absorbed in 1996, not the club of the page), Young Violets-Rapid (`Rivalen SK Rapid Wien` in two cup accounts), La Louvière (`rival borain`, `rival carolo`, match accounts naming regions) and Salzburg (`der Rivale aus Linz`, no club named). **Greece and Serbia batch, 2026-10-18 (a ninth PR): 21 rows for 8 of the 37 clubs (tiers 1-2: Greece 18, Serbia 19) that had none**, so the file now holds 792 rows for 314 clubs: 640 `other`, 121 `local`, 31 `main`; 240 with a blank `rivalQ`; 348 with a blank quote (the older rows, unchanged). Each row comes from the club's own Wikipedia page: English first (37 pages), then, for a club whose English page states no rivalry, the Greek (14 pages) or Serbian (16 pages) edition, found by the English page's language link. **El and sr answered from the sandbox (one 429 on sr, waited out), so no probe job and no dispatch was used**; User-Agent `FootballPlannerBot/1.0`, `maxlag=5`, one request a second; no page failed after four tries. Quotes are one contiguous piece of the saved plain text, 15 words at most, checked in code. Rows by club: Anagennisi Karditsa 3 (Trikala and Ionikos `main` by `main rivals`, AOK `local` by `bitter local rivalry`), Kifisia 5 (Kallithea, Egaleo, Fostiras, Apollon Smyrnis, Proodeftiki, `other`), Kalamata 3 (Paniliakos, Egaleo `other`; Messiniakos `local` by `cross-town rival`), AEL Larissa 2 (PAOK, Olympiacos, `other`, `strong rivalry`), Apollon Kalamarias 2 (Greek page: Π.Α.Ο.Κ. `main` by `μεγαλύτερος αντίπαλος`; Ηρακλή `other`, `μεγάλη αντιπαλότητα` in the 1980s-90s), OFK Beograd 4 (FK Rad `main` by `biggest rivals`; Crvena zvezda and Partizan `other`, `to a much lesser degree`; FK Zemun `other`), Mačva 1 (FK Vojvodina `other`, an interwar `fierce rivalry`), Loznica 1 (FK Proleter Loznica `other`). **`rivalQ`** was filled for 6 rows from a link in the quote's paragraph whose Q-id is a map club (Kallithea `Q1547133`, PAOK `Q204888`, Olympiacos `Q19628`, Crvena zvezda `Q173009`, Partizan `Q188656`, Vojvodina `Q207501`; the `rivalName` is then the map club's name) and is blank for 15: 13 rivals that are not on the map (Trikala, Ionikos, AOK, Egaleo twice, Fostiras, Apollon Smyrnis, Proodeftiki, Paniliakos, Messiniakos, FK Rad, FK Zemun, FK Proleter Loznica), **one `identity?`** (Apollon Kalamarias's Π.Α.Ο.Κ.: the Greek page's link is the multi-sport club `Q3201027`, not the football club `Q204888` the map holds, so the cell stays blank) and one with no link (Ηρακλή, Greek page, plain text). No quote lacks the rival's name. **Judgement calls, Alexandru's to overrule:** `main rivals` is read as `main` (Anagennisi); Kifisia's `main football rivals` has `football` inside the phrase and is read as `other`; `local rivalry` and `cross-town rival` are read as `local`; Mačva's rivalry is historic (interwar) and Kalamata's, Kifisia's and Apollon's `long-standing`/past-decade wording is kept as `other`. **The 29 clubs with none stated** (the English page, and the Greek or Serbian page for all but Asteras Tripolis B, state no rivalry by name): Greece, Olympiacos B, PAOK B, Asteras Tripolis B (no English article; the Greek page of PAOK B and of Asteras B was read), Panserraikos, Panetolikos, Marko, PAS Pyrgos 1968, Niki Volos, Panthrakikos, Volos, Iraklis, Asteras Tripolis, Levadiakos; Serbia, Železničar Pančevo, Voždovac, Proleter 023, Mladost Lučani, Bor 1919, Čukarički, Teleoptik, Javor Ivanjica, Grafičar, IMT, Radnik Surdulica, Vršac, Metalac, Borac Čačak, TSC, Napredak. **Not written, borderline:** Kifisia's `supporters' rivals are Pefki, Maroussi, Colonos, Irakleio, and Elefsina` (names that are towns as much as clubs, no link); Apollon's `ξεκίνησε κόντρα με τη Δόξα Δράμας, και την Αναγέννηση Καρδίτσας` (a feud under the rivalries heading, with no rivalry word); Panthrakikos's `τοπικό ντέρμπι την Ξάνθη` and Voždovac's `од локалног ривала ФК Рад` (each a match account), Bor's `local rivals FK Bor and Metalac` (the first match at a ground), Napredak's `оба вечита ривала` (the league's two eternal rivals, not Napredak's), Mačva's `main rivals Vojvodina` in a 1928 league account (the pair has a row from the other sentence), Iraklis's Greek `See also` links to derby articles (no sentence), and an Asteras Tripolis group-stage mention of `rivals Schalke 04`. 67 source rows `C433`-`C499` were added for every page opened (37 English, 14 Greek, 16 Serbian), the 59 pages without a row included; the PAOK FC page (opened by a search that missed the PAOK B article) is among them and is used by no row, which `check_club_culture.py` reports as a warning by design. **Fix-ups of 2026-10-18 (a tenth PR; Wikipedia en, fr, nl, ro, el read from the sandbox, User-Agent `FootballPlannerBot/1.0`, many 429s waited out, no probe, no dispatch).** Only class and `rivalQ` cells changed, plus one deleted row; no source row was added or removed, and the file now holds 791 rows for 313 clubs: 634 `other`, 121 `local`, 36 `main`; 239 with a blank `rivalQ`; 348 with a blank quote. (1) **Corvinul's Politehnica Timișoara `rivalQ` blanked** (the identity trap of Argeș and Reșița: the page's `[[FC Politehnica Timișoara|Politehnica Timișoara]]` resolves to `Q4654417` (the cell already carried it from the earlier passes; not looked up again, Wikidata lookups were rate-limited), which the map holds as Știința Poli Timișoara); the row and its `rivalName` stay. (2) **One rule for "main rivals" sentences: a sentence that calls clubs the main rivals of THIS club is `main`; a sentence about the supporters' rivals only is not a rivalry of the club.** Anagennisi Karditsa's sentence (`Anagennisi Karditsa's main rivals are Trikala, from the neighbouring city of Trikala, and Ionikos`) is the club's and its two rows were already `main`. Kifisia's (`A.E. Kifisia's main football rivals are smaller Athens football clubs like Kallithea, Egaleo, Fostiras, Apollon Smyrnis, Proodeftiki and more`) is the club's too (the supporters' rivals - Pefki, Maroussi, Colonos, Irakleio, Elefsina - are the next sentence and have no row), so its five rows went `other` to `main`; their 15-word quote is the piece without the words `main football`. Nothing deleted. (3) **Apollon Kalamarias's `Π.Α.Ο.Κ.` row got `rivalQ` `Q204888`**: exactly one club of `GR.json` has the folded name `paok` (PAOK FC; `Q107849577` `P.A.O.K. F.C. B` folds to `paok b`) and the sentence (`Ο Π.Α.Ο.Κ. θεωρείται ο μεγαλύτερος αντίπαλος του Απόλλωνα`, then the 1974 league defeat) is about football; the Greek page's link points at the multi-sport club `Q3201027` (as recorded in the earlier pass; not looked up again), so the cell rests on that rule and not on the link, and `rivalName` was left as written. (4) **Dender's `FC Denderleeuw` row deleted**: both sentences of the French page that call it a rival are season accounts (`le club rival de Denderleeuw remporte le titre dans la même série`, the 1992-93 relegation; `Il croise à nouveau la route de son rival de Denderleeuw, tout juste relégué de Division 2`, the 2004-05 season), and the club is a predecessor that merged into Dender in 2005 (matricule 5647 struck off), so no statement of a rivalry remains; source `C250` is now used by no row (a warning by design). **Rule of 2026-10-18 (an eleventh PR; Wikipedia en, de, nl, fr, ro, es, el, sr read from the sandbox, no probe): a rivalry row whose quote's sentence names three or more clubs as rivals is class `other`; a sentence naming one or two follows the class table.** All 36 `main` rows were checked against their opened pages (the sentence of each quote found with grep -F, none failed): 8 went `main` to `other` (Kifisia's five, whose sentence lists Kallithea, Egaleo, Fostiras, Apollon Smyrnis, Proodeftiki and more, which reverses the one-sentence rule of the tenth PR for those five; Bolton's Manchester United and Oldham, whose sentence names five clubs; Bournemouth's Southampton, whose sentence names Southampton as the biggest rival and four more clubs after it, a judgement by the rule's wording, Alexandru's to overrule). Bolton's Wigan row stays (its own sentence names Wigan only), as do the 27 others; two-club sentences (Mainz, Meppen, Anagennisi) stay `main`. Only class cells changed; 28 `main`, 121 `local` (unchanged), 642 `other`. **Rule of 2026-10-18 (a twelfth PR; Wikipedia en read from the sandbox, User-Agent `FootballPlannerBot/1.0`, no probe) refining the eleventh PR: a sentence that names several clubs together as the main or biggest rivals gives class `other` for each of them; a sentence that singles out ONE club as the biggest or arch-rival gives `main` for that club even if other clubs follow in the same sentence.** The eight rows the eleventh PR changed were re-read against it, each sentence printed from the opened page: Kifisia's five (`A.E. Kifisia's main football rivals are smaller Athens football clubs like Kallithea, Egaleo, Fostiras, Apollon Smyrnis, Proodeftiki and more`) stay `other` (several clubs together); Bolton's Manchester United and Oldham (`Bolton supporters named Manchester United, Blackburn Rovers, Wigan Athletic, Oldham Athletic and Bury as their biggest rivals`) stay `other` (five together); **Bournemouth's Southampton goes back to `main`** (`Bournemouth supporters named their club's near neighbour Southampton as its biggest rival, with Portsmouth, Brighton and Hove Albion, Reading and Leeds United following`: the sentence singles out one club, the others only follow). Only that class cell changed: 29 `main`, 121 `local`, 641 `other`; `check_club_culture.py` exits 0. **German targets batch, 2026-10-19 (Part A of a two-part pass; Wikipedia de read from the sandbox with the API, User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, `maxlag=5`, one request a second, every 429 waited out, no probe, no dispatch).** Targets: the 87 German clubs on the map that had neither an own row nor a mirrored one (by tier 1: 2, tier 3: 6, tier 4: 74, tiers 6 to 8: 5), found by comparing `data/clubs/DE.json` with this file by `clubQ` and by `rivalQ`. Each club's German page was opened (plain text and link list); 16 pages redirect to the parent club (the II sides of Stuttgart, Mönchengladbach, Kaiserslautern, Braunschweig, Hannover 96, Hoffenheim, RB Leipzig, Schalke, Werder, Nürnberg, Augsburg, Ingolstadt, HSV, Fürth, Hertha and Bayern) and were skipped, Bayer 04 Leverkusen II has no German page and its English one states no rivalry; 71 pages were opened and have a source row (4 reused ids, `C23`, `C24`, `C58`, `C59`; 67 new, `C500`-`C566`, `retrievedOn` 2026-10-19). **Source URLs with a non-ASCII character are written percent-encoded**, because the club sheet test compares the link the browser resolves with the cell; the older raw `C57` (Würzburger Kickers) and `C60` (Großaspach) are used by no row and were left unchanged, and new encoded rows were added for the same two pages. 34 rows were added for 19 clubs (825 rows for 332 clubs now: 654 `other`, 132 `local`, 39 `main`; 250 with a blank `rivalQ`; 348 with a blank quote, the older rows, unchanged): 10 `main`, 11 `local`, 13 `other`; 23 with a `rivalQ`, 11 without. The class comes from the wording of the row's quote with the rules of the twelfth PR above (one club singled out as biggest rival or arch-rival is `main`; a sentence naming three or more clubs together gives `other` for each; a sentence of two clubs follows the class table); `rivalQ` comes from the page's own link list (a linked title whose Q-id is a map club and whose name shares a folded word with the rival, the page-level link and not the sentence-level one), else the exact-name rule, else blank. Clubs and rows: Kickers Offenbach 9 (Eintracht Frankfurt `main` by `Der größte Rivale`; Darmstadt, Waldhof Mannheim and the six `lokale Rivalen` of one sentence `other`), Koblenz 4 (Mayen `main` by `Erzfeind`, three `Rivalitäten` `other`), SSV Ulm 2 (Reutlingen and Heidenheim `main`, `größten sportlichen Rivalen`, a two-club sentence), Kickers Emden 2 (Delmenhorst and Oldenburg `main` by `Hauptrivalen`, two clubs), Wiedenbrück 2 (Verl `other`, Rödinghausen `local` by `Ostwestfalenderby`), Hessen Kassel 2 (CSC 03 Kassel `main` by `Erzrivale`, KSV Baunatal `local`), and one row each for Garching, Homburg, Jena (Erfurt `main` by `Erzrivale`), Lok Leipzig (Chemie `local`), Erfurt (Jena `other`, `große Rivalität`), Zwickau (Aue `main` by `größte Rivalität`), Heimstetten, Illertissen (Memmingen `local` by `Derbyrivalität`), Würzburger Kickers, Verl (Gütersloh), Weiche Flensburg, Aue (Dynamo Dresden `main`) and Babelsberg (SV Bornim). **The club item and the map's item differ for Aue and Babelsberg (the Augsburg shape)**: the rows use the map's team items `Q97927365` and `Q97927380` as `clubQ`, and Zwickau's row for Aue uses `Q97927365`, not the club item `Q141882` the page links. **Three quotes do not name the rival** (Offenbach's lists of six local rivals: Hessen Kassel, Mainz 05 and Viktoria Aschaffenburg are named in the part of the sentence beyond 15 words). Borderline cases, **not written**, each with its wording: a match account or one fixture (Eutin `Derbys` with VfB Lübeck, which the page says are of lesser weight for Lübeck; Rödinghausen `Kreisderby gegen den SC Herford`; Jeddeloh and Eichstätt `Derby` of one game; Trier `beim Erzrivalen 1. FC Saarbrücken` on the last matchday; Aue `Erzfeind FSV Zwickau` and `Rivalen` in a cup final; Babelsberg `Erzrivale Energie Cottbus` in a cup tie and `Rivalen Union Berlin` in a defeat; Memmingen `Lokalrivalen SSV Ulm` in a first meeting and `Allgäu-Derby gegen den FC Kempten` as an opening game; Verl `Ostwestfalen-Derby gegen Bielefeld`; Großaspach `Lokalderby bei der TSG Backnang` and `Ligarivalen TSG Balingen`; Havelse `Derby gegen Hannover 96` as an attendance record; Fulda-Lehnerz `Lokalrivalen Borussia Fulda` in a defeat and a merger partner), narratives before 1945 or of clubs that no longer exist (Chemnitz `Lokalrivale Motor West`, Bonner SC's `BFV` and `Tura`, Neumünster `Stadtrivale Olympia`, Plauen `Konkordia` and `Stadtrivalen`, Verl `TV Verl`, Eutin `Ortsrivalen` of 1933, Illertissen `Rivalität bestand mit der SpVgg Au/Iller`), a rivalry with no rivalry word (Ulm `brisant` with Stuttgarter Kickers). **The 19 clubs that gained rows**: Garching, Homburg, Ulm, Jena, Koblenz, Offenbach, Lok Leipzig, Erfurt, Zwickau, Emden, Heimstetten, Wiedenbrück, Illertissen, Würzburger Kickers, Verl, Hessen Kassel, Weiche Flensburg, Aue, Babelsberg. **Clubs with none stated** (their page holds no rivalry word or only the borderline wording above): the others of the 71 pages. `tools/check_club_culture.py` exits 0 and `tools/test_sheet_tickets.js` was run. **German web pass, 2026-10-19 (Part B, a second PR).** Targets: the 64 German clubs on the map that still had neither an own nor a mirrored row after Part A (the 17 reserve sides whose Wikipedia title redirects to the parent club included). **Allowed pages**: the club's own site, regional or national press, fan media; **not allowed**: forums, Reddit, social networks, video sites, ticket resellers, Wikipedia mirrors, AI-generated sites; a page in a language other than German is skipped and reported (the two English pages the searches returned were not opened). **Cap**: at most 3 searches and 3 opened pages per club; 68 WebSearch queries were used (66 for German clubs, 2 for Strasbourg; one or two for each first team, one for each of 9 reserve sides, none for the other 8 reserve sides because the first 9 returned only pages about the parent club). **A page counts only if** it is opened and its plain text holds a sentence that names the club and the rival and states the rivalry by a rivalry word; a match report, a preview that only labels one game `Derby`, and a negation (Neustrelitz: `ist es kein richtiges Derby`) are not statements. **How pages were opened**: WebFetch cannot resolve these hosts from the sandbox, so a temporary probe job in `build-clubs.yml` (the clubs job set to `if: false`, dispatched twice on the branch, removed before the merge) read `robots.txt` of each host first and skipped what it disallows (heidelberg24.de disallows the page found for Sandhausen: skipped), treated a 401, 403 or 429 or a bot challenge as a stop (none occurred) and used no archived copy; User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`. 13 distinct pages were opened in 14 opens, the Hoffenheim page a second time for the quote check (freiepresse.de 7, nordkurier.de 1, schwaebische.de 1, stuttgarter-zeitung.de 2, infranken.de 1, hessenschau.de 1; never more than 3 for one club). **One row added, source kind `press`** (`C567`, the exact URL of the page, retrievedOn 2026-10-19): TSG 1899 Hoffenheim's `VfB Stuttgart` (`local`, `rivalQ` `Q4512`; Schwäbische Zeitung, preview of the match at Stuttgart: `beim Landesrivalen VfB Stuttgart am Samstag`; `Landesrivale` is read as a regional rivalry; the sentence is from a match preview and the row is a judgement, Alexandru's to overrule; the quote was verified by the probe on the opened page). The file now holds 826 rows for 333 clubs (654 `other`, 133 `local`, 39 `main`; 250 with a blank `rivalQ`; 348 with a blank quote). German clubs with neither an own nor a mirrored row: 64 before, 63 after. **Not written, with the reason**: Chemnitzer FC (three Freie Presse pages: the titles say `Derby light` and `Hochrisikospiel`, the text holds no rivalry word for Aue, Zwickau or Leipzig), VFC Plauen and VfB Auerbach (`Vogtlandderby` and `Bezirksderby` label single games in previews), Neustrelitz (`ist es kein richtiges Derby`), Großaspach (`Derby` of one game), Eltersdorf (`Bayernliga-Derby` of one game), Steinbach Haiger (`Derby` of one game), Sandhausen (page disallowed by robots.txt), the stadium-magazine PDFs found for VfB Hüls (not opened), the Volksstimme live-stream page for Halberstadt (a match page). **Strasbourg (RC Strasbourg Alsace, `Q126334`)**: the French (`Racing Club de Strasbourg Alsace`), English and German Wikipedia articles and two searches were read with the class words; every rival they state for the present day already has a row (Metz, Colmar, Mulhouse, Sochaux, Bordeaux), so **no row was added** and no class was changed (the English page calls Metz `main rival`, the Metz row stays `local`). Not written: Red Star Strasbourg (1940-45 derbies), Kehl, Lahr and Offenburg (1909-12) and the FC Neudorf rivalries, all historic. The existing rows with a blank `rivalQ`: SR Colmar (Wikidata `Q1753870`), FC Mulhouse (`Q640726`), Bordeaux (read as FC Girondins de Bordeaux `Q172476`; the row only says `Bordeaux`); none of the three is on the map (the Q-ids come from the French Wikipedia pageprops, not from Wikidata, which the sandbox cannot reach), so a `rivalQ` would point at no club and the cells stay blank. **Statement rule widened, 2026-10-19 (Alexandru's instruction; applies from here on, and to the borderline cases of the earlier batches only where re-read).** A characterizing word (Erzrivale, Erzfeind, Hauptrivale, Rivale, Lokalrivale, Stadtrivale, Derbygegner, Rivalität mit) attached to a named club counts as a statement **even inside a match account, a transfer or coaching sentence or a history paragraph**, if it is present tense or the pairing is described as a standing rivalry. Still not written (listed as borderline): `im Derby gegen X` as the label of one game, the attitude of the OTHER club's fans, antipathy or dislike without a rivalry word, a list of cities naming no club, past tense without a standing rivalry (the table has no status column). Class stays from the quote's wording only: main = arch-rival or biggest rival (Erzrivale, Erzfeind, größter Rivale, Hauptrivale, größte Rivalität; arch-rival, main/biggest/fiercest rival; rival principal, plus grand rival, ennemi juré), one club singled out as biggest rival is main, a sentence naming three or more clubs together gives other for each; local = Derby as a standing name of the pairing, Stadtderby, Lokalrivale, Lokalderby, Derbygegner, Ortsrivale, Ortskonkurrent, Nachbar, Landesrivale, local or cantonal rival, rivalité locale; other = everything else and whenever the wording does not clearly decide (superlatives of intensity are not main). **Part A, 2026-10-19 (a data PR; Wikipedia de, en, fr answered from the sandbox, User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, `maxlag=5`, one request a second, 429s waited out, no probe, no dispatch).** (1) The borderline cases of the German web batch were re-read: **four rows added** (all from the German Wikipedia article of the stating club, quote checked as one contiguous piece of the saved plain text): Eintracht Trier's 1. FC Saarbrücken (`main`, `beim Erzrivalen 1. FC Saarbrücken`, a last-matchday account), Aue's FSV Zwickau (`main`, `schlug Aue den Erzfeind FSV Zwickau`), Babelsberg's Energie Cottbus (`main`, `Der Erzrivale Energie Cottbus gewann mit 2:1.`) and Babelsberg's 1. FC Union Berlin (`other`, `beim Rivalen Union Berlin`, a coaching sentence; `Rivale` without a superlative). **Not written:** Eutin 08 and VfB Lübeck (`Zu erfolgreicheren Zeiten wurde ... den Duellen mit dem VfB Lübeck eine besondere Bedeutung beigemessen`, past tense; the next sentence says the derbies no longer have comparable relevance FOR LÜBECK, the other club's attitude), Illertissen and SpVgg Au/Iller (`Eine besondere Rivalität bestand`, past tense, no standing rivalry), and the pre-1945 narratives (Chemnitz's Motor West, Bonner SC's BFV and Tura, Neumünster's Olympia, Plauen's Konkordia, Verl's TV Verl, Eutin's Ortsrivalen of 1933: past tense, predecessor or defunct clubs). Other borderline cases of the German web batch (Memmingen's `Lokalrivalen SSV Ulm`, Großaspach, Fulda-Lehnerz and others) were not part of this pass. (2) **Würzburger FV, Gütersloh and Bornim were kept**: each sentence holds a characterizing word attached to the named club (`Lokalrivale Würzburger FV`, `Lokalrivalen FC Gütersloh`, `Stadtrivalen SV Bornim`), which is the test applied. Two of the three are past-tense narratives (Verl's 1986-87 season; a mid-1990s Babelsberg season) and FC Gütersloh (1978) no longer exists, so they would fail the `past tense without a standing rivalry` line above: kept by the literal test, Alexandru's to overrule. (3) Hoffenheim's VfB Stuttgart row kept (`beim Landesrivalen VfB Stuttgart am Samstag`, `local`). (4) **Strasbourg (`Q126334`), the one exception to `existing rows keep their class`: the five rows of 2026-10-09 got a quote and the class was re-derived from its wording.** Metz `local` to **`main`** (English page: `Racing Strasbourg's main rival is Metz.`; the row's source is now `C568`, the English article, not `C6`, because the quote is from it), Colmar `local` (`le principal derby se joue à nouveau contre le SR Colmar`; `principal derby` is a derby, not a `rival principal`), Mulhouse `local` (`le « grand derby alsacien »`, a 1936 account, `C6`), Sochaux `other` (`quelques rivalités contre leur voisin du FC Sochaux-Montbéliard`) and Bordeaux `other` (`il existe une rivalité entre ces deux groupes de supporters`, `C7`, the fan groups; the quote does not name the rival). `checkedOn` of those rows is unchanged. The file now holds 830 rows for 334 clubs: 655 `other`, 132 `local`, 43 `main`; 250 with a blank `rivalQ`; 343 with a blank quote. **German first teams, Part B, 2026-10-19 (a second PR; the widened statement rule above applies).** Part 0 (counted before any row): 63 German clubs on the map had neither an own row nor a mirrored one (tier 1: 1; tier 3: 4; tier 4: 54; tiers 6 and 8: 4); **42 first teams and 21 reserve sides** (tier 3: 2 first teams and 2 reserve sides; tier 4: 35 and 19; the rest first teams). Reserve sides are skipped and not searched. **Step 1, the club's own German Wikipedia article, re-read for the 42 first teams** (all 42 pages already had a source row; the two derby articles of step 2 and 17 press pages got new ones, `C569`-`C587`): the one new finding is **Bonner SC**, whose article has a `Fan- und Vereinsrivalitäten` section that earlier passes read as pre-1945 narrative only. **Three rows written** (source `C545`): FV Bonn-Endenich (`local`, `besteht eine besondere Rivalität durch das sogenannte Karnevalsderby`, present tense, Karnevalsderby as the standing name), Siegburger SV 04 (`other`, `Hass sowie die Rivalität beider Vereine verstärkt`; the quote does not name the rival) and FV Bad Honnef (`other`, `zu einem der größten Rivalen der BSC-Anhänger zählt`: one of several, the BSC fans' view; the same paragraph first calls Bad Honnef `ein ehemaliger Rivale`). None of the three clubs is on the map, so `rivalQ` is blank. Not written: Friesdorf (`war ... ein weiterer Rivale`, ended with its insolvency), the predecessor clubs Bonner FV and Tura, SV Beuel 06 (1930s), `Ligarivalen`. **Step 2, derby articles (German `list=backlinks` of each club's article, titles with Derby, Rivalit, Duell, Klassiker or Lokalkampf):** 41 clubs queried (Bonner SC already had rows); three hits, `Ostberliner Stadtderby` (Berliner AK 07) and `Ostderby` (Chemnitzer FC, FC Viktoria 1889 Berlin), opened; no paragraph names a rivalry of the target, **0 rows**. **Step 3, web:** 57 WebSearch queries (1 to 3 per first team, none for the reserve sides; the form `<club> Erzrivale`, `Rivalen Derby`, `Lokalrivale` and two longer ones); WebFetch cannot resolve the newspaper hosts from the sandbox, so 17 candidate pages (Freie Presse 8, Volksstimme 3, Nordkurier 2, Stuttgarter Zeitung 2, Rheinpfalz 1, Die falsche 9 1) were opened by a temporary probe job in `build-clubs.yml` (clubs job set to `if: false`) on a throwaway branch `probe-b` that was **never merged** (this PR's diff has no workflow change); **2 dispatches** (of 8), `robots.txt` of each host read first (all allowed), User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, one request a second, no 403, 429 or bot challenge, no archived copy. Never more than 3 searches or 5 opened pages for one club. The two quotes of the Freie Presse and Rheinpfalz pages rest on the part of the page that is readable without a subscription (the paywall cuts the article after one or two paragraphs). **Three rows written, all `press`:** Chemnitzer FC to FC Erzgebirge Aue (`other`, `C571`, `Die Rivalität der Clubs geht bis in die DDR-Zeit zurück`; the previous sentence calls the match a `Lokalderby` but names the clubs only in the title, so the quote does not name the rival and the class is left at `other`; `rivalQ` `Q97927365`, the map's item for Aue by the exact-name rule, not the club item `Q141882`), VFC Plauen to VfB Auerbach (`local`, `C574`, `Vogtlandderby der Fußball-Oberliga zwischen dem VFC Plauen und dem VfB Auerbach`, read as the standing name of the pairing; written from Plauen's side only, so Auerbach shows it mirrored) and SV Elversberg to 1. FC Saarbrücken (`local`, `C579`, `der Drittliga-Lokalrivale ... Der 1. FC Saarbrücken`, a 2022 match report; Saarderby). All three are judgements, Alexandru's to overrule. **Not written (borderline):** Großaspach (`im Lokalderby bei der TSG Backnang`, `Ligarivalen TSG Balingen`, `Nachbarschaftsduell` with the Kickers: labels of single games), Havelse (`Derby gegen Hannover 96`), Fulda-Lehnerz (`Lokalrivalen und künftigen Fusionspartner Borussia Fulda`, a defeat, the rival has merged into the club), Jeddeloh and Eichstätt (`Derby` of one game), Neustrelitz (`ist es kein richtiges Derby`; `MV-Derby gegen den Torgelower FC Greif`, one game), Halberstadt (`Wernigerode-Halberstadt-Derby`, `Regionalliga-Derby` with Magdeburg: labels of games), Eutin and VfB Lübeck (past tense, the Lübeck side's attitude), Velbert (the post-war rivalry with VfB Velbert, merged in 1964), Chemnitz (`Lokalrivale Motor West`, 1958), Plauen (`Lokalrivale Konkordia Plauen`, 1916-17), Neumünster (`Stadtrivale Olympia`, past), Sandhausen (only match reports found; the Heidelberg24 article was disallowed by `robots.txt` in the earlier batch and was not opened). **The 37 first teams still with neither an own nor a mirrored row:** Viktoria 1889 Berlin, Meuselwitz, Eutin 08, Neugersdorf, Egestorf, Tasmania Berlin, Fulda-Lehnerz, Steinbach Haiger, Vilzing, Seligenporten, Neustrelitz, Bahlinger SC, Jeddeloh, Eichede, Eichstätt, Hüls, Rain, Bergisch Gladbach 09, Havelse, Velbert, Optik Rathenow, Idar-Oberstein, Buchbach, Germania Halberstadt, Goslarer SC, Neumünster, Sandhausen, Bayern Alzenau, Pfullendorf, Lotte, Berliner AK 07, Großaspach, Kray, Rehden, Eltersdorf, Ismaning, Lupo Martini Wolfsburg (plus the 21 reserve sides). The file now holds 836 rows for 338 clubs: 658 `other`, 135 `local`, 43 `main`; 253 with a blank `rivalQ`; 343 with a blank quote (the older rows, unchanged). **Past-tense line, 2026-10-19 (Part A of a three-part pass; Wikipedia de read from the sandbox, User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, no probe, no dispatch): three rows of the widened-rule batch were deleted because their sentence is a past-tense season account that states no standing rivalry**, each sentence printed from the opened page first: Verl's FC Gütersloh (`Erstmals traf der Verein dabei auf den Lokalrivalen FC Gütersloh`, the 1986-87 Oberliga season; FC Gütersloh (1978) no longer exists), Babelsberg's SV Bornim (`hinter dem Stadtrivalen SV Bornim gelandet`, the 1994-95 Verbandsliga table) and Würzburger Kickers' Würzburger FV (`nachdem der in der Bayernliga Nord spielende Lokalrivale Würzburger FV, Nachfolgeverein des 1981 insolventen Würzburger FV 04, die Regionalligaqualifikation seither stets verfehlte`, an account of the 2012 promotion in the past tense; the club still exists, so this one is a judgement, Alexandru's to overrule: re-add the row if he reads `Lokalrivale` as a standing statement). **The line from here on: a characterizing word in a sentence that tells what happened in one season, a merger or a transfer, in the past tense, with no wording that the pairing is a standing rivalry, is not written; this holds for a club that still exists too.** No source row was removed, so `C59` and `C539` are used by no row (a warning of `check_club_culture.py` by design). The file now holds 833 rows for 336 clubs: 658 `other`, 132 `local`, 43 `main`; 250 with a blank `rivalQ`; 343 with a blank quote. Verl and Würzburger Kickers have no own row again. `tools/check_club_culture.py` exits 0. **German first teams, deeper pass, 2026-10-19 (Part B of the three-part pass; the widened statement rule and the past-tense line above apply).** Part 0 (counted before any change): 58 German clubs on the map had neither an own row nor a mirrored one, **37 first teams and 21 reserve sides** (first teams: tier 3 2, tier 4 31, tier 6 3, tier 8 1; reserve sides: tier 3 2, tier 4 19); after Part A's deletions Würzburger Kickers is a 38th target, and the 21 reserve sides were not searched. **B1, derby articles** (German Wikipedia `list=backlinks` with `blnamespace=0`, `bllimit=max` and redirects, titles kept if they contain derby, rivalit, duell, klassiker or lokalkampf case-insensitively or are a `Liste` with derby or rivalit; plus `list=search` for `<club> Derby`, 5 results; Wikipedia answered from the sandbox, `maxlag=5`, one request a second): 38 clubs queried, five articles kept and read (Ostderby for Viktoria Berlin, Frankenderby and Fränkisch-Bayerisches Derby for Würzburger Kickers, Ostberliner Stadtderby for Berliner AK 07, Münchner Stadtderby from the search for Eichstätt); **no paragraph or table row states a rivalry of the target with another club, 0 rows** (Ostderby lists Viktoria in a table of grounds; the Frankenderby article only says that games against other Franconian sides such as the Würzburger Kickers are sometimes called Frankenderby, a label of games; the Ostberliner Stadtderby article names BAK 07 in no rivalry paragraph; the Münchner Stadtderby article does not name Eichstätt). **B2, official websites:** Wikidata `P856` was read through a temporary probe job for all 38 (38 have a site); `robots.txt` of each host first, the home page, then at most 6 links whose text or URL holds Chronik, Geschichte, Historie, Verein, Derby, Rivale, Tradition or Über uns, each grepped for Rivale, Rivalit, Erzrivale, Derby, Lokalrivale, Erzfeind or Feindschaft. **34 sites fetched, 4 not:** Viktoria Berlin (home page HTTP 423), Oberlausitz Neugersdorf (`robots.txt` disallows the home page), Seligenporten (`robots.txt` did not answer, read as a stop) and Lupo Martini Wolfsburg (HTTP 410). 147 pages were opened on the first run and 139 on the last (the news items on a home page change); the two PDFs found (VfB Hüls Ehrenkodex, FC Ismaning) were not read as pages and have no source row. Nine pages held a pattern hit; **one row written:** TSG Neustrelitz's `FC Neubrandenburg` (`main`; the club's own chronicle, present tense, `beim Erzrivalen FC Neubrandenburg` in one season and `beim Erzrivalen FC Tollense Neubrandenburg` in another; both titles redirect to `1. FC Neubrandenburg 04` on German Wikipedia, so they are one club and one row, and it is not on the map, so `rivalQ` is blank; the quote was checked with an exact substring test on the opened page). Not written, with the wording: Velbert (`Lokalrivalen SSV` against the old VfB Velbert, merged in 1964), Würzburger Kickers (`ersten Lokalderby gegen den 1. Würzburger Fußballverein`, 1908), Optik Rathenow (`Irgendwie ist es doch ein Derby` about Lok Stendal, one game), Sandhausen (`Derby gegen den Karlsruher SC` and `VfB Stuttgart II` in season accounts), Großaspach (`Derby gegen die TSG Backnang`, a title decider), Neustrelitz's `MV-Derby` (a game), TSV Rain (`Landkreisderby`, table tennis), Lotte (`Abteilungsrivalitäten` between handball and football). **B3, press and fan media:** 51 WebSearch queries (the forms `<club> Erzrivale`, `Rivalen Derby`, `Lokalrivale Rivalität` and `Rivalität Fans Derby Gegner Verein`; 1 to 2 for each of 37 clubs, never more than 2) returned almost only statistics and fixture pages; 4 press pages were opened (Schwäbische Zeitung 2, Volksstimme 2) through the probe: the Schwäbische Zeitung preview calls Pfullendorf the `Lokalrivalen` of FV Ravensburg, a statement of the other club's side (FV Ravensburg is not on the map), so no row for Pfullendorf; its second article labels a game `Derby`; the Volksstimme pages for Halberstadt are a 2013 cup match and a general text, no statement. Not allowed hosts (forums, social networks, ticket sellers) were not opened. **B4, sources:** 141 rows `C588`-`C728` (137 `club`, 4 `press`, `retrievedOn` 2026-10-19; a club page's title is the page's own `<title>` followed by `(club website)`; non-ASCII URL characters percent-encoded); 140 of them are used by no row, a warning by design, as for every page opened without a row. **Probe:** 6 workflow dispatches (3 probe runs, 2 failed at once because Wikidata answered `maxlag` and the site list was then fixed in the job, 1 for the page titles), removed before the merge; this PR's diff has no workflow change. The file now holds 834 rows for 337 clubs: 658 `other`, 132 `local`, 44 `main`; 251 with a blank `rivalQ`; 343 with a blank quote. **The 37 first teams still with neither an own nor a mirrored row:** Viktoria 1889 Berlin, Meuselwitz, Eutin 08, Oberlausitz Neugersdorf, Germania Egestorf, Tasmania Berlin, Fulda-Lehnerz, Steinbach Haiger, Vilzing, Seligenporten, Bahlinger SC, Jeddeloh, Eichede, Eichstätt, Hüls, Rain, Bergisch Gladbach 09, Würzburger Kickers, Havelse, Velbert, Optik Rathenow, Idar-Oberstein, Buchbach, Germania Halberstadt, Goslarer SC, VfR Neumünster, Sandhausen, Bayern Alzenau, Pfullendorf, Lotte, Berliner AK 07, Großaspach, Kray, Rehden, Eltersdorf, Ismaning, Lupo Martini Wolfsburg (plus the 21 reserve sides). `tools/check_club_culture.py` exits 0. **Reserve sides, 2026-10-19 (Part C of the same pass; data, checker and page).** `data/club-parents.csv` (file entry above) names the first team of 19 reserve sides on the map, each proved by a Wikipedia redirect. **The club sheet's Rivalries section now shows, for a club with a row there, "Reserve side of <parent>. Its rivals are listed on the first team's sheet." (`riv.parent`, ro unchecked), with the parent tappable like any rival: instead of the "No rivalry recorded for this club yet." line when the reserve side has no own or mirrored row, and under its rows when it has some. A club with no row in the file is unchanged.** Nothing is inferred from the names. Of the 21 reserve sides without an own or mirrored row (Part 0 above), 16 now show the sentence; the other five (1. FC Köln II, 1. FSV Mainz 05 II, Bayer 04 Leverkusen II, VfL Wolfsburg II, Borussia Dortmund II) have an article of their own and keep the neutral line. `tools/test_sheet_tickets.js` (157 checks) works out every expected sentence from the file, taps the parent, injects an own row and a mirrored row onto reserve sides, and runs in English and Romanian; `SHELL_VERSION` is `v38`. **Würzburg, 2026-10-19 (a data PR, Part D1; Wikipedia de answered from the sandbox, no probe, no dispatch): no row written.** The German articles of Würzburger Kickers and of Würzburger FV were read for Derby, Rivale, Rivalit, Stadtderby, Lokal and Würzburger FV. The Kickers article has the 2012 promotion sentence with `Lokalrivale Würzburger FV` (the one deleted on 2026-10-19 as a past-tense season account) and the `Frankenderby` as a label of games, and no sentence that states a standing rivalry with the FV; the FV article names the Kickers only as the club that took its place in the Regionalliga, in the past tense. The Kickers' and the FV's own history pages could not be opened from the sandbox and no probe was spent on them (search summaries showed chronicle text only), so the pair stays without a row, Alexandru's to overrule if he reads the 2012 sentence as a standing statement. **Würzburger Kickers to Würzburger FV restored, 2026-10-19 (a data PR, on Alexandru's instruction; German Wikipedia read from the sandbox, one request, a 429 waited out).** The row deleted by the past-tense line is back, unchanged (`local`, `rivalQ` blank, source `C539`, `checkedOn` 2026-10-19, quote `Lokalrivale Würzburger FV, Nachfolgeverein des 1981 insolventen Würzburger FV 04`, which `grep -F` finds once in the saved plain text of the Kickers' article, in the sentence about the 2012 promotion). The reason is the widened statement rule: `Lokalrivale` attached to a named club counts as a statement in a season account exactly as `Erzrivalen` does for Trier to Saarbrücken, so the **past-tense line above no longer applies to this row**; the FV side was not written (a club gets its row only from its own page). Verl's Gütersloh and Babelsberg's Bornim stay deleted. The file now holds 835 rows for 338 clubs (658 `other`, 133 `local`, 44 `main`).
- `data/club-friendships.csv` — added 2026-10-09. **Fan friendships between a club and another, hand-written, never written by a script or job.** Filled on 2026-10-10 for the German tier-1 clubs (70 rows; 18 clubs' pages opened, one page per club). Filled on 2026-10-16 for the German tier 2 and tier 3 clubs (62 rows from 36 German Wikipedia pages, sources `C27`-`C62`; VfB Stuttgart II and TSG 1899 Hoffenheim II are redirects to a section of their parent club's page and have no page of their own). `clubQ,friendQ,friendName,scope,status,groupsText,sourceId,checkedOn,quote`; `friendQ` is blank when the friend is not on the map; `scope` is `fan-groups`, `clubs` or `unclear`; `status` is `active`, `ended` or `unclear`; `groupsText` holds the fan groups the source names and is blank if it names none; sources are rows of `club-culture-sources.csv`. **The scope and the status come only from the wording of the source** ("fan groups are friends" is `fan-groups`, "the clubs are friends" is `clubs`, a source that says neither is `unclear`). **Nothing is inferred from rivalries, shared enemies or the same side of a derby, and no row exists without an opened source** (a search-result summary is not an opened page; a source that could not be opened means no row). Shown on the club sheet as **Fan friendships**, directly below Rivalries: active, then not clear, then ended, alphabetical within each; the first 5 rows, the rest behind "Show all (n)"; the note "As stated by the cited source. Fan friendships change and can end."; a friend on the map opens its sheet; a club with no rows shows no section. **Every friendship row needs a source quote** (since 2026-10-10): `quote` is the source's own words behind the status, in the original language, 15 words at most, one contiguous piece of the opened page; the club sheet shows it under the row as "Source says: «…»" (the quote marked `data-content`, never translated; the label is `fri.quote` in `I18N`, the Romanian unchecked by the user). **A friendship status of `active` needs present-tense wording** in the source; `ended` needs wording that says so ("beendet", "in die Brüche", "kündigten auf", "bis 19xx", "nicht länger gepflegt", or a closed period that the page contrasts with now); past tense with no end stated stays `unclear`. **A row exists only if that club's own page uses a friendship word** (Freundschaft, freundschaftlich, amitié, prietenie, înfrățire); "Kontakte", "Verbindungen", "Verbundenheit", a cooperation or a partnership match are not enough, and seven rows resting on them were removed on 2026-10-10 (Union–St. Pauli and Union–Gladbach "Verbundenheiten", Dortmund–Aris, –Brøndby and –Burghausen "enge Verbindungen", HSV–Rangers "gute Kontakte" and "Vereinskooperation", and Rapid–Poli, whose Rapid page says nothing). A row for each side only when that side's page was opened and states it; `friendQ` only on an exact name match in `data/clubs/*.json`, or from the cited source page's own link (the page's links in its own language, resolved id to id with `prop=pageprops`, `redirects=1`) to a Q-id that is in `data/clubs/*.json`, **and** either (a) every folded word of the row's `friendName` is among the folded words of the map club's name, or the reverse (a dotted initialism such as "F.C." counts as one word, as in the fixture matcher), or (b) the link sits inside the sentence of the row's `quote`, is the only link in that sentence whose Q-id is a map club, and its link text shares a word with `friendName` (without that last check, a sentence that lists several friends would give a row the one friend that happens to be on the map: Bayern's "Bordeaux" would have become VfL Bochum). A name that resolves to two Q-ids, a club item where the map holds a different item for the same club (the Augsburg shape), or a sentence with more than one map club leaves the cell blank, and so does a friendship whose pair is also in `club-rivalries.csv` while it is not ended. `rivalQ` in `club-rivalries.csv` follows the same rule, with the sentence that names the rival in place of the quote. On 2026-10-17 six blank `friendQ` cells were filled this way (five by (a), Hertha BSC's Racing Straßburg by (b)); 26 stay blank after the four of the same day below, 4 `rivalQ` cells stay blank. **Four more `friendQ` cells were filled on 2026-10-17 (Frankfurt's Atalanta Bergamo, KSC's Racing Straßburg, Kaiserslautern's US Palermo and Hellas Verona)** from the cited page's own link in the quote's sentence, on three checks: the link text shares a folded word with `friendName`, the Q-id's label shares one, and the Q-id is in `data/clubs/*.json`; Wikidata was unreachable from the sandbox that day (403), so the labels were the pages' sitelink titles. The friendships file holds 133 rows (96 active, 24 not clear, 13 ended). **A pair of clubs cannot be in both this file and `club-rivalries.csv` unless the friendship has ended**: the checker exits 1. **One-sided rows also show on the friend's sheet (since 2026-10-15, drawn by the page only; no file or checker changed).** For a row A to B with a non-blank `friendQ`, if B has no row of its own with `friendQ` = A, B's sheet also shows that row mirrored: the friend shown is A (its name from the club files, tappable to A's sheet), with scope, status, groups and quote exactly as A's row states them, and the label "Stated on <A>'s page only" under the row (`fri.mirror` in `I18N`, the Romanian unchecked by the user). If B has its own row for A, B shows only its own and nothing is mirrored; a row with a blank `friendQ` is never mirrored, and a mirror needs A on the map. Mirrored rows sort and group like own rows, count in the first 5 and "Show all (n)", and a club whose only rows are mirrored gets the section. Mirroring is not inference: it repeats only what A's opened page says, and it says on the sheet whose page said it. Rivalries and Fan friendships are keyed by Wikidata id only, so they show for any club in any country (the page has no country condition on them; the earlier German-only scope was the research scope, not code). `tools/check_club_culture.py` reads it: exits 1 on an unknown `clubQ`, `friendQ` or `sourceId`, a scope or status outside its list, a duplicate row, a club that is its own friend, a quote of more than 15 words, a pair that is also in `club-rivalries.csv` while the friendship is not `ended`, or a future day-level date in a text cell; warns on a missing `checkedOn` and on a friendship row with no quote. Tested by `tools/test_sheet_tickets.js` (since 2026-10-15 also the mirrored rows, from the real file and from injected rows): temporary rows injected for order, labels, quotes and "Show all", every real row's quote on its sheet, and a scratch copy of the data run through the checker. **Re-read of the German tier 1-3 pages, 2026-10-19 (a data PR; Wikipedia de answered from the sandbox, User-Agent `FootballPlannerBot/1.0 (https://github.com/AlexGrozavul/Football)`, one request a second, 429s waited out, no probe, no dispatch): 23 rows added for pairs earlier left out.** The German page of each of the 54 clubs of tiers 1-3 with an article of its own (VfB Stuttgart II and TSG Hoffenheim II redirect to the parent) was fetched as plain text and searched for freund, befreundet, friendship, Allianz, Bündnis, verbündet, Brüderschaft and Bruderschaft; a row was written only where the club's own page uses one of those words about another club or its fans, the quote is one contiguous piece checked as a substring of the saved text, and the stating club had no row for that friend. Rows: Duisburg to Mainz (`fan-groups`, `active`, `Kohorte Duisburg`; the page writes `Ultraszene Mainz` with no link, so `friendQ` is blank), Dresden to Wismut Gera, GKS Katowice and FK Sarajevo (`unclear`, `ended`: the page says the friendly contacts `bestehen hingegen nicht mehr`, outside the quote; the Sarajevo quote does not name it), Bochum to Münster and BFC Dynamo, Braunschweig to Basel and Waldhof (`fan-groups`, `active`), Waldhof to Basel and Worms (`unclear`, `active`: `Kontakte` between clubs), Münster to Heracles Almelo, Pescara, Bordeaux, Charleroi and CKS Czeladź (`fan-groups`, `active`, `Münsteraner Ultragruppen`; Charleroi stays blank because the sentence has two map clubs and the map's name is `Royal Charleroi SC`), Hannover to Bielefeld (`fan-groups`) and to AIK Solna, Heerenveen, Perth Glory, Odense, St Patrick's Athletic and Sporting Lissabon (`unclear`, `active`: the sentence gives them a `zu` of their own), and HSV to Hannover (`clubs`, `unclear`: the page says the three clubs `bildeten die Nordallianz`, past tense; each club of the alliance now has a row for each partner). `friendQ` follows the page link of the sentence where it is a map club and the folded names are equal. **Not written, with the page's wording:** Mainz's Iraklis Thessaloniki, Winterthur and Casertana (`Weitere Verbindungen bestehen`), Heidenheim's Ahlen (`Kontakte gibt es`) and Ingolstadt and VfR Mannheim (`gab es außerdem Verbindungen`), Meppen's Club Brugge (`Kontakte zwischen Fans`), Kaiserslautern's Wattenscheid (`kurzzeitige Verbindung`), Waldhof's Magdeburg (`einzelne Kontakte`), Darmstadt's Hanau and Beşiktaş (`Kontakte`), none with a friendship word; Magdeburg's Braunschweig (`Eine offizielle Fanfreundschaft ... gibt es aber nicht`, a negation); Gladbach's Israeli FA (`Freundschaft`, not a club); Hertha's Union (`besteht heute kaum noch`, not `ended` by wording, and the pair is in `club-rivalries.csv`) and Frankfurt's FSV Frankfurt (`eher freundschaftliches, harmonisches Verhältnis`, not ended, pair in `club-rivalries.csv`). Union's row for Hertha was already there. No source row was added: every page was already a row of `club-culture-sources.csv`. **Duisburg's Mainz row got `friendQ` `Q105254` on 2026-10-19**: the exact-name rule (legal-form words and founding years set aside, same country) finds `Mainz` equal to exactly one German map club, `1. FSV Mainz 05`; `1. FSV Mainz 05 II` is excluded by its reserve marker. Mainz's own row for Duisburg was already there, so nothing is mirrored.
- `data/club-parents.csv` — added 2026-10-19. **Which club on the map is the first team of a reserve side on the map, hand-written, never written by a script or job.** `clubQ` (the reserve side), `parentQ` (the club it belongs to), `source` (the URL of the reserve side's Wikipedia page, written as `index.php?title=...&redirect=no`, whose redirect to the parent's article proves it) and `checkedOn`. **A row exists only where both hold:** the club's German, English or local-language Wikipedia article is a redirect (`redirects=1`) to the article of another club on the map, **and** the club's name equals that club's name plus a reserve marker (II, III, U23, Jong and the like). Anything else is reported and not written: a reserve side with its own article (1. FC Köln II, 1. FSV Mainz 05 II, VfL Wolfsburg II, Borussia Dortmund II, Bayer 04 Leverkusen II, Jong FC Utrecht, Știința Poli Timișoara II), a redirect that lands on the reserve side's own article under another title (Real Sociedad B), and a name that is not the parent's name plus a marker (Jong Genk, whose English article redirects to KRC Genk, Club NXT, RSCA Futures, Jong AZ, Jong Ajax, Jong PSV, Olympiacos B, PAOK B, Asteras Tripolis B, Young Violets Austria Wien, FC Liefering, RC Celta Fortuna). **Read 2026-10-19 from the sandbox with the Wikipedia API (`maxlag=5`, one request a second): 19 rows**, Germany 16 (the German article of VfB Stuttgart II, Borussia Mönchengladbach II, 1. FC Kaiserslautern II, Eintracht Braunschweig II, Hannover 96 II, TSG 1899 Hoffenheim II, RB Leipzig II, FC Schalke 04 II, Werder Bremen II, 1. FC Nürnberg II, FC Augsburg II, FC Ingolstadt 04 II, Hamburger SV II, SpVgg Greuther Fürth II, Hertha BSC II and FC Bayern München II is a redirect to the parent's page), Austria 2 (SK Rapid Wien II and SK Sturm Graz II, English article) and Belgium 1 (Jong KAA Gent, English and French article). **FC Augsburg II's parent is the map's team item `Q97905916`** (the Augsburg shape: the article the redirect lands on is the club item `Q15755`, found equal by name). Read by the Rivalries section of the club sheet and by `tools/check_club_culture.py`, which exits 1 on a `clubQ` or `parentQ` on no club file, a repeated `clubQ`, a club that is its own parent and a parent that is itself a reserve side, and warns on a missing source or `checkedOn`. **A line is an identity claim** (this club is the second team of that one), like a `fixture-links-manual.csv` row, and Alexandru's to overrule. **Second rule, 2026-10-19 (Part D2): a reserve side with an article of its own is a row when the article's opening paragraph states that it is the second or reserve team of a club that is on the map, and the club's name is that club's name plus a marker or the first sentence names the parent.** The source is the article's own URL (not `redirect=no`), the opening sentence was printed and read first. **18 rows added** (the file holds 37): Germany 5 (1. FC Köln II, 1. FSV Mainz 05 II, VfL Wolfsburg II, Borussia Dortmund II and Bayer 04 Leverkusen II, the last from the English article, the German page has none), Netherlands 4 (Jong FC Utrecht, Jong AZ, Jong Ajax, Jong PSV, English), Belgium 3 (Jong Genk from the Dutch article `de beloftenploeg van KRC Genk`, Club NXT and RSCA Futures from the English: `youth academy of Club Brugge/Anderlecht ... acts as ... reserve team`), Spain 2 (Real Sociedad B, RC Celta Fortuna: `it is the reserve team of Celta Vigo`, English), Romania 2 (Știința Poli Timișoara II and FC Rapid II București, Romanian: `echipa a doua`), Greece 1 (Olympiacos B, English) and Austria 1 (Young Violets Austria Wien, German: `die zweite Mannschaft des ... Bundesligisten FK Austria Wien`). The five German first-team-article sides above, listed earlier as keeping the neutral line, now show the reserve-side sentence. **Judgement calls, Alexandru's to overrule:** Club NXT and RSCA Futures (the pages call them the academy that acts as the reserve team, and their names are not the parent's name plus a marker), Jong Genk (the name is the parent's `Genk` plus Jong, the Dutch article states it, the English title redirects) and Celta Fortuna. **Not written:** PAOK B (no article in the English or Greek edition, so no opening paragraph to read), Asteras Tripolis B (no English article; the Greek title `Αστέρας Τρίπολης Β` returns the parent club's own opening paragraph, which states nothing about a reserve side) and FC Liefering (its English article says in the third sentence `Since 2012, Liefering has been a reserve team for Austrian Bundesliga side Red Bull Salzburg`, but the first sentence does not name the parent and the name is not the parent's plus a marker, so it fails the rule as written; the German article has no such sentence in the opening lines read; whether the rule should widen to a later sentence is Alexandru's call). The older 19 rows keep their `redirect=no` source URLs unchanged. **FC Liefering added, 2026-10-19, on Alexandru's instruction (the file holds 38):** `Q1387293` to FC Red Bull Salzburg `Q994811`, source the English article. The opening paragraph, read that day, ends `Since 2012, Liefering has been a reserve team for Austrian Bundesliga side Red Bull Salzburg.` (its third sentence; the first does not name the parent), so the rule above, which asked for the first sentence, was read as the opening paragraph for this row. A judgement, Alexandru's to overrule.
- `data/attended.json` — added 2026-10-09. **The matches and events Alexandru attended**, moved unchanged from the old Meciuri app's `data.js` (`matches`: 23, `events`: 3; every entry deep-equal to the original, ids and order unchanged; nothing added, corrected or completed). **Since 2026-10-13 each event carries one `note` instead of `what` and `why`** (a deliberate exception to "moved unchanged": per language, `note` is the old `what`, a blank line, then the old `why`, word for word; the same `{ro, en}` shape; nothing else in the file changed). **Hand-written; no script ever writes to it.** **Its factual notes (`note` on a match or an event) were written by an assistant from memory and are unverified**; they are shown on the detail sheet with the label "Written by an assistant from memory, not yet verified", and a verification pass is what would change that. Read by the Me tab's first three sub-tabs, loaded only when one of them is opened. **Since 2026-10-12 a match may carry `kickoff` (the local time at the ground, HH:MM, written only where an opened source states it as local or names its time zone, never inferred) and `kickoffSource` (that page's URL, or `user-supplied` for a time Alexandru gives); 19 of the 23 have one (five of them `user-supplied` on 2026-10-13: FCB–PSG, Hoffenheim–FCSB, Dumbrăvița–Vâlcea, Poli–ASA, VfB–Heidenheim), a match without one shows no kick-off, events have none, and an imported match may carry `kickoff` in the same format with no source.** **`data/attended.json` is never written by the page** (imported matches are device-only, under `football-attended-imported`; see Conventions, "Imported matches, supporter choices and media"). **Device-only items are never committed**: the old app kept the personal notes, supported team, ticket, seat, block and companions in the phone's `localStorage` (`mf_personal`), photos and videos in IndexedDB (`mf_media`, store `items`) and imported matches in `mf_imported`; none of that is in this repo, none is read by this site yet, and none may ever be committed.

### Generated — safe to overwrite

- `calendars/*.ics`, `calendars/skipped.md`, `calendars/.stamps.json`
- `data/fixtures/*.json` — football-data.org, one file per competition
- `data/fixtures/openligadb-*.json` — OpenLigaDB, one file per
  competition, and `openligadb-index.json` beside them. Kept apart from
  `index.json` because `fetch_fixtures.py` rewrites that one whole
- `data/clubs/*.json` — Wikidata plus manual corrections
- `data/clubs/unmapped-leagues.csv` — seed list for `league-tiers.csv`
- `data/clubs/capacity-review.csv` — disagreements for Alexandru to judge
- `data/clubs/coordinate-review.csv` — proposed coordinates for clubs
  Wikidata cannot place, for Alexandru to judge
- `data/clubs/country-review.csv` — clubs that may be in the wrong
  country's file, for Alexandru to judge. Reported, never removed
- `data/clubs/stadiumdb-review.csv` — a **third** capacity opinion,
  beside Wikidata and OpenStreetMap. Disagreements only, with every
  figure and every source on the row. It picks no winner
- `data/clubs/fixture-links.json` — which football-data.org and
  OpenLigaDB team each map club is, and which fixture files hold its
  matches. What the club sheet reads. A club not in it has no
  confident link and its sheet says fixtures are unavailable
- `data/clubs/fixture-link-review.csv` — everything the fixture
  matcher would not decide: ambiguous teams and clubs, teams with no
  country, cross-country name clashes, venue disagreements and German
  fixture teams with no club on the map
- `data/clubs/proposal-<CC>.csv` and `data/clubs/proposal-<CC>.md` — added
  2026-10-21 by `tools/propose_country.py` / `propose-country.yml`, once per
  country the day it is being added. **Evidence for the decisions of adding a
  country, never a decision**: one row per piece of evidence
  (`kind,tier,clubQid,label,evidenceUrl,evidenceText,detail`) and the read-back
  with the printed wiring patch. Written only by that run; a run that failed
  writes neither (a proposal is not partial). Not read by any other tool.
- `data/clubs/roster-review.csv` — one row per club per division, with
  a verdict saying whether the club is on the map, and if not, **which
  kind of missing** it is

### Code

- `index.html` — the whole app. Single file, no framework, Leaflet from
  a copy in `vendor/` (from the unpkg CDN until 2026-10-02), four tabs: map, bucket list, ticket info and,
  since 2026-10-04, **Me** (memberships and tickets held, kept on the device only - Conventions, "The Me tab"; since 2026-10-09 its first three sub-tabs show the attended matches and events from `data/attended.json` and the held tickets are the fourth - Conventions, "The Me tab's attended matches and events").
  **Since 2026-10-04 the Ticket info tab holds rules only and the dated
  reminders are the Bucket list tab's** (Conventions, "Ticket info and
  the Bucket list"). **Since the same day the Bucket list tab has two
  sub-tabs, List and Calendar**, a star on every entry, a sort
  (Earliest, Favorites) and a bottom sheet for an item tapped in the
  calendar (Conventions, "The Bucket list: List, Calendar, favorites"). Tapping a club opens
  the **club detail sheet** (built 2026-09-25), a pull-up panel that
  replaced the map popup: ground, capacity, competition by name,
  distance, fixtures and ticket info, each saying "unavailable" with a
  reason rather than being hidden. Since 2026-10-02 the map tab also has
  a **route panel** (the Route chip): a start and an end - typed, tapped
  on the map, or home - one Stadia Maps road route drawn on the map, and
  every club within an adjustable distance of it (default 25 km) listed
  in route order, each tappable to its sheet, with an optional "home
  match on" date filter. See the Conventions entry on routes.
  Since 2026-10-03 a route can be **saved on the device** - named,
  renamed, deleted, exported and imported as a JSON file, reopened with
  no Stadia request, refreshed for one, reversed as an approximate route
  back - place searches are kept on the device for 7 days, and the panel
  shows an estimate of this month's route and search credits. **None of
  it is ever in the repo.** See the Conventions entry "Saved routes".
  Since 2026-10-03 a **Derbies** chip beside it opened the **derbies
  panel**: every derby in `data/derbies.csv` with both clubs on the map,
  within an adjustable distance of home (default 100 km), nearest
  first; tapping one shows both clubs, opens either sheet, and the next
  meeting from the fixture files. See the Conventions entry on derbies.
  **Later the same day the Derbies chip became a "Near me" chip**, on
  Alexandru's instruction: it opens the same panel with two tabs, **Clubs**
  (shown first) and **Derbies** (the derbies panel exactly as before). The
  Clubs tab lists every club on the map within an adjustable distance
  (default 100 km, 10-500) of home - or, on request, of where the phone is
  - nearest first, with tier chips; tapping a club does what choosing a
  search suggestion does. See the Conventions entry "Clubs near me".
  Since 2026-10-03 the map tab also has a **club search** (top right:
  matches as you type, ignoring case and accents, and flies to the club
  and opens its sheet), a **coverage panel** (tap the club-count chip:
  clubs and leagues in total, per tier, and by country and league), and
  the sheet's ticket section shows **two labelled sources**, "Your notes"
  from `football-rules.json` and "Researched rules" from the club-tickets
  files, with a **Next window** line. See the Conventions entries on
  each. The zoom rule changed the same day: every club is drawn from z9
  (Conventions, "Tier zoom bands").
  Since 2026-10-03 the tier **legend**, bottom left, is a collapsible
  tab: closed it shows only "Leagues shown" and an arrow, open it shows
  the same tier rows and shared-ground row as before. Whether it is open
  is remembered **on the device only**. See the Conventions entry "The
  legend tab".
  Also since 2026-10-03 (Conventions, "Phone layout and plain words"):
  the club's Wikidata link is a **Details** line at the foot of the
  sheet, and the Fixtures and Ticket info sections say why something is
  missing in plain words, with the file-level reason under a collapsed
  **Why?** (or **Source**) line.
- `manifest.webmanifest`, `sw.js`, `icons/`, `vendor/leaflet-1.9.4/` —
  the **installable app** (built 2026-10-02): the manifest Chrome reads
  to offer "Install app", the service worker that lets the installed app
  open offline, an original icon (a map pin with a ball; drawn by
  `icons/draw-icon.js`, no crest or third-party mark), and Leaflet
  1.9.4 copied byte for byte from npm with its BSD-2 licence. See the
  Conventions entry "The installable app".
- `tools/test_pwa.js` — headless Chromium test of the installable app
  at phone width: Chrome's own installability errors, a second load
  offline, fresh data after a data change, a new deploy replacing the
  shell, and since 2026-10-03 refused tiles raising the map card. Run
  by `test-pages.yml` (below) on every change to the page; by hand
  with the instructions at its top.
- `tools/check_derbies.py` — read-back and checks for `data/derbies.csv`,
  in the style of `check_tickets.py`: prints every row as understood,
  rejects by line (no source, not a Q-id, a Q-id on no map without
  `offMap`, a pair entered twice, an unquoted comma), reports and keeps
  the rest (an unknown `kind`, a stale `offMap`, a derby in which neither
  club is tier 1-2, a pair in different divisions, a club with no
  fixture source), cross-checks `football-rules.json` through `rulesId`,
  and prints the per-country counts. Exits 1 on a rejected row. Run by
  `check-derbies.yml` on a push to `main` touching the file, the club
  layer or the tool, and on a pull request touching the file.
- `tools/test_derbies.js` — headless Chromium test of the derbies panel
  at 390x844 (reached since 2026-10-03 through the Near me chip and its
  Derbies tab): the default 100 km list, nearest first, every row in the
  file accounted for, the slider, every derby's detail giving one of the
  four honest answers, a sheet opening above the panel, no sideways
  scroll, no script error. Run by `test-pages.yml` since 2026-10-03.
- `tools/test_nearme.js` — added 2026-10-03: the Near me panel. Both
  tabs; the Clubs list checked against the club files themselves (the
  test works out which clubs are within the distance, at 100 and 500 km,
  without asking the page), nearest first, each row's competition, ground
  and road estimate; the slider, every tier chip, "Show more" and the
  empty messages; no club without a position, and every listed club drawn
  at z9; a tapped row closing the panel, flying to the club and opening
  its own sheet, for both clubs at the Grünwalder; "Use my location"
  granted (Playwright's mocked position in Bucharest gives Romanian clubs
  only), denied, timed out, unavailable and unsupported; the position in
  no storage, cookie, URL or request and gone after a reload; the panel
  opened before every club file has loaded; and the top row (club count,
  search box and its placeholder, home, Route, Near me) at 390x700 and
  390x500 at zooms 3, 8, 9, 10 and 13 - no overlap, nothing cut off or
  off screen. It prints how long the list takes at 500 km with the CPU
  slowed 4x. Run by `test-pages.yml`.
- `tools/test_routes.js` — headless Chromium test of the route panel and
  its saved routes at 390x844, added 2026-10-03, every Stadia request
  stubbed and counted: search, route, the 7-day search cache (and its
  expiry), save (and what a save keeps and does not), reload, open with
  no request, rename, route back, refresh, the credit estimate, opening
  a saved route offline, export, delete, import (good, repeated, broken
  and foreign files), a second tab seeing the same routes.
- `tools/test_zoom.js` — added 2026-10-03: **fails, naming each club, if
  any club inside the visible bounds plus 50% padding is not drawn at z9**
  (since 2026-10-19; before that, any club on the map), the tier-3
  threshold, **if a ground outside that padding is drawn, and if a far
  club is not drawn after the map flew to it from a search suggestion**
  (expected sets worked out from the club files and the live map's bounds,
  and the chip must still count every club and shared ground); also
  that tiers 1 and 2 keep z0 and z7, that `minZoom` is 3 and `zoomDelta`
  and `zoomSnap` are 1 (read from the live map, and the + button moves
  exactly one level), that every `data/clubs/??.json` is in
  `COUNTRY_FILES`, and that every club in those files with a position
  and a tier is on the map. It then **measures, and does not judge**, the
  redraw at z7, z8 and z9 over the Ruhr, northern Italy and Bucharest with
  the CPU slowed 4x, beside the old draw-everything behaviour, and prints
  the numbers.
- `tools/test_search.js` — added 2026-10-03: the club search at 390x844
  with the keyboard stood in for by shrinking the window to 390x500 (see
  its Conventions entry for what that does and does not cover).
- `tools/test_coverage.js` — added 2026-10-03: the coverage panel,
  checked against counts the test makes from the club files itself.
- `tools/test_sheet_tickets.js` — added 2026-10-03 (since 2026-10-17 also the rivalry quote: an injected row with a quote shows "Source says: «…»" in the `data-content` element, one without shows none, every real row with a quote shows it, and a 16-word rivalry quote makes a scratch copy fail the checker; extended 2026-10-09 with the Rivalries order and "Show all"; the atmosphere assertions were replaced on 2026-10-10 by checks that the section is gone from a club that used to have it, with Rivalries and Fan friendships still showing): the sheet's ticket
  section for VfB, KSC, Kaiserslautern, Kickers, Poli, UTA, Bayern,
  Nürnberg and Inter, checked against the files: each source shown
  exactly when it exists and labelled, every text field of a notes entry
  on the sheet as written, the Next window line naming only that club's
  own entries, never a disputed one, always labelled, and never an
  estimate to the day.
  **Since 2026-10-16 it prints one `TIME <section>: n s` line per section and a total** (about 42 s locally; it had grown to 31 min in CI because `click('.frmore')` waited Playwright's 30 s default for every club with 5 rows or fewer, which has no "Show all" button - it now clicks only when the button exists). A slow section shows in the log; keep any click on an optional element guarded.
- **All sheets and panels share one expand-to-full mechanism (`sheetDrag()` in `index.html`, 2026-10-11): drag the handle or title row up for full size, tap the handle to toggle, a sheet reopens at half. New sheets must use it (any `.sheet` is wired at boot); `tools/test_layout.js` section 7 finds every `.sheet` and fails one with no trigger.**
- `tools/test_layout.js` — added 2026-10-03: the phone-layout problems
  Alexandru saw on a real phone, at 390x844 with the real data. Fails if
  the Ticket info or Bucket list tab scrolls sideways or any card or tag
  reaches past the screen (every warning in `football-rules.json` is
  checked, the longest - Inter's, 135 characters, and Poli's - by name);
  if a club sheet (a Regionalliga Bayern club, a Südwest club, Bayern)
  can be moved off the bottom bar by scrolling past its end, or the map
  pane can be scrolled at all; if a sheet shows a Wikidata id anywhere
  but its bottom Details line; if the visible Fixtures or Ticket info
  text names a file, a path, OpenLigaDB or football-data (checked on every
  club with ticket information and one club per country and tier); if a
  club with no fixtures is not told which leagues are covered; if Next
  window does not say "No window recorded" / "No upcoming window
  recorded" as the files require; and if any sheet with ticket
  information, every section open, is wider than the screen. Run against
  the page as it was before, it failed 255 of 287 checks.
- `tools/test_legend.js` — added 2026-10-03: the collapsible tier legend
  at 390x700 and 390x500 (and 390x300 for the scrolling fallback). Fails
  if the legend does not start closed on a first visit, if its header is
  not a button with `aria-expanded` and at least 44 px tall, if a tap
  does not open and close it (the arrow must rotate), if "Leagues shown"
  is not above every tier row and the shared-ground row, if the zoom
  dimming stops following `zoomForTier`, if the open legend overlaps the
  attribution bar or the bottom navigation or reaches the top row - also
  with the attribution forced to wrap to several lines and after the
  window shrinks while it is open - if its last row is cut off, if a
  too-short screen does not scroll inside the legend with its header in
  view, if the choice does not survive a reload (open or closed), or if
  blocked storage breaks it. With the fitting code disabled in a scratch
  copy it failed 4 of 48 checks.
- `tools/test_tickets_bucket.js` — added 2026-10-04: the Ticket info and
  Bucket list tabs at 390x844, every card opened, checked against the
  files: no sideways scroll on either; one Ticket info row per country
  with national rules and per club with ticket information; Italy's
  rules each with "Applies to" in plain words (never blank, never "all"
  where the row says unknown), condition, authority, status and source;
  Inter's "Country rules: Italy" above its researched rules and notes,
  and its notes marked unverified where the file marks them; Nürnberg's
  "No national rules researched for Germany (DE) yet." (since 2026-10-06,
  when Germany got national rows, Nürnberg's "Country rules: Germany"
  holding all of them, and the Frankenderby's Germany section above
  Nürnberg's researched rules - the test follows the file); no upcoming-dates
  section on Ticket info; every bucket entry a card; every ticket event
  inside the entry `bucket-links-manual.csv` links it to, or under
  Reminders (soonest first, undated last); the Frankenderby's Nürnberg
  (host) then Fürth ("No ticket rules researched for SpVgg Greuther Fürth
  yet."); the Milan derby's AC Milan and Inter; no `inferred` or
  `disputed` date shown to the day; no script error. With the
  month-level rule and the country-rules order broken in a scratch copy
  it failed 15 of 53 checks.
- `tools/test_calendar.js` — added 2026-10-04: the Bucket list's List
  and Calendar at 390x844, checked against the files. No sideways scroll
  on either; the sort's two options and Earliest's order (worked out by
  the test from the files, past entries checked with the clock at June
  2027, in a collapsed Past section); the star (44 px, aria-pressed, does
  not open the card) and the sort surviving a reload; a stored id that is
  no entry ignored; blocked storage; then, with the clock at 2026-10-25
  23:30 UTC and the page under **Europe/Berlin and under UTC**, every
  month from July 2026 to October 2027: the local today, exactly the
  confirmed day-level items on their day cells, every month-level item
  in the strip and never on a day, no disputed item placed, the "No
  date" list, holiday shading on exactly each block's days, the school
  start, the not-entered notice outside the entered span, both time
  zones drawing every month identically; a movable day (in a served copy
  of the file only) shaded differently; the sheet against the bottom
  bar, scrolling inside itself, holding the same text as the List's
  opened entry (or Reminders card); "School holiday: Pfingstferien" on
  the Europa League final and on nothing that is not in a block. Prints
  a month's render time at 4x CPU. With estimates also put on a day cell
  and each holiday block's last day dropped, in a scratch copy, it failed
  49 of 195 checks.
- `tools/test_me.js` — (since 2026-10-09 it also covers the Dark/Light theme: the toggle and its persistence, the pre-paint script, no colour literal outside the variable sets, 4.5:1 text contrast on every main tab, Me sub-tab and sheet in both themes, the light-tile fall-back to dark, the palette's distinctness, nothing overflowing at 390 px; and the translated interface: see "The interface is translated", 32 more checks) added 2026-10-04: the Me tab at 390x844, the clock
  at 2026-10-04 12:00 Berlin time. Fails if the four tabs do not fit the
  bottom bar (one wider than its slot, wrapped or off screen); if adding,
  editing or deleting a membership or a ticket goes wrong; if "Renewal due
  in N days", "Renewal overdue by N days" or the window setting is wrong;
  if a non-euro cost lacks its euro figure in brackets or "euro figure not
  entered"; if a ticket with no kick-off does not say "time not set"; if
  anything is lost on a reload; if a card number (13-19 digits passing
  Luhn, spaced, hyphenated or not) is saved, or digits failing Luhn are
  refused; if "You hold tickets" is missing from the linked entry in the
  List, its opened detail, the calendar's day cell and item, or the
  sheet - or is on any other entry; if a downloaded `.ics` is not valid
  (CRLF, lines of at most 75 octets, one VEVENT, one VALARM, the required
  properties, escaping, folding) or its alarm does not go off at exactly
  the lead time (1 day before kick-off; 14 days before a renewal at 09:00;
  a changed lead time); if the backup banner does not show after an edit
  or a star and go after an export or an import; if export, delete
  everything, import does not give back exactly what was exported,
  favorites included; if any of seven broken files (not JSON, another
  app's file, a newer version, a ticket with no status, a card number in a
  note, a repeated id, a missing list) is not refused with the device
  unchanged; if blocked storage breaks the tab; if the tab scrolls
  sideways with forms or cards open; or if anything typed on the tab is in
  any request's URL, headers or body, in a cookie, sessionStorage,
  IndexedDB or the repository, or any request other than GET reaches the
  site. 83 checks; since 2026-10-09 131 (113 before the detail sheet), as it also covers the Me tab's four
  sub-tabs (Conventions, "The Me tab's attended matches and events"): their order
  and fit at 390 px in English and Romanian, the file requested only once the Me
  tab is opened, the stats and list counts against counts made from
  `data/attended.json` itself, every entry rendered and opening its detail sheet (line-ups, pitch, timeline, stats, note, personal fields),
  identical `en` and `ro` key sets, no `mf_` key read or written and no `mf_` IndexedDB opened (only the two new `football-attended-*` keys are read by the list tabs), a failed load said; and the device-only additions of the same day (Conventions, "Imported matches, supporter choices and media"). Since 2026-10-13 it also covers the Add a match form and Edit this match (Conventions, "The Add a match form"): 385 checks in all (before the event form). Since 2026-10-13 it also covers the Add an event form, imported events and the version 3 backup file (Conventions, "The Add an event form and imported events"), and the single red-cards card.
- `tools/test_ksc_tickets.js` — added 2026-10-06: Karlsruher SC's ticket
  information at 390x844, checked against the files. Fails if KSC is not
  listed under Clubs on the Ticket info tab; if its entry does not open
  with "Country rules: Germany" holding every DE row of
  `country-ticket-rules.csv` (or "No national rules researched for
  Germany" if the file has none) **above** "Researched rules", itself
  above "Your notes"; if any KSC row of `club-ticket-rules.csv` or window
  of `club-ticket-windows.csv` (label and typical opening) is missing from
  the entry; if the club sheet has another order or its Next window words
  an estimate other than as one; if the Bucket list's Südwestderby entry
  does not show KSC (host) with its researched rules under Germany's and
  Kaiserslautern as not researched; if an `inferred` or `disputed` date is
  shown to the day in any of the three; on sideways scroll or a script
  error. 22 checks.
- `tools/test_vfb_tickets.js` — added 2026-10-07: VfB Stuttgart's ticket
  information at 390x844, checked against the files. Fails if
  `football-rules-links.csv` does not link `vfb` to `Q4512`; if VfB is not
  under Clubs on Ticket info; if its entry does not open with "Country
  rules: Germany" holding every DE row, above "Researched rules", above
  "Your notes" (and the notes must hold the `vfb` entry); if any VfB rule,
  window (label and typical opening) or phase is missing, or the Prices or
  Sell-out record section holds a different number of rows from the files
  (counted in the page) - the same on the club sheet; if the Next window
  line words an estimate other than as one; if the Bucket list's
  `vfb-regular` entry lacks VfB's block with Germany's rules above its
  researched rules; if an `inferred` or `disputed` date is shown to the day
  in any of the three; on sideways scroll or a script error; and, since the
  same day, if a `confirmed` vfb ticket event is shown other than to the day,
  or the soonest one is missing from Next window when it falls in the current
  month (these checks follow today's date, so they stop once the sales are
  past). 27 checks on 2026-10-07.
  With a price row and the `minors` rule dropped from the page in a
  scratch copy it failed 5.
- `tools/check_translations.py` — added 2026-10-11: read-back and checks for `data/ro/*.json` (Conventions, "Romanian translations of data texts"). **Fails (exit 1)** on a file that is not a registered source or not an object, a malformed entry, a duplicate key, an empty `ro`, an unknown row key or field, a Romanian that lacks a number group, ISO date or URL of its English, and a fingerprint function that does not reproduce `tools/translation-fingerprints.json`; **warns** on a stale entry and on a glossary term (`data/ro-glossary.csv`) the Romanian does not use; prints coverage per source. `--registry` prints the translated fields as JSON, `--root DIR` checks another checkout. Never writes. Run by `test-pages.yml`.
- `tools/check_sale_dates.py` — added 2026-10-07 (rule 8): offline, warnings
  only, always exits 0. Lists dated `ticketEvents` entries missing `source` or
  `checkedOn`, dates passed more than 14 days ago, and `checkedOn` over 30 days
  old with the date still ahead. Run by `build-calendars.yml`. Never writes.
- `tools/check_competitions.py` — added 2026-10-08: read-back and checks for
  the three competition files. **Fails (exit 1)** on an invalid topic,
  status or type, an unknown `competitionId` or `sourceId`, a repeated id, a
  malformed row, a bad date and a day-level date after today in a text or
  basis cell; **only warns (exit 0)** on a row with no source or no
  `checkedOn` and on one checked over 365 days ago. Never writes. Run by
  `test-pages.yml`.
- `tools/test_competitions.js` — added 2026-10-08: the Competitions tab at
  390x844, checked against the three files (48 checks): five tabs fit, every
  competition listed in the fixed group order, "Not researched yet", every
  researched sheet with its seven topics in order, status labels, source
  links and "Checked on", no future day-level date, the country filter and
  name search. Run by `test-pages.yml`.
- `tools/check_holidays.py` — added 2026-10-04: read-back and checks for
  `data/holidays-manual.csv`, in the style of `check_derbies.py`. Prints
  every row as understood (weekday, length), rejects by line (bad or
  unreal date, end before start, missing source, unknown `dateSource`,
  an unquoted comma), reports an unknown kind as **not accepted**, and
  reports overlaps, a school start longer than a day, an unconfirmed row
  and the absence of any movable day. Never writes. Exits 1 on a rejected
  row. Run by `check-holidays.yml` (push to `main` or pull request
  touching the file, the tool or the workflow) and by `test-pages.yml`.
- `.github/workflows/test-pages.yml` — added 2026-10-03: runs
  `test_pwa.js`, `test_derbies.js` and `test_routes.js`, and since the
  same day `test_zoom.js`, `test_search.js`, `test_coverage.js`,
  `test_sheet_tickets.js` and `test_layout.js`, then `test_legend.js`
  and `test_nearme.js`, and since 2026-10-04 `test_tickets_bucket.js`
  and `python3 tools/check_tickets.py` (which must exit 0), and since the
  same day `test_calendar.js` and `python3 tools/check_holidays.py`
  (which must exit 0), and since the same day `test_me.js`, and since
  2026-10-06 `test_ksc_tickets.js`, and since 2026-10-07
  `test_vfb_tickets.js`, on a push to
  `main` or a pull request touching `index.html`, `sw.js`, the manifest,
  a `tools/test_*.js`, `data/football-rules-links.csv`,
  `data/bucket-links-manual.csv`, `data/event-ticket-rules.csv`,
  `data/holidays-manual.csv`, `tools/check_holidays.py`, and since
  2026-10-06 the ticket files themselves (`data/club-ticket*.csv`,
  `data/club-tickets.csv`, `data/country-ticket-rules.csv`,
  `data/ticket-sources.csv`) and `tools/check_tickets.py`, or
  itself. Playwright is installed in the job,
  pinned, not added to the repo. **Since 2026-10-16 the job's `timeout-minutes` is 60 (was 40) and a last step, "Step durations", prints each step's duration** (needs `actions: read`). **Every Stadia request in all three is
  stubbed**, so a run spends no credit and does not show that Stadia
  itself answers; that was checked separately (Secrets). **Since 2026-10-19 the club-culture files trigger it as well: `data/club-parents.csv` joined `data/club-rivalries.csv`, `data/club-friendships.csv`, `data/club-culture-sources.csv` and `tools/check_club_culture.py` in the `push` and `pull_request` path lists** (the checker step already ran; only the parents file had been missing, so a change to it alone ran no workflow).
- `tools/link_fixtures.py` — joins fixture-source teams to map clubs
  and writes `fixture-links.json` and `fixture-link-review.csv`. Reads
  committed files only, no network. Run by `link-fixtures.yml` after
  each fixture fetch and club build. Also reads back the Q-id join
  between `club-tickets.csv` and the map. See Conventions.
- `tools/build_calendars.py` — `.ics` generation
- `tools/fetch_fixtures.py` — football-data.org
- `tools/fetch_openligadb.py` — OpenLigaDB: 2. Bundesliga, 3. Liga,
  DFB-Pokal and the Regionalliga divisions it carries. **Never the
  Bundesliga.** Daily, `fetch-openligadb.yml`, no secret. Exits 1 when a
  competition that should have come back did not; the files that did
  come back are still committed
- `tools/fetch_clubs.py` — Wikidata club layer, and the **novalue
  fallback**: the only route by which a club hidden from the club
  query by a preferred-rank "no league" statement reaches the map.
  It decides **visibility and never tier**, and it surfaces nothing
  unless a current-season roster names the club. See Conventions.
  Since 2026-09-26 it also names, on every run, each club on the map
  whose item carries **more than one truthy ground**, and says whether
  a hand row pins it — the SC Freiburg shape, reported rather than
  found by accident. It picks no ground itself.
  Since 2026-09-27 it has a third route, the **hand-named fallback**:
  a `clubs-manual.csv` row naming a Q-id no query returned, with a
  country and a tier, brings that club in under its own Q-id when a
  tracked roster names it. One roster read per country per run is
  shared by both fallbacks. See Conventions.
- `tools/crosscheck_capacity.py` — OpenStreetMap capacity comparison.
  Since 2026-09-30 it decides `capacity-review.csv` **country by
  country**, the way `propose_coordinates.py` decides its file (see
  Conventions)
- `tools/propose_coordinates.py` — OpenStreetMap coordinates for the
  clubs Wikidata cannot place. Matches on names, proposes only, and
  flags anything ambiguous rather than settling it with a rule.
- `tools/check_tickets.py` — read-back and checks for the eight ticket
  files (the original three plus phases, rules, demand, sources and,
  since 2026-09-24, country rules), and since 2026-10-03
  `data/football-rules-links.csv`, which `check-tickets.yml` now also
  runs on, and since 2026-10-04 `data/event-ticket-rules.csv` and
  `data/bucket-links-manual.csv` (both also on `check-tickets.yml`'s
  paths). Reads, never writes; exits 1 on a
  problem. Also prints a **layered** view of what applies to each club
  and each derby — the club's rows, then its country's rows marked
  `[national]` with their `appliesTo` and `condition`, never filtered
  by them — plus a **CHECK THESE AGREE** list and every `unverified`
  row in one list.
- `tools/crosscheck_stadiumdb.py` — StadiumDB capacity comparison, the
  third opinion. Matches by club name and country because StadiumDB
  publishes no coordinates; reports, never corrects.
- `tools/check_rosters.py` — the roster check. Asks, from the league's
  side, whether a club that should be on the map is missing from it.
  Reads, never writes to a club file. Since 2026-09-26 it **leaves out,
  and names**, a table row whose first link is a parent club under a
  reserve side's name ("SK Rapid II" linking SK Rapid Wien), or whose
  team cell has no link at all, so the first link is a city
  ("Austria Wien II" linking Vienna).
  Since 2026-09-27 **one club is one finding**: a row it leaves out
  can be joined to its Q-id by hand in `data/roster-links-manual.csv`,
  read back every run; a map club whose `P831` (parent club) is a
  roster club not on the map, with the same reserve marker, is read as
  that club - the club-and-men's-team shape, joined id to id, never by
  name; and a club whose position a hand row clears on purpose reads
  `unplaced-no-coordinates` with that reason, not as missing from
  Wikidata.
  It also exports `roster_qids(country, tiers)`, which is how
  `fetch_clubs.py` asks "does a division this project tracks say this
  club is playing" for the novalue fallback. The question belongs to
  this file, so it is answered by this file's reader rather than by a
  second copy of it — all three bugs this reader has had failed
  silently, in the sitelink hop and the redirect hop, and a duplicate
  of those steps would earn its own three. It returns **Q-ids and nothing
  else**: which divisions name a club, never which tier the club
  should be given.
- `tools/diagnose_p118_rank.py` — which clubs the club query's truthy
  `wdt:P118` join hides, and why: a preferred-rank statement asserting
  no league, or every statement deprecated — and, since 2026-09-25,
  **query C**: a mapped league at normal rank under a preferred
  statement naming a *different* league. Reads `P576` so a
  `<novalue>` on a club that folded is not mistaken for an error.
  Reads and writes **nothing** — not a club file, not a review file —
  and exits 1 on a failed call. Since 2026-09-25 query C ends with
  **the bill** — which of the clubs it lists a tracked roster names,
  i.e. which ones the next club build surfaces — and the tool refuses
  to run at all if `league-tiers.csv` maps a country its `COUNTRIES`
  does not list, rather than half-check it. It has its own workflow,
  `diagnose-rank.yml`, which runs on every push to `main` that touches
  `league-tiers.csv` or `league-rosters.csv` — the moment a new
  country is mapped — and weekly after the club build. **All three
  rank shapes are therefore checked for every country by default**,
  not by somebody remembering to.
- `tools/propose_country.py` — added 2026-10-21. **The repeatable part of
  adding a country (tiers 1 and 2), so that a person only decides.**
  READ-ONLY: it never edits a hand-written file (`clubs-manual.csv`,
  `league-tiers.csv`, `league-rosters.csv`, `roster-links-manual.csv`,
  `fixture-links-manual.csv`, `coordinate-reviews.csv`,
  `football-rules.json`), never writes a club file, and reads no
  hand-written file at all (it reads `data/fixtures/index.json` and the
  source of the tools only, to print candidates and line numbers). It
  writes exactly `data/clubs/proposal-<CC>.csv` and `.md`, and writes
  **neither** when anything failed (a failed fetch is not an empty answer;
  `--write-partial` exists for probes). Rule 2 holds: a gap is reported in
  the cell, never filled. **Run by `propose-country.yml`** (`workflow_dispatch`
  only; inputs: country code as the club files use it, the country's
  Wikidata item, the tier 1 and tier 2 season articles with the en dash,
  optional `below_articles` separated by `;`, extra label languages, league
  items if the articles do not lead to them); an offline test of the
  classification, `tools/test_propose_country.py`, runs first. It imports
  `check_rosters.py` (the roster reader and the sitelink hop),
  `diagnose_p118_rank.py` (its truthy-rank functions and its two rank
  queries) and `fetch_clubs.py` (the not-a-club net, `COUNTRIES`); the only
  change to another tool is an extra `ground` / `ground_title` key in
  `check_rosters.table_rows()`, which nothing else reads. Politeness: User-Agent
  `FootballPlannerBot/1.0`, `maxlag=5` on Wikimedia APIs, one request a second
  per host, `Retry-After` honoured, at most 4 tries, no secret.
  **What it reads, in this order.** (1) The season articles' stadiums (or
  league) tables with the existing reader: club, Q-id by the sitelink hop,
  ground, capacity; a table that does not resolve, a hop that returns
  nothing, or a row the reader cannot read (a reserve side linked to its
  parent, a team cell with no link) is printed as a failure or as kind
  `roster-unread`. (2) The league items: season article -> its item ->
  `P3450`, else the infobox's league link; **P3983 and P17 are printed and
  never used to decide the country**; every non-human item carrying either
  league at any rank (SPARQL, with rank, `P580`/`P582`, `P576`); items
  labelled like a tier (or like a redirect to its article) that are not the
  tier's item, with how many clubs carry them and any dissolution or
  successor (the "old Second Division" trap, Belgium's `Q233199`). (3) The
  candidates, each a row with evidence: `roster-ok` (tagged at the roster's
  tier), `roster-untagged` (the hand-named fallback's candidates, with a
  `P576` noted as refused without `allowDissolved`), `roster-wrong-tier`
  (both lists' evidence and the season article's team-changes rows),
  `roster-unread`, `extra-tagged` (a truthy-tagged item in no roster: its
  `P576`, the tag's dates, the first intro sentence of its article that names
  a league, 30 words at most with the URL, whether its intro is in the past
  tense, whether it mentions a tracked league, whether either complete
  article names it in its team changes, whether a lower article given with
  `--below` lists it, **and whether the build would draw it at all**: an item
  with no `P625` on itself or on a `P115` ground is dropped at the
  coordinates gate and has nothing on the map to remove), `not-a-club`
  (`fetch_clubs.not_a_club`), `duplicate` (one folded label, or one ground,
  among items with the same reserve markers), `women-candidate` (rule 6, four
  angles: type, label and description words, `P2094`, and a women's football
  item pointing at a roster or tagged club by `P361`/`P749`/`P831`/`P127`,
  marked as not reaching the map when it carries neither tag; other-sport
  items are ignored and counted), `rank-shape` (A: every tracked statement
  deprecated; B: a preferred novalue; C: a preferred statement naming another
  league, LR Vicenza's shape; cross-checked against
  `diagnose_p118_rank.QUERY_HIDDEN` and `QUERY_STALE_PREFERRED`, a
  difference is printed) and `two-grounds` (several truthy `P115`). A
  dissolved tagged item and a tagged extra whose tag is not truthy are
  counted and listed in the `.md`, not given a row. (4) The wiring patch in
  the `.md`: the `league-tiers.csv` and `league-rosters.csv` rows (en dash,
  season), `COUNTRY_BOX` proposals from `P1332`-`P1335` at best rank and at
  normal rank only, with a note when a point is at preferred rank, when the
  box is large, or when a roster club's position lies outside it (an island),
  football-data.org candidates by name (printed only), and the places a
  person must edit with their line numbers, read off the most recently added
  country. (5) The summary: counts per kind and every step's duration.
  **What it never does:** decide a tier, a `skip`, a hand-named row, an
  identity link, a ground, a capacity or a box; read or edit a hand-written file; use an end date to
  decide anything; open a page of a host other than Wikipedia, Wikidata and (with `--grounds`)
  StadiumDB, each after reading its robots.txt; and, with `--grounds`, the public Overpass API, which is governed by its published usage policy and not by its robots.txt (Known open problems, "Overpass and robots.txt: resolved 2026-10-21").
  **Order of use for a new country.** (a) Dispatch `propose-country.yml` on
  `main` with the two season articles and, as `below_articles`, the third-
  and fourth-tier ones, whose clubs are the independent statement a `skip`
  needs. (b) Read the `.md` top to bottom: failures, reader gaps, the leagues
  table (does P17 name the country given?), the same-label items. (c) Wire
  the country with the printed patch and the list of places. (d) Build, then
  decide each candidate in the order: tier rows, `skip` rows (two complete
  division articles agreeing on the absence and an independent statement:
  the Hermannstadt standard), hand-named rows, hand links for
  `roster-unread`, pins for `two-grounds`. (e) Then the checks of "Adding a
  country". **Known limits.** It needs the season articles to exist in the
  shape the reader knows (a stadiums table, or a league table); a rowspan can
  shift the ground column. It reads the tags as Wikidata has them and decides
  nothing from an end date. The intro sentence is chosen by a word list
  (league, division, liga, tier ...) and can be a past season: it prints the
  sentence for a person to read, with its tense flag. `drawn_by_build` is a
  position test on Wikidata items only; a hand row that places a club is not
  seen. The football-data candidates match names only. It covers tiers 1 and
  2; lower articles are evidence for an extra, nothing more. It needs
  Wikidata, its query service and Wikipedia, which only a runner reaches. It
  was tested on Portugal only. **A line of its output is an identity or
  evidence claim like a `fixture-links-manual.csv` row, and Alexandru's to
  overrule.**
- `tools/propose_grounds.py` — added 2026-10-21, **the ground and capacity half of `propose_country.py`** (`--grounds`, on by default in the workflow; imported by it, which passes itself in so the HTTP clock and politeness are shared). It adds two kinds of row, `ground-proposal` and `capacity-proposal`, one pair per roster club, and a "Grounds and capacities" section in the `.md` listing the clubs that need a look. **It reads, per club:** (a) the ground the season table gives and the club's own English article's infobox ground; (b) the Wikidata ground item (`P115` at best rank, several truthy flagged) with `P625`, labels, aliases and `P1083`; the ground's English article's coordinates; and, for a ground nothing else positions, the Wikidata item whose label equals the ground's name (`wbsearchentities`, the route that placed Alverca and AFS); (c) OpenStreetMap elements named like the ground, asked of the public Overpass API **under its published usage policy, since 2026-10-21** (User-Agent as every other request, one request at a time, waits that double from 30 s up to 120 s (Retry-After if longer), up to 6 tries per request and a retry on HTTP 429, 502, 503 and 504, at most 10 club positions per request, at most 60 requests per run (retries included) and **at most 15 minutes for the whole OpenStreetMap step** (so a server that never answers cannot run the job into its 90-minute limit and lose the proposal); a read timeout counts as a 504; **a failure of the whole OpenStreetMap step is a warning, not a failed run** (the log, the `.md` and every row say `asked and failed`, and the rest of the evidence is written); the `.md` says how many requests were used; robots.txt is still read first for every other non-Wikimedia host, StadiumDB); (d) the distances between those positions; (e) capacity figures from the table, Wikidata, OpenStreetMap and StadiumDB (`crosscheck_stadiumdb.py`'s parser and club-matching signals, imported; the slug is the configured one, or found by probing the first three letters of the country's name, its two-letter code and its IOC code and saying which answered a table, and `--probe-slug` forces the probe). **The rules it applies, mechanically.** A ground is named by two independent places for 2026-27 (table, club article, Wikidata, StadiumDB) or the row says one; the names are compared with the club's own name words, stadium words and pitch numbers set aside (so "Benfica Campus" and "Benfica Stadium" are not one ground), and when the places split into groups, a table that is the odd one out is a note and not a problem. A position is proposed from ground-specific sources only (the Wikidata ground's `P625` **only when its name agrees with the table's**, the ground's own article, a Wikidata item found by the ground's name, an OpenStreetMap element whose name equals it), the first available in that order, with the 150 m agreement test between them; one source says so. The "map" is what the build would show (the club's `P625`, else its `P115` ground's), so the row says **`UNPLACED by the build`** (the `unplaced-no-coordinates` reason) or **`THE MAP WOULD BE n m FROM THE PROPOSAL`**. A `P115` shared with another roster club is flagged on a reserve side (a copied first-team ground) and noted on the first team. A capacity is proposed only where two **independent** sources agree within 5%, and **the table and Wikidata are one source** (both Wikipedia's, CLAUDE.md's own reading of Casa Pia); a Wikidata or StadiumDB figure about another ground is not used and is said ("CLEAR the map's 8500: it is the capacity of another ground"); of two agreeing figures the table's is taken, else StadiumDB's, Wikidata's, OpenStreetMap's; with no agreement the cell is BLANK and every figure is listed. **Known limits.** **The OpenStreetMap step, live on Portugal on 2026-10-21 (the fifth live attempt; Overpass was at capacity for the four before it, see Known open problems):** 5 requests, 483 named elements within 3 km of 38 positions, and against the Portugal hand rows: Casa Pia proposed 12 m from the hand row (OpenStreetMap relation/13900988 agrees with the ground article), AVS 0 m from it (way/1206431139 agrees at 9 m), **Porto B found by OpenStreetMap alone** (way/1003177522, 16 m from the hand row, 2,342 m from the copied Wikidata ground that anchored the search), **Lusitânia and Sporting CP B missed**, because the search is anchored on positions the other sources already gave: Lusitânia has none (`osm_search_centres=NONE`), Sporting CP B's only anchor is the copied Alvalade ground, about 29 km from the Estádio Aurélio Pereira. No false positive among the five. A club with no anchor, or a wrong one, is never searched by name; the independence rule is stricter than some hand rows (AVS's 6,230, taken as "table and the ground item agree"); the club's infobox ground and the StadiumDB club match are text matches; a ground column shifted by a rowspan gives a wrong table ground.
- **Measured accuracy of `propose_country.py` and `propose_grounds.py`, 2026-10-22 (Belgium and Greece hold-out, then the fixes).** On 2026-10-21 the tool was run for Belgium and Greece (tiers 1 and 2, grounds on) **before the hand rows were read**, then compared with them (`data/clubs-manual.csv` BE and GR, `coordinate-reviews.csv`, `roster-links-manual.csv`, the BE/GR entries here). Counts below are from the proposal files, positions compared with the hand rows' lat/lon (within 20 m counts as a hit), capacities with the hand figures (within 5%). **Classification (BE):** every hand-named fallback club (7: Francs Borains, Hasselt, Lierse, Lokeren, Patro Eisden, RFC Liège, Virton) was `roster-untagged`; both tier corrections (Lommel to 1, Dender to 2) were `roster-wrong-tier`; the four clubs skipped or rejected for a stale tag (Roeselare, Tubize, SL16, RWDM) were `extra-tagged` with the reason read from their article; the four U23 sides were `roster-unread` (the four roster links) and two were also `extra-tagged`; the two club seasons were `not-a-club`; SL16's two grounds were `two-grounds`. No false positive among the classified rows. **Grounds, hand rows against the first run and against the fixed tool (OpenStreetMap down in the BE run, see below):** Belgium positions within 20 m **3 of 14 → 7 of 14**, missed 10 → 6 (the four U23 sides have no ground row because the roster reader refuses their rows, and Sporting Hasselt is unplaced), capacities agreeing with a hand figure 3 → 4, blank where the hand row has a figure 8 → 7; Greece positions 0 of 3 → 0 of 3 (the three hand rows are the clubs no source positions: Zakynthos, Nestos, Panathinaikos' Olympic Stadium), capacities 1 of 4 → 2 of 4; Portugal positions within 20 m **5 of 8 → 7 of 8** (first run before the fixes: Casa Pia 12 m, AVS 0 m, Porto B found, Lusitania and Sporting CP B missed; fixed tool, 2026-10-22 15:08, OpenStreetMap answering: Porto B 16 m, Sporting CP B 0 m by the new by-name search, Lusitania still missed), capacities 3 of 4. **Bugs the comparison found, each fixed with the case that exposed it:** (1) the infobox ground was read with a regex that cut at the first `|`, so grounds were `[[Lier, Belgium`, `{{cite web` or `{{ill`: now `parse_infobox_ground()` reads links, `{{ill}}`, footnotes and the town after a comma (Belgium); (2) the 2026-27 Challenger Pro League article has no stadium table, so six clubs had an empty ground and were searched for nothing: the ground now falls back to the club article's infobox and the row says `ground_read_from=club article infobox` (Belgium); (3) a ground no source positioned was never searched in OpenStreetMap, because the search started from a position: it is now also asked by NAME across the country (`overpass_by_name`, one request per 12 distinctive words, sharing the request cap and time budget), an element counting only when its full name equals the ground's, and several exact elements more than 150 m apart are reported as ambiguous and none is used (Lusitania, Sporting CP B, six Belgian clubs); (4) a Wikidata ground whose NAME differs from the table's but whose position is within 150 m of the table ground's own article or OpenStreetMap element is now read as the same ground (Kifisia and Famalicao shapes), where before it was an `ONE place only` problem and its capacity was cleared; (5) a P115 shared by two clubs whose tables name the same ground is a genuinely shared ground, and one whose other club's ground is different is a note on the club whose name agrees (Kifisia against Panathinaikos), not a problem; (6) `find_league` had no answer for a new season article with neither P3450 nor an infobox league link (the 2026-27 Super League Greece): it now also tries the article's title without its season, and prints that it is a fallback; (7) a failed league discovery still spent 8.6 minutes of the public Overpass API on a proposal that would not be written: step 6b is now skipped when the proposal already has failures and `--write-partial` is not set. **A bug the fix itself exposed, found by the Greece re-run and fixed the same day:** the by-name search accepted a ground named by ONE distinctive word, and Panathinaikos' ground `Olympic Stadium` (its article title without the qualifier) matched the `Olympic Park` of Volos, 211 km away; a name must now have at least two distinctive words to be searched across a country. **Live OpenStreetMap results:** in the Belgium re-run and the first Portugal re-run the public Overpass API answered HTTP 502 (at capacity) until the 15-minute budget ran out, so those two proposals were written without it (and say so on every row); the Greece runs and the last Portugal run had it (7 requests). Portugal, by name: Sporting CP B's `Estádio Aurélio Pereira` was found by the country search (way/135459411, 0 m from the hand row) and Porto B by the search around positions (16 m); **Lusitania is still missed, on purpose**: three OpenStreetMap elements carry exactly the ground's name and lie up to 1,070 m apart, so the ambiguity rule uses none (the hand row took the one of the three that the table's pin and a 3.6 m twin support; picking it is a person's call). Greece, by name: 0 of 4 grounds found an element of exactly that name, none wrong after the fix. Belgium's by-name effect was not measured live (Overpass was down); it is covered offline only. **Reading the numbers:** the tool finds a position when a ground-specific source exists (Wikidata ground, the ground's article, a Wikidata item found by name, an OpenStreetMap element of the same name); it cannot place a club whose ground has no article, item or OpenStreetMap element of that name in a language the tool asks in, and it leaves the capacity blank wherever two independent sources do not agree, which is stricter than several hand rows (they take the table and Wikidata as agreeing). A person still decides every row.
- `tools/test_propose_country.py` — added 2026-10-21: the classification of
  `propose_country.py` on hand-made items (every kind, the club item / team
  item join, the dissolved and hidden extras, the women's pointer, and since
  2026-10-21 the Overpass client of `propose_grounds.py`: retries on 429, 502, 503
  and 504, waits that double from 30 s up to 120 s (Retry-After if longer), up to 6 tries per request, the cap of 60 requests, 10 centres per
  request, the 15-minute budget, a read timeout retried like a 504, an Overpass failure as a warning), no network. Run by `propose-country.yml` before the real run, and
  **since 2026-10-21 also by its `offline-test` job on a push to `main` or a
  pull request that touches `tools/propose_country.py`, `tools/propose_grounds.py`,
  the test itself, the tools they import or the workflow file** (the real
  run, job `propose`, stays dispatch-only).

---

