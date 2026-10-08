# Football fixture and ticket planner

A personal, mobile-first static site on GitHub Pages that helps Alexandru
(Leonberg, near Stuttgart) plan which football matches to attend and not
miss ticket windows. Data is refreshed by GitHub Actions cron jobs that
commit JSON back to this repo. There is no server and no build step.

Alexandru does not write code. Explanations should say what to do and
what he should see, not how the code works.

---

## The rules that matter most

**1. Never generate a ticket rule, sale date, application window or
deadline.** No API has them. They are hand-written by Alexandru because a
plausible-sounding wrong deadline is worse than a blank field. If you
find yourself about to write a date because it "usually" falls around
then, stop.

**2. A missing field stays blank and gets reported.** Never fill a gap
with a guess, an inference or a rounded-off "typical" value. Every tool
here prints what it could not resolve, with a reason. That reporting is a
feature, not noise — keep it when you change things.

**3. Hand-written data beats fetched data, always.** `clubs-manual.csv`
overrides Wikidata. `fixtures-manual.csv` is never touched by the cron.
`football-rules.json` is never written by any script. If a fetched source
and a hand-written one disagree, the hand-written one wins and the code
does not get a vote.

**4. Fetched data never becomes a calendar event.** The `.ics` feeds are
hand-curated. `data/fixtures/` feeds the map and the app only. Bundesliga
alone is 306 matches; putting fetched fixtures in a subscribed calendar
would bury the handful of things that actually need acting on.

**5. Ask before building when something is ambiguous. Push back when he
is wrong.** He has asked for this explicitly and has been right often
enough that it matters — several of the better decisions in this project
came from him correcting a proposal.

**6. Men's football only, for now.** No women's league has been added to
`data/league-tiers.csv`, so the club layer is compliant by construction
— with one hole, found 2026-09-30: a women's club whose Wikidata item
carries a MEN'S league tag reaches the map like any other item.
Fundación Albacete did, at tier 2 in Spain, and has a `skip` row. A
filter on Wikidata's type was measured and **not built**: the only
other items typed as a women's team that carry a mapped league are
Atromitos and Asteras Tripoli, the real men's Greek clubs, whose items
carry that type too. So the roster check is what catches this shape,
as it did. **England was checked for it deliberately, 2026-09-30, from
three angles, before any build**: no item carrying either English tag at
any rank is typed, labelled, described or classed (`P2094`) as women's,
and no women's team item points at a big English club with `P831` or
`P361`. Zero. **The Netherlands was checked the same way, 2026-10-01, from
four angles: zero again** - though there, three women's items do point at
big Dutch clubs through `P361` (none carries either men's league tag, so
none reaches the map). **Belgium was checked the same way, 2026-10-01,
from four angles: zero** - no item carrying either Belgian tag at any rank
is typed, labelled, described or classed as women's, and no women's item
points at a Belgian roster club by `P831`, `P361`, `P749` or `P127`. One
trap, recorded: KV Mechelen's women's team `Q19974079` carries the DUTCH
label "KV Mechelen", identical to the men's club's; it has no mapped tag
and never reaches the map. It applies beyond leagues: a
future club addition, a badge, or a piece of research is also men's
football only until this rule changes, so don't reach for a women's
team, a women's competition, or a women's-team crest just because a
men's counterpart already has one.

**7. Sessions merge their own work once its checks pass clean.**
Standing policy from 2026-09-25, at Alexandru's instruction: a session
does not stop and ask before merging each time. It works on its branch,
opens a pull request so the diff can be read, and merges it itself
once everything it touched has come back clean — the workflows it
dispatched are green on the branch, `check_tickets.py` exits 0, no
hand-written row was rejected, and the read-back says what was meant.
**Clean means clean**: a red run, a rejected row, or a review file
that was left unchanged because a fetch failed is not a pass, and the
branch is not merged over it. **Merging is not deciding.** Anything
that is Alexandru's call — a tier written off one table, a `skip`
that does not meet the documented standard (two complete division
articles agreeing on the absence **and** an independent statement of
the reason, the Hermannstadt standard), a Q-id identity question, a link in `fixture-links-manual.csv` he did
not ask for — is still left undone and written up under Known open
problems; the merge carries the write-up, never the decision. Rules 1
to 6 are unchanged by this and outrank it.

**8. Sale dates are shown only in the Bucket list.** Since 2026-10-07,
on Alexandru's instruction: the map's club sheet and the Ticket info tab
show no sale date - no "Next window" line, no window's "Typically opens"
or past-cycle line - and the Bucket list tab and its calendar are the
only place one is drawn. Sale phases, rules and prices stay on the sheet
and Ticket info, and every data file is unchanged. **A hand-written dated
sale or deadline entry** (a `ticketEvents` entry of `football-rules.json`
with a date) **needs a source URL (`source`) and a `checkedOn` date**, and
**nothing fetches or verifies them automatically**.
`tools/check_sale_dates.py` lists, offline and as warnings only (it always
exits 0), the dated entries missing either field, those whose date passed
more than 14 days ago, and those whose `checkedOn` is over 30 days old
while the date is still ahead; `build-calendars.yml` runs it. Existing
entries have neither field yet: the warnings are the to-do list, and no
value was filled in for them (rules 1 and 2).

---

## dateSource

Replaces an older `confirmed` boolean. Three values, used in
`football-rules.json` and `fixtures-manual.csv`:

| value | meaning | behaviour |
|---|---|---|
| `confirmed` | from a published source | normal calendar event |
| `inferred` | reasoned from a known pattern; right season, possibly wrong by days or weeks | emits with a `[?]` prefix and an alarm saying "check whether this has been announced" |
| `disputed` | may be the wrong year or the wrong event entirely | never emits; listed in `skipped.md` only |

The distinction is imprecision versus possible nonsense. An entry whose
date might be eleven years old is `disputed` and stays out of the
calendar entirely — a `[?]` prefix is not enough, because anything inside
a subscribed calendar reads as a schedule regardless of its description.

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
  instruction too.
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
  "Asteras Tripolis B" (also on his instruction). **A link is a hand-written identity claim** - the same kind of
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
  existing data**, each line's note saying how: 13 club lines for 12
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
- `data/clubs/roster-review.csv` — one row per club per division, with
  a verdict saying whether the club is on the map, and if not, **which
  kind of missing** it is

### Code

- `index.html` — the whole app. Single file, no framework, Leaflet from
  a copy in `vendor/` (from the unpkg CDN until 2026-10-02), four tabs: map, bucket list, ticket info and,
  since 2026-10-04, **Me** (memberships and tickets held, kept on the device only - Conventions, "The Me tab").
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
  any club on the map is not drawn at z9**, the tier-3 threshold; also
  that tiers 1 and 2 keep z0 and z7, that `minZoom` is 3 and `zoomDelta`
  and `zoomSnap` are 1 (read from the live map, and the + button moves
  exactly one level), that every `data/clubs/??.json` is in
  `COUNTRY_FILES`, and that every club in those files with a position
  and a tier is on the map. It then **measures, and does not judge**, the
  redraw at z9 over the Ruhr, northern Italy and Bucharest with the CPU
  slowed 4x, beside the old rule, and prints the numbers.
- `tools/test_search.js` — added 2026-10-03: the club search at 390x844
  with the keyboard stood in for by shrinking the window to 390x500 (see
  its Conventions entry for what that does and does not cover).
- `tools/test_coverage.js` — added 2026-10-03: the coverage panel,
  checked against counts the test makes from the club files itself.
- `tools/test_sheet_tickets.js` — added 2026-10-03: the sheet's ticket
  section for VfB, KSC, Kaiserslautern, Kickers, Poli, UTA, Bayern,
  Nürnberg and Inter, checked against the files: each source shown
  exactly when it exists and labelled, every text field of a notes entry
  on the sheet as written, the Next window line naming only that club's
  own entries, never a disputed one, always labelled, and never an
  estimate to the day.
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
- `tools/test_me.js` — added 2026-10-04: the Me tab at 390x844, the clock
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
  site. 83 checks.
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
- `tools/check_sale_dates.py` — added 2026-10-07 (rule 8): offline, warnings
  only, always exits 0. Lists dated `ticketEvents` entries missing `source` or
  `checkedOn`, dates passed more than 14 days ago, and `checkedOn` over 30 days
  old with the date still ahead. Run by `build-calendars.yml`. Never writes.
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
  pinned, not added to the repo. **Every Stadia request in all three is
  stubbed**, so a run spends no credit and does not show that Stadia
  itself answers; that was checked separately (Secrets).
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

---

## Conventions the tools rely on

**Determinism.** `build_calendars.py` produces byte-identical output when
nothing has changed, using `.stamps.json` to freeze `DTSTAMP` and bump
`SEQUENCE` only on real changes. Without this the daily cron commits a
diff every morning and every calendar client re-syncs every event
forever. Do not break this.

**Read-back.** Anything parsed from a hand-written file is printed back
in the run summary exactly as understood, with line numbers for rejected
rows. Alexandru cannot read the code, so this is how he verifies that
what went in is what he meant.

**Failure is visible.** Use `set -o pipefail` in workflow steps that pipe
to `tee`, or a crashing script shows a green tick. This has already
caused one silent failure.

**A comma inside a hand-written CSV cell has to be quoted.** `note` is
the usual victim: `a, b` is two cells, not one, and the second one falls
off the end of the row. Every reader in `tools/` now rejects a row that
has more values than the header has columns and prints the line number,
instead of throwing the overflow away without a word — which is what cut
two notes in half before anyone noticed. Wrap the whole cell in double
quotes, `"a, b"`, and the comma survives.

**A cell reading `<clear>` deletes a fetched value; an empty cell does
not.** The rule of `clubs-manual.csv` is that only the cells you fill in
are changed, so an empty cell says *leave what Wikidata gave us alone*.
That is right for almost every correction and useless for the one case
that matters most: a value that is known to be wrong when nobody yet
knows the right one. Left empty, the wrong value stays on the map,
looking exactly like a checked fact.

`<clear>` in a cell removes what was fetched and puts nothing in its
place. Angle brackets, because "none" and "unknown" could one day be
somebody's real note and `<clear>` cannot be anybody's ground.

- Only **`venue`, `capacity`, `lat` and `lon`** can be cleared — the
  four cells that can hold a fetched value.
- `name`, `clubQid` and `country` are refused: they are how a row finds
  the club it is correcting, not something the club has.
- `tier` is refused, and the message says what to use instead. A club
  with no tier is off the map but still in the file, which is not what
  clearing means anywhere else — `skip` is the way to remove a club.
- `ticketUrl`, `source` and `note` are refused: nothing fetches them,
  so emptying the cell already does the whole job.
- Clearing a position needs `<clear>` in **both** `lat` and `lon`. Half
  a coordinate is not "no position", it is a broken one, and a broken
  one is what gets drawn somewhere wrong. One half alone is refused and
  both cells are left as they were.

A club left without coordinates **drops off the map entirely**, exactly
as if no source had ever placed it — not at 0,0, not at a
half-coordinate, not anywhere. Both gates that decide this used to ask
for a latitude alone, which was safe only while "Wikidata supplied
neither" was the only way to have no position; `fetch_clubs.py` and
`index.html` now both ask for latitude **and** longitude. And because a
club vanishing from a count is exactly the kind of silent change this
project does not allow, the run summary names every club that left the
map this way and says how to bring it back.

**A preferred-rank "no league" statement is read through ONLY where a
roster says the club is playing, and reading through it settles
visibility, never tier.** Built 2026-09-20. `CLUB_QUERY` joins on
`wdt:P118`, which yields the preferred-rank statements if an item has
any and the normal-rank ones otherwise — so one preferred statement
asserting **no league** (Wikidata's `<novalue>`, or a `<somevalue>`)
suppresses every true league tag underneath it and the club never
reaches the map at all.

**Three conditions, all required**, and the first two are in the query
so that nothing downstream can forget them:

1. **The suppression is a preferred-rank statement asserting no
   league, and the tags read through are NORMAL rank.** A **deprecated**
   statement stays exactly as invisible as it always was. Deprecated
   means somebody looked at that statement and marked it wrong, and
   reading through it is how a club gets put in a league it left in
   1994 — the failure `league-tiers.csv` and the truthy join exist to
   prevent. FC Augsburg `Q15755` is the deprecated shape and this rule
   does not touch it.
2. **No dissolution evidence** — the same `P576` gate `CLUB_QUERY`
   already applies. A `<novalue>` on a club that **folded is correct**,
   not a mistake: the club is in no league because there is no club,
   and the tags underneath it are history. Twelve of the eighteen
   Romanian clubs hidden this way carry a dissolution year, from 1946
   to 2026.
3. **A current-season roster article named in `league-rosters.csv`
   names the club.** This is the condition that makes the rule safe,
   and it is not decoration: **a missing `P576` is not evidence that a
   club is playing**, it means only that nobody has recorded a
   dissolution. A league's own membership list is evidence; an absent
   property is not.

**Since 2026-09-25 the fallback asks a second shape, under exactly
the same three conditions**: a preferred statement naming a
**different, unmapped** league over a mapped one at normal rank — LR
Vicenza's shape, found in the Italy pass. Alexandru's instruction:
the normal-rank Serie B is current, the preferred Serie C is stale,
use the live one. It is `STALE_PREFERRED_FALLBACK_QUERY` in
`fetch_clubs.py`, and the run summary says which shape surfaced each
club. **Condition 3 matters more here than for a `<novalue>`**: a
club relegated last season, with its new lower league correctly
preferred and its old mapped league left at normal rank, has the
Vicenza shape with the ranks the right way round. Only the roster
tells them apart — the relegated club is not in the mapped division's
article, and is left out. A preferred statement naming a league that
**is** mapped is not this shape: the club is on the map already, at
the preferred league's tier, and a wrong tier there is the roster
check's `wrong-tier` and a hand row, as before. If either shape's
query fails, **nothing** is surfaced by either. **And, for both
shapes, a surfaced club whose ordinary-rule tier its roster
contradicts is not drawn** until a hand row in `clubs-manual.csv`
gives it a tier — the roster's tier is never written for it, and a
club is never drawn at a tier its own division contradicts. FC Inter
Sibiu is the case (Known open problems).
**This is not the shape-5 resolution, and the difference matters.**
Augsburg was settled by keeping a *second item* whose own tag is
already truthy; nothing was read through. Vicenza is one item, and
the builder reads *past* its preferred statement. Same outcome — the
live league wins — by a different mechanism with a different risk,
which is why the roster condition is not optional.

**Condition 3 earns its place on a real club rather than a
hypothetical one.** Fotbal Comuna Recea `Q55625920` is **named by the
2026-27 Liga III article** and carries `P576` 2021. Condition 2 stops
it before condition 3 is ever asked, which is the right order: a roster
naming a club is not a reason to put a dissolved one on the map.

**Visibility is not tier, and this is the part that must not drift.**
A surfaced club is tiered by the ordinary rule — the most senior
mapped league its normal-rank statements name — exactly as if the
suppression had never been there. The roster article is evidence that
the club is **playing**; it is not authority for **which division**,
and this project does not write a tier off one English Wikipedia
table. Where the two disagree the run summary says so on its own line,
and the remedy is a hand row in `clubs-manual.csv`. Farul is the
worked example: read through the suppression its tags give **tier 2**,
the Liga I article says **tier 1**, and the 1 on the map is
hand-written with the article in its `source` cell.

**A failed roster fetch surfaces NOTHING and says so loudly.** Reading
"the article did not load" as "no club is confirmed" is the exact shape
of the bug that once reported all 246 roster clubs as missing with a
green tick. Surfacing nothing is also the status quo, so a failed run
leaves the map as it was rather than changing it on no evidence — and
the summary names what is therefore missing from that build.

**What it costs, measured on 2026-09-20 rather than guessed.** The
Romanian fallback query answered in **49.5s**. That is under the query
service's 60-second ceiling and **not by much**, so the run summary
prints the time on every run the way the discovery query already does
— this is the number to watch before it starts failing rather than
after. When it does fail the summary says so and **nothing is
surfaced**, which means a club that only reaches the map this way is
missing from that build; it is named as missing rather than quietly
dropped.

**The roster articles are fetched only after the query has found a
candidate** — verified against the code, not just intended — so a
country with nothing hidden makes no Wikipedia request at all.
Germany should be that country, since its only rank-hidden club is
Augsburg's deprecated shape, which this query does not match. **That
was not read off a run log and is not claimed as a measurement**: what
the logs of both 2026-09-20 runs do show is that no German club was
surfaced and Germany's count was unchanged at 149.

**A pre-existing flakiness to keep separate from this.** The German
**discovery** query — a different query, older than the fallback —
failed on both runs, HTTP 503 after 166.1s and HTTP 502 after 191.1s.
`unmapped-leagues.csv` was correctly left as the last good run left it
both times, which is the review-file guard doing exactly its job. It
is unrelated to the fallback and was already the known behaviour.

**A club the club query cannot see at all reaches the map under its
own Q-id through a hand row - the hand-named fallback, built
2026-09-27.** Written from FC Rapperswil-Jona and FC Stade Nyonnais, at
Alexandru's instruction to fix the roster check's double count
properly. A club promoted into a tracked division whose only league tag
still names the lower league it left carries no mapped tag, so neither
the club query nor either rank shape returns it, and
`apply_manual`'s guard - rightly - refuses a `clubQid` the queries did
not return. Until then the only way onto the map was a hand row with no
`clubQid`, a made-up `MANUAL-` id, and the roster check, which joins on
Q-ids, reported one club as two errors on every run.

The fix is the one the Farul case already taught: **make the club be
there**, then correct it with an ordinary row. `hand_named_fallback()`
in `fetch_clubs.py` takes as candidates exactly the Q-ids a hand row
names - with this country and a numeric tier - that no query returned,
and holds them to the novalue fallback's three conditions:

1. **a hand row names it with a tier.** The tier is the hand row's,
   never the roster's and never Wikidata's; where it disagrees with
   the roster's the summary says so and the hand row still wins.
2. **Wikidata has the item, it is not a person and it has no `P576`**,
   asked as flags rather than filters so each left-out candidate is
   named with its reason - no such item (a typo), a person, dissolved.
3. **a tracked 2026-27 roster names it** - by the sitelink hop, or by a
   hand link in `data/roster-links-manual.csv` for a row the reader
   refuses. This is what makes a typing mistake in `clubQid` harmless:
   a mistyped Q-id is not in a division's membership list.

Then `apply_manual` corrects the surfaced club like any other, guard
unchanged. **A failed roster read or a failed query surfaces nothing,
and says so** - the same rule as the novalue fallback, with the same
cost: a club that only reaches the map this way (Rapperswil-Jona,
Nyonnais, the seven Austrian additions, seven Serbian ones) is missing
from a build whose roster read failed, and is named as missing. One
roster read per country per run is shared by both fallbacks, so the
second never asks again or gets a different answer.

**A failed fetch never rewrites a review file.** `capacity-review.csv`
and `coordinate-review.csv` are evidence waiting to be judged, and the
cron commits whatever it finds. If Overpass or Wikidata does not answer,
the run has only part of the picture — a country missing, or rows reading
"not checked" — and writing that would delete work nobody has acted on
yet, with a green tick. So when anything did not come back, the file is
left exactly as the last good run left it and the summary says so:
"Overpass unreachable, review file unchanged from the last successful
run." The first run is the one exception: with no file there is nothing
to protect, so a partial list is written and labelled as partial.

**`coordinate-review.csv` is decided country by country, since
2026-09-26.** The rule above is unchanged in strictness and applied per
country instead of per run: a country whose answer came back complete
replaces **its own** rows; a country with anything missing keeps its
rows exactly as its last good run left them, byte for byte, and the
summary prints `WRITTEN` or `UNCHANGED` against every country. Until
then one country's failed step threw away every country's answer — run
#9 discarded complete German, French and Italian results because
Romania's pitch lookup did not come back. The first-run exception
still applies to the whole file only: an incomplete country is never
written into an existing file, even one that holds no rows for it yet.
**A green tick still does not mean every country is current** — read
the per-country lines.

**`capacity-review.csv` follows the same per-country rule since
2026-09-30**, at Alexandru's instruction, after six runs in two days each
lost a different country to Overpass 504s and so wrote nothing at all. A
country Overpass answered for replaces its own rows; one it did not
answer for keeps its rows byte for byte; the summary says `WRITTEN` or
`UNCHANGED` against each. Same first-run exception, whole file only.

`unmapped-leagues.csv` now follows the same rule. It is read from and
pasted out of exactly like a review file, and it used to be rewritten
unconditionally — so a run where one country's league discovery failed
replaced the whole seed list with the other country's half, with a green
tick. It now keeps the last good file and says which country was
missing.

**Past dates drop out of calendars but stay in the JSON.** The file is
the history and the anchor for next year's estimate; the calendar is only
what lies ahead.

**A bot-management 403 is a stop. The Internet Archive is not a way
round it — it is a different source, and that is standing policy, not a
judgment made once for one club.**

When a live site refuses this infrastructure with a bot-management 403 —
Akamai, Cloudflare and their like — that is an access control the site
operator deliberately put up. It is not retried until it gives way and
it is **not worked around**: no rotating user agents, no residential
proxies, no TLS fingerprint spoofing. `fcbayern.com` is the case this
was written from and the rule is not about Bayern.

Reading the **same page from the Internet Archive is allowed**, and it
is the same category of source this project already leans on when it
cites a news article or a search result that quotes the club: **a third
party's own public record.** It does not touch the refusing server, it
does not pretend to be a client that server would accept, and it takes
nothing the archive is not already handing to anybody who asks. The
block is on the club's server; the archive is not the club's server. So
an archive read is not a smaller version of the thing that was refused,
it is a different thing — and treating it as a loophole would get the
reasoning exactly backwards.

**What it is not is a route around the block.** If the archive has no
capture, the page stays unread, and that is the answer rather than a
reason to go back at the live site harder.
`/de/tickets/info/anfragen-fuer-die-neue-saison-2026-2027` has no
snapshot, so it is unread and will probably stay unread.

**Two things every archive-sourced row carries.** The **original URL**
goes in `source`, because that is where Alexandru verifies it in an
ordinary browser, where the page opens normally. The **capture date**
goes in the note, because an archived page is the page as it stood on a
day, not as it stands now — a figure read from a 2025-09-02 capture is a
fact about 2025-09-02, which is exactly how the Bundesliga price rows
ended up correctly labelled `2025-26` instead of `2026-27`.

The same holds for every other third-party record this project uses: a
search result quoting the club, a ticket reseller's page, a news report.
They are evidence about what the club said. They are never the club
saying it, and a row says which of the two it rests on.

**The ticket files hold rules, not dates.** Rule 1 says never generate a
ticket rule, sale date, application window or deadline. The three ticket
files are built so that obeying it is the path of least resistance.

`club-tickets.csv` has no date column at all. `cutoff` says whether the
club states a deadline (`stated`, `none`, `unknown`) and never when it
falls; a specific match's actual deadline belongs in
`football-rules.json` or `fixtures-manual.csv`, hand-written, as it
always did. `closesEarly` says whether the window can shut before that
stated deadline, which for a club like Bayern is the fact that actually
decides whether you get in.

`club-ticket-windows.csv` is the one place an estimate may live, and it
is a *pattern*, not a deadline: "Bundesliga home and away requests have
opened in late June in past cycles" is a different kind of claim from
"requests close on 17 August". It estimates a future window from a past
one and it never states a past window as fact without a source.

Every window row carries two provenance columns, because `dateSource`
alone cannot say what a reader needs to know:

| column | what it answers |
|---|---|
| `dateSource` | how much to trust the date — `confirmed`, `inferred`, `disputed`, exactly as in `football-rules.json` |
| `basis` | where the pattern came from — `published`, `observed-past-cycle`, `user-supplied`, `unknown` |

`inferred` plus `basis` `user-supplied` is the honest combination for an
estimate Alexandru supplied that no source has confirmed. It is not the
same as `inferred` plus `observed-past-cycle`, which is an estimate
reasoned from a past window somebody actually read. Collapsing the two
into one column would lose exactly the distinction that matters, which
is why there are two.

`pastCycle` holds the past window the estimate reasons from, and it is
blank unless a source says so. A blank `pastCycle` beside a filled
`opensEstimate` is the file admitting that the pattern rests on nothing
written down — which is a thing the file is allowed to say, and says out
loud, rather than quietly inventing a past window to justify a future
one.

`opensEstimate` is deliberately **loose text** — `late June`, `after the
UCL draw` — not a date. There is no format that makes "late June" into a
day, and rounding it to one would be the exact failure rule 1 exists to
prevent. `estimateFor` says which cycle the estimate is about, because
"late June" alone means nothing.

**A price is a fact about a season, and observed is not stated.**
`club-ticket-prices.csv` carries `season` on every row, because a face
value without a season is a wrong number waiting to happen. `kind`
separates `face-value` — what the club publishes — from
`resale-observed`, a price somebody actually saw once. An observation is
never written as though the club had stated it, and `priceBasis` records
whether a figure is before or after VAT and fees, because German clubs
quote both and the difference is real money.

`priceBasis` has **four** values, and the fourth was added on
2026-09-19 because the three before it could not say what was true of
every Bayern face value in the file. A German consumer price **includes
VAT by law** — the Preisangabenverordnung requires it — so
`excl-vat-fees` was simply wrong on a figure copied off the club's
consumer-facing price page. But the club adds a 1 EUR
Vorverkaufsgebühr and 2–8 EUR Systemgebühren **on top** at checkout, so
`incl-vat-fees` is wrong in the other direction. `incl-vat-excl-fees`
is the honest one: **VAT in, booking fees out.** That is what a German
consumer price page quotes, so expect it to be the common value rather
than the exotic one.

`unknown` is not a worse answer than a wrong one. The DFB-Pokal rows
carry it because nothing has ever been read for them, and inheriting a
basis from the Bundesliga rows beside them would be a guess wearing a
checked fact's clothes — which is how `excl-vat-fees` got onto them in
the first place.

**The three ticket files are read back and checked, and the checker has
two kinds of vocabulary on purpose.** `tools/check_tickets.py` is the
reader this project went without for as long as the files existed. It
reads all three, prints every accepted row back exactly as understood,
and names every rejected row with its line number. It never writes to
any of the three, and it exits 1 when it finds a problem, because a
green tick over a file with a rejected row in it is the same failure
`set -o pipefail` was added elsewhere to prevent.
`.github/workflows/check-tickets.yml` runs it on a push that touches one
of the files — with the same caveat as `build-clubs.yml`, that the
`paths` filter only applies to pushes on `main`, so an edit on a working
branch still needs a `workflow_dispatch`.

**Closed vocabularies are the ones this file actually lists**, and a
value outside them rejects the row: `dateSource`, `basis`, `cutoff`,
`kind`, `priceBasis`, since 2026-09-23 `confidence`, `scope` and
`urlComplete`, and since 2026-09-24 `clubLatitude`.

**Open vocabularies are every other controlled column** — `access`,
`salesModel`, `requestTypes`, `closesEarly`, `demand`, `resale`, `team`,
`window`, `competition`, `stage`, `category`, `placeType`,
`opponentTier`, and since 2026-09-23 `updateTracking`,
`minorEligibility`, `priceClass`, `eligibility`, `topic`, `outcome` and
`publisherKind`, and since 2026-09-24 `authorityKind` and `condition`
(both `;`-lists, checked token by token). The country file's `topic`
is **the same list** as the rules file's, not a copy: layering
matches on topic, and two lists would drift apart. Nobody has written down what their allowed values are,
because there is one club in the file and whatever Bayern needed is all
that exists. A closed list
for them would reject the first legitimate value a second club needs, so
the tool holds the values currently in use, **reports** anything new and
**keeps the row**. A typo is by definition a new value, so it is still
caught; a real new value is caught too, and the remedy is to add it to
`KNOWN` in the tool, which is a deliberate edit rather than a silent
one. The lists are seeded from the FC Bayern rows and from nothing else,
and the tool says so.

**It enforces rule 1 rather than describing it.** No cell that states a
rule may hold a day-level date, and `opensEstimate` above all: `late
June` passes, `30 June` and `2027-06-30` do not. A month is a pattern, a
day is a deadline, and the line between them is the whole reason
`opensEstimate` is loose text. `estimateFor` and `season` must be cycles
like `2027-28`. The overflow guard from `fetch_clubs.py` is here too, so
an unquoted comma is named with its line number instead of truncating a
note. `checked` must be an ISO date; a future one is reported.

**The price file's key has been one column short twice, and both times
the file already held the proof.** This is worth keeping as a shape
rather than as two anecdotes: a key gap does not announce itself, it
shows up as a row that looks like a duplicate of a row it is not.

**`kind` was the first**, found by the checker on its first run. The
file was described as one row per club per team per season per
competition per stage per category, and FC Bayern had both a
`face-value` row and a `resale-observed` row for the same Bundesliga
category 1 seat. Two different facts about one seat, both belonging in
the file.

**`opponentTier` was the second**, found on 2026-09-19 when the
Champions League prices were written out properly. The club's own price
page carries **two league-phase tables side by side** — one for the
strongest visitor, one for everybody else — same competition, same
stage, same categories, different prices. Without the column the second
table is not a second fact, it is a duplicate key, and the checker
throws away whichever table was written second. Verified rather than
assumed: with `opponentTier` taken back out of the key, the checker
rejects five rows and exits 1.

So the key is club, team, season, competition, stage, category,
**`kind`** and **`opponentTier`**. A blank `opponentTier` means the club
publishes one price for that row's stage, which is the ordinary case —
the Bundesliga and DFB-Pokal rows all leave it empty.

**The tier label is ours, not the club's.** Bayern names the visitors
in its table headings; it publishes no tier scheme, and nothing read
says which table a future opponent would fall into. `top-opponent` and
`standard-opponent` describe what two tables did in one season. They are
not a rule for predicting the next one, and they must not quietly become
one.

A repeated `resale-observed` row is **reported, not rejected** — two
sightings of one category at two prices is a real thing, and a file that
records observations has to be able to hold more than one. A repeated
`face-value` row is rejected: a category has one published price.

**The derby PDF extended the ticket schema, 2026-09-23, and every
extension was forced by something the PDF held that the three files
could not.** The source is *Derby ticket rule set, compiled 23 Sep 2026*
(1. FC Nürnberg v Greuther Fürth, Inter v AC Milan), supplied by
Alexandru and read directly, not from a retyped summary. Every one of
its 47 numbered items, N-1 to N-22 and I-1 to I-25, is carried in some
file with its number in `ref`, so any row can be traced back to the
page it came from.

| what the PDF had | why the old files could not hold it | where it went |
|---|---|---|
| several sale phases in order, each with its own past date | one window row holds one `opensEstimate` | `club-ticket-phases.csv` |
| derby rules layered over the club's general ones | `club-tickets.csv` is one row per club, no fixture | `club-ticket-rules.csv`, `scope` + `opponentQid` |
| a confidence tag on **each** fact | the old files carry confidence per row, in prose | `confidence` column |
| a source list, 32 citations with titles and dates | `source` is a bare URL list | `ticket-sources.csv` + `sourceRefs` |
| resale platform and price-cap **rules** | `resale-observed` is one price somebody saw | rules rows, topics `resale-platform`, `resale-price-cap` |
| sell-outs across several seasons | `demand` is one word per club | `club-ticket-demand.csv` |
| a normal and a member price for one seat | the price key had no column for it | `priceClass` in the price key |
| a price given as a range, 420–440 | `price` holds one number | `priceMax`; nothing picks a point |

**The confidence mapping, applied exactly and not reinterpreted:**
`[VERIFIED]` → `confirmed` with `basis` `published`; `[INFERENCE]` →
`inferred` with `basis` `observed-past-cycle`; `[UNVERIFIED]` →
`unverified` with `basis` `unknown`, **kept and flagged** rather than
dropped. `confidence` is a new column and deliberately **not** a
fourth `dateSource` value: `dateSource` decides what a calendar does
with a date, and `confidence` decides nothing — it only says how sure
anybody is. `unverified` is also not `disputed`: disputed is "possibly
the wrong year or the wrong event", unverified is "somebody looked and
could not confirm it". The checker prints every `unverified` row in one
list so an honest gap cannot hide inside a long read-back.
**One item fits the mapping badly and was mapped anyway**: N-14 (the
derby is probably price category A) is reasoned from the club's labels
for two *other* 2026-27 fixtures, not from a past cycle, so its
`observed-past-cycle` is the mapping's word and not a description. Its
note says so. **One table carries no tag at all**: the Inter sale
sequence. Its phases are marked `confirmed` because its only sources
are the club's own pages — a judgement made on 2026-09-23, not the PDF's
tag, and every row of it says so.

**Layering.** A `derby-home` row in `club-ticket-rules.csv` replaces the
club's `general` rows **on the same topic, for that fixture only**; a
topic the derby does not mention falls through to the general rule.
Inter's derby transfer rule (I-16) overrides its general one (I-2) and
nothing else. A **`derby-away` row does not fall through at all**: a
club's general rows describe its own home sales, and at the other
club's ground the other club's rules apply. The checker prints the
merged result for each derby, so nobody has to do the merge by eye.

**Rule 1 still holds, and the phases file is how.** The PDF's exact
per-phase dates are all **past** — the 2025-26 Inter derby, the December
2025 Frankenderby, the 2026-27 Wolfsburg home game — and they live in
`pastCycle`, which was always the place for a sourced past window. No
2026-27 sale date exists in the PDF, because neither club had
announced one, and none was written. The only forward-looking cells are
two month-level estimates in `opensEstimate`: `late November or early
December` for Nürnberg (N-19) and `early to mid January` for Inter
(I-9), both `inferred`. The fixture dates were **not** written to the
ticket files either; they belong in `football-rules.json`, which no
tool writes.

**The price key was one column short a third time.** Before
`priceClass` existed the checker rejected nine Nürnberg member rows as
duplicates of the normal rows beside them. Same shape as `kind` and
`opponentTier`: the file already held the proof. The key is now club,
team, season, competition, stage, category, `kind`, `opponentTier`,
`priceClass`, `scope`, `opponentQid`. Nürnberg's `category-a` and
`category-b` are **the club's own** Preiskategorie labels, unlike
Bayern's `top-opponent` / `standard-opponent`, which are ours.

**A citation the source document cut short is recorded as cut short.**
Three goal.com/Calciomercato URLs are printed with `…` in the middle in
the PDF itself, one cross-check is a bare domain, and one SSC Napoli URL
carries a probable HTML-entity artefact (`&root;=3448`). All five are
kept exactly as printed, marked in `urlComplete`, and reported on every
run. None is reconstructed. The checker splits a `source` list only at a
`;` followed by the next `http`, so a URL that itself contains a `;`
survives.

**The two standing fields.** `club-tickets.csv` gained
`updateTracking` — how the club announces a sale, as tokens
(`newsletter;per-match-article` for Nürnberg,
`notify-button;news-section` for Inter) — and `minorEligibility`,
whether an under-18 can buy. **Nürnberg's `minorEligibility` is
`unknown`, and that is the finding, not a gap left by accident**: the
PDF established that minors can be members from 7 and that child rates
exist, neither of which says a U18 may buy. Inter's is
`via-guardian-account` (I-13: a profile can link the cards of minors
the holder is responsible for). Bayern's two cells are blank and
reported blank on every run. `football-rules.json` has its own
`ageRules.minAgeToBuy` for each club; the two were not reconciled.

**A contested figure is written down whole: every number, every source,
and which one is in use.** Added 2026-09-20, when a third capacity source
turned one disagreement into a three-way one and there was no shape for
recording it.

UTA Arad is the case it was written from and is the template. The map
held Wikidata's **7,287**. StadiumDB says **12,584**. Romania's own
Superliga site and Romanian Wikipedia say **11,500**, and English
Wikipedia's Liga I stadiums table agrees with them. The row in
`clubs-manual.csv` now reads 11,500 — and its note names all three
figures, says where each came from, and says which is in use:

> CONTESTED CAPACITY. In use: 11500 (Romania's own Superliga site and
> Romanian Wikipedia, and the English Wikipedia Liga I stadiums table
> agrees). Not taken: 12584 (StadiumDB…); 7287 (Wikidata, which the map
> held until now). Every figure is written down on purpose — the one not
> in use is recorded rather than dropped, so nobody has to rediscover
> the disagreement.

**Dropping the figure you did not take is the failure this prevents.**
A row that says only "11500" looks like a checked fact with no history,
and the next person to see 12,584 somewhere has no way to know it was
already weighed and set aside. Six months on, that is indistinguishable
from nobody having looked.

**The rule for choosing, stated so it is applied the same way twice.**
Where two independent sources agree within the 5% band and the map's
figure sits outside it, the map's figure is the outlier and is replaced.
Which of the two agreeing figures is taken: **the league's own current
season stadium table on Wikipedia**, because its coverage is that season
by construction — and where there is no such table, whichever figure a
second source corroborates. Where the sources do **not** agree with each
other, nothing is changed and the row stays contested. FC Botoșani is
that case: 12,000 on the map, 8,500 from StadiumDB, 7,782 from
Wikipedia, no two of them within the band, so it is still contested and
says so.

**A country's club file is that country's league pyramid, not its
territory — and a club based across the border is a real exception,
not a bug.** Written 2026-09-25 from AS Monaco (`Q180305`), and framed
this way on purpose. Its `P17` is Monaco and its ground is in Monaco,
so the country check in `fetch_clubs.py` flags it on every run; it is
in `FR.json` because it plays in Ligue 1, which is exactly what that
file is for. The flag is the check **working**: it says "this club is
not in France", which is true, and the reason it is still right is
something only a person can supply. A note-only row in
`clubs-manual.csv` records that, so the flag is read once and not
rediscovered.
**It is not a pattern to hunt for and it must not be "fixed" in
either direction.** Do not remove Monaco, do not move it to a file of
its own, do not change its `P17`-derived country, and do not widen
`COUNTRY_BOX` so the flag goes quiet — a box that swallows Monaco
swallows everything else within the same distance of the border.
The difference from SC Veltheim and FC Triesenberg is the whole point:
those two were flagged because a **wrong** league tag put them on a
German map; Monaco is flagged because a **right** one put it on a
French one. Same signal, opposite meaning, and only the roster can
tell them apart — Monaco is in the 2026–27 Ligue 1 article, Veltheim
and Triesenberg were in no German one.
The same shape exists elsewhere in football (Welsh clubs in the
English pyramid, Liechtenstein's in the Swiss one). **The second one
arrived on 2026-09-26: FC Vaduz `Q216773`**, `P17` Liechtenstein, in
`CH.json` because it plays in the Swiss Super League, which the complete
2026–27 article confirms. It has its note-only row, the Monaco way. If
another arrives, it gets the same, only after the division's own article
confirms it plays there.

**Fixture teams are joined to map clubs once, in a file, and never by
the page.** Built 2026-09-25. Neither football-data.org nor OpenLigaDB
publishes a Wikidata id, so `link_fixtures.py` matches by name, with
the lessons of the StadiumDB and roster work applied:

- **Equality, not containment.** Both sources give full names, so after
  legal forms (`FC`, `SV`, `TSG`, from the StadiumDB matcher's own list,
  imported rather than copied) and founding years are set aside, the
  remaining words must be the same words. Containment would put
  "1. FC Köln" inside "Fortuna Köln".
- **A dotted initialism is one word**, since 2026-09-30: "F.C." is
  "FC", "A.F.C." is "AFC". The shared fold in `crosscheck_stadiumdb.py`
  used to turn the dots into spaces, so "Arsenal F.C." could never equal
  "Arsenal FC" and 43 of 44 English clubs linked to nothing. Only runs of
  single letters each followed by a dot are joined; "St. Pauli" and
  "1. FC" are untouched. Measured before it went in: no club outside
  England gained, lost or changed a fixture link, and no StadiumDB review
  row outside England changed.
- **The reserve marker must agree on both sides.** `II`, `U23`, the Dutch
  prefix `Jong` (added 2026-10-01, when the matcher paired "Jong AZ" with
  AZ's own stadium) and the rest. This refused **SSV Jeddeloh II**, and that is worth knowing:
  Jeddeloh II is a *village*, not a reserve side, and the club is very
  likely the map's `Q2207914` SSV Jeddeloh. The guard is right to
  refuse — a hand row is the remedy, not a looser rule.
- **A legal form or year may be absent, never different.**
- **A short name counts only with two words or more.**
- **A team's country comes from its competition, never its name.** A
  team seen only in the Champions League has no country here and is
  never linked; a would-be match goes to the review file.
- **Ambiguity links nothing.** A name matching two clubs, or a club
  matched by two teams of one source, is reported. A venue may settle
  it only when OpenLigaDB records a ground and exactly one candidate's
  agrees, and the link then says `name+venue`. A disagreeing venue
  never breaks a name match — sponsors again — it is reported.

**First run, 2026-09-25: 75 of 212 map clubs linked.** All 18
Bundesliga clubs (football-data.org for the league and Champions
League, OpenLigaDB for the Pokal), all 18 of the 2. Bundesliga, 18 of
the 3. Liga's 20, and 21 at tier 4 — the Regionalliga Nord and Nordost
plus DFB-Pokal sides. **No Romanian club**, because neither source
carries a Romanian competition, and that is the expected state.
Two 3. Liga clubs are **ambiguous by OpenLigaDB's own doing**: it gives
1. FC Saarbrücken ids 417 (3. Liga) and 3078 (Pokal), and Würzburger
Kickers 398 and 5276. Same name, same country, two ids, so nothing was
linked and a pair of `link` rows would settle each. "1. FC Lok
Leipzig" is not matched to "1. FC Lokomotive Leipzig" — an abbreviation
is not an equality, and the review file lists it as a pointer.

**Ticket info joins by `clubQid`**, which is exact, so no name is
matched for it. `FC Bayern München II` cannot pick up Bayern's rows
because it is a different Q-id. Inter `Q631` has ticket rows and,
since Italy was mapped on 2026-09-25, **is on the map under the same
Q-id** — the read-back says so, and reports only that the two files
label it differently ("FC Inter" against "FC Internazionale Milano").

**The club sheet does not trust the club file's `competition` field.**
Until 2026-09-25 `fetch_clubs.py` filled it, for a club whose own tags
did not name a league at its tier, with the **first** league mapped at
that tier — which put Wacker Burghausen, Hallescher FC, VfB Lübeck,
Werder Bremen II, SSV Ulm 1846 and 1. FSV Mainz 05 II in the
"Regionalliga Suedwest", a guess dressed as a fact. The fallback now
fires only when the country maps exactly one league at that tier, and
the sheet applies the same rule itself from `league-tiers.csv`, so it
is right before the next rebuild and stays right if the field drifts.

**Six feeds plus admin**: `bayern`, `germany-nt`, `local`, `italy`,
`romania`, `uefa-finals`, `admin`. `local` means within day-trip range of
Leonberg, not a fixed list of clubs. `bayern` is a loyalty feed and stays
separate even though Munich is also day-trip range. Hand-entered fixtures
go to `fixtures-<feed>.ics`, never into the ticket-window feeds.

**StadiumDB is matched by NAME because it has no coordinates, so it
needs two signals to agree.** `crosscheck_capacity.py` matches a club to
a ground **by position, within 500m, deliberately not by name**, because
name matching is what scored Eutin 08 against FC 08 Homburg on a shared
"08". StadiumDB publishes no coordinate on any page — checked across 27
pages in nine countries — so that matcher cannot be reused and name
matching is all there is.

Worse, the name StadiumDB publishes is a **short** one. A country page is
`Name | City | Clubs | Capacity`, and the Clubs cell holds "Borussia",
not "Borussia Dortmund"; "Bayern", not "FC Bayern München". The city is
carrying half the club's identity. And the short name is not unique:
"Borussia" appears against Dortmund, Mönchengladbach **and** Neunkirchen.

So a match needs two signals, and the review file says which two agreed:

1. **The club signal.** Every word of StadiumDB's short name must appear
   in our club's name. Containment, not equality, because the short name
   is by design a fragment of the long one.
2. **The place signal**, which is what stops "Borussia" matching three
   clubs. Either StadiumDB's city appears in our club's name, **or** our
   ground name and theirs agree. One or the other, not both, because the
   city column is in English — Munich, Cologne, Nuremberg — and our names
   are not, so requiring the city would throw away every club in a city
   with an English exonym.

**Three guards were each added because the matcher got something wrong
without them**, and they are worth keeping as shapes rather than as
anecdotes:

- **The reserve marker has to match on both sides.** StadiumDB lists
  "Borussia" and "Borussia II" as two grounds. Without this, every
  reserve side in the file matched its first team's stadium and took on
  a capacity ten times too big — Borussia Dortmund II against the Signal
  Iduna Park.
- **A short name that is only the town names that town's main club and
  nobody else.** StadiumDB writes VfL Wolfsburg as "Wolfsburg", and
  "Wolfsburg" is inside "Lupo Martini Wolfsburg" too. Where the short
  name says nothing but the town, our club may say nothing beyond the
  town either, bar its legal form and a founding year.
- **The place signal may not cross the country.** "AFC Metalul Buzău"
  matched the "Stadionul Metalul" in **Aiud**, 300km away, on the ground
  name alone, because both grounds are named after the same works. If
  our club's own name carries a town, the ground has to be in that town;
  where it carries none, as German club names mostly do not, the rule
  does not apply.

**Ground names disagreeing does not mean the grounds are different.**
Half the German ones in the file are a sponsor's name against the old
one — the Uhlsport Park is the Sportpark Unterhaching. So when the names
clash the **figures get a say in the verdict**: agreeing figures read as
one ground under two names, disagreeing figures as a real question about
which ground each source means. Neither claims more than it knows.

**Distance** is straight-line times `settings.estimateMultiplier` (1.25).
No routing API. It is a road-distance estimate and is deliberately not
converted into a travel time, because that would need an invented average
speed. **That is still true of every distance on the club sheet, the
shared-ground popup and the bucket list.** The route panel (next entry)
is the one place a routed distance and a travel time appear, and both
are Stadia Maps' own figures for the route it returned, labelled as such.

**Routes: one request for the road, everything else worked out in the
browser.** Built 2026-10-02. The route panel asks Stadia Maps' Standard
Routing API **once** per route (`POST api.stadiamaps.com/route/v1`,
`costing: auto`, no turn-by-turn text) and draws the line it returns.
Which clubs are near it is computed in `index.html` from that line - the
straight-line distance from each club's ground to the nearest point of
the line, and how far along the route that point is - so the distance
slider and the date filter cost no request at all, and no request is
made per club. The listed distance is **from the ground to the road
line, straight**, not a drive, and the list says so.
- **A typed place costs one request**, Stadia's forward geocoding
  (`/geocoding/v1/search`), on pressing Find, never per keystroke.
  Autocomplete v2 is cheaper per call (1 credit) but returns **no
  coordinates** - measured on 2026-10-02, `geometry: null` on every
  result - and its Place Lookup costs 20 per place, so it would cost
  more, not less. Tapping the map or using home costs nothing.
- **The date filter never hides a club on a guess.** A club is left out
  only when one of its linked **league** fixture files (`LEAGUE_CODES` in
  `index.html`: BL1, PL, ELC, PD, SA, FL1, DED, PPL, BSA, bl2, bl3, rln,
  rlno) spans that day and shows no home match for it. A club with no
  fixture source, a club linked only to a cup (Club Brugge to the
  Champions League, many tier-4 clubs to the DFB-Pokal), a club whose
  file did not load, or one with undated home matches is **kept and
  marked** with the reason. A competition code not in the list is
  treated as a cup, so adding one can never quietly hide clubs.
- **A placeholder day, not only a placeholder time.** football-data.org
  puts a whole unscheduled matchday on one day as `SCHEDULED` at 00:00
  UTC - all nine Bundesliga matchday-12 games on Sat 5 Dec 2026, where a
  scheduled matchday runs Friday to Sunday, measured across BL1, PD, SA,
  FL1 and ELC. So the "time not set" match's **day** is provisional too.
  OpenLigaDB has no status, but has the same shape: whole rounds at one
  kickoff (all nine Regionalliga Nord round-12 games at Sun 4 Oct 13:00,
  all nine Nordost round-12 games at Sat 10 Oct 11:00, the last
  matchdays of every league). The filter reads a SCHEDULED match, and an
  OpenLigaDB round where three or more matches share one kickoff, as
  provisional, and keeps a club whose provisional home match is within
  **three days** of the chosen day as "home match, day not fixed". The
  three days are a judgement - a matchday runs Friday to Monday - and it
  errs towards keeping. It also flags a genuinely simultaneous last
  matchday as "may be provisional", which is the cautious way to be
  wrong. The existing "time not set" display is reused as it is.
- **Found on the way, not fixed: the club sheet shows those OpenLigaDB
  round times as real kick-offs.** The sheet's "time not set" test is
  football-data's status, which OpenLigaDB does not have, so a
  Regionalliga round entered at one placeholder time reads as nine
  confirmed 13:00 kick-offs. Nothing proves those are placeholders - a
  round can be simultaneous - so the sheet was left alone; the route
  filter only treats them cautiously.
- **Tested** in headless Chromium at 390x844 (Leaflet from npm, tiles,
  routing and geocoding stubbed, because the sandbox cannot reach
  Stadia): a Leonberg-Munich route listed 13 clubs at 25 km in route
  order and 4 at 5 km; on 31 Oct 2026 Augsburg and Bayern read "home
  match", VfB Stuttgart was left out (BL1 shows it away) and the nine
  clubs with no fixture source stayed, marked; on 5 Dec 2026 Augsburg and
  Bayern read "home match, day not fixed" with "time not set"; a tap on a
  listed club opened its sheet above the panel; tap-to-set worked; the
  page did not scroll sideways; one route request and one search were
  made; no script error; a failed route and an empty search each said
  so. **Not tested against Stadia itself from the page** - the sandbox
  cannot reach it. A route and a search request were made from a GitHub
  runner with the page's key, and both answered with the shapes the code
  reads (`trip.legs[].shape`, polyline6; GeoJSON points), with CORS open
  to any origin. Since 2026-10-03 `tools/test_routes.js` repeats the
  route checks automatically on every change to the page.

**Derbies: every row names its source, and the source names the
derby.** Built 2026-10-03, on Alexandru's instruction, for the twelve
countries on the map. Rule 2 applied to rivalries: a derby a person
"knows" but nothing read names is not written.
- **What counts as a source, decided before any row was written.**
  (a) The derby's **own Wikipedia article** (English, or German where
  English has none), whose opening paragraph or infobox names both clubs
  - checked on a runner by resolving the article's links to Q-ids, not
  by reading the title. (b) An entry in one of Wikipedia's rivalry
  **lists** that gives the derby a **name**, names **both clubs**, and
  carries **its own citation**; the row's note names the cited
  publisher. An unnamed list line ("OFK Belgrade vs Red Star"), an
  uncited one, a table row whose first club is only implied by a merged
  cell, and an overview article ("London derbies", "Basque football
  derbies") were **not used**. Where both exist, the article is the
  source. A club-article sentence was used once, for the Südwestderby,
  and its note says why.
- **Where the rows came from.** Three throwaway probes on a runner
  (removed in the same branch): Wikipedia's list of European club
  rivalries (Austria, Romania, Serbia, Switzerland, Wales), the per-
  country lists (German, French, Italian, Spanish, Belgian, Dutch, Greek;
  **England has none**), Wikidata's rivalry items, and every article in
  each country's rivalry category on English Wikipedia, opening
  paragraph read. Wikidata's query service was rate-limiting to one
  request a minute ("active wdqs outage"), and Wikidata's rivalry items
  list only some participants, so the categories did most of the work.
- **Names are the source's.** A row's name is the derby's name in its
  source, or "A v B" where the source titles it that way. Where one
  entry names three clubs, each pair is its own row with the pair in
  brackets ("Rotterdam derby (Sparta v Excelsior)").
- **`kind` is a judgement, and it is this session's**: `city` for one
  city (Piraeus counted as Athens, as the Greek list does), `regional`
  for a named region or neighbouring towns, `historic` for a national
  rivalry between clubs of different regions. Nothing hangs on it but a
  tag.
- **Scope, Alexandru's answer of 2026-10-03**: one club at tier 1 or 2
  is enough; the other may be lower on the map (VfB v Kickers, tier 4)
  or off it (with `offMap`). **The panel lists a derby only when both
  clubs are on the map**, and a pair in different divisions this season
  - different tier, different country, or two leagues at one tier - is
  flagged "different divisions: cup only", with "Probably not played
  this season" in its detail.
- **Augsburg is joined through `P831`.** Its two rivalry articles link
  the club item `Q15755`; the map draws Augsburg as its men's-team item
  `Q97905916`, whose `P831` is `Q15755` (the shape-5 protection below).
  The rows use `Q97905916` and say so.
- **Distance** is home (settings.home) to the **nearer ground**, the
  club sheet's road estimate (straight line × 1.25), and both grounds'
  distances are shown.
- **Next meeting** is read through `fixture-links.json`, never by name:
  a match counts only when its two teams are the two clubs' linked ids
  **in the same source**. Four honest answers: a dated meeting (with the
  sheet's "time not set" and the route's "may be provisional" for an
  OpenLigaDB round at one kick-off); "<club> has no fixture source";
  "linked to different fixture sources"; "No meeting in the fixture
  data." No hand-entered date - Alexandru said not yet.

**Club search: names only, clubs on the map only.** Built 2026-10-03.
The box at the top right of the map tab matches as you type against the
names of the clubs on the map (`CLUBS`, the clubs with a position and a
tier), never against anything off it. Case, accents and punctuation are
set aside (Unicode NFD with the marks dropped, plus a short hand list for
the letters NFD cannot split: ß, ø, đ, ł, æ, œ, ı, þ, ð), so "timisoara"
finds Știința Poli Timișoara and "munchen" finds FC Bayern München. Every
word typed must be in the name; a name that starts with what was typed
comes first, then one where a word does, then the rest, the senior tier
first within each. At most eight suggestions, each with the club's
country and its competition as the club file records it - "league not
recorded (tier N)" where it records none, never a guess - and a count
of the rest. No match says "No club on the map matches". Enter, the
arrow keys or a tap fly to the club at z10 or its tier's zoom if that
is higher, and open its sheet, with its ground-mates if it shares one;
picking closes the keyboard. **The keyboard, honestly**: headless
Chromium has none, so `test_search.js` stands it in by shrinking the
window to 390x500 after focusing the box - what a phone does when the
keyboard resizes the page - and checks the list ends above it and its
first row can be tapped. Chrome on Android can instead lay the keyboard
over the page without resizing it; for that, the list's height is capped
by `visualViewport.height` (the `--vvh` CSS variable), which the test
checks follows the visible height. **No real keyboard has been opened.**

**The coverage panel counts from the club files, never from a list.**
Built 2026-10-03. Tapping the club-count chip at the top left opens it:
total clubs on the left and total leagues on the right, large; then
clubs and leagues per tier; then every league grouped by country, with a
tier filter and a country filter; a league lists its clubs, and a club
flies to its ground and opens its sheet. A **league is a competition
name the club data records** (the club file's `competition` field),
counted once per country and tier. The club sheet works its competition
out from `league-tiers.csv` instead (see "The club sheet does not trust
the club file's competition field"); **on 2026-10-03 the two agree for
every one of the 556 clubs** (checked), so the panel and the sheet name
the same league. A club whose file records none is listed under "league
not recorded (tier N)" and is **not counted as a league**. First count:
**556 clubs and 32 leagues**; 11 clubs with none recorded (six at tier
4, three at tier 6, one each at 7 and 8). **One of the 32 is worth
knowing about**: "Regionalliga (the generic fourth-division item)" is
the label `league-tiers.csv` gives the generic Regionalliga item
`Q2188121`, and it holds one club, VfB Oldenburg. It is counted because
the data names it; it is a league history, not a sixth Regionalliga
(see Known open problems on `Q2188121`).

**The club sheet shows two kinds of ticket information side by side and
reconciles neither.** Built 2026-10-03 on Alexandru's instruction.
*(Since 2026-10-04 the section is the shared club renderer of "Ticket info
and the Bucket list" below, under the Next window line: **country rules
first**, then Researched rules, then Your notes. Until then the national
rules sat inside Researched rules, below the club's own, and only for a
club with a `club-tickets.csv` row. The notes no longer list the club's
`ticketEvents` or bucket items with their dates - only their titles, and
the dates are on the Bucket list tab.)*
"**Your notes**" is `football-rules.json`, joined through
`data/football-rules-links.csv`: every field of the club's entry as
written (nested fields indented, `null` as "not recorded", `true` and
`false` as yes and no), its `ticketEvents` (shown the way the Ticket
info tab shows them) and the bucket-list items that name it.
"**Researched rules**" is the club-tickets files, as before, with each
window's **phases** from `club-ticket-phases.csv` now listed under it -
which is where most of what the Inter entry below disagrees about
lives. Where the two disagree each says what it says; the sheet says
so in one line and picks nothing. A club with neither keeps "Ticket
info unavailable".
- **Next window** is the soonest window ahead across both sources.
  A `football-rules.json` event counts unless it is `disputed`; a
  `confirmed` one is shown to the day; **anything else is shown to the
  month only** ("estimated: December 2026 - check whether it has been
  announced"), never a day, even where the file holds one. A
  `club-ticket-windows.csv` row has loose text and a cycle, never a
  date, so to put it in order the **first month its text names** is
  read in the cycle's first year if it is May to December and its
  second if January to April (a pre-season window falls before the
  season, an in-season one inside it). That rule fits every row in the
  file today and it is a judgement: the line shows the row's own words
  and says how it was placed ("read as January 2027 to put it in
  order"). A row or event with no month or date ("about six weeks before
  each match", the Pokal second round) cannot be placed and is named as
  not counted. Where several fall in the soonest month all are shown,
  since a month cannot be put before or after a day inside it.
- **What it said on 2026-10-03**: VfB - presale right activates,
  estimated November 2026 (your notes); KSC - KSC v FCK ticket release,
  estimated December 2026 (your notes); Kaiserslautern, Kickers, Poli,
  UTA - no window ahead (Poli's cup sale was September; UTA and Kickers
  have none); Bayern - the away season ticket cycle, "late May"
  2027-28, confirmed (researched); Nürnberg - the Frankenderby home
  leg and the half-season ticket, both estimated November 2026
  (researched); Inter - the derby home leg, "early to mid January"
  2026-27, estimated (researched; the disputed August phase-1 event in
  your notes is not counted). AC Milan - the derby sale, estimated
  October 2026, the current month, so "check whether it has been
  announced".

**Karlsruher SC and Germany's first national rows, 2026-10-06.**
Researched on Alexandru's instruction for an outside buyer - a member of
neither club, living in Germany but not in Karlsruhe, wanting **two
tickets together** - with the Südwestderby against Kaiserslautern as the
high-demand fixture. Written in the shape of the Nürnberg and Inter rows.
- **How it was read.** The sandbox's proxy refuses ksc.de and every news
  site, so pages were read on a GitHub runner by a throwaway probe in
  `build-clubs.yml` (four rounds, removed in the same branch; the file is
  byte-for-byte as before). ksc.de answered 200 everywhere and its
  `robots.txt` disallows only `/*?id=*`. **Two refusals, not worked
  around:** bnn.de answered 403 (a stop; its Internet Archive capture of
  June 2025 then answered 429, rate-limited, and was not retried), and
  the Polizei NRW copy of the DFB security rules put up a "Security
  Check" page (503) - the DFB's own PDF was read instead.
- **The fixture.** KSC is `Q105853`, Kaiserslautern `Q8466` (both from
  `data/clubs/DE.json`). The OpenLigaDB 2. Bundesliga file has the first
  leg **at Kaiserslautern**, matchday 2, played 15 Aug 2026 (0-0), and the
  second leg **at Karlsruhe**, matchday 19, with all nine matches of the
  round at one kick-off in late January 2027 - a placeholder by this
  project's reading, so the day is not fixed. dpa (K23) and KSC's own away
  sale (K26) confirm the first leg; no DFL or club source for the second
  leg's date was read. `bucket-links-manual.csv` already says KSC hosts
  the second leg, and that agrees; **nothing in it was changed**.
- **What a non-member can do, in one paragraph.** An ordinary KSC home
  game reaches free sale (members, then season-ticket holders with
  members, then everyone, a week or so apart, three to five weeks before
  kickoff; up to four tickets per KSC-ID). **The home derby has not: no
  free sale in 2022-23 ("aus Sicherheitsgründen"), 2023-24, 2024-25 or
  2025-26**, and 2025-26 sold out a few hours into the members' presale.
  The routes are a membership taken out well ahead (EUR 75 a year for an
  adult from July 2026; up to 30 working days to process; one presale
  right per KSC-ID, so two people need two), a seated season ticket, or
  the club's Ticketzweitmarkt once the game is sold out (nothing
  guaranteed). The guest blocks NO and N4 are sold only by Kaiserslautern.
- **Germany's national rows, and the boundary test applied to each
  candidate.** Three went in, each from a source that speaks for the
  federation or the league: **DFB § 25** (the home club reserves 10% of
  seats and of standing for the away club; away fans not charged more -
  `may-add`, a floor), **DFB § 32** (a "match with increased risk" is
  decided by the home club after hearing the police, the DFB may classify
  one itself, and limiting ticket sales, buffer blocks and alcohol limits
  are measures to consider - `implements`), and the **DFL's fair-play
  rules** for the official secondary market (at most the original
  single-ticket price, a service fee of at most 15% - `implements`,
  `appliesTo` Bundesliga and 2. Bundesliga). **Kept as club rows**: KSC's
  ban on away colours in home areas, its alcohol ban at the 2024-25 derby
  (the consequence of a classification, one fixture), its "no free sale",
  its 40/20/40 split of away tickets, its ATGB resale terms (+15%) - each
  something KSC could change tomorrow. **Not written**: a PAngV row on VAT
  (gesetze-im-internet.de timed out from the runner, so the law was not
  read), and a German personalisation rule (none found; an absence is a
  fact only when stated). The DFB text read is the edition of 1 Feb 2023.
- **What moved because Germany now has national rows** - listed exactly:
  (1) Ticket info tab: Nürnberg's and Bayern's entries lost "No national
  rules researched for Germany (DE) yet." and gained "Country rules:
  Germany" with the three rows, above their researched rules; (2) the
  same on both club sheets; (3) **every other German club sheet** - 149
  German clubs are on the map - now shows "Ticket info unavailable"
  followed by Germany's three rows, because a sheet shows its country's
  rules wherever there are some (the DFL row says it applies to the
  Bundesliga and 2. Bundesliga, but like every country row it is shown,
  not filtered, so tier 3-8 clubs show it too, with its "Applies to");
  (4) the Bucket list: the Frankenderby's Nürnberg and Fürth blocks, the
  Südwestderby's KSC and Kaiserslautern blocks and every other entry with
  a German club; (5) `check_tickets.py`'s layered view: three
  `[national]` lines under Bayern, Nürnberg and KSC, Nürnberg's
  `resale-price-cap` (line 19) and KSC's (line 53) now read as "this
  club's implementation of it", and KSC's derby `risk-classification`
  rows likewise. Nothing moved into "CHECK THESE AGREE": no German row is
  `none`. `test_tickets_bucket.js`'s Nürnberg check now follows the file.
- **Prices.** The club's PDFs are headed "TAGESKARTEN 26 / 27"; ka-news
  prints exactly the same figures as the **2025/26** prices and reports
  the club adjusts prices every two years. The rows say 2026-27, the
  club's own label, and their note says what ka-news says. `priceBasis`
  is `unknown`, as the brief asked, because no source states VAT or fees
  for a home ticket; the only fees stated are EUR 2 at the matchday box
  office and EUR 1 on away tickets. The derby was category A in 2024-25
  and 2025-26; 2026-27 is `inferred`. For two adults in category A the
  cheapest seats (N1-N3) are 2 x EUR 37.80, standing 2 x EUR 20.30.
- **Timing.** The members' presale for a home derby opened 26-34 days
  before kickoff in all four seasons read, so for a late-January kickoff
  the estimate is "late December or early January", `inferred` /
  `observed-past-cycle`. **When the DFL scheduled each past derby was not
  read**, so the start is stated relative to kickoff only.
- **Minors.** Under-18s can be members (7-17, EUR 40, with a presale
  right), pay the reduced rate, and a child's ticket (up to 14 in one
  wording of the ATGB) is sold only with an adult ticket and admits the
  child only with an adult. Whether an under-18 may buy in their own name
  is not stated: `minorEligibility` is `unknown`.
- **Kaiserslautern's own selling rules are not researched.** Its pages for
  the 2024-25 and 2025-26 derbies were read in passing (K29, K30), only to
  confirm that FCK sells the guest blocks at the Wildpark.

**VfB Stuttgart, 2026-10-07.** Researched on Alexandru's instruction for
an outside buyer - a member of no club, living near Stuttgart, wanting
**two tickets together** - for Bundesliga and Champions League home games
at the MHPArena, men's first team only. `Q4512`, from `data/clubs/DE.json`;
`football-rules-links.csv` already linked `vfb` to it, so "Researched rules"
and "Your notes" show under one club. Written in the shape of the KSC rows:
1 club row, 4 windows, 10 phases, 23 rules, 3 demand rows, 50 prices,
31 sources (`V1`-`V31`).
- **How it was read.** The sandbox's proxy refuses vfb.de and every news
  site, and WebFetch is refused too; web search works. Pages were read on a
  GitHub runner by a throwaway probe - five rounds, removed in the same
  branch. **`workflow_dispatch` answered HTTP 500 all session** (and `git
  push` did for the first quarter of an hour), so the probe ran as a job in
  `check-holidays.yml` on the pull request's own trigger; the file is byte
  for byte as before. vfb.de, shop.vfb.de, tickets.vfb.de and
  service.vfb.de all answered 200 - **no bot-management block**;
  `vfb.de/robots.txt` disallows only `/fileadmin/` (PDFs allowed). The
  Stuttgarter Zeitung and Stuttgarter Nachrichten are paywalled: only their
  teasers, captions and first lines were read, and the rows say so. The
  Internet Archive's CDX answered 503 for the one club page that had gone
  (the 2025-26 sale calendar), so the 2025-26 members' sale dates seen in a
  search-result summary were **not** written.
- **What a non-member can do, in one paragraph.** Every home sale opens
  with a **members' sale**: online, a virtual queue with one random place
  per member, **up to two tickets per member** - so one membership covers
  the buyer and a companion. A **free sale** happens only when tickets are
  left; it did for every Bundesliga home game of early 2026 (press), but on
  7 Oct 2026 the Atlético and Gladbach games were sold out in the members'
  sale. A new member waits **three months** for the presale right (since
  1 Jul 2025), after about **two weeks'** processing. Adult membership is
  EUR 60 a year (26-64; EUR 30 for 15-25). The club's **Ticketbörse**
  resells returns of sold-out games at the official price (seller refunded
  minus 20%); for season-ticket seats it is visible to "other members", for
  day tickets who may buy is not stated. Away: nothing from VfB's
  allocation reaches a non-member; the home club's own sale is the route.
- **Prices: the earlier claim, verified half-way.** The club's own help
  centre says day-ticket prices vary from match to match and appear only
  once a match's sale starts (SPOX said the same in 2024) - **no single
  price list, verified**. **By opponent or by game category: not stated by
  anything read** (an `unverified` row). The only 2026-27 list by category
  is for **season tickets** (written, labelled `stage` `season-ticket`, not
  open to non-members); the only day-ticket list by category found is the
  **2024-25 Champions League** one (written, season `2024-25`, never
  relabelled). One Bundesliga day price: EUR 70 at the side of the
  Gegengerade, January 2026, from one press report (`unverified`).
  `priceBasis` is `unknown` throughout.
- **Timing.** The club's shop on 7 Oct 2026 announced members' sales
  opening **46 and 43 days before kickoff** (Frankfurt, Lille) - both still
  ahead, so neither date is written anywhere; the window says "about six
  weeks before kickoff", `inferred`. Sales are listed only for games the
  DFL has timed; when the DFL timed each game was not read. Season tickets:
  late May to June (one cycle read). Champions League packages: early
  August (two cycles).
- **Germany's national rows: nothing added.** Every candidate failed the
  boundary test or the source test: the under-14 rule is the ground's
  Stadionordnung and the club's ATGB (the club could change them); the
  resale caps and banned platforms are the ATGB; the draft federal law on
  the ticket secondary market (seen in the Bundestag's lobby register in
  search results) is a proposal, not a rule. **So nothing moved above the
  Bayern, Nürnberg or KSC entries.**
- **A key gap, the fourth of its shape, not fixed (the brief said: use the
  existing schema).** `club-ticket-demand.csv`'s key is club, team, scope,
  opponent, season, and only a derby row may name an opponent - so a club
  can hold ONE general demand row per season, and VfB v Bayern and VfB v
  Dortmund in the same season cannot each have one. The 2025-26 row is
  therefore `varied-by-fixture` (a new value) with the fixtures in its
  `timing` and note. Alexandru's call (Known open problems).

**Ticket info and the Bucket list, 2026-10-04: rules on one tab, dated
reminders on the other.** Built on Alexandru's instruction.
- **One renderer for a club's ticket information**, `clubTicketsHtml()`
  in `index.html`, used on the club sheet (below its Next window line,
  which is unchanged), in the Ticket info tab's club rows and in a bucket
  entry's Ticket rules. Always in this order: "**Country rules:
  <country>**" (every row of `country-ticket-rules.csv` for the country
  of the club's ground - `club-tickets.csv`'s `country`, else the map's -
  or "No national rules researched for <country> yet."), "**Researched
  rules**" (standing fields including how to track updates and under-18s;
  sales windows with their typical opening, which is the row's own
  month-level text, and their phases in order; general rules; derby
  overrides; prices in their own currency; the sell-out record; a source
  line on each row), then "**Your notes**". A club with neither club
  source says "No ticket rules researched for <club> yet." (on the sheet
  it keeps "Ticket info unavailable", with its country's rules below only
  where that country has some). Nothing reconciles the two.
- **Each country rule says which matches it covers in plain words**:
  `appliesTo` `unknown` reads "The sources do not say which matches this
  covers." - never blank, never "all". Also its condition, authority,
  the club's room (`clubLatitude`), its confidence tag and its sources
  (publisher and title from `ticket-sources.csv`, linked).
- **"Unverified" is shown where `football-rules.json` says
  `"verified": false`, and only there**: a red tag on the notes naming
  the part ("Age rules", "the whole entry") and on the nested block. For
  Inter that is **Age rules only** - the file does not mark Inter's
  procedure, so its "phase 1 open worldwide" claim is not marked by this
  (see Known open problems).
- **Prices: the euro figure goes in brackets only for a row not in
  euros, and no exchange rate is held**, so such a row would say "euro
  figure not recorded". Every price row today is EUR.
- **The Ticket info tab** has two sections, **Countries** (one row per
  country with a national rule - Italy only today) and **Clubs** (one row
  per club with a row in any club-ticket file or a line in
  `football-rules-links.csv` - 12 today), each opening to the renderer
  above. No ticket window, no Next window, no list of dates.
- **Dates: one function decides what may be shown**, `placeDate()`, used
  by the sheet's Next window line and everywhere on the Bucket list tab:
  a `confirmed` day is shown to the day; anything else - `inferred`,
  `disputed`, an inferred range like `2027-01-30/2027-02-01`, a month -
  to the month only ("estimated: January or February 2027"). **Since
  2026-10-04 a `confirmed` range of whole days is day-level too** ("Sat
  30 Jan 2027 to Mon 1 Feb 2027") and the calendar draws it across its
  days: it is a published fact, not an estimate. No range in the files is
  confirmed today, so nothing shown changed. A `disputed` date
  says "disputed: possibly the wrong year or the wrong event" and its
  warning is shown as written.
- **The Bucket list tab** keeps every `bucketList` entry *(since
  2026-10-04 ordered by the sort, not in Live / Blocked or deferred
  groups - see the next entry)*, each a card that opens to
  `bucketDetailHtml()` (the renderer the next prompt reuses inside a
  sheet): what it is, the venue if known, every hand-written date with
  its dateSource label, every other field of the entry as written; the
  clubs, host and leg from `bucket-links-manual.csv`; for a fixture,
  **Next meeting** - the derby panel's own `derbyMeetings()` when the
  pair is a `derbies.csv` row (by `rulesId`, or by the two Q-ids) and
  both clubs have a fixture source, otherwise why not and the
  hand-written date, labelled as such; **Ticket rules** - host first,
  each club through the shared renderer; **Event rules** from
  `event-ticket-rules.csv`; and **Ticket windows (reminders)**, every
  ticket event linked to it: title, window with its dateSource label,
  the reminder lead time in words ("21 days (3 weeks) before the date"),
  action, derivation and any warning. At the top, **Reminders**: the
  ticket events no entry claims, soonest first, undated last, rendered
  the same way. Facts only; nothing recommends.
- **What it said on 2026-10-04**: Reminders - Poli v Rapid (September
  2026, past), the Pokal second round and Strasbourg's resale (undated).
  The Milan derby's Next meeting reads **Sat 31 Oct 2026, 20:45** from
  the Serie A file, while your notes give Sun 1 Nov 2026, confirmed -
  both are on the card (Known open problems). The Frankenderby's is Sun
  31 Jan 2027, 13:30, "day and time may be provisional".

**The Bucket list: List, Calendar, favorites, 2026-10-04.** Built on
Alexandru's instruction. Two sub-tabs at the top of the Bucket list tab.
- **List.** Reminders first, as before, then the entries in the chosen
  sort. **Earliest** (the default): upcoming entries with a day-level
  date, by date; then month-level ones, by month start, labelled
  "estimated" and showing no day; then entries with no date; then past
  entries in a collapsed **Past** section. An entry's place is its
  soonest upcoming date; a disputed date places nothing. Equal dates
  keep live before blocked or deferred, then priority. **Favorites**:
  starred entries first, then the rest, each group in Earliest order.
  Each card shows its date line under the title, through `placeDate()`.
- **The star** on every card is a 44 px button with `aria-pressed`; a
  tap stars the entry without opening the card.
- **Favorites and the sort are kept on THIS DEVICE only**, in
  `localStorage` (`football-planner-favorites`, a list of bucket entry
  ids; `football-planner-bucket-sort`, `earliest` or `favorites`). **Not
  in the repo and not read by any tool.** Since 2026-10-04 the favorites
  travel in the Me tab's export file (and a star puts up its backup
  banner); the sort does not. Every read and write is wrapped, so with
  storage blocked both still work for the visit. An id that is no longer
  a bucket entry is ignored. *Clear & reset* for the site deletes them.
- **Calendar.** A month grid, Monday first, with previous, next and
  Today. A **confirmed** day-level date - an entry's date or fixture, or
  a ticket window - goes on its day cell, a confirmed range on every day
  it spans; an entry is a round dot, a ticket window a diamond, a
  favorite adds a star. Tapping a day lists its items under the grid.
  **A month-level date (an estimate) never goes on a day**: it is in a
  strip above the grid, "Estimated this month, date not fixed", in every
  month it spans. **A disputed date is not placed**: it is listed under
  the grid as "Not placed: disputed date". Items with no date are listed
  under **No date**.
- **School holidays** from `data/holidays-manual.csv`: a fixed holiday
  is shaded green, a movable day hatched with a dashed border, the school
  start outlined in blue; the block's name is on its first day in the
  month and in a line under the grid. **Outside the span the file covers
  (today 30 Jul 2026 to 13 Sep 2027) the month says "School holidays not
  entered for this period"** (with "before" or "after" a date for a month
  partly outside); it never implies there are none. While no movable day
  is entered, every month inside the span says so too.
- **Tapping an item opens a bottom sheet** (`#bsheet`), built like the
  club sheet, sitting on the bottom bar and scrolling inside itself. It
  uses the List's own renderers - `bucketDetailHtml()` for an entry,
  `eventHtml()` for a reminder no entry claims - so it holds the same
  text; a ticket window that belongs to an entry opens the entry,
  scrolled to the window. Switching tab closes it.
- **"School holiday: <name>"** is shown in an entry's (or a window's)
  detail when one of its day-level dates falls inside a holiday block,
  and nothing otherwise. Today that is the Europa League final, 26 May
  2027, in the Pfingstferien.
- **Dates are plain local dates.** Nothing is converted between time
  zones; "today" is the phone's own calendar day (`todayISO()`), which
  `isPast()` and the Next window line now use too (they used UTC's day
  before). Tested under Europe/Berlin and UTC at 23:30 UTC on 25 Oct
  2026, when the two days differ.
- **What it said on 2026-10-04** (today 2026-10-04): 2 entries with an
  upcoming day-level date (Derby della Madonnina, 1 Nov 2026; Europa
  League final, 26 May 2027), 2 month-level (Frankenderby, January or
  February 2027; KSC v FCK, January 2027), 17 undated, none past. No
  ticket window is day-level (every one is inferred or disputed), so
  none is on a day cell. A month renders in about 17-19 ms in headless
  Chromium with the CPU slowed 4x (this sandbox, not a phone).

**The 160-entry bucket batch, 2026-10-08: undated, in a fixed order, with
unverified "why" texts.** Added on Alexandru's instruction: 145 new
`bucketList` entries and 15 existing ones that already covered the same
fixture, in his order, which the List now shows by default.
- **The why texts were written from memory by an assistant and stay
  unverified until a verification pass.** Nothing in them was read from a
  source. They carry no date, capacity, ticket rule or sale window of ours,
  and every entry shows them under "Not yet verified" (`whyStatus`
  `unverified`). Some contain ticket-access claims (lottery, members first,
  away fans not allowed); they are claims to check, not rules, and live
  only in `why`. A verification pass flips `whyStatus` entry by entry.
- **Fields.** New: `group`, `country` (`none` where the entry has no
  country), `sortKey` (10, 20 ... 1600, in his order), `why`, `whyStatus`,
  `leagueCheck: true` where his line ends in [LC] (the label reads "Needs a
  league check: both clubs must share a league or cup in that season"; the
  check itself is not built), and `listOnly: true`, which keeps an entry off
  the calendar (undated entries would otherwise fill its "No date" list).
- **The 15 existing entries kept every hand-written field, date and link.**
  They got `group`, `country`, `sortKey`, `whyStatus`, `leagueCheck` and,
  because each already has a hand-written `why`, his new text in
  `whyAssistant` instead (rule 3: hand-written wins). They are not
  `listOnly`, so the calendar is unchanged for them.
- **Clubs** are linked in `bucket-links-manual.csv` only where a club's name
  equals one on a map club file of the entry's country (the fixture-link
  matcher's rules), never from memory; the host is left empty, since the order
  of names in a title says nothing about home or away. A club without an exact
  match stays unlinked, and an ambiguous one (Dinamo București: two items)
  too. A line may therefore name one of two clubs; its note says which is not
  linked.
- **The List** has three sorts: Group order (default; entries by `sortKey`
  under their group, the "other countries" group with a sub-heading per
  country, entries without a `sortKey` last), Earliest and Favorites. An
  undated entry reads "Date not set". A stored choice of Earliest or
  Favorites is kept. `SHELL_VERSION` is `v9`.

**The Me tab: memberships and tickets held, on the device only,
2026-10-04.** Built on Alexandru's instruction. A fourth tab in the bottom
bar (its four labels fit 390 px, one line each - `test_me.js` checks it).
- **Where it lives: this browser's `localStorage`, nothing else.** Keys
  `football-planner-me` (memberships, tickets, settings),
  `football-planner-me-unsaved` (an edit since the last export) and
  `football-planner-me-exported` (when). **Never in the repo, never read
  by any tool, never sent in any request, and the service worker never
  sees it** - the saved-routes arrangement. Every read and write is
  wrapped: with storage blocked the tab says what you add lasts only until
  the page is closed, and works for the visit.
- **Memberships**: club or organisation (required), who it is for, scheme
  name, cost (amount, a three-letter currency, and - only when not EUR - a
  euro figure **he types**: no exchange rate is held, so a missing one
  reads "euro figure not entered", the price-file rule), how often it is
  charged (`yearly`, `per season`, `half-yearly`, `quarterly`, `monthly`,
  `one-off`, `other` or not recorded), renewal date, benefits, notes.
  Within the window (default 30 days, set on the tab, 1-365) a card reads
  "Renewal due in N days" (or "due today"); before today, "Renewal
  overdue by N days" in red; outside it, "Renews <date>". Overdue first,
  then soonest, undated last. Days are counted between plain local dates.
- **Tickets held**: match (required), date, kick-off (optional; none
  reads "time not set", the club sheet's wording, and "date not set" with
  no date), venue, block, seats, who each ticket is for (one text field),
  price paid (as the cost), where bought, status (`requested`, `won`,
  `bought`, `transferred`) and **Link to bucket event** - a dropdown of
  the bucket entries **by id**, never matched by name. A link to an id no
  longer in the bucket list is kept and says so. Past tickets (date before
  today) are in a collapsed Past section.
- **"You hold tickets"**: a bucket entry with at least one linked ticket
  carries a green "You hold tickets" tag with the statuses beside it
  ("bought", "2 requested, won"), on its List card and its sheet's header
  (both through `bucketTags()`), a "You hold tickets" box at the top of
  its detail (`bucketDetailHtml()`, so the List and the sheet), a green
  "T" on its calendar day cell (and "you hold tickets" in the cell's
  label) and the tag on its calendar item. **Every status counts,
  `requested` included**, as the brief worded it - see Known open problems.
- **What is not stored, by design**: no field for a barcode, a QR code, a
  password or a card number, and **any free-text value holding 13-19
  digits (spaces or hyphens between them allowed) that pass the Luhn check
  is refused**, on Save and on Import, naming the field. The tab says why:
  an export file ends up in cloud backups and downloads folders. Digits
  that fail Luhn (a phone number, a booking reference) are kept.
- **"Add to phone calendar"** (a page cannot alert while closed) downloads
  a one-event `.ics` with a `VALARM` (`ACTION:DISPLAY`). **The dates are
  his own entries and are used exactly as typed**: a kick-off is written
  as a floating local time (`DTSTART:20261101T204500`, no time zone, so
  the phone shows it as typed) and **no end time is invented** - the event
  is the kick-off moment; a renewal, or a match with no kick-off, is a
  whole-day event (`VALUE=DATE`, `DTEND` the next day). The lead time is
  per record, set in its form: default **14 days for a renewal, 1 day for
  a match**. For a whole-day event the alarm goes off at **09:00** that
  many days before (`TRIGGER:-P13DT15H` for 14), because midnight is when
  a whole-day alarm would otherwise ring; for a timed match, that many
  days before kick-off (`-P1D`). Text is escaped and lines folded at 75
  octets. Rule 4 is not touched: this is hand-entered data, one file per
  tap, never a subscribed feed.
- **Export / Import**: one JSON file, `format: football-planner-me`,
  `version: 1`, `exportedAt`, `memberships`, `tickets`, `favorites` (the
  bucket list stars) and `settings.renewWindowDays`. **An import is
  checked whole first** - format, version (a newer one is refused), every
  record through the same checks as the form, ids unique, the card-number
  rule - and **any problem refuses the whole file with nothing changed**,
  naming up to six reasons. A good file first says what it holds and what
  it would replace, and **Replace** then replaces this device's
  memberships, tickets and favorites with the file's (a favorite naming an
  entry no longer in the list is left out, and said). Saved routes merge on
  import; this replaces, because it is a restore, and merging would bring
  back records deleted since.
- **The backup banner**, "Back up your data — export", is on the tab after
  any edit - a record, the renewal window, a star - until the next export
  (or an import). The tab also warns that clearing Chrome's site data
  deletes everything on it.
- **Can saved routes share the same export? Yes, technically, and it was
  not done (as asked).** Both are this origin's storage and JSON, and the
  routes already have a validated export of their own
  (`football-planner-saved-routes`, `checkImported()`). Three reasons it
  is not a free merge: the routes import *merges* by id and this one
  *replaces*, so one file would need two rules; the place-search cache and
  the credit estimate must never go in a file (Stadia's 7-day rule, and
  the estimate is per device); and a saved route line rests on Stadia's
  "offline use ... per device" exception - a routes export already moves
  lines off the device on purpose, but putting them in every routine
  backup is a wider reading of that clause. Alexandru's call: keep two
  files, or add routes to this one as an optional section that merges.

**Phone layout and plain words, 2026-10-03.** Five problems Alexandru
saw on a real phone at about 390 px, each reproduced in headless
Chromium first and each held by `tools/test_layout.js`:
- **Sideways scroll on the Ticket info tab** was two warning tags that
  could not wrap (`.tag` was `white-space: nowrap`): Inter's 135-character
  warning made the tab 724 px wide, Poli's 479. Tags now wrap inside
  their card, and a field's value wraps anywhere. The Bucket list tab
  had the same tag and is tested too.
- **The sheet ending mid-screen was a real bug, not the screenshot.**
  The map pane was itself scrollable by 394 px, because the hidden route,
  derbies and coverage panels sit in it pushed below its bottom edge
  (`translateY(105%)`) and a transformed element still counts towards
  its container's scroll area. A swipe past the end of a sheet then
  scrolled the whole pane, carrying the sheet up and leaving an empty
  band above the bottom bar. The map pane is now `overflow: clip` (it
  cannot scroll at all, even by script) and every panel's body is
  `overscroll-behavior: contain`, so it scrolls inside itself.
- **The bare Q-id on the distance note** was a link to the club's
  Wikidata item - where its name, ground, capacity and position come
  from, and the id a `clubs-manual.csv` row uses. It is kept, as a
  "Details · Wikidata (item Q…)" line at the foot of the sheet.
- **Fixtures and Ticket info name no file** in what the sheet shows.
  Each says why in plain words; a club with no fixtures is told which
  competitions are fetched (`FIXTURE_COVERAGE` in `index.html` - keep it
  in step with `fetch_fixtures.py` and `fetch_openligadb.py`), and a club
  linked only to a cup is told its league is not covered. The file-level
  reason is under a collapsed "Why?" (or "Source") line. The Club
  section's competition note still names `league-tiers.csv` when it
  cannot place a league; that was outside the ask and was left.
- **Next window, when nothing is ahead**, says "No window recorded"
  when neither source records any event or window for the club (on
  2026-10-03: Kaiserslautern, Kickers, UTA, Dumbrăvița), "No upcoming
  window recorded" when what is recorded is all past or disputed (Poli),
  and "No upcoming window with a date or month recorded" when what is
  left names no month (Strasbourg's resale). It used to say "No window
  ahead with a date or a month, in either source" for all three.

**The installable app: what is cached, what deliberately is not, and
how an update reaches the phone.** Built 2026-10-02 on Alexandru's
instruction. The site is served from `/Football/`, not from `/`, so
every path in `manifest.webmanifest` and `sw.js` is **relative**
(`./`, `data/`, `icons/...`) and resolves inside `/Football/`. A
root-relative `/` path would point at `alexgrozavul.github.io/`, which
is not this site. `start_url` and `scope` are `./`, which the test
checked resolves to `/Football/`.

| what | rule | why |
|---|---|---|
| the page, manifest, icons, the Leaflet copy (the **shell**) | **network first**, saved copy only when the network fails; cache `football-shell-<SHELL_VERSION>` | online, the phone always gets what GitHub serves now, so a deploy cannot be stuck behind an old copy |
| everything under `data/` | **network first**, saved copy **only when the network fails**; cache `football-data-v1` | stale data must never look current: online, the saved copy is never used, only replaced |
| map tiles, routing, place search (Stadia, another origin) | **not touched, not saved** | Stadia's terms, below |
| anything else in the site (`calendars/*.ics`, `docs/`) | not touched, not saved | not part of the app |

**The shell is network first, not cache first, and that was a choice.**
The brief asked for a cached shell with a versioned cache name so a new
deploy replaces the old one. A cache-first shell only changes when
somebody remembers to change the version, and forgetting once leaves the
phone on the old page indefinitely - the failure the brief was guarding
against. Network first, with the saved copy as the offline fallback,
gets the versioned cache and cannot be stuck. The cost is one
revalidation request per shell file per open, answered 304.

- **Offline, data is labelled.** A file answered from the saved copy
  carries `x-served-from: cache` and the time it was saved, and the page
  puts up a banner: *"Offline. Showing data saved on Fri, 2 Oct 2026,
  16:34. It may be out of date."* - the **oldest** saved time among the
  files it used. A file never saved on that phone is **named** in the
  banner ("Never saved on this device, so missing: clubs/GR.json"), not
  silently left off the map - rule 2. A 404 or a 500 from GitHub is
  **not** a network failure and is passed through as it always was.
- **What gets saved, and when.** Every data file the page loads while
  online. On the very first visit the page loads before the worker is in
  charge, so it then hands the worker the list and the worker fetches
  those files once (all twelve country files and `football-rules.json`,
  about 350 KB). A fixture file is saved only once a club sheet has
  opened it online, so a sheet opened offline for the first time says
  its fixtures are unavailable, and why.
- **Offline, the map says so.** Tiles are never saved, so offline the
  map shows a card - "The map needs a connection" - over the club
  markers, which still work. The same card appears online if tiles keep
  failing (four in a row), worded as "no connection, or Stadia Maps
  refused them", since a refused key looks the same from the page. The
  route panel's errors say "this phone is offline" when it is.
  **Found 2026-10-02, fixed 2026-10-03: a refusal did not raise the
  card.** Stadia answers a refused tile with HTTP 401 **and a PNG** (an
  error image, 14,885 bytes), which an `<img>` decodes and Leaflet counts
  as loaded - served as from a made-up domain, 12 of 12 tiles were
  "loaded" and the card stayed down (measured again 2026-10-03 on a
  runner, same result). An `<img>` cannot see a status code, so the map
  now fetches each tile with `fetch()` (`StatusTiles` in `index.html`)
  and hands the picture to Leaflet only when the answer is 2xx; anything
  else is a `tileerror` carrying its status. **That works only because
  Stadia sends `Access-Control-Allow-Origin: *` on tiles, refused ones
  included** - measured 2026-10-03 on a runner: 200 and 401 tiles both
  carry it. If Stadia ever drops that header, every tile fetch fails and
  the card says "no connection reached Stadia Maps" - wrong in wording,
  but loud, never a silent blank. The card now has three wordings: this
  phone is offline; Stadia **refused** the tiles (401/403, "not a
  connection problem"; 429, "the monthly allowance may be used up");
  and tiles not reaching Stadia. Four failures in a row still raise it,
  whatever the kind. Tiles still go through the browser's ordinary HTTP
  cache exactly as an `<img>` did (Stadia sends `max-age=21600`), and
  the worker still never touches them. The decoded picture is handed
  over as a blob URL and released as soon as it is drawn.
- **Leaflet is a copy in the repo, `vendor/leaflet-1.9.4/`, not the
  CDN.** Measured, not assumed: with the page loading Leaflet from unpkg
  and unpkg unreachable, the page throws `L is not defined` and **nothing
  renders - not the map, not the bucket list, not ticket info**, because
  start-up stops at the map. Caching the CDN file in the worker would
  also have worked, but only after a first online visit, and it keeps a
  third-party server between Alexandru and his own app. The copy is
  npm's `leaflet@1.9.4` (sha256 of `leaflet.js` `db49d009…5641a`); unpkg
  serves npm's files verbatim. It is also the pinned local copy the
  future page check needed (Known open problems).
- **How an update reaches the phone, and how long it takes.** A merge
  to `main` is live on GitHub Pages about a minute later. GitHub serves
  every file with `Cache-Control: max-age=600`, but the worker asks for
  the shell and the data with `no-cache` (revalidate), so the ten
  minutes do not apply: **the next time the app is opened online, it
  shows the new page and the new data.** An app left open in the
  background is not reloaded by itself; closing it (swipe it away from
  recent apps) and reopening is a reload, and the banner has a Reload
  button. A change to `sw.js` itself is found by Chrome when the app is
  opened (registered with `updateViaCache: 'none'`, so the check skips
  the HTTP cache), installs in the background, takes over at once
  (`skipWaiting` + `clients.claim`, harmless because both rules are
  network first), and deletes every cache it does not name.
- **`SHELL_VERSION` in `sw.js`: change it whenever `sw.js` changes**
  (`v1` → `v2` → `v3` → `v4` → `v5` → `v6` → `v7` → `v8` → `v9`; it has been `v9` since
  2026-10-08, when the 160-entry bucket batch and Group order shipped, `v8` before that, from 2026-10-07, when the sheet and Ticket info lost their sale dates, `v7` before that, from
  2026-10-04, when the Me tab shipped, `v6` before that, the same day,
  when the Bucket list got its calendar, `v5` before that,
  the same day, when the Ticket info and Bucket list tabs were rebuilt, `v4` before
  that, when the Near me panel shipped, `v3` before that, when the collapsible legend
  shipped, and `v2` before that, when the Stadia key left the page - each
  bump makes every installed phone drop the old shell cache).
  `test_pwa.js` reads the current version from `sw.js` and bumps it one
  further for its own deploy test, so it needs no edit when this changes. That is what drops the old shell cache. It is **not**
  needed for an ordinary change to `index.html` or the data - the test
  checked both: a new `index.html` with `sw.js` untouched reached the page
  on the next online load and became the offline copy, and a `v2` worker
  created `football-shell-v2`, deleted `football-shell-v1` and kept the
  data cache. Adding a shell file (a new icon, a second script) means
  adding it to `SHELL_FILES` and changing the version.
- **Stadia's terms on caching, read 2026-10-02** from
  `stadiamaps.com/terms-of-service/` ("Effective March 18, 2026",
  fetched on a GitHub runner: the sandbox cannot reach Stadia, and
  `docs.stadiamaps.com` answered the runner 403, which is a stop, so no
  documentation page on offline use was read). Its list of prohibited
  conduct forbids "proxying or caching access to our Services in any
  way", **except** (a) "caching small amounts of data for offline use in
  a mobile application, not to exceed 100MB cached at a time per
  device", (b) the paid cacheable static maps endpoint, and (c)
  "standard client-side caching (server-side caching is prohibited) for
  performance reasons provided that the cache is local to the client
  device and the data is not retained for longer than the HTTP caching
  headers, or 7 days in the case that a header is not returned". It also
  forbids "permanently storing results ... from the Stadia Maps Geocoding
  APIs without an active Standard, Professional, or Enterprise
  subscription", and the pricing page marks geocoding on the Free plan
  "Temp storage". **What that means here:** the browser's ordinary HTTP
  cache of tiles is (c) and is untouched. Saving tiles for offline use
  might fit (a) - an installed web app may or may not count as "a mobile
  application", which the terms do not define - but it would have to be
  capped at 100 MB, every saved tile is a credit spent in advance, and it
  is a reading of a contract, so **it is Alexandru's call and was not
  built**. Saving geocoding results is ruled out on the Free plan. **Do
  not add tiles, routes or searches to `sw.js` without reading the terms
  again.**
- **Force-refreshing the installed app if it misbehaves**, in order,
  stopping at the first that works:
  1. Make sure the phone is online, then **close the app completely**
     (swipe it away from recent apps) and open it again. That fetches
     the page and the data fresh. If the yellow "Offline" banner shows
     while the phone is online, GitHub did not answer; try again later.
  2. **Clear what it saved**: Chrome → ⋮ → Settings → Site settings →
     All sites → `alexgrozavul.github.io` → *Clear & reset*. That deletes
     the saved copies and the service worker; the next open is a first
     visit. The home-screen icon may need adding again (step 3).
     **It also deletes every saved route on that phone** (and the search
     cache and the credit estimate), **and everything on the Me tab and
     the bucket list favorites**: **Export both first** - saved routes
     from the route panel, the Me tab from its Back up section - and
     Import the files afterwards. Step 1 deletes nothing.
  3. **Reinstall**: long-press the icon → App info → Uninstall, then open
     `https://alexgrozavul.github.io/Football/` in Chrome → ⋮ → *Install
     app* (or *Add to Home screen* → Install).
  On a computer, Chrome DevTools → Application → Storage → *Clear site
  data* does step 2.
- **Tested 2026-10-02 in headless Chromium at 390x844**,
  `tools/test_pwa.js`, 22 checks, all passing: the site served at
  `localhost:8765/Football/` with GitHub Pages' own cache header, tiles
  stubbed. Chrome's own installability check (`Page.getInstallabilityErrors`,
  what DevTools' manifest panel shows) returned **no errors** in a normal
  profile (it says `in-incognito` in a private one, which is Chrome
  refusing to install from incognito, not a fault). Lighthouse was not
  used: its PWA category was removed in Lighthouse 12. **Not tested on a
  real phone or against GitHub Pages itself** - the sandbox reaches
  neither.

**Clubs near me: the location is device-only - in fact memory-only - like
saved routes.** Built 2026-10-03 on Alexandru's instruction. The Near me
chip, beside Route, opens one panel with two tabs, **Clubs** first and
**Derbies**; the Derbies tab is the derbies panel unchanged (same code,
same list, same detail). The panel remembers which tab was open while the
page is open, nowhere else.
- **The Clubs tab** lists every club **on the map** - the clubs in
  `CLUBS`, which have both halves of a position and a tier, so a club
  whose position was cleared by hand never appears - within the slider's
  distance (default 100 km, 10 to 500 km), nearest first, ties by tier
  then name. A row shows the name, the tier's colour dot, the competition
  as the club file records it (`competitionLabel()`, the search box's: a
  club with none reads "league not recorded (tier N)", never a guessed
  name), the ground (or "ground not recorded") and "≈ N km by road
  (estimate)" - the same `roadEstimate()` as the club sheet, straight line
  × the settings multiplier, and the panel says it is not a travel time.
  Clubs sharing a ground each have their own row. One chip per tier
  present on the map, all on; the chips remember the tiers turned **off**,
  so a tier whose club file loads after the panel first opened is on.
  "N clubs within X km" heads the list; the first 50 rows are drawn and
  "Show more" adds 50 at a time. Nothing in range says "No clubs within X
  km. Widen the distance."; every tier off says so too.
- **Tapping a row** closes the panel and calls `goToClub()`, the function
  a search suggestion calls: fly to the club at its tier's zoom or z10,
  whichever is higher, and open its sheet with any ground-mates. It is not
  a second copy. Checked on the Grünwalder pair: TSV 1860 München and FC
  Bayern München II each open their own sheet, the other listed as also
  there.
- **"Use my location"** asks the browser (`navigator.geolocation`,
  `enableHighAccuracy: false`, a 15 s limit, a position up to 5 minutes
  old accepted from the browser itself) **only when pressed**, and says
  "Finding your location…" meanwhile. Granted, the origin line reads
  "From: your current location (approx.)", every row "from your location",
  the list re-sorts, and **Back to home** restores home. Refused, timed
  out, unavailable or unsupported, a plain sentence says which and the list
  stays on home (or on the last position, when an update fails). The panel
  always says "Your location stays on this device."
- **Where the position lives: one variable, `NEAR.here`, in the open
  page.** It is never written to `localStorage`, `sessionStorage`,
  IndexedDB, a cookie, the URL or the repo, never sent in any request, and
  the service worker never sees it: it is only subtracted from club
  positions already in the page. **A reload forgets it**, and so does
  closing the app. `test_nearme.js` checks all of that (every storage
  dumped, every request's URL, body and headers searched for the mocked
  position). **Nothing in the repo may ever read or write it.** The
  derbies tab, the club sheet's distance and the route panel still measure
  from home; only this list uses the position.
- **The label is the data's**: the origin line reads "From: Leonberg, DE
  (home)", `settings.home.label` as written, not a shortened name.
- **Measured 2026-10-03** (headless Chromium, 390x844, this sandbox, not
  a phone): within 100 km of Leonberg there are 9 clubs on the map - 2
  at tier 1, 1 at tier 2, 3 at tier 3, 3 at tier 4. At 500 km there are
  184; with the CPU slowed 4x the list (50 rows) is built in about 8 ms
  (worst 18), and the painted frame follows about 16 ms after an empty
  two-frame wait.
- **Not tested on a real phone**: Playwright's mocked position stands in
  for a real one, and a real permission prompt was never seen.

**The legend tab: device-only, like saved routes.** Built 2026-10-03 on
Alexandru's instruction. The map's tier legend, bottom left, is a
collapsible tab. **Closed** it is a button reading "Leagues shown" and an
arrow, nothing else. **Open** (tap the header or the arrow) the same
header sits above the tier rows, with their zoom dimming, and the
shared-ground row; their content and the dimming logic were not changed.
The header is a real `<button>` with `aria-expanded`, 44 px tall, and the
arrow rotates between the two states. It **starts closed on a first
visit**.
- **Whether it is open is remembered on this device only**, in the
  browser's `localStorage` under the key `football-planner-legend-open`
  (`1` open, `0` closed). **Nothing here is ever committed**: no
  workflow, file or tool in the repo reads or writes it, and the service
  worker does not touch it - the same arrangement as saved routes
  (below), with the same consequences: another phone, a Chrome Incognito
  tab, another browser and an iPhone home-screen app each keep their own
  choice, and *Clear & reset* for the site (step 2 of "Force-refreshing
  the installed app") puts it back to closed. There is no export; a
  legend setting is not worth one.
- **Storage may be blocked**, and even reading `localStorage` can throw
  (private window, site data off), so every read and write is wrapped:
  blocked storage means the legend starts closed and works for that
  visit, with no error. `test_legend.js` checks it with the accessor
  made to throw.
- **It never sits under the attribution bar or the bottom navigation,
  and the open legend is capped, not trusted to fit.** The original
  legend sat 12 px above the pane's bottom edge, and the attribution bar
  is 16 px tall on a one-line screen - so the bottom row, "Shared ground,
  tap for the list", was under it (measured 2026-10-03: legend bottom 624,
  attribution top 621 at 390x700; on a real phone the attribution can
  wrap to two or three lines and cover more). The page now **measures**
  the attribution's height and the top row's, and sets the legend's
  bottom edge above the attribution (`--attrH`) and its maximum height
  below the top row (`--legMax`), again whenever the window, the top row
  or the attribution changes size (a `ResizeObserver`, plus `resize`).
  If every row does not fit, the legend scrolls **inside itself**, its
  header kept in view and the map pane not scrolling. Measured: at
  390x700 and 390x500 all nine rows fit, with 9 px between the legend
  and the attribution; at 390x300 the rows scroll inside a legend 124 px
  tall. The bottom navigation is outside the map pane, so the legend can
  only reach it if the pane itself collapses; the test checks it anyway.
- **Not tested on a real phone.** Headless Chromium has one attribution
  line at this width; the wrapped case is forced in the test with a
  narrower attribution, not seen on a device.

**Saved routes: kept on the device, never in the repo, and shaped by
Stadia's terms.** Built 2026-10-03 on Alexandru's instruction. **Nothing
here is ever committed**: saved routes, the place-search cache and the
credit estimate live in the browser's IndexedDB
(`football-planner-device`, stores `routes`, `searches`, `credits`) on
the one device that made them. No workflow, file or tool in the repo
reads or writes them, and the service worker does not touch them.
Export / Import (a JSON file, `format: football-planner-saved-routes`)
is the only way to move them to another device.

- **What a saved route holds**: its name ("Start → End" by default,
  editable, renameable), the route line in Valhalla's own polyline6
  encoding (the compact form Stadia sends), both ends (a label, a kind -
  `search`, `tap` or `home` - and a position), the options it was saved
  with (the distance slider and the "home match on" date), the length and
  driving time Stadia gave, when it was saved and when its line came from
  Stadia. **Not the club list**: that is worked out again from the club
  files every time the route is opened, so a club added or moved since is
  right, and opening a route offline uses the saved club files.
- **Opening a saved route asks Stadia for nothing.** It shows the saved
  date and the line's date, and a **Refresh route** button that says it
  costs about 20 credits; a refresh replaces the line, length and time
  and keeps the name and options.
- **Route back** reverses the line already on screen, with no request,
  and is labelled **approximate** (dashed line, a tag, and "one-way
  roads, junctions and motorway exits may differ; the length and time
  are the outbound's"). It can be saved as such; refreshing it asks for
  the real route back and drops the label.
- **The terms, re-read 2026-10-03 on a runner** (`stadiamaps.com/terms-
  of-service/`, still "Effective March 18, 2026"; the clauses as quoted
  in "The installable app" above, unchanged). Two clauses decide this:
  client-side caching is allowed only as long as the HTTP caching
  headers say, **or 7 days when there is no header**; and "permanently
  storing results ... from the Stadia Maps Geocoding APIs" is forbidden
  without a paid plan. **Stadia's search and route answers carry no
  `Cache-Control` header** (measured the same day; tiles carry
  `max-age=21600`). So, **Alexandru's decisions of 2026-10-03, both the
  recommended option put to him**:
  - **A place-search answer is kept 7 days**, then dropped (on reading,
    and on every opening of the route panel) and asked again. A search
    answered from the device says so: "saved copy ... no request made.
    Kept 7 days, then asked again." The key is the typed words, folded
    for case and spacing, plus home's position.
  - **A saved route never keeps a search answer.** An end found by
    search is saved as **the words that were typed** and **the route
    line's own first or last point** - routing output, not a geocoding
    result. Stadia's label ("Leonberg, Baden-Württemberg, Germany") and
    its coordinates are not saved. Map taps (a club's name, or "Point on
    the map") and home are saved as they are; neither came from Stadia.
  - **Saved route lines rest on the terms' one exception for keeping
    data**: "caching small amounts of data for offline use in a mobile
    application, not to exceed 100MB cached at a time per device".
    **Whether an installed web app is "a mobile application" the terms do
    not say**; this reading is Alexandru's, made by asking for saved
    routes after the question was put to him. The page refuses a save
    that would take saved routes past **50 MB**. Measured: Stadia's line
    for a real 17.6 km route (Leonberg to Stuttgart) is 2,650 characters,
    so a long trip is tens of KB and the cap is a backstop, not a limit
    anyone should meet.
- **The credit estimate** counts, per device and per UTC calendar month,
  the routes and searches Stadia **answered with success** (a failed or
  refused request is not counted, a search answered from the device is
  not counted), at 20 credits each, and says it is an estimate that
  **leaves out map tiles** (1 credit each, the bulk of the allowance) and
  other devices. The Stadia dashboard is the real figure.
- **Installed app and Chrome tab: the same saved routes, on Android -
  by Chrome's design, not by a test on a phone.** An app installed from
  Chrome on Android runs inside Chrome's own profile, and storage belongs
  to the site (`alexgrozavul.github.io`), so the installed app and a
  Chrome tab on that phone read one IndexedDB. **What was tested**
  (`test_routes.js`): a second tab in the same browser profile sees the
  same saved routes. **What could not be tested here**: a real installed
  app on a real phone - the sandbox has neither. **Where they would NOT
  be shared**: a Chrome Incognito tab, a different browser on the same
  phone, another phone, and an iPhone home-screen app, which Safari
  keeps apart from Safari tabs. Export/Import covers all of those.
- **What deletes them**: *Clear & reset* for the site in Chrome (step 2
  of "Force-refreshing the installed app"), clearing Chrome's browsing
  data for the site, uninstalling Chrome. Uninstalling just the app
  icon is not known to delete them (not tested). The page asks for
  persistent storage on the first save (`navigator.storage.persist()`),
  which Chrome may grant or not; **Export is the backup**.
- **Tested 2026-10-03 in headless Chromium at 390x844**,
  `tools/test_routes.js`, 26 checks, all passing, run by
  `test-pages.yml` - Stadia stubbed throughout. Opening a saved route
  **offline** listed the same 15 clubs as online and the map showed its
  needs-a-connection card.

**Clubs on the same coordinate share one marker.** `drawClubs()` used to
make one circle per club with no idea that another club was already
standing on that pixel, and the circle drawn second covered the first
completely: the club underneath was in the data, on the map, and had no
marker anyone could see or click. It was silent — nothing counted it,
nothing reported it, and the club count in the corner said it was there.
Measured on 2026-09-19 across both country files, before that day's
corrections: **10 grounds carried more than one club, 21 clubs sat on
them, and 11 of those 21 had no reachable marker.** That was one club in
eighteen on the map.

After the corrections of the same day — CS Dinamo București given its
own coordinates, and `skip` rows for the second SSV Ulm item and for FC
Triesenberg — the count was **191 clubs on 182 grounds, 8 of them
shared by 17 clubs**, and all eight were genuinely shared. Two of the
original ten were never shared grounds at all: one was a copied
coordinate and one was a parent club beside its football department.
The feature is what made both of them visible.

Clearing TSV 1860 München II's ground later the same day took one more
club off a shared pin. Counted against the rebuild of 2026-09-19:
**190 clubs on 182 grounds, 8 of them shared by 16 clubs**, and every
one of the eight is now exactly two clubs — six reserve sides at their
first team's ground, plus the Waldau-Stadion and the Stadionul Ion
Oblemenco, which two unrelated clubs really do share. *(Corrected
2026-09-26: the Waldau was never really VfB Stuttgart II's. It was one
of two grounds on that club's Wikidata item, and in 2026-27 the club
plays at neither - see the entry on two grounds under Known open
problems.)* No ground on
either map carries three clubs any more.

Clubs are now grouped by coordinate *before* anything is drawn. A
coordinate with one club is the same circle it always was. A coordinate
with more than one gets a single marker carrying the number of clubs on
it: tapping it lists them, and tapping a name opens that club's own
popup, with a way back to the list. Nothing is merged — the list is a way
in to each club, not a club made out of several. The marker takes the
colour and size of the most senior club on it, and the pale ring round it
is what tells it apart from an ordinary one-club circle.

The grouping is on the **exact** coordinate, and it must stay that way.
Two clubs a few metres apart stay two markers. This is not clustering and
must not be allowed to grow into it: clustering is a different problem
with its own zoom trade-offs, and this only rescues clubs that would
otherwise be invisible. The data says the distinction costs nothing
today — no two distinct grounds in either country file are within 150m of
each other, so exact matching and matching rounded to four decimal places
pick out the same 10 grounds.

**The tier/zoom filter runs first and the grouping second, never the
other way round.** The zoom rule therefore keeps meaning exactly what it
always meant: a club is drawn once its tier's zoom is reached and never
before. A shared marker lists exactly the clubs visible at the current
zoom, and its number is how many those are — it never drags a club onto
the map early because a more senior club happens to share its ground, and
it never hides one that the zoom has switched on. The Fritz-Walter-Stadion
is a plain 1. FC Kaiserslautern circle from z7 and turns into a "2" at
z9 (z11 until 2026-10-03), when 1. FC Kaiserslautern II's tier switches
on. The Grünwalder
used to do it twice — a "2" at z11 and a "3" at z12, when TSV 1860
München II's tier 5 switched on — and since that club's ground was
cleared it is a plain "2" from z9 and stays one at every zoom above.
The corner chip says
how many shared grounds are on screen, so the count is visible rather than
something to discover.

**Tier zoom bands: tier 3 and everything deeper switch on together at
z9, and that is a GUARANTEED PROPERTY, since 2026-10-03.** At z9 - the
zoom tier 3 used on its own before - **every club on the map is drawn,
whatever its tier**, and at every zoom above it. Tiers 1 and 2 keep
their thresholds (z0 and z7), so the country view is unchanged.
`TIER_FROM_ZOOM` lists tiers 1 and 2 only and `zoomForTier()` gives
every tier from 3 down `DEEP_TIER_ZOOM`, 9, so a tier 9 or 10 club found
later needs no change. The map's `minZoom` is 3 (it was unset), and
`zoomDelta` and `zoomSnap` are 1 - Leaflet's defaults, **checked in the
vendored copy and on the live map rather than assumed**, and now also
set explicitly - so the map always rests on a whole zoom and is either
below 9 or at it. **`tools/test_zoom.js` holds the property**: it fails,
naming each club, if any club on the map is not drawn at z9, and it runs
on every change to the page. First run: 556 of 556 clubs drawn at z9.
**The earlier "eight taps" framing is dropped.** It is not written
anywhere in this repo or its history (searched on 2026-10-03), so it is
recorded here only as dropped: the rule is no longer how many zoom steps
it takes to reach a deep club, it is that z9 shows them all.
**What it costs, measured 2026-10-03** in headless Chromium at 390x844,
CPU slowed 4x, z9, median of 15 (this sandbox, not a phone):

| area | clubs on screen at z9 | `drawClubs()` | zoom 8 to 9, to painted frame | one pan |
|---|---|---|---|---|
| Ruhr, this rule | 22 | 75 ms | 154 ms (worst 220) | 61 ms |
| northern Italy (Milan), this rule | 6 | 80 ms | 161 ms (worst 209) | 79 ms |
| Bucharest, this rule | 16 | 69 ms | 155 ms (worst 244) | 59 ms |
| Ruhr, the old rule | 11 | 62 ms | 133 ms (worst 411) | 57 ms |
| northern Italy, the old rule | 6 | 65 ms | 153 ms (worst 291) | 67 ms |
| Bucharest, the old rule | 16 | 70 ms | 128 ms (worst 210) | 66 ms |

531 markers are in the layer at z9 now, against 443 under the old rule.
**The change costs roughly 10-20 ms on a zoom to z9 and nothing
measurable on a pan**; the pan cost is the same under both rules. The
numbers are noisy run to run (the "worst" column shows it), and a pan at
about 60 ms with the CPU slowed 4x is the existing SVG renderer, not
this change: every marker is an SVG path (the canvas line in `initMap()`
still does nothing - see Known open problems), and 556 clubs is still
well under the 1,000 to 2,000 at which canvas was measured to win.
`test_zoom.js` prints the same table on every run. **On the first GitHub
runner (PR #53)** the same measurement read: `drawClubs()` 27-31 ms
under this rule against 24 ms under the old one, zoom 8 to 9 38-45 ms
against 32-34 ms (worst 81 against 72), and a pan **below the
resolution of the method** - the empty two-frame wait is subtracted, and
on a fast machine a pan takes less than one frame, so the pan column
came out between -11 and +1 ms. Read a negative pan as "under a frame",
not as a number. Neither machine is a phone.

**Tier zoom bands for tier 4 and deeper were merged into one, 2026-09-19.**
*(Superseded on 2026-10-03 by the entry above: the shared band now starts
at tier 3 and z9. Kept as written for the reasoning.)*
Until then `TIER_FROM_ZOOM` gave every tier its own threshold, topping out
at tier 5's z12. europlan-online's own club-to-ground link (see below)
turned up real clubs as deep as tier 8 — Bezirksliga, two levels past
where the scheme stopped — and a scheme with a ceiling has only two ways
to handle a tier it was never built for: drop the club off the map
entirely, or draw it at the deepest tier it knows, which is a false
shallow tier. Neither is acceptable, so the per-tier scheme now stops at
tier 3: `TIER_FROM_ZOOM` lists zooms for tiers 1-3 only, and tier 4 plus
every tier deeper than it — 5, 6, 7, 8, and whatever is found after —
switch on together at z11, the zoom tier 4 used on its own before.
`zoomForTier()` in `index.html` is what does this, and a newly
discovered tier 9 or 10 club falls into the same band with no code
change. The Fritz-Walter-Stadion and Grünwalder examples just above
still read true — both are tier 4 clubs and tier 4's own zoom did not
move — but a shared ground pairing a tier 4 club with a tier 7 one now
turns from a "1" straight into a "2" at z11, never a "1" and later a "2".

Tiers 1-8 also got their own colour, because tier 4 and 5 used to both
render as barely-different greys. Tier 1 stays red, 2 amber, 3 blue; 4
is now teal, 5 green, 6 purple, 7 pink, 8 a warm gold-brown. The legend
still lists all eight separately, each with its own colour and label,
even though several now share one zoom threshold.

**Five of the six europlan clubs found below tier 5 are now at their
real tier.** The entry on the 20 europlan corrections below explains
why six of them were left at Wikidata's stale Regionalliga tag: the
zoom scheme topped out at tier 5, so writing their true level would
have taken them off the map rather than moved them down it. Now that
tier 4 and everything deeper share one band, `clubs-manual.csv` gives
five of the six their real tier: FC Kray, Lupo Martini Wolfsburg and
Eutin 08 to 6 (their Landesliga), VfR Garching to 7 (Bezirksliga
Oberbayern Nord), VfB Hüls to 8 (Bezirksliga Westfalen 11). The sixth,
FC Viktoria 1889 Berlin, is left as it was: europlan's own pages never
named the men's first team's league on any page read, only the
women's team's and the reserve side's, so there is no level to put in
the cell. A blank stays blank rather than guessing tier 4 is wrong or
right.

---

## Secrets

`FOOTBALL_DATA_TOKEN` is in Actions secrets. It must never appear in
client code, in `data/`, or anywhere under `calendars/`. No other key is
needed: Wikidata, Overpass and OpenLigaDB are all free and keyless.

**The Stadia Maps key in `index.html` is a deliberate, documented
exception to "no keys in client code."** The map tiles moved off
`tile.openstreetmap.org` on 2026-09-19 — OpenStreetMap's own tile policy
says that server may be blocked without notice and carries no SLA, which
is not something to build an ongoing-use app on. Stadia Maps requires
either an API key or domain-based authentication for anything other than
`localhost`/`127.0.0.1`, and this project has no server to keep a key
behind: it is a static site with no build step, so the key has to sit in
the page that requests the tiles or the map does not load at all.
Domain-based auth (binding the key to `alexgrozavul.github.io` in the
Stadia dashboard instead of writing the key into the page) was the other
option and was not taken here — if the domain ever needs to change, or
the key needs rotating, that is a plain edit to the `L.tileLayer` URL in
`index.html`. This key only unlocks map tiles; it is not the kind of
secret `FOOTBALL_DATA_TOKEN` is, and it is fine for it to be visible in
a page anyone can already view in their browser's network tab.

**Since 2026-10-02 the same key also pays for routing and place
search**, from the route panel on the map tab, on Alexandru's
instruction. It is now the one constant `STADIA_KEY` in `index.html`
*(removed 2026-10-03; the page now uses no key at all)*,
used by the tile URL, the route request and the place search, so
rotating it is still a single edit. **What each costs, read on
2026-10-02 from stadiamaps.com/pricing** (fetched on a runner; the
sandbox cannot reach Stadia): the **Free plan is 200,000 credits a month,
commercial use not allowed, and no overage** - past the allowance
requests fail rather than bill. Raster tile **1 credit per tile**;
Standard Routing **20 per request**; Forward Geocoding **20**;
Autocomplete v1 **20**, v2 **1** (but no coordinates); Place Lookup **20
per place**; Reverse Geocoding 20. The routing and autocomplete
documentation pages both carry the "Free" plan badge. So a route between
two typed places is 60 credits, and between home and a tapped point 20;
ten routes a day of the dearer kind is about 18,000 a month, under a
tenth of the allowance. Tiles are what the allowance is mostly spent on,
and nobody has measured how many a month this app uses - the Stadia
dashboard shows it.

**The key is NOT restricted to a domain, and the brief that asked for
this entry said it was.** Measured on 2026-10-02 from a runner: a tile
request with the key and **no** Origin or Referer header, and one sent
as from `https://example.com`, were both answered HTTP 200, and the
route and geocoding API answer `Access-Control-Allow-Origin: *`. That is
consistent with the paragraph above (domain-based auth "was not taken").
So anyone who copies the key from the page can spend this account's
credits, and since routing is 20 times a tile per request, that matters a
little more than it did. On the free plan the worst case is the
allowance running out and the map going blank until the month turns, not
a bill. **Restricting it is Alexandru's call and is done in the Stadia
dashboard, not in this repo**: Stadia's own documentation recommends
domain-based authentication for web apps (it checks the browser's Origin
and Referer), and with it the page could drop the key altogether.
Nothing was changed here.

**Domain-based authentication is now on, 2026-10-02, and the page
STILL ships the key - on purpose, until Alexandru says otherwise.**
*(He said otherwise on 2026-10-03: the key is out of the page - see
"The key left the page" below. Kept as written, for the measurements.)*
Alexandru registered `alexgrozavul.github.io` in the Stadia dashboard
before the session that measured this. Stadia's own page,
`docs.stadiamaps.com/authentication/` (read on a runner; it answered 200
this time), says domain auth "works by validating the Origin and Referer
headers that browsers automatically send with every request", calls it
"the most secure option" for production websites, needs no key for
`localhost`/`127.0.0.1`, and warns about a `Referrer-Policy:
no-referrer` (this page sets none) and about forgetting a subdomain. An
API key is still needed outside a browser. **Measured from a runner, no
key on any request** (tile / route / place search):

| Origin and Referer sent | tile | route | search |
|---|---|---|---|
| `https://alexgrozavul.github.io` (both headers, or Referer only) | 200 | 200 | 200 |
| `https://football-planner-test-q7x2k.example.net` | **200** | **200** | **200** |
| `https://example.com` (Referer only for the tile) | 200 | - | 200 |
| `https://fbplanner-q7x2k-test.net` | 401 | 401 | 401 |
| `https://alexgrozavul.gitlab.io` | 401 | 401 | 401 |
| `https://example.org` | 401 | 401 | 401 |
| `https://someoneelse.github.io`, `https://alexgrozavul.github.io.evil-test.net` (tile only) | 401 | - | - |
| `https://football.alexgrozavul.github.io` (a subdomain) | 200 | 200 | 200 |
| `http://localhost:8000` (tile only) | 200 | - | - |
| neither header | 401 | 401 | 401 |
| `https://alexgrozavul.github.io` **with a made-up `api_key`** | 200 | 200 | 200 |
| neither header, made-up `api_key` | 401 | 401 | 401 |

The CORS preflight for the route POST answers 204 for any origin.
**Why the key was not removed.** The instruction was: remove it only if
the three real-domain requests succeed AND a made-up domain is refused.
The first made-up domain chosen happened to sit under `example.net`, a
name reserved for documentation, and Stadia **accepted** it, as it
accepts `example.com` - but refuses `example.org` and every ordinary
made-up domain tried. So the condition as written failed, and the
measurement says that was the choice of test name, not a hole in the
restriction. That is a judgement about Alexandru's stated condition,
so it is his: nothing in `index.html` changed.
**What removing it would take, already tested.** A keyless copy of the
page (the three `api_key` uses taken out, nothing else) was opened in
headless Chromium on a runner AS IF served from
`https://alexgrozavul.github.io/Football/` (the page and data answered
from the checkout, every Stadia request real): 12 of 12 tiles loaded,
"Leonberg" and "Augsburg" were found, a 173 km route was drawn, no
request carried a key, no script error. Served as from
`https://fbplanner-q7x2k-test.net` the same copy got 401 on every tile
and both searches, and said "Place search failed: HTTP 401".
**Correction to the paragraph above**: its `example.com` request proved
nothing, since `example.com` is let through with no key at all; its
no-header request with the key answering 200 is what showed the key is
usable anywhere, and that is still true of the key.
**Deleting the old key in the dashboard** looks safe even while the page
still carries it: a request from the real domain with a made-up key is
answered 200 on all three, so Stadia falls back to the domain when a key
is unknown. Not measured: whether a key that existed and was revoked is
treated like a made-up one (it could not be tested without revoking it).
The cautious order is page first, key second; nothing else in the repo
uses the key (searched), and git history keeps it, which is the reason
deleting it matters.

**The key left the page on 2026-10-03, on Alexandru's instruction**
(the three edits tested 2026-10-02: the tile URL, the place search and
the route request; `STADIA_KEY` is gone). Every Stadia request is now
authenticated by the domain alone. `sw.js` went to `SHELL_VERSION` `v2`
in the same change, so every installed phone drops its keyed shell copy.
**Checked keyless on a GitHub runner the same day**, the edited page in
headless Chromium served as from `https://alexgrozavul.github.io/Football/`
with every Stadia request real, and again on the final code of the same
change (tiles fetched by `StatusTiles`, saved routes in): 12 of 12 tiles
HTTP 200, "Leonberg" and "Augsburg" found, a 173 km route drawn, saved,
the page reloaded and the saved route reopened with **no** second route
request, the credit estimate at 60 (one route, two searches), **0 of 51
requests carrying a key**, no script error. Served as from a made-up
domain: 401 on every tile and search, and the map card read "Stadia Maps
refused the map tiles ... HTTP 401". The probe that did this was a
temporary job, removed before the merge. Nothing else in the repo uses the key (searched again).
**When the old key can be deleted in the dashboard: once this change is
live on GitHub Pages**, about a minute after the merge. From then on no
copy of the page anybody loads carries it. What is left: a phone that
has not opened the app online since still holds the old page, but it
only uses that page offline, where it asks Stadia for nothing; and an
old page left open in a browser tab still sends the key until it is
reloaded - which, from the real domain, keeps working with an unknown
key (the made-up-key measurement above). Not measured, because it
cannot be without doing it: whether a *revoked* key is treated like a
made-up one. After deleting it, open the app once and check the map
loads; if it does not, the card now says Stadia refused the tiles.
The key stays in git history, which is why deleting it is worth doing.

**The service worker saves nothing from Stadia** - no tile, no route,
no search result. **The page itself keeps two things since 2026-10-03,
in the browser's IndexedDB on that device**: routes Alexandru chose to
save, and place-search answers for 7 days. What Stadia's terms say, and
how each rests on them, is in Conventions, "The installable app" and
"Saved routes". Read both before changing either.

---

## Known open problems

- **The VfB research contradicts the hand-written VfB entries of
  `football-rules.json` in several places - found 2026-10-07, nothing
  changed: Alexandru decides** (no tool writes that file).
  - **`vfb-presale-active`** (2026-11-30, inferred; "3 months after
    joining"). **The rule is supported** - three months, since 1 Jul 2025,
    for the e.V. and the kids' clubs alike (V1, V4, V6, V7). **The date
    cannot hold**: `vfb.memberStatus` says "not a member - decision
    pending", and a membership applied for on 7 Oct 2026 takes about two
    weeks to process, so the right would activate around mid to late
    January 2027 at the earliest. **It matters for the Bayern home game**:
    matchday 18 is a placeholder at late January 2027, and by the
    six-weeks pattern its members' sale would open in December 2026 -
    before a membership taken out now would have its presale right.
  - **`vfb.procedure.home`**: "High-demand fixtures use an application
    lottery". **Since 2025-26 home games are not drawn**: every members'
    sale is an online sale with a virtual queue, and applications with a
    draw are used only for away games with a members' allocation under 500
    (V1, V18). The lottery was 2024-25's Champions League practice (V16).
  - **`vfb.procedure.pricing`**: "Member discount EUR 17". The **EUR 17 is
    the season-ticket member discount** (V14). For day tickets the club's
    help centre lists reductions for under-18s, 65+ and disability and says
    "Weitere Ermäßigungen sind nicht vorgesehen" (V8) - no member discount
    on a day ticket was found. On "verify whether they stack": on the
    season-ticket list, member and reduced are alternative prices, not
    stacked.
  - **`vfb.procedure.membership`**: "Fritzle- und Jugendclub cheaper,
    exact fee unconfirmed" - **EUR 33 a year each, plus EUR 18.93 joining
    fee for the Fritzle-Club** (V5, V6, V7). The adult EUR 60 is right
    (ages 26-64; 15-25 pay EUR 30).
  - **`vfb.ageRules.note`**: "Under 18 joins the VfB Fritzle- und
    Jugendclub, not the adult e.V." - **the e.V. has under-18 rates too**
    (EUR 21 to 14, EUR 30 from 15; V5), so it is a choice, not a rule.
  - **`vfb.ageRules.idAtGate: false`**: the ATGB (2.7) require carrying an
    official photo ID and showing it on request, and proof of a reduction
    must be shown unasked when buying (V8, V11) - the KSC finding again.
  - **`vfb-regular`'s action** ("Join the Fritzle- und Jugendclub, then
    wait three months") applies only to someone aged 5-18 (Fritzle 5-12,
    Jugendclub 13-18); for an adult the route is the e.V. Which applies
    depends on an age the files do not hold.
  What the research **supports**: max 2 tickets; the three-month wait;
  "home matches frequently sell out in the member presale" (with the
  early-2026 free sales as the exception); the REWE family block for
  kids'-club members only; "cheapest is standing"; VVS travel included.
- **VfB rows left `unverified`, 2026-10-07, and why** - each a gap, not a
  rule: **`price-category`** (whether prices depend on the opponent - no
  source says); **`capacity`** (below); **`resale-prices`** (no credible
  data; only asking prices on platforms the club bans); and the one
  Bundesliga day price, **EUR 70** (one press report, category and price
  class unstated). **Single-source rows**, confirmed but resting on one
  source: the adult fee (the club's fee table; a 2019 press list gave the
  pre-2022 EUR 48, so it is not a second source), personalisation and ID
  (the ATGB), the 2026-27 sell-outs and "no free sale yet" (the shop's
  live calendar), the season-ticket prices (the club's PDF). **The two
  free-sale press reports are one newsroom** (Stuttgarter Nachrichten and
  Stuttgarter Zeitung, one author), so the early-2026 free sales rest on
  one press source.
- **Which MHPArena capacity the sources use: they disagree, 2026-10-07.**
  60,058 (German Wikipedia's infobox, the map, and English Wikipedia's
  attendance for the Köln game, 4 Sep 2026); 60,449 (the 2011 figure, and
  English Wikipedia's highest 2025-26 home attendance - above 60,058);
  54,812 all-seated for international games (German Wikipedia), while
  English Wikipedia gives 57,000-60,000 for European home games. No club
  figure was read. The club gives 2024-25's average as 59,438.
- **VfB's resale fee against Germany's DFL row - does not sit easily,
  found 2026-10-07.** The DFL row (from the KSC session) caps the official
  secondary market's service fee at 15% of the order value; VfB's
  Ticketbörse keeps 20% from the seller (V1, V8, V12). Either VfB is not in
  the DFL scheme (its page does not say every club takes part) or the 15%
  is a buyer-side fee. Not settled. **Nothing else in the VfB research
  contradicts the KSC or Nürnberg entries on German rules**: the private
  handover caps differ (KSC +15%, Nürnberg +10%, VfB +20% plus EUR 5) but
  each is a club rule, as their rows already say. **VfB's own pages
  disagree** on that cap: the ATGB allow +20% plus EUR 5, the help centre
  says "zum Originalpreis"; both are in the row.
- **REMOVED 2026-10-07, on Alexandru's instruction: the three published VfB
  sale reminders below** (`vfb-schalke-away-members-sale`,
  `vfb-frankfurt-members-sale`, `vfb-lille-members-sale`) are out of
  `football-rules.json` (git history has them); the paragraph is kept for the dates.
- **The three published sale dates are in `football-rules.json` since
  2026-10-07, hand-written on Alexandru's instruction** (no tool wrote them;
  the ticket files still hold none). On 7 Oct 2026 the club's shop announced
  the members' sale for Schalke away (21 Nov) Thu 8 Oct 2026 09:00, for VfB v
  Frankfurt (28 Nov) Tue 13 Oct 2026 09:00 and for VfB v Lille (UCL, 9 Dec)
  Tue 27 Oct 2026 09:00 (for members with no or one 4-package). They are
  `ticketEvents` `vfb-schalke-away-members-sale`, `vfb-frankfurt-members-sale`
  and `vfb-lille-members-sale`, `confirmed`, in the `local` feed (Schalke away
  too, though Gelsenkirchen is not day-trip range - it is a VfB sale), lead
  times 1, 3 and 7 days; the 09:00 is in the title, because a ticket event
  has no time field and the calendar draws it as a whole day. **Each is a
  members' sale**: it needs a presale right, which `vfb.memberStatus` ("not a
  member - decision pending") does not give, and each event says so. They are
  in no bucket entry (`bucket-links-manual.csv` was not touched), so they show
  under Reminders; linking them to `vfb-regular` is Alexandru's call. **The
  dates come from a live shop page read once**; if the club moves a sale, the
  JSON is not updated by anything.
- **The demand file's key cannot hold a non-derby fixture - found
  2026-10-07, not changed (the brief said to use the existing schema).**
  One general row per club per season; VfB's 2025-26 row is therefore
  `varied-by-fixture`, with Bayern (sold out, December) and the January
  free sales in its text. The fix, if wanted, is the familiar one: a
  `fixture` column in the key (or letting a general row name an opponent),
  and one line in the Sell-out record renderer. Alexandru's call.

- **The KSC research contradicts the hand-written KSC entries of
  `football-rules.json` in four places - found 2026-10-06, nothing
  changed: Alexandru decides** (no tool writes that file).
  - **`ksc-fck-sale`**: `dateEstimate` 2026-12-15 (inferred), derivation
    "sales for a late-January fixture typically open around December".
    In the four home derbies read the members' presale opened **26 to 34
    days before kickoff**; mid-December is about six weeks before a
    late-January kickoff, earlier than any of them. The evidence supports
    **late December or early January**, and only the end of December, not
    its middle. The 30-day lead time still puts the reminder in good time.
  - **`ksc-fck-sale`'s action** ("Decide home end or away end FIRST. Away
    end requires FCK membership arranged before release") implies the home
    end is open to a non-member. **It has not been**: no free sale for the
    home derby in four seasons, so the home end too needs a KSC membership
    (or a season ticket) arranged before release - and a membership can
    take up to 30 working days to process.
  - **`ksc.ageRules.idAtGate: false`**: KSC's ticket terms (ATGB 2.6)
    require carrying an official photo ID and showing it on request. No
    derby announcement read mentions an ID check, so "false" may be what
    happens at the gate, but the terms allow one.
  - **`fck.procedure.away` and `sudwest-derby.ticketRoutes.awayEnd`**
    ("requires FCK membership"): Kaiserslautern's own pages for the
    2024-25 and 2025-26 derbies, read in passing, say FCK members
    **and/or FCK season-ticket holders**. FCK's rules are not researched,
    so this is a pointer, not a finding.
  What the research **supports**: `ksc.procedure.home` (ordinary games in
  general sale, the derby sells out), `ksc.procedure.away` (the away end
  at KSC is allocated by the visitor), `sudwest-derby.nextFixture`
  (matchday 19, late January; the fixture file's round is a placeholder)
  and its `missed` (first leg at Kaiserslautern, 15 Aug 2026).

- **KSC rows left `unverified`, 2026-10-06, and why** - all three are
  gaps, recorded so they are not mistaken for rules: the derby's **sector
  separation** (fans in away colours are refused in home areas, but no
  source says whether home areas are otherwise separated; an ordinary
  2026-27 game had separation only towards the guest area); the derby's
  **capacity and attendance** (no source read gives either; see the next
  item); and **resale prices** for the derby (none credible found).
  `inferred`: the 2026-27 derby's price category (A, as in the two seasons
  before) and the "routes in for a non-member" synthesis. **Single-source
  rows**, confirmed but resting on one source only: the membership fees
  (the club's page), the fees row, the 40/20/40 away split, the 2024-25
  alcohol ban, the 2025-26 high-risk classification (press), the 2026-27
  away-derby prices (press restating the club; the club's 2025-26 article
  gives the same figures), and the DFB § 32 country row (the DFB's own
  text).
- **Which Wildpark capacity applies to the derby: none of the sources
  says, 2026-10-06.** The figures in play: **33,180** (the club's
  announced matchday capacity for 2025-26, on the map and on German
  Wikipedia), **34,302** (English Wikipedia's 2026-27 table), **32,190**
  (the largest 2024-25 home attendance, v 1. FC Köln, Die falsche 9), and
  Wikidata's old **29,699** (repeated by news.de). No derby attendance was
  read, and nothing says whether the derby is played with buffer blocks
  (which DFB § 32 lists as a measure for high-risk matches).
- **KSC's ticket terms page holds two wordings of clause 5.1, found
  2026-10-06.** One makes children up to 14 "Kindertickets" and under-18s
  reduced; the other makes every under-18 reduced. Which is current was
  not settled; the rows cite only what both say. No "Stand" date was found.
- **The DFB rules were read in the edition of 1 Feb 2023**; whether a
  newer edition exists was not looked for. Both DFB country rows say
  `appliesTo` `unknown`, because which competitions count as
  "Bundesspiele" is defined in §§ 41-42 of the DFB-Spielordnung, not read.

- **A `requested` ticket shows "You hold tickets" - built as the brief
  worded it, 2026-10-04, Alexandru's to confirm.** The brief says an
  entry linked to "a held ticket" shows the phrase, and every record on
  the Me tab's "Tickets held" list is one, whatever its status. So a
  ticket only *requested* (a ballot entered, nothing won) and one
  *transferred* (which may mean passed on to someone else) both put
  "You hold tickets" on the entry; the statuses are shown beside the tag
  so it never hides which. If he wants the phrase only for `won` and
  `bought` (or not for `transferred`), it is one line in `heldFor()`.

- **No movable school day is entered - found 2026-10-04, Alexandru's to
  fill in.** The brief's holiday rows ended with a placeholder,
  `[movable days: Beweglicher Ferientag,YYYY-MM-DD,YYYY-MM-DD,...]`,
  which was never filled in. It was left out rather than guessed (rule
  1), so `data/holidays-manual.csv` holds six blocks and the school
  start, and the calendar says in every month of the span that movable
  days are not entered. The ministry's page says the schools of
  2026/2027 still have **four** movable days, chosen by each school - so
  the dates have to come from his school calendar. One line each:
  `Beweglicher Ferientag,2027-MM-DD,2027-MM-DD,school-holiday-movable,confirmed,school calendar photo,`.
- **The ministry's footnotes 1 and 2, read 2026-10-04 on a GitHub runner
  (no date changed because of them).** Footnote 1, on Herbstferien 2026:
  "Am 31. Oktober ... 2026 ... (Reformationsfest) ist schulfrei" - 31 Oct
  2026 is a Saturday, the day after the block ends. Footnote 2, on
  Osterferien 2027: "Am ... 25. März 2027 ... (Gründonnerstag) ist
  schulfrei" - Thursday 25 March, five days before the block starts on 30
  March (26 March is Good Friday and 29 March Easter Monday, public
  holidays the file does not hold either). **25 March 2027 is therefore
  school-free and shows unshaded**; adding a row for it is his call.
  Footnote 3 is about the movable days (above). Both notes are in the
  rows' `note` cells. Every date in his rows matches the ministry's page.

- **The map's top row at 390 px: nothing overlaps or is cut off at the
  default text size, but it breaks at a larger phone font size, and the
  search box is the reason - reported 2026-10-03, nothing changed:
  Alexandru decides.** Measured in headless Chromium at 390x700, every
  chip's rectangle compared with every other and each checked for text
  wider than its box.
  - **At the default text size: no overlap, no cut-off, nothing
    off-screen.** The club-count chip and the search box sit side by side
    with a 6 px gap and the search box shrinks to fit it (167 px wide at
    z3, 161 at z7-9, 154 from z10, when the count reads "556 clubs · z10 ·
    25 shared grounds"); the home chip, Route and Derbies (Near me since
    the same day) sit on the row below. The home chip has room for about 45 characters of label before
    it touches Route (the label is `settings.home.label`, "Leonberg, DE"
    today). Real Android phones use Roboto, which is narrower than this
    sandbox's fallback font, so there is probably a little more room there.
  - **Re-measured 2026-10-03 after "Derbies" became "Near me"**, at
    390x700 and 390x500, zooms 3, 8, 9, 10 and 13, by `test_nearme.js` on
    every change since: **still no overlap, no cut-off and nothing off
    screen** at the default text size, including the search placeholder.
    Near me is 66 px wide against Derbies' 61, so the free space between
    the home chip and Route went from 159 px to 154 px; nothing else on
    the row moved. Nothing needed fixing. The larger-font breakage below
    is unchanged and still Alexandru's to decide.
  - **The search text really is larger than the chips, on purpose:** the
    box is 16 px (the chips are 12 px) and 33 px tall against the chips'
    31, because under 16 px iOS zooms the page when a box is focused.
    Android Chrome does not, so the reason does not apply on Alexandru's
    phone, but the page cannot know which phone it is on.
  - **With the phone's font size raised, the row does break - emulated,
    not seen on a device**: the page's text sizes were multiplied by 1.15,
    1.3 and 1.5 (what Android's "font size" setting does to web text).
    From **1.15** the club-count chip wraps to two lines and grows to 54
    px, so the whole top block grows from 70 px to 94 px and covers more
    map; at **1.3** the search box has shrunk to 133 px, and its
    placeholder is **cut off - "Find a clu"** - which is exactly what the
    screenshot showed; at 1.5 the box is 121 px. Even then no chip overlaps
    another and none leaves the screen, so the only damage is the wrapped
    count chip and the clipped placeholder.
  - **"The Route button overlaps map labels" is the chips being slightly
    see-through, not an overlap of chips.** Every chip is 94% opaque
    (`rgba(22,27,34,.94)`) with an 8 px blur behind it, the search box 96%,
    so a street or place name under Route shows through faintly. The
    sandbox cannot load Stadia's tiles, so this was read from the style,
    not seen on a real map.
  - **Proposed fix, for him to choose between**: (a) put the search box on
    its own full-width row above the chips, which gives the placeholder
    room at any font size and moves nothing else - costs about 35 px of
    map; (b) keep the row and shorten the count chip to "556 clubs · z9"
    with the shared-ground count only in the coverage panel - the chip
    stops wrapping at 1.15 and the search box keeps its width, but the
    shared-ground count leaves the map; (c) make the chips fully opaque,
    the cheap answer to the see-through complaint and independent of the
    other two. (a) and (c) together would deal with everything above;
    none is built.

- **The Milan derby's first leg: your notes and the fixture file
  disagree by a day - found 2026-10-04, not changed: Alexandru decides.**
  `football-rules.json`'s `derby-madonnina` gives the first leg as
  **Sun 1 Nov 2026**, matchday 10, `dateSource` `confirmed`;
  football-data.org's Serie A file has AC Milan v Inter, matchday 10, at
  **2026-10-31T19:45Z, status TIMED** - Sat 31 Oct, 20:45 German time, a
  set kick-off, not a placeholder. The bucket card shows both, each
  labelled. Rule 3 says the hand-written date wins wherever it is used
  (a calendar built from it says 1 Nov), and no tool may write to that
  file, so the fix, if the fixture file is right, is his edit.
  `milan-derby-sale-nov`'s derivation ("one month before the 1 Nov
  fixture") rests on the same date.

- **The Inter card on the Ticket info tab states "phase 1 (open
  worldwide)" flatly, and the researched rules contradict it - reported
  2026-10-03, not changed: Alexandru decides.** *(Since 2026-10-04 that
  card is on the Bucket list tab, inside the Derby della Madonnina entry
  under "Ticket windows (reminders)", with the same disputed tag and
  warning, and Inter's researched phases are in the same card under
  "Ticket rules". Inter's notes now carry an "unverified" tag - but only
  for Age rules, which is all the file marks.)* The card is
  `football-rules.json`'s ticket event `inter-derby-phase1`, titled
  "Inter home derby phase 1 (open worldwide)". It sits under "Past,
  disputed or undated" with a red "disputed — do not trust" tag and its
  warning about the year (13/21/24 August match 2026 and 2015). **Both
  marks are about the DATE**; nothing on the card questions the claim in
  its title. `club-ticket-phases.csv` (from Inter's own 2025-26
  announcement, the derby PDF's I2) has four season-ticket-holder phases
  first and no open-to-everyone phase before open sale - the
  contradiction already listed under "The derby PDF contradicts
  `football-rules.json` on Inter". The same claim is in the `inter` club
  entry ("Phase 1 - OPEN TO EVERYONE WORLDWIDE") and the
  `derby-madonnina` bucket item's `saleRoute`, both shown as written on
  Inter's club sheet beside the researched phases, and on the Bucket list
  tab. **Smallest honest fix, for him to choose**: either edit the three
  texts in `football-rules.json` himself (no tool writes to it), or have
  the page add one tag to a Ticket info card whose club has researched
  phases that disagree - "unverified, see researched rules on the club
  sheet" - which would be a page change keyed by hand to that event id,
  since nothing machine-readable says the two disagree.

- **Derbies, 2026-10-03: 248 rows, 197 with both clubs on the map,
  102 of those with a fixture source on both sides.** Per country
  (country of the clubs; a cross-border pair has its own line):

  | | rows | both on map | fixture source both sides |
  |---|---|---|---|
  | AT | 8 | 6 | 0 |
  | BE | 15 | 12 | 0 |
  | CH | 13 | 10 | 0 |
  | DE | 25 | 24 | 21 |
  | ES | 17 | 15 | 11 |
  | FR | 35 | 25 | 9 |
  | GB (incl. Wales) | 50 | 37 | 37 |
  | GR | 16 | 9 | 0 |
  | IT | 16 | 13 | 10 |
  | NL | 28 | 28 | 13 |
  | RO | 15 | 11 | 0 |
  | RS | 9 | 6 | 0 |
  | DE/ES (Bayern v Real Madrid) | 1 | 1 | 1 |

  76 of the 197 are in different divisions this season. 51 rows wait
  with `offMap`. `check_derbies.py` exits 0. The panel was tested in
  headless Chromium at 390x844 (`tools/test_derbies.js`, 16 checks):
  4 derbies within 100 km of Leonberg (Stuttgart derby, Baden-
  Württemberg derby, Südwestderby KSC v FCK, Ostalb derby), 171 within
  1,500 km, every one opened: 70 show a meeting, 27 "no meeting in the
  fixture data", 74 a club with no fixture source. `test_pwa.js` still
  passes 22 of 22. **Not tested on a real phone.**
  - **Well-known derbies with both clubs on the map and no fixture source
    on at least one side**: every Austrian, Swiss, Romanian, Serbian,
    Greek and Belgian derby (the Vienna derby, the Zürich derby, both
    Eternal derbies, the Cluj derby, the Derby of the Eternal Enemies,
    the Classico, Anderlecht v Club Brugge - Brugge is linked to the
    Champions League only), the Stuttgart derby (Kickers, tier 4), the
    Derby della Lanterna (Sampdoria, Serie B), Lyon v Saint-Étienne
    (Ligue 2), the Asturian and Canary Islands derbies (Segunda), and
    the Dutch derbies with an Eerste Divisie side.
  - **The Südwestderby is ambiguous, and football-rules.json's
    `sudwest-derby` was pointed at only one reading.** German Wikipedia
    uses the name for KSC v Kaiserslautern (the KSC article), KSC v VfB
    Stuttgart (the Baden-Württemberg-Derby article) and Kaiserslautern v
    Waldhof Mannheim; English Wikipedia's German list uses it for
    Kaiserslautern v Saarbrücken. The `rulesId` row is KSC v FCK, the
    pair football-rules.json names. Which name Alexandru wants is his.
  - **football-rules.json's derby entries, read and not written**: nine
    of its derby-shaped bucketList entries have a row pointing at them.
    The Ostderby (Dynamo Dresden v Hansa Rostock) has **no row**: no page
    the probes read names it (the German list's Union v Hansa row is
    unnamed). Old Firm, the Intercontinental Derby and the Prague derby
    are outside the twelve countries. Both German fixture files put the
    Frankenderby and KSC v FCK on Sun 31 Jan 2027 13:30, an OpenLigaDB
    round at one kick-off, inside both entries' inferred windows.
  - **Left out on purpose, so the next pass does not rediscover them**:
    unnamed list lines (Dinamo v Rapid, OFK v Red Star and the other
    Belgrade pairs, Union v Hansa, Gent v Lokeren, PSV v Feyenoord,
    Roda v VVV and v MVV, Almere v Telstar, Sion v Lausanne, Xamax v
    Sion); named but uncited ones (Lustenau, Vorarlberg and Lower Austria
    derbies, Hunedoara derby, Severnobački derby, Serbian El Clasico,
    the Southern Railway rivalry, Derby de Vaud, Derby Neuchâtelois,
    Battle of Flanders, Hainaut derby, Vissersderby, Graafschap v Go
    Ahead, the Bochum derby, most of the Greek and Italian lists); the
    Holstein derby (Kiel is not linked as a club in the row); rowspan
    rows of the German table; and Wikidata rivalry items with no article
    found (Südderby Bayern v VfB `Q16637328`, Kölner Stadtderby,
    Aris v Iraklis, PAOK v Iraklis, Kennemerland derby). Each needs a
    source that names it before it goes in.
  - **`check-derbies.yml` could not be dispatched on the branch**: a
    new workflow file runs by `workflow_dispatch` only once it is on
    `main`, so the branch check was its `pull_request` trigger.
  - **Every row rests on Wikipedia** (articles, and lists' cited
    entries). That is a third party's record of the rivalry, which is
    what was asked for; no club's own page was read.

- **Belgium's top two tiers are on the map, 2026-10-01: Pro League 18 of
  18, exact; Challenger Pro League 13 drawn for 15, nothing at the wrong
  tier, and the four U23 sides wait on four roster links that are
  Alexandru's call.** *Since 2026-10-02 the Challenger Pro League is
  **15 of 15**: the four links are in, Jong KAA Gent and RSCA Futures are
  on the map, and the roster check reads Belgium **33 `ok`** and nothing
  else (sub-entry "Jong KAA Gent and RSCA Futures" below).* Same pipeline and standard as the eleven countries
  before it, run through six throwaway probes on a GitHub runner (removed
  in the same branch); the sandbox still answers 403 to CONNECT for
  Wikidata, Wikipedia, StadiumDB and Overpass. Tiers 1 and 2 only; the
  Belgian Division 1 (third tier) and below were deliberately not touched.
  The roster check reads **29 `ok` and 2 `extra-not-in-roster`**.
  - **The file is `BE.json`. The league Q-ids were read, not
    remembered**: `Q216022` Pro League (enwiki *Belgian Pro League*;
    *Belgian First Division A* redirects to it) and `Q23925620` Challenger
    Pro League (enwiki *Challenger Pro League*; *Belgian First Division B*
    redirects to it). Neither carries `P3983`; both carry `P17` Belgium
    (`Q31`), as does every club item read. **A trap worth naming:**
    `Q233199` is labelled "Belgian First Division B" in English but is the
    old Second Division (1909-2016, `P576` 2016, succeeded by
    `Q23925620`). Six Belgian items carry it - Virton's and Lierse's as
    their only tag, Lierse's at PREFERRED rank - and it is **not mapped and
    must not be**: it is a league history. Labels are asked in English,
    then Dutch, then French.
  - **The country check is weak for BE, and that is written down rather
    than fixed.** The box (`Q31`'s own `P1332`-`P1335`) holds Lille and
    the French Nord, the north of Luxembourg, Zeelandic Flanders,
    Maastricht and Aachen, so a neighbouring club carrying a Belgian tag
    would be caught only by `P17`. It flagged no Belgian club.
  - **The season articles.** The Pro League's is one stadiums table with a
    matricule column, 18 of 18 resolved. **The Challenger Pro League's
    stadiums table is not recognised by the parser** (the Swiss Super
    League shape), so the reader takes the league table: 15 rows, 11 read
    and resolved, and **four U23 sides left out and named** - "Club NXT
    U23" and "RSCA Futures U23" link articles WITHOUT the U23 marker (the
    reserve side's own article, so the guard refuses on the marker), and
    "Jong Genk U23" and "Jong KAA Gent U23" link their PARENT clubs (the
    Rapid II shape). The guard is right to refuse all four; the remedy is
    a hand link.
  - **Jong KAA Gent and RSCA Futures are on the map, 2026-10-02, on
    Alexandru's instruction to add each only if two independent sources
    confirm its ground** - lines 255-256 of `clubs-manual.csv`, the
    hand-named fallback, tier 2 by hand, each under its own Q-id. Read on
    a runner through three throwaway probes, removed in the same branch.
    **Jong KAA Gent** (`Q117384089`) at the **Planet Group Arena**: Dutch
    Wikipedia (from 2025-26, after three seasons at the Chillax Arena in
    Oostakker) and europlan-online's ground page, which lists Jong KAA
    Gent there at level 2 - and lists KAA Gent Ladies, not Jong, at the
    old Oostakker ground. It shares KAA Gent's pin and figure exactly
    (20,000), the reserve-side shape. **RSCA Futures** (`Q114056326`) at
    the **Dakota Arena** in Deinze (formerly the Burgemeester Van de
    Wielestadion): Dutch Wikipedia's article on the ground (since January
    2025), the English season article's note, and europlan's ground page
    listing RSCA FUTURES at level 2; position the ground's item
    `Q2653249`, europlan's 10 m away. **Capacity blank**: 7,515 three
    times against Dutch Wikipedia's reduced 3,482. **Two limits, said
    out loud**: europlan is user-submitted and nobody has shown it did
    not copy Wikipedia - it is this project's usual second source, not a
    proven independent one; and the club's own article, *Het stadion van
    Deinze blijft de thuisbasis van RSCA Futures*, is **unread** - rsca.be
    answered HTTP 202 with an empty body from CloudFront (a bot challenge,
    a stop) and the Internet Archive, which has 2026-05 captures, answered
    429. kaagent.be's Jong pages name no ground in their text. The build
    on the branch named both "surfaced by the hand-named fallback ... ON
    THE MAP"; Belgium is **18 at tier 1 and 15 at tier 2**, and the
    roster check on the branch moved exactly those two verdicts, from
    `missing-from-wikidata` to `ok` - **33 `ok`**. No other country's
    club file or verdict changed; `link_fixtures.py` re-run changes
    nothing (neither club has a fixture source). The OpenStreetMap
    capacity check left Belgium `UNCHANGED` on its first branch run (HTTP
    504), which is not a pass; the second (19:48 UTC) wrote **all twelve
    countries**, Belgium 33 clubs, adding one row: RSCA Futures, "neither
    source has a capacity" - true, its cell is blank on purpose.
  - **The four roster links are written, 2026-10-02, on Alexandru's
    instruction**, lines 6-9 of `data/roster-links-manual.csv`. The roster
    check on the branch read **Club NXT and Jong Genk `ok`**, and **Jong
    KAA Gent and RSCA Futures `missing-from-wikidata`** - and no other
    verdict moved. The instruction expected all four `ok`; two could not
    be, for the reason the paragraph below already gave: neither club is
    on the map, and a link only lets the roster name them. What each
    still needs is a `clubs-manual.csv` row with country BE, tier 2 and a
    ground, so the hand-named fallback brings it in - a tier and a ground
    are Alexandru's to approve, and RSCA Futures' Deinze ground has still
    not been read, so **neither row was written**. Until then the two read
    `missing-from-wikidata` every run, which is true: they are named by
    the division and not on the map. Belgium now reads **31 `ok` and 2
    `missing-from-wikidata`**. As first written:
  - **The four roster links, written up and NOT written (rule 7 - a
    link is an identity claim and Alexandru's to make).** Each is one line
    in `data/roster-links-manual.csv`, ready to paste:
    `2026–27 Challenger Pro League,Club NXT U23,Q101625593,...`,
    `2026–27 Challenger Pro League,Jong Genk U23,Q113884742,...`,
    `2026–27 Challenger Pro League,Jong KAA Gent U23,Q117384089,...` and
    `2026–27 Challenger Pro League,RSCA Futures U23,Q114056326,...`. What
    each changes: **Club NXT and Jong Genk are on the map today** (both
    carry a Challenger Pro League tag) and read `extra-not-in-roster`
    until their line is in; **Jong KAA Gent and RSCA Futures are not on
    the map at all** - neither carries a mapped tag, so only the
    hand-named fallback can bring them in, and its third condition needs
    the roster to name them, which needs the link. With the link each also
    needs a `clubs-manual.csv` row with country BE and tier 2, and a ground:
    Jong KAA Gent plays at the Planet Group Arena from 2025-26 (Dutch
    article; the first team's pin), RSCA Futures in Deinze (the
    Challenger Pro League article's note) - which Deinze ground nobody has
    read.
  - **What the first build brought, 23 clubs against 33 teams, and what
    each difference was:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 17 | 6 |
    | after this pass | **18** | **13** |

    - **Dender** (`Q1065328`) arrived at tier 1 on a PREFERRED Pro League
      tag from 2024 and is at **tier 2 by a hand row** (the FC Wil shape:
      both articles complete, the Challenger article's Team changes table
      and the club's own article say relegated via the play-off).
    - **Lommel SK** (`Q1668203`) arrived at tier 2 on its only tag and had
      no position; it is at **tier 1 by a hand row** (promoted via that
      play-off) and placed at the Soevereinstadion.
    - **Three `skip`ped to the Hermannstadt standard**, each drawn at tier
      2 on a Challenger Pro League tag with no dates: **KSV Roeselare**
      (dissolved 2020, English infobox; "opgeheven 2021", Dutch),
      **Royale Union Tubize-Braine** (Nationale 1, third tier, French
      article) and **SL16 FC**, Standard's U23 side (Eerste nationale per
      its Dutch infobox; not in the 2025-26 Challenger Pro League either;
      it also sat on Standard's own pin with two grounds, the Freiburg
      shape). Shape 4.
    - **Seven promoted clubs whose tags did not follow reach the map
      through the hand-named fallback**, tier 2 by hand, each under its
      own Q-id: **Francs Borains** (no `P118`), **Royal Excelsior Virton**
      and **K. Lierse SK** (only the old Second Division item), **KSC
      Lokeren** (the 2025 club, no `P118`; not the bankrupt Lokeren
      `Q221940`, which `P576` drops), **Sporting Hasselt** (third tier
      tag), **RFC Liège** (fourth tier tag) and **Patro Eisden
      Maasmechelen** (third tier tag).
    - **Three placed that the query returned with no coordinates**:
      **RAAL La Louvière** at the Easi Arena (opened 2025; not the Stade
      du Tivoli next door), **RFC Seraing** at the Stade du Pairay and
      **Club NXT** at the Schiervelde in Roeselare - **that pin rests on
      Wikipedia alone** (the club's English and Dutch articles); its row
      says so.
    - **RWDM Brussels** carries a preferred Challenger Pro League tag, no
      ground and no `P576`; the Challenger article says it was relegated
      to the Belgian Division 1 after being refused a licence. Off the map
      at the coordinates gate, and now a whole-club `rejected` row in
      `coordinate-reviews.csv` so the monthly run cannot offer it a ground
      (shape 6's relegated relative, the Gilortul shape).
  - **Rank blind spot, all three shapes, run by `diagnose-rank.yml` on
    the branch: nothing owed.** Queries A and B: **KV Oostende** (every
    statement deprecated, no `P576` on Wikidata, bankrupt in 2024 by its
    infobox, no position) and **Royal Excel Mouscron** (deprecated,
    `P576` 2022) - both rightly invisible, neither in either article.
    Query C: no Belgian club; the bill has no BE line. The build's own
    fallbacks found nothing hidden.
  - **The league-tag end date (`P582`), measured for Belgium: zero.** Of
    30 truthy Pro League or Challenger Pro League statements on items with
    no dissolution date (two of them the Anderlecht season items), **none**
    carries an end date. Every wrong item
    above (Roeselare, Tubize, SL16, Dender, Lommel, RWDM) has a tag with no
    end date at all, so honouring `P582` would have caught none of them -
    the 2026-09-29 finding a third time.
  - **Not-a-club: the England gaps and the Dutch season-naming gap,
    looked for deliberately.** Two club SEASONS carry a Pro League tag -
    *1991-92* and *1996-97 R.S.C. Anderlecht season*, typed "association
    football team season" - and the net catches both by type; their names
    are caught too, the English one by the 2026-10-01 Dutch fix (year
    range ... "season") and the Dutch one, "RSC Anderlecht in het seizoen
    1991/92", by the trailing year range. **No item carrying either tag at
    any rank is typed "aspect of history", "fictional" or as a match**, so
    England's two kinds and Spain's do not occur here. Because Belgium is
    the first country whose labels can fall back to Dutch AND French,
    **the Dutch word "seizoen" is now a type word and a title opening**
    beside "saison"; checked before it went in, it matches no club name on
    any of the 523 map entries, and the rebuild changed no other country's
    file.
  - **Women's club with a men's tag (rule 6): none, from four angles** -
    see the rule.
  - **Every duplicate shape, looked for rather than waited for.** Shapes 1
    and 2: none - every label of the 33 roster clubs, in all four
    languages, belongs to one club item only, and the roster check names
    each club once. Shape 3: **KAA Gent has a multi-sport parent item**,
    `Q2741852`, typed "sports club", carrying no league tag - never on the
    map. Shape 4: Roeselare, Tubize, SL16 and RWDM, above; the dissolved
    namesakes (Beerschot AC, the old Lommel, Lokeren, Seraing, RWD
    Molenbeek, Excelsior Mouscron and seven more) carry `P576` and the gate
    drops them. Shape 5: none - one club at a time, nothing typed "men's
    association football team" points at a roster club; what does point at
    them is an academy, a futsal club, an U19 side, two stadiums, a
    streaming service and a German squad list. Shape 6: RWDM.
    **One shared pin, genuine**: Club Brugge and Cercle Brugge at the Jan
    Breydel.
  - **Grounds - two wrong, and one copied.** **KAA Gent was drawn at the
    Jules Ottenstadion**, its only `P115`, which carries `P576` 2014; it
    is now at the **Planet Group Arena** (20,000). **Royal Antwerp was
    drawn at the Stadion Broodstraat**, `P576` 1923; now at the
    **Bosuilstadion** (21,000) - 54 m away, so the pin hardly moved, the
    name and the capacity did. **Jong Genk sat on Genk's Cegeka Arena**,
    a copied first-team ground; the Challenger article, its Dutch infobox
    and the ground's Dutch article all say **De Leunen in Geel**, and its
    capacity is cleared (10,524 twice, which Dutch Wikipedia says is the
    pre-2016 figure; 8,000 since). Dender's ground is the same place under
    its 2022 name, the Dender Football Complex. **Sporting Hasselt's pin
    is OpenStreetMap's alone**: its ground's Wikidata item has no position.
  - **Capacities, the UTA Arad rule - every source read, including the
    ones that agree with the map.** Corrected, each where the Pro League
    table and StadiumDB agree within 5% and the map sat outside:
    **Charleroi** 14,891 -> **14,000**, **Mechelen** 13,213 -> **16,700**,
    **OH Leuven** 9,493 -> **10,000**, **Union SG** 5,100 -> **9,400** and
    **Zulte Waregem** 10,200 -> **12,500**; with the ground changes,
    **Gent 20,000**, **Antwerp 21,000**; filled: **La Louvière 8,050**,
    **Francs Borains 6,000**, **Hasselt 8,800**, **Lokeren 12,136**.
    **Two against two, nothing changed, each with a note-only row** (the
    AEL shape): **Genk** (25,000 and the table's 24,956 against 23,718 on
    StadiumDB and the infobox) and **Beveren** (13,290 on Wikidata and
    StadiumDB against 8,190 in the table and the infobox - possibly one
    source, Wikipedia, twice). **Contested and left blank**: Lommel
    (8,000 / 12,911), Seraing (8,207 / 14,328), RFC Liège (4,147 / 3,500
    / 3,000), Jong Genk (above), Club NXT and Patro Eisden (one source
    each). **Contested, the map's figure kept**: Dender (12,000 / 6,429 /
    8,548) and Lierse (14,538 with the ground's infobox / 13,539 /
    15,500). **The map stands** where it agrees with the table and
    StadiumDB is the outlier: Anderlecht (StadiumDB's 28,063) and Standard
    (StadiumDB's 27,670, which is the ground's limited capacity).
    **Antwerp is worth a look**: Dutch Wikipedia says the Bosuil holds
    24,500 since a stand reopened on 5 December 2025, newer than the
    season table - one source, so not taken.
  - **StadiumDB: 37 grounds; 9 agree, 3 differ, 19 not matched** on short
    names ("Zulte", "St-Truiden VV", "Waasland-Beveren"). The three that
    differ are Anderlecht, Standard and Lierse, all weighed above.
  - **OpenStreetMap confirms almost nothing in Belgium**: 208 stadiums,
    **4 with a capacity** - Romania's and Italy's shape. It confirmed
    positions (Gent, Antwerp, La Louvière, Lommel, RFC Liège, Virton,
    Eupen within tens of metres) and supplied Hasselt's. **The first run
    on the branch left Belgium `UNCHANGED`** (HTTP 504, with France, the
    Netherlands and Serbia), so it was not a pass; the second, on the final
    layer (14:35 UTC), wrote Belgium: **31 clubs, 1 agree (Hasselt, 8,800),
    0 differ, 20 Wikidata only, 6 neither, 6 with no OpenStreetMap stadium
    within 500 m** - Club NXT's Schiervelde pin and Jong Genk's De Leunen pin
    among them, so both rest on their Wikidata ground items and Wikipedia,
    nothing else. Italy was `UNCHANGED` on that run. **Worth one look:**
    the OpenStreetMap stadium 22 m from Seraing's Pairay pin is named
    "Stade Hubert Freson" - most likely the same ground under another name,
    not checked.
  - **Fixtures: none.** football-data.org's free tier carries no Belgian
    league and OpenLigaDB is German only; the club sheet says so, and was
    opened in the real page for ten Belgian clubs. **Club Brugge plays
    in the Champions League** and football-data's team 851 "Club Brugge KV"
    is in the review file as `country-unknown` - a team seen only in the
    Champions League is never linked by name. **One `link` row
    (`Q190916,football-data,851,link`) would give Club Brugge its
    Champions League fixtures - Alexandru's call, not written.** *Written
    2026-10-02 on his instruction: the linker reads it back as `linked`,
    and Club Brugge's sheet, opened in the real page (headless), lists its
    eight league-phase matches - seven ahead (Inter, Lens, PSV, Liverpool,
    Napoli, VfB Stuttgart, Bodø/Glimt) and Aston Villa played.
    Its Pro League games are still not fetched, and the sheet's source line
    says Champions League only.*
  - **Merge, under rule 7, 2026-10-01 - and what it rests on.** Every
    workflow dispatched on the branch is green (15 runs), no hand row was
    rejected (the builder's reader first refused twelve Belgian rows for a
    missing name - fixed before any build used them), `check_tickets.py`
    exits 0, the roster check reads Belgium 29 `ok` and the two
    `extra-not-in-roster` written up above and changed no other country's
    verdict, the rank diagnostic owes nothing, and `link_fixtures.py`
    re-run on the final files changes nothing. The real page was opened
    headless (Leaflet from npm, tiles stubbed): all twelve country files
    load, 31 Belgian clubs, no script error. **The OpenStreetMap capacity
    check took four runs**: Belgium, France, the Netherlands and Serbia
    `UNCHANGED` on the first (HTTP 504), Italy on the second, Germany,
    France, Italy and the Netherlands on the third - each left byte for
    byte. **The merge rests on the fourth, 15:15 UTC, on the final code:
    all twelve countries `WRITTEN`.** Nothing that is Alexandru's call
    was decided: the four roster links and the Club Brugge fixture link
    are written up, not written, and every tier, skip and ground change
    is a reviewable hand row that says how to undo it.
  - **Found on the way**: the Overpass name search for the grounds to be
    placed answered HTTP 504 three times and gave nothing; the per-club
    positions rest on Wikidata's ground items, which the earlier
    whole-country OpenStreetMap read confirmed where it could. And a
    women's-team label identical to a men's club's (rule 6, above), which
    is the case for never joining on a name.

- **`index.html` has no automated check of its own - a known gap,
  recorded 2026-10-01 on Alexandru's instruction, to be addressed later
  and deliberately not now.** Every data file has a reader that turns a
  run red: `check_tickets.py`, `check_rosters.py`, the club builder's
  read-back. The page has nothing. No workflow opens it, loads the
  country files through it, or opens a club sheet; a script error, a
  country file missing from `COUNTRY_FILES`, or a sheet that says
  "unavailable" for the wrong reason would reach `main` with every tick
  green. **The last two UI fixes merged on manual headless testing
  only**: "time not set" for placeholder kick-offs (#45, `b8367c8`) and
  the Eerste Divisie fixtures message (`253020f`), and since 2026-10-02
  the route panel. Each was checked by a
  session opening the real page in headless Chromium (Leaflet from npm,
  tiles stubbed) and reading the sheet text by eye - real, but not
  repeatable, not run on a later change, and not part of rule 7's
  "clean". The same is true of every country pass's "the real page was
  opened" line, this one's included. What a check would need is written
  here so the next session does not rediscover it: a local server for
  the repo, Leaflet from a pinned local copy (unpkg is unreachable from
  the sandbox), stubbed tiles, then load every country file and fail on
  any page error, and open a sheet per country. Not built.
  **Two pieces of it exist since 2026-10-02**: Leaflet is now a pinned
  copy in `vendor/`, and `tools/test_pwa.js` is a repeatable headless
  test of the installable app (local server, stubbed tiles, fails on any
  page error, loads every country file). It does not open club sheets,
  and **no workflow runs it**, so it is still not part of rule 7's
  "clean" on its own - a session runs it by hand.
  **Since 2026-10-03 a workflow runs the page tests**:
  `.github/workflows/test-pages.yml` runs `test_pwa.js`,
  `test_derbies.js` and the new `test_routes.js` on every push to `main`
  and every pull request that touches `index.html`, `sw.js`, the manifest
  or the tests, and a failure turns it red - so for a change to the page
  those three are part of rule 7's "clean" from now on. **What is still
  not covered**: no test opens a club sheet per country or checks a
  sheet's "unavailable" reasons; every Stadia request is stubbed, so a
  change on Stadia's side (a header, a status, CORS) shows up only on a
  phone or in a probe like the one in Secrets; a data-only change (a
  cron commit, `data/derbies.csv`) does not trigger it; and nothing has
  run on a real phone.
  **Since 2026-10-03 four more page tests run in the same workflow**:
  `test_zoom.js` (every club drawn at z9, and every club file loaded -
  which closes the "country file missing from `COUNTRY_FILES`" hole
  above), `test_search.js`, `test_coverage.js` and
  `test_sheet_tickets.js` (the ticket section of nine named clubs'
  sheets). Still not covered: a sheet per country, and the fixtures
  section's "unavailable" reasons. `test_legend.js` and, since the Near
  me panel, `test_nearme.js` (its list checked against the club files,
  the location kept off storage and the network, and the top row at
  390x700 and 390x500) run there too.

- **The Netherlands' top two tiers are on the map, 2026-10-01: Eredivisie
  18 of 18 and Eerste Divisie 20 of 20, exact - nothing missing, nothing
  extra, nothing at the wrong tier.** Same pipeline and standard as the
  ten countries before it, run through five throwaway probes on a GitHub
  runner (removed in the same branch); the sandbox still answers 403 to
  CONNECT for Wikidata, Wikipedia and StadiumDB. Tiers 1 and 2 only; the
  Tweede Divisie and below were deliberately not touched. The roster check
  reads **all 38 `ok`**.
  - **The file is `NL.json`.** The league Q-ids were read, not
    remembered: `Q167541` Eredivisie (enwiki *Eredivisie*) and `Q610823`
    Eerste Divisie (enwiki *Eerste Divisie*), neither carrying `P3983`.
    `P17` is Netherlands (`Q55`) on both leagues and on every club item
    read; the Kingdom of the Netherlands (`Q29999`) appears on one 2008-09
    season item and nothing else. The 2026-27 articles are one
    stadiums-and-locations table each: **18 of 18** resolved (17 directly,
    one through a redirect) and **20 of 20**. Four of the twenty are
    reserve sides with articles of their own - Jong Ajax, Jong AZ, Jong PSV
    and Jong FC Utrecht - which the table says are not eligible for
    promotion; they are men's football and are on the map like Rapid II.
    Labels are asked in English first, then Dutch.
  - **The country check is weak for NL, and that is written down rather
    than fixed.** The box is Wikidata's own extreme points (north 53.55,
    south 50.7504, west 3.3561, east 7.2274, with a margin) and holds the
    north of Belgian Limburg and Antwerp, a strip of Wallonia and the west
    of North Rhine-Westphalia, so a Belgian or German club carrying a Dutch
    tag would pass it and be caught only by `P17`. `Q55` also carries
    Bonaire's points at PREFERRED rank for south and west, which is why the
    box uses the normal-rank European ones; a Caribbean club is nowhere
    near any box. The check flagged no Dutch club.
  - **What the tags looked like, 91 statements on 54 items, all
    listed and read.** Dutch league tags are well kept - most clubs carry
    a dated history with the current league preferred - but the club query
    does not read an end date, and four items are drawn from a tag that has
    ended. Volendam's is the subtle one.
    | | what Wikidata says | what the 2026-27 articles say | done |
    |---|---|---|---|
    | FC Volendam `Q738060` | PREFERRED Eredivisie 2025-2026 (ended) over a normal Eerste Divisie 2026- | Eerste Divisie, and the Eredivisie article's own Team changes table says 'relegated' | tier **2** by a hand row; arrived at tier 1 |
    | Achilles '29 `Q2426022` | Eerste Divisie 2013-2017 | neither; English article: the seventh-tier Tweede Klasse, Dutch infobox: 1e klasse (2026/27) | `skip` |
    | VV DOS `Q784572` | Eredivisie 1956-1970, drawn at tier 1 on **FC Utrecht's pin** | neither; German and French articles: merged into FC Utrecht in 1970 | `skip` |
    | Jong FC Twente `Q14229572` | Eerste Divisie, no dates | not listed; Dutch article: Reservecompetitie since 2018/19 | `skip` |
    | VCV Zeeland `Q134609074` | Eerste Divisie 1990-1992, no ground, **no English label** | not listed; 'was een betaaldvoetbalclub' | whole-club `rejected`, never proposed a ground |

    All three skips meet the Hermannstadt standard: both articles complete
    (18 of 18 and 20 of 20), neither lists the club, and an independent
    statement of the reason. **VV DOS carries a trap worth keeping:** its
    ENGLISH article, titled *VV DOS*, describes DHSC, the 2007 merger that
    dissolved in 2024 - a different club under this item's name - so the
    reason was read from German, French and Dutch Wikipedia instead.
    VCV Zeeland dies at the coordinates gate and would have been offered a
    ground in Vlissingen by `propose_coordinates.py` next month; that is
    shape 6. **Predicted before the build from the probe's read of the
    tagged items, and not measured by a build without the hand rows**: they
    would have brought 40 clubs, 19 at tier 1 and 21 at tier 2.
  - **Rank blind spot, all three shapes, run by `diagnose-rank.yml` on the
    branch: no Dutch club is hidden.** Queries A and B: the worldwide
    census holds two Dutch items, ESV `Q13575023` and VV Concordia
    `Q652605`, both preferred `<novalue>` and both dissolved (2011, 1891),
    and neither carries either mapped league, so nothing is owed. Query C:
    no Dutch club; the bill has no NL line.
  - **The league-tag end date (`P582`), measured for the Netherlands.** Of
    47 truthy Eredivisie or Eerste Divisie statements on items with no dissolution
    date, **four**
    get their tier from a tag that has ended - Volendam, Achilles '29,
    VV DOS and VCV Zeeland - all four dealt with above. The fifth wrong
    item, Jong FC Twente, carries **no end date at all**, so honouring
    `P582` would not have caught it: the same finding as 2026-09-29, again.
  - **Not-a-club: five club SEASONS, caught by type, and a gap in the name
    fallback closed because of it.** *2007-08 AZ Alkmaar season*, the same
    for Heracles Almelo and Vitesse, and two MVV Maastricht seasons are
    typed 'association football team season', which the type word 'season'
    catches. The NAME fallback - for an item whose type says nothing - did
    not know them: it only matched names that START with 'season'. A name
    that opens with a year range and ends in 'season' is now caught too.
    Checked before it went in: it matches those five and no club name on
    any of the 523 map entries, and the rebuild changed no other country's
    file. **England's two kinds (a history article, a fictional club) were
    looked for here and not found**: no item carrying either Dutch tag at
    any rank is typed 'aspect of history' or 'fictional', so nothing new
    was needed for them.
  - **Women's club with a men's tag (rule 6), checked deliberately, from
    four angles: none.** No item carrying either tag at any rank is typed,
    labelled (English or Dutch - 'women', 'vrouwen', 'dames', 'ladies',
    'WFC'), or classed (`P2094`) as women's. **The fourth angle came out
    differently from England's, and the difference is worth knowing:** three
    women's items DO point at big Dutch clubs with `P361` - SBV Excelsior
    Vrouwen `Q29509701`, Go Ahead Eagles (vrouwenvoetbal) `Q138016367` and FC
    Groningen (vrouwen) `Q132315919` - where England had none. None carries
    either men's league tag, so nothing reaches the map; the Vrouwen
    Eredivisie (`Q1785497`) exists on Wikidata and is not mapped. Two of the
    first-pass queries answered HTTP 504 and were redone per club.
  - **Every duplicate shape, looked for rather than waited for.** Shapes 1
    and 2: none - every English label of the 38 roster clubs belongs to one
    item only, no two pins share a ground (the closest pair is Jong FC
    Utrecht and FC Utrecht, 280 m apart on two different grounds), and the
    roster check names each club once. Shape 3: none - no multi-sport
    parent; AFC Ajax's one item is typed club and 'public company' together.
    Shape 4: the clubs above. Shape 5: none - no item typed 'men's
    association football team' points at a roster club; the reserve sides
    (ADO Den Haag II, De Graafschap II, Vitesse II, the U21s) carry no
    league tag and are not on the map. Shape 6: VCV Zeeland, rejected.
  - **Two grounds on one item (the Freiburg shape): one, pinned.** Vitesse
    carries the GelreDome (from 1998) and Klarenbeek (dated 1896-1915, no
    coordinates on its item) at the same rank, so the ground could have
    alternated and Klarenbeek would have dropped the club off the map. The
    GelreDome is pinned: the Eerste Divisie table and StadiumDB both say
    21,248, and the position is the ground item's own.
  - **Grounds - and one wrong one, found by the OpenStreetMap check.**
    **SC Cambuur was drawn at a ground that no longer exists.** Wikidata's
    only `P115` is the old Cambuur Stadion, which the club left in August
    2024 and which was demolished in late 2025 (its English article, and the
    club's own). OpenStreetMap's nearest stadium to the pin was the Kooi
    Stadion, 3,134 m away; the club's article, Dutch Wikipedia, the
    2026-27 table and StadiumDB all say the Kooi Stadion, 15,000. It is now
    at the ground item's own position (`Q122459692`, which OpenStreetMap
    puts within 10 m). The Brentford shape again. **The four Jong sides are
    drawn at training complexes**, not stadiums: Jong Ajax at De Toekomst,
    Jong PSV at De Herdgang, Jong FC Utrecht at Zoudenbalch (280 m from
    FC Utrecht's Galgenwaard, a different ground), and **Jong AZ's pin rests
    on one source** - Wikidata's 'AFAS Training Complex', where the club's
    English infobox says 'Sportcomplex Kalverhoek'; OpenStreetMap has no
    stadium within 12 km and nobody has checked they are the same place. Its
    row says so. Wikidata's `P115` on the Cambuur item still names the old
    ground; the hand row's note says how to go back.
  - **Capacities, the UTA Arad rule - every source read, including the
    ones that agree with the map.** OpenStreetMap carries a figure for only
    five Dutch grounds, so the OpenStreetMap run (all eleven countries
    `WRITTEN`) settled one row, and **a single-country probe printed
    OpenStreetMap's figure for every club before any correction was
    written**, because the review file lists disagreements only and the
    England pass (Villa, Fulham, Stoke) showed what an unread agreement
    costs. OpenStreetMap had no figure for four of the five corrected
    clubs; Den Bosch's is the one that agrees with StadiumDB. **Corrected**, each where the league table and StadiumDB agree
    within 5% and the map sat outside: **AZ Alkmaar** 17,023 -> **19,478**
    (table, StadiumDB and the ground's article, identical), **Excelsior**
    3,531 -> **4,500**, **Go Ahead Eagles** 6,700 -> **10,000** (StadiumDB's
    10,400 not taken), **VVV-Venlo** 7,500 -> **8,000** (table and StadiumDB,
    identical) and **FC Den Bosch** 9,000 -> **8,713** (the table; Open-
    StreetMap and StadiumDB both say 8,500 and the table is within 2.5% of
    both); and **Cambuur** with its ground, above. **Left contested, each
    with a row listing every figure**: **PEC Zwolle** (12,500 on Wikidata,
    14,000 in the table, 13,250 on StadiumDB - no two within 5%),
    **FC Volendam** (6,200 on Wikidata, 7,384 in the table, 6,984 on StadiumDB
    and in both English articles - the table and StadiumDB are 5.7% apart, and
    Wikipedia's own two figures disagree with each other) and **Jong Ajax**
    (5,000 for the whole complex against 2,250 in the table). **The map
    stands where it agrees with a second source and the third is the
    outlier**: Feyenoord (51,577 with StadiumDB's 51,117, the table's 47,500
    the outlier), Telstar (5,200 with OpenStreetMap's 5,200 and the table's 5,338;
    StadiumDB's 3,625 is the outlier, and the ground's own article says 6,000), FC Eindhoven,
    Helmond Sport (StadiumDB's 4,200 is the old Lavans Stadion) and Ajax
    (54,990, OpenStreetMap's 52,342 within 5%). Jong AZ's capacity is blank
    on purpose: 1,000 appears in one source.
  - **StadiumDB: a ground for 18 of 18 Eredivisie clubs and 16 of 20 Eerste
    Divisie clubs**, the four without being the Jong sides. **It caught a
    reserve side on its first run: "Jong AZ" was matched to AZ's own
    stadium** - the Borussia Dortmund II failure on a prefix instead of a
    suffix - because the matcher's reserve markers had no `jong`. It does
    now (`TEAM_MARKERS`); no club name in any other country and no fixture
    team name in any file contains the word, so nothing else moved, and
    the Jong AZ row left the review file on the next run. Short names again:
    "Exelsior" (sic), "Utrecht", "Roda" and "NEC" matched or were read by
    hand where the matcher refused.
  - **Fixtures: 13 of 18 Eredivisie clubs link to football-data.org's
    DED**, which was already fetched. **Five are abbreviations the matcher
    rightly refuses, and each needs one `link` row in
    `fixture-links-manual.csv` - Alexandru's call, so none was written
    (rule 7):** AZ Alkmaar (`Q191264` -> football-data 682 "AZ"), PSV
    Eindhoven (`Q11938` -> 674 "PSV"), Excelsior Rotterdam (`Q370712` -> 670
    "SBV Excelsior"), SC Cambuur (`Q875120` -> 1909 "SC Cambuur-Leeuwarden")
    and Willem II (`Q332664` -> 672 "Willem II Tilburg"). Until then those
    clubs' sheets say fixtures are unavailable. The Eerste Divisie has no
    fixture source; the club sheet says so. **All five rows were added on
    2026-10-01 on Alexandru's instruction**, the Le Mans way: each read
    back as `linked`, the Eredivisie is 18 of 18 linked, and each club's
    sheet was opened in the real page (headless) and lists its Eredivisie
    fixtures - PSV's its Champions League ones too.
  - **Found on the way, not Dutch**: two of the first-pass SPARQL queries
    that look for items pointing at the roster clubs answered HTTP 504 with
    zero rows, which is a failed query and not an empty answer; they were
    rerun one club at a time.
  - **Merge, under rule 7, 2026-10-01 - and what it rests on.** Every
    workflow dispatched on the branch is green on the final code, nothing
    was rejected, `check_tickets.py` exits 0 ("No problems. Every row was
    read."), and the roster check reads **38 `ok`**. The club build is
    green, the rank diagnostic is green (no Dutch club hidden), the StadiumDB
    check is green with Jong AZ's false match gone, and `link_fixtures.py`
    re-run on the final files changes nothing. The real page was opened
    headless (Leaflet from npm, tiles stubbed): 38 Dutch clubs load with no
    script error, Cambuur's sheet reads Kooi Stadion and 15,000, Ajax's and
    Telstar's list their Eredivisie fixtures, and Volendam's and Jong AZ's
    say why an Eerste Divisie club has none. **The OpenStreetMap capacity
    check did NOT come back complete on its first three runs**, which is
    the usual Overpass flakiness and not a pass: all eleven countries
    `WRITTEN` at 11:10 UTC (before the corrections), then Romania
    `UNCHANGED` (HTTP 504) at 11:46 and Greece `UNCHANGED` at 12:03 - a
    different country each time, each left byte for byte as it was. **The
    merge rests on the fourth, 12:21 UTC, on the final code: all eleven
    `WRITTEN`.** Netherlands in that run: 38 clubs, 5 agree, 0 differ, 30
    Wikidata only, 1 neither, 3 with no OpenStreetMap ground nearby (Jong
    Ajax, Jong AZ and Jong PSV, drawn at training complexes - Cambuur has
    one now). Nothing that is Alexandru's call was decided: the five
    `fixture-links-manual.csv` rows above are written up, not written, and
    the three skips and one tier correction are each reviewable and say how
    to undo them.

- **England's top two tiers are on the map, 2026-09-30: Premier League
  20 of 20 and Championship 24 of 24, exact - nothing missing, nothing
  extra, nothing at the wrong tier, on the first build.** Same pipeline
  and standard as the nine countries before it, run through three
  throwaway probes on a GitHub runner (removed in the same branch); the
  sandbox still answers 403 to CONNECT for Wikidata, Wikipedia and
  StadiumDB. Tiers 1 and 2 only; League One and below were deliberately
  not touched.
  - **The file is `GB.json`, and that was a choice.** Every other tool
    already said GB for England - `link_fixtures.py` for PL and ELC,
    `build_calendars.py` for the time zone - and the OpenStreetMap tools
    ask Overpass for an ISO 3166-1 area, which England does not have. It
    is England's league PYRAMID, the Monaco convention: three Welsh clubs
    are in it. **If Scotland is ever added it needs a code of its own**;
    GB is taken.
  - **The league Q-ids were read, not remembered**: `Q9448` Premier
    League (enwiki *Premier League*) and `Q19510` EFL Championship
    (enwiki *EFL Championship*). Neither carries `P3983`. **Both carry
    `P17` United Kingdom (`Q145`), not England (`Q21`)**, and so does
    every English club item read, so the builder's country is `Q145`:
    `Q21` would have discovered no league and flagged every club. The
    rank diagnostic counts both as GB. The 2026-27 articles are one
    stadiums-and-locations table each, **20 of 20 and 24 of 24
    resolved**, and the Championship's Team changes table names the
    three relegated to League One (Oxford United, Leicester City,
    Sheffield Wednesday) and the three promoted from it (Lincoln City,
    Cardiff City, Bolton Wanderers).
  - **The country check is weak for GB, and that is written down rather
    than fixed.** The box (Wikidata's `P1332`-`P1335` on `Q21`: Marshall
    Meadows, the Isles of Scilly, Lowestoft Ness) holds all of Wales,
    the Isle of Man, southern Scotland and the east of Northern Ireland,
    and `P17` says United Kingdom for all four. A Scottish or Northern
    Irish club carrying an English tag would pass unflagged. For tiers 1
    and 2 the roster check covers it.
  - **The three Welsh clubs are the Monaco shape** - Cardiff City,
    Swansea City and Wrexham, all in the complete Championship article -
    and, unlike Monaco and Vaduz, **the country check does not flag
    them**, because their items say United Kingdom (Wrexham's also says
    Wales). Each has a note-only row saying what the flag would have.
  - **English tags are well kept.** Every item carrying either tag at
    any rank was listed: 108 statements, about 60 items. Most clubs carry
    a dated history with the current league preferred.
    - **Rank blind spot, all three shapes, run by `diagnose-rank.yml`
      on the branch.** Queries A and B: **no English item.**
      Middlesbrough and Stoke carry the Premier League at deprecated
      rank, but their normal-rank Championship tags are truthy, so
      nothing is hidden. Query C: **eight** (Barnsley, Burton Albion,
      Huddersfield Town, Leicester City, Luton Town, Oxford United,
      Sheffield Wednesday, Wigan Athletic), every one relegated with its
      new lower league correctly preferred; **bill 0**.
    - **The league-tag end date (`P582`), measured for England: zero.**
      No club's tier comes from a tag that has ended. Every mapped tag
      with an end date sits under a preferred statement (the query C
      eight), and the build reads past none of them.
    - **Not-a-club, two new kinds, and the net now names both**:
      *History of Rotherham United F.C.* (`Q16840698`, typed "aspect of
      history") carries a Championship tag **and a ground**, so it would
      have been drawn at tier 2 on the New York Stadium; *Melchester
      Rovers* (`Q6811996`, Roy of the Rovers' club, typed "fictional
      association football team") carries a Premier League tag and no
      ground. Four club seasons (Manchester City 2022-23, three Leeds)
      were caught by the season net, as before. Checked on the rebuild:
      the two new words catch those two items and nothing else in any
      country.
    - **Every duplicate shape, looked for rather than waited for.**
      Shapes 1 and 2: none - the roster check names each of the 44 once,
      no two pins share a ground and none is within 2 km of another
      (nearest: Fulham and Chelsea, 2.2 km). Shape 3: none - no
      multi-sport parent carries either tag. Shape 4: none on the map;
      New Brighton Tower carries a Championship tag and `P576` 1901, and
      the gate drops it. Shape 5: none - Chelsea, Manchester United and
      Wolves are typed "men's association football team" **on the one
      item the roster links**, with no `P831`; there is no second item.
      Shape 6: none - no English club dies at the coordinates gate.
    - **Two grounds on one item (the Freiburg shape): none on the
      map.** Arsenal (Emirates, Highbury), Tottenham (the new stadium,
      White Hart Lane) and Oxford United carry two, at different ranks,
      so the query yields one.
    - **Women's club with a men's tag (rule 6), checked deliberately**:
      none, from three angles - see the rule.
  - **Grounds.** **Brentford was drawn at Griffin Park**, its only
    `P115`, closed in August 2020 and demolished in 2021 (the ground's
    infobox), and OpenStreetMap's check found no stadium within 500 m of
    that pin. It is now at the **Gtech Community Stadium**, `Q4961609`'s
    own position, 17,250 (the table, StadiumDB, the club's and the
    stadium's infoboxes; not taken: 20,000 on the ground's item).
    **Queens Park Rangers** came back from Wikidata **with no name** - no
    English label - and has a name-only row from its Wikipedia title.
  - **Capacities, the UTA Arad rule - and a correction undone the same
    day, which is the part worth keeping.** Corrected, each where the
    league table and StadiumDB agree within 5%, the map sat outside, and
    OpenStreetMap does not disagree: **Manchester City** 52,900 →
    **61,038** and **Wrexham** 13,341 → **10,771**. **Aston Villa,
    Fulham and Stoke were corrected too, and undone**: the OpenStreetMap
    re-run on the corrected map showed that OSM carries Wikidata's
    figure for all three (Villa 42,640 / OSM 42,788 against the table's
    36,887 and StadiumDB's 37,000; Fulham 25,700 / 25,700 against 28,107
    / 27,782; Stoke 27,740 / 27,740 against 30,089 / 30,089). On the
    first run OSM *agreed* with the map, so the rows never surfaced - and
    agreement was not read. **Two against two is the AEL shape: nothing
    changed**, and each club has a note-only row with all four figures.
    That OSM equals Wikidata to the seat on two of them suggests a copy,
    which would make it one source, not two - a judgement, and
    Alexandru's. **The lesson: before applying the rule, read every
    source's figure, including the ones that agree with the map.**
    **Left alone, contested**: **Lincoln City** (10,120 on Wikidata,
    11,400 in the table, 10,669 on StadiumDB - no two within 5%). **The
    map stands** where it agrees with the table within 5%: Bournemouth
    (12,000 / 12,357; StadiumDB's 11,307 is the outlier) and Chelsea
    (41,875 / 40,044). **OpenStreetMap is the outlier** at Liverpool
    (54,074 against 61,276 three times) and West Ham (66,000 against
    62,500 three times).
  - **StadiumDB: 44 clubs, 36 matched (28 agree, 3 differ, 5 name
    clashes), 8 not matched** after the dotted-initialism fix (Brentford,
    Derby, Preston, QPR, Stoke, West Brom, West Ham, Wolves - short
    names like "Derby" and "WBA" that the town-only guard rightly
    refuses). Unmatched is unchecked, never agreement; all eight have
    the league table's figure beside the map's. The name clashes are
    sponsors: Dean Court is the Vitality Stadium, Sincil Bank the
    ProAmpac Stadium, the Liberty the Swansea.com Stadium, the Racecourse
    Ground the STōK Cae Ras.
  - **OpenStreetMap is better in England than anywhere but Germany and
    France**: 1,040 stadiums in the UK, 98 with a usable capacity. First
    run, every country `WRITTEN`: GB 44 clubs, 22 agree, 2 differ, 19
    Wikidata only, 1 with no OSM ground nearby (Brentford, at Griffin
    Park). On the final layer: 22 agree, 2 differ (Liverpool and West
    Ham, OSM the outlier), 20 Wikidata only, **0 with no ground nearby**
    - Brentford's new pin has one. Overpass dropped a different country
    on three of the five branch runs (Germany and France on one, Spain
    on the next, Serbia on the one after), each left `UNCHANGED` as it
    should be. **The merge rests on the fifth, 2026-10-01 08:33 UTC: all
    ten countries `WRITTEN`.**
  - **Fixtures: 44 of 44**, from football-data.org's PL and ELC, both
    already fetched - the first country whose second tier has a fixture
    source as well. Five Premier League clubs link to the Champions
    League too. It took the dotted-initialism fix (Conventions) and QPR's
    name; no `fixture-links-manual.csv` row was needed.
  - **Found on the way, not English, and FIXED 2026-10-01: a placeholder
    kick-off was shown as a time.** football-data.org marks a match whose
    kick-off is not set yet as `SCHEDULED` at **00:00 UTC**, and the club
    sheet printed that as "01:00" German time (02:00 in summer), like a
    real time. The sheet now says "time not set" on a second line under
    the date. **The test is status AND midnight together, never midnight
    alone**, and that was checked across every football-data file rather
    than assumed: every `SCHEDULED` match in every file is at midnight UTC
    and every `TIMED` one in the club-sheet files has a real time - but
    Brazil's BSA has 3 `TIMED`, 13 `FINISHED` and 1 `POSTPONED` match at
    00:00 UTC, and the World Cup file 6 `FINISHED`, which are genuine
    (21:00 Brasília is 00:00 UTC) and keep their time. Counted on
    2026-10-01 and all now labelled: Bundesliga 198, La Liga 280, Serie A
    190, Championship 264 and **Ligue 1 192** (not on the original list,
    same code path); also 100 Eredivisie and 198 Primeira Liga, which no
    club sheet reads. None in the Premier League. OpenLigaDB never has the
    problem: it writes no time as `null`, which already reads "date not
    set". **Left as they were, on purpose**: a `POSTPONED` match at
    midnight (BSA and Primeira Liga, neither read by a club sheet) - its
    original time is unknowable, and a Brazilian one could be genuine, so
    it keeps the "postponed" tag and its time. **A second bug in the same
    function was fixed with it**: a `SCHEDULED` match later today sorted as
    already played, because its placeholder midnight had passed, and got a
    false "no result recorded" tag. A placeholder match now counts as
    ahead until its date is over.

- **Spain's top two tiers are on the map, 2026-09-30: La Liga 20 of 20
  and Segunda División 22 of 22, exact - nothing missing, nothing extra,
  nothing at the wrong tier.** Same pipeline and standard as the eight
  countries before it, run through three throwaway probes on a GitHub
  runner (removed in the same branch); the sandbox still answers 403 to
  CONNECT for Wikidata, Wikipedia and StadiumDB. Tiers 1 and 2 only;
  the Primera Federación and below were deliberately not touched.
  - **The league Q-ids were read, not remembered**: `Q324867` La Liga
    (`P3983` 1, enwiki *La Liga*) and `Q35615` Segunda División (enwiki
    *Segunda División*; its English label on Wikidata is "LaLiga 2", and
    it carries **no** `P3983`). Both 2026–27 articles are one
    stadiums-and-locations table, **20 of 20 and 22 of 22 resolved**, and
    the Segunda one has a Team changes table naming the four clubs
    relegated to the Primera Federación and the four promoted from it.
    The country box's four edges are Wikidata's own `P1332`-`P1335` on
    `Q29`; the Canaries make it wide enough to hold Portugal, Andorra,
    Gibraltar, northern Morocco and southern France up to Toulouse, so
    `P17` is the signal that catches a club across a border
    (`COUNTRY_BOX`'s comment). Labels are asked in English first, then
    Spanish, because the English label is the short form football-data
    uses ("Villarreal CF") and the Spanish one the full legal name.
  - **What the first build brought, 48 clubs against 42:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 20 | 28 (20 right, 8 extra, 2 missing) |
    | after this pass | **20** | **22** |
  - **Eight extras `skip`ped, seven of them to the Hermannstadt
    standard** - both articles complete, neither lists the club, and the
    club's **own English and Spanish articles** name the league it is in
    now. (The English infoboxes are no help here: they fill `league`
    from a template, `{{Spanish football updater}}`, so the reason was
    read from each article's opening lines.) For four of them the
    Segunda article's Team changes table says it too.
    - **Relegated in 2026, tag stale**: Cultural Leonesa (a *preferred*
      Segunda tag from 2025), CD Mirandés (a Segunda tag ending 2026) and
      SD Huesca (a *preferred* Segunda tag dated 2021-2022) - all three
      in the Team changes table as relegated to the Primera Federación.
    - **Relegated earlier, one undated Segunda tag and nothing else**:
      SD Ponferradina, Racing de Ferrol, FC Cartagena - each now in the
      Primera Federación by its own article.
    - **Jerez Industrial CF**, drawn at tier 2 on a Segunda tag dated
      **1968-1969** - the end-date shape - is in the Primera Andaluza
      Cádiz, the seventh tier.
    - **Fundación Albacete (`Q15966154`) is a women's club** - typed only
      "women's association football club", and its English article
      says it is Albacete Balompié's women's section - drawn at tier 2 on
      a Segunda tag on the **men's** league item. **Rule 6**, and the
      rule's own paragraph now says so. A filter on type was measured
      across every country and not built: it would also remove Atromitos
      and Asteras Tripoli, the men's Greek clubs, whose items carry the
      same type.
  - **Two promoted clubs whose tags did not follow reach the map through
    the hand-named fallback**, tier 2 by hand, the FC Wil standard (both
    complete articles plus the club's own article; reviewable): **CE
    Sabadell** (`Q12260`, only a Primera Federación tag) and **RC Celta
    Fortuna** (`Q2311865`, Celta's reserve side, only a Segunda B tag).
    **CD Tenerife** was surfaced automatically by the Vicenza shape - a
    stale *preferred* tag naming an unmapped league over a normal-rank
    Segunda one.
  - **Rank blind spot, all three shapes, run by `diagnose-rank.yml` on
    the branch.** Queries A and B: **no Spanish item** - no preferred
    "no league" and no all-deprecated one. **SD Amorebieta** carries a
    Segunda tag at deprecated rank, but its normal-rank Primera
    Federación tag is truthy, so it is invisible and rightly so. Query C:
    **ten Spanish clubs** (Alcorcón, Tenerife, Fuenlabrada, Lugo,
    Numancia, Barcelona Atlètic, Hércules, Zaragoza, Logroñés, Xerez),
    every one a relegated club with its new lower league correctly
    preferred except Tenerife, which was promoted back; **bill 1,
    Tenerife, surfaced and `ok`**.
  - **The league-tag end date (`P582`), measured for Spain**: of 50 live
    items with a truthy La Liga or Segunda tag, **two** get their tier
    from a tag that has ended - Huesca and Jerez Industrial, both caught
    by the roster and `skip`ped. The other five wrong men's extras carry
    **no end date at all**, so honouring `P582` would not have caught
    them - the same finding as the 2026-09-29 measurement. One boundary
    case: Mirandés's Segunda tag ends "2026" at year precision, which the
    measurement counts as still live.
  - **Every duplicate shape, looked for rather than waited for.** Shape
    1 and 2: none - no two items for one club, and the roster check names
    each of the 42 clubs once. Shape 3: none - no multi-sport parent
    carries either tag. Shape 4: the seven relegated clubs above, all on
    the map until this pass. Shape 5: none - no map item has a `P831`,
    and Espanyol's one item carries both "club" and "men's team" types.
    Shape 6: none - no Spanish club dies at the coordinates gate (0
    dropped), so none can be offered as a coordinate proposal. **One
    shared pin, genuine**: Celta Vigo and Celta Fortuna at Balaídos. No
    two other Spanish pins are within 2 km.
  - **Not-a-club, a third kind: a match.** Three items typed "association
    football club match" ("Real Madrid v Almería, 22 March 2009" and two
    more) carry `P118` La Liga. They had no ground and died at the
    coordinates gate, and `propose_coordinates.py` would have offered
    them one next month. `fetch_clubs.py` now leaves them out and names
    them. Checked on the rebuild: those three and nothing else, in any
    country.
  - **Grounds.** **Real Betis** is drawn at **La Cartuja**, where it
    plays while the Benito Villamarín is rebuilt (the La Liga table, the
    club's English infobox, StadiumDB and La Cartuja's tenant list; the
    row says to empty it when Betis goes home). **FC Andorra** is drawn
    at the **Estadi de la FAF** in Encamp, opened 2025 (Wikidata still
    names the old Estadi Nacional), and is **the Monaco shape** - `P17`
    Andorra, flagged every run, kept because it plays in the Spanish
    pyramid; its row says so. **Celta Fortuna** is at Balaídos, not the
    Barreiro its `P115` names. **RCD Espanyol** is the Freiburg shape
    (the RCDE Stadium and the Estadi de Sarrià, demolished 1997) and is
    pinned. **Rayo Vallecano** played at Butarque while its Vallecas
    ground was closed; the La Liga article says the ban was lifted on 14
    September 2026. The map already had Vallecas, and StadiumDB agrees.
  - **Capacities, the UTA Arad rule.** Corrected: **Barcelona** 105,000
    → **62,652** (Wikidata held the post-rebuild figure), **Cádiz**
    26,000 → **20,724**, **Leganés** 11,454 → **14,422**, **Burgos**
    16,000 → **12,194** (the table and OpenStreetMap's 12,642 agree;
    StadiumDB's 11,380 not taken - without OpenStreetMap this one would
    have stayed contested); filled:
    **Eldense 5,776**; with the ground changes, **Betis 70,000** and
    **Andorra 5,108**. **Left alone, contested**: Espanyol (Wikidata
    and the ground's infobox 40,500 against the table and StadiumDB
    37,776 - two and two, the AEL shape; pinned only so it cannot flap),
    Villarreal (24,891 / 23,008 / 21,332), Almería (22,000 on Wikidata, 15,000 in the table, 18,331 on
    StadiumDB and the club's infoboxes - a ground being rebuilt, and
    Wikidata's label still names the old Juegos Mediterráneos) and Real
    Sociedad B (blank; the table's 4,000 against 2,500 twice).
    **The map stands where StadiumDB is the outlier**: Real Madrid,
    Getafe, Celta and Celta Fortuna; and Mallorca, where the map and
    StadiumDB agree (25,736) against the table's 23,142.
  - **StadiumDB covers Spain well, and that was measured, not carried
    over from another country.** `/stadiums/esp`: 89 grounds, a ground
    for 40 of the 42 clubs (not FC Andorra, not Real Sociedad B). The
    matcher paired 31: 25 agree, 6 differ, 11 not matched by name
    (Mallorca's "Real CD Mallorca", Gijón's "Real Gijón" and the like).
    Unmatched is still unchecked, never agreement.
  - **OpenStreetMap, two runs on the branch.** The first: Spain
    `WRITTEN`, 42 clubs, 6 agree, 3 differ - and **Austria `UNCHANGED`**
    (HTTP 504), so it was not a pass. Burgos was the difference it
    settled (above). The second, after the rebuild: **all nine countries
    `WRITTEN`**; Spain 7 agree, 2 differ, 31 Wikidata only, 1 neither, 2
    with no OpenStreetMap stadium within 500 m (one is Real Sociedad B,
    4.7 km from the nearest - Zubieta is a training complex; nobody has
    looked at which pitch the tags miss). The two that differ are
    OpenStreetMap as the outlier: Barcelona (99,354, the post-rebuild
    figure again) and Cádiz (25,033), against the table and StadiumDB.
    Spain has more to compare than Italy or Romania: 1,829 stadiums, 68
    with a usable capacity.
  - **Fixtures: 15 of 20 La Liga clubs link to football-data.org's PD**,
    which was already fetched. **Five are abbreviations the matcher
    rightly refuses**, and each needs one `link` row in
    `fixture-links-manual.csv` - **Alexandru's call**, so none was
    written: Real Madrid (`Q8682` → football-data 86 "Real Madrid CF"),
    Atlético Madrid (`Q8701` → 78 "Club Atlético de Madrid"), Osasuna
    (`Q10286` → 79 "CA Osasuna"), Deportivo de A Coruña (`Q8760` → 560
    "RC Deportivo La Coruña") and Racing de Santander (`Q12236` → 5335
    "Real Racing Club de Santander"). The Segunda División has no
    fixture source; the club sheet says so. **All five rows were added
    on 2026-09-30 on Alexandru's instruction**, the Le Mans way, and La
    Liga is 20 of 20 linked; each club's sheet was opened in the real
    page and lists its fixtures (Real Madrid and Atlético their
    Champions League ones too).
  - **Found on the way, not Spanish: the roster reader ran a footnote
    mark into a capacity.** `check_rosters.py` read a capacity cell as
    every digit in it, so "19,840 [7]" became 198,407. Spanish tables
    footnote nearly every capacity. It now sets the mark aside and gives
    no figure for a cell with two ("14,500 14,708", Rayo's two grounds).
    No other country's `roster-review.csv` row changed.

- **The 2026-09-30 pass: Asteras Tripolis B linked, Lotru Brezoi and
  Victoria Ineu off the map, and the capacity cross-check saved country
  by country.** Three instructions from Alexandru. The Wikipedia reads
  went through four throwaway probes on a runner (removed in the same
  branch); the sandbox still answers 403 to CONNECT for Wikipedia.
  - **Asteras Tripolis B is one club, `ok`.** The 2026-27 Super League
    Greece 2 table row reads exactly "Asteras Tripolis B" and links the
    parent club, Asteras Tripolis F.C. (`Q757320`) - read on a runner
    with the roster reader's own functions before the line was written.
    Line 5 of `data/roster-links-manual.csv` joins it to `Q135213959`.
    The roster check on the branch moved exactly that verdict, from
    `extra-not-in-roster` to `ok`, and nothing else in Greece.
  - **CS Lotru Brezoi and Victoria Ineu are `skip`ped.** Checked first,
    as asked, on each club's own Wikipedia pages at their current
    revisions:
    - **Victoria Ineu**: the English article's infobox says `league =
      Liga VI` (its last season row is 2024-25, Liga VI); the Romanian
      article's infobox says `Liga a VI-a`, and its lead says the club
      plays in Liga a VI-a - Arad. Clear.
    - **Lotru Brezoi has no English article.** Its only page is Romanian,
      *CS Lotru Brezoi (fotbal)*: infobox `league = IV`, and the text
      puts it in Liga a IV-a Vâlcea in 2024-25, 16th. Clear about the
      league; the page names no season later than 2024-25.
    - **Neither page states a 2026-27 season.** So the removal was
      backed by one more read: neither club is named by the English
      2025-26 or 2026-27 Liga III article, by the Romanian *Liga a III-a
      2025-2026* or *2026-2027*, or by the 2025-26 or 2026-27 Liga II
      article. One false alarm, recorded so it is not rediscovered: the
      Romanian 2026-27 Liga III article does name **"Tricotaje Ineu"**,
      Victoria Ineu's old name (it redirects there), but only in its
      historical table of 2002-03 promotions.
    - **The instruction's premise was not quite right, and it matters
      for the next removal.** It called this "the same standard already
      used for Hermannstadt and CSM Bacău". Hermannstadt's standard
      rests on *complete* division lists agreeing on the absence plus an
      independent reason. Liga III's list is not complete, so that
      standard cannot be met here. CSM Bacău was never on the map, so it
      got a whole-club rejection in `coordinate-reviews.csv`, not a
      `skip`. What was applied is the **FC Bistrița standard**: the
      club's own page plus Alexandru's instruction. Both rows say so.
    - The club build on the branch removed exactly these two, both
      `extra-not-in-roster` rows left `roster-review.csv`, and Romania's
      tier 3 went from 40 clubs to 38.
  - **`crosscheck_capacity.py` saves country by country** (Conventions).
    Checked offline first, with Overpass mocked: a failing country's
    rows stay byte-identical, every country failing leaves the file
    byte-identical, and with no file a partial list is written and
    labelled. **The first real run, across all eight countries, was the
    test the instruction asked for, and Overpass supplied the failure**:
    DE, IT and RO answered HTTP 504 and stayed `UNCHANGED`, their rows
    byte for byte as before. AT, CH, FR, GR and RS were `WRITTEN`. The
    file's only change was **Greece's first row**, G.S. Marko ("no
    stadium in OSM within 500m"); the other four countries came back
    with the same rows they already had. Under the old rule that run
    would have written nothing.
    **The second run, straight after, came back complete: all eight
    `WRITTEN`**, the first complete capacity check since Greece was
    added. After six failures in a row on 2026-09-29 and 2026-09-30,
    this is the first run with nothing `UNCHANGED`. Its one change was
    Victoria Ineu's row going, because the club is off the map. File
    now: AT 2, CH 2, DE 12, FR 4, GR 1, IT 0, RO 28, RS 5. Greece: 27
    clubs, 3 agree, 0 differ, 20 Wikidata only, 1 neither, 4 no OSM
    ground nearby, the same as the two partial runs of 2026-09-29.
    **Not changed, and worth the look the Greece entry asked for**: the
    tool's retry behaviour is still the old one (60 s after a busy
    answer, 30 s after a timeout, three tries, no backoff). Saving per
    country makes a failure cost less. It does not make one less likely.

- **The 2026-09-29 pass: Greece's top two tiers on the map, the
  league-tag end date measured in every country, the shape-5 join
  checked, and the Ub ground kept unplaced.** Four instructions from
  Alexandru in one session, run through five throwaway probes on a
  GitHub runner (removed in the same branch), because the sandbox still
  answers 403 to CONNECT for Wikidata, Wikipedia, StadiumDB and
  OpenStreetMap.
  - **The Aue / Babelsberg / Augsburg join is structural, and the
    premise that Augsburg "broke again" was not quite right.** The join
    in `check_rosters.py` reads `P831` (parent club) on every map club a
    roster does not name, in every country, and joins it to the roster's
    club by Q-id; nothing in it names a club. Read back through the
    history of `roster-review.csv`: **Augsburg never broke.** It read as
    two findings (`missing-from-wikidata` under `Q15755`,
    `extra-not-in-roster` under `Q97905916`) on every single run from
    2026-09-20 until the join landed on 2026-09-27. What was "resolved"
    on 2026-09-20 was the **map** - Augsburg drawn once, under the item
    that works, and protected from cleanup - and that never changed. The
    roster check's double count was **documented as permanent** then,
    with `_sameNameOnMap` as the only mitigation, and that annotation
    could not do the job: it compares names exactly and the `extra`
    branch never looked at all. So the lesson is about wording: an
    entry that says a club is settled should say *which* finding is
    settled. **What the join still does not cover, so a fourth case is
    loud rather than silent:** a team item with no `P831` (Babelsberg's
    also has `P361`; a pair linked only that way would not join), and a
    team item on the map at a different tier from the one its club
    item's roster names - the join only looks within one country and
    tier. Either reads as a missing club and an extra one, two findings
    on every run, which is how the first three were found. Greece's team
    items (AEK, Aris, Olympiacos, PAOK and others are all `men's
    association football team` items with `P831` to a multi-sport
    parent) are the items the rosters link, so nothing needed joining.
  - **The league-tag end date (`P582`) was measured in all seven
    countries, and it is NOT the main driver of Serbia's cleanup - the
    earlier entry said so and was wrong.** Asked of Wikidata directly:
    every club whose **truthy** mapped `P118` statements (what the club
    query reads) decide its tier through a tag whose end date has passed,
    dissolved clubs left out because the `P576` gate already drops them.

    | | clubs with a truthy mapped tag | tier decided by an ended tag |
    |---|---|---|
    | DE | 167 | 3 |
    | RO | 171 | 4 |
    | FR | 43 | 2 |
    | IT | 64 | 3 |
    | CH | 26 | 3 |
    | AT | 35 | 6 |
    | RS | 46 | 6 |
    | GR | 15 (measured before Super League 2 was mapped) | 0 of those; 2 more found at tier 2 later, Niki Volos and F.S. Kozani |

    **Serbia**: 5 of its 14 skips (BSK Borča, Budućnost Banatski Dvor,
    Proleter Novi Sad, Proleter Zrenjanin, Sloboda Užice) and 1 of its 6
    tier corrections (Smederevo) rest on an ended tag. The other nine
    skipped clubs carry **no end date at all** - honouring `P582` would
    not have touched them. The Serbian cleanup was heavy because
    Wikidata's Serbian tags are stale, not because they are dated.
    **In the other six countries the shape is small and almost all of it
    is already handled.** Of the 21: 11 already carry a `skip`, a
    whole-club rejection or a hand tier (VSE St. Pölten, the five old
    Vienna clubs, Anglo-American Club Zürich, FC Wil, FC Torinese, La
    Dominante, Hermannstadt, VfR Garching, Babelsberg).
    - **Two were trivial and the same shape as one already resolved,
      and are done**: SC Fives (`Q1514915`, Ligue 1 1932-39, merged into
      Lille in 1944) and the wartime ÉF Reims-Champagne (`Q3590859`,
      Ligue 1 1943-44, dissolved 1944) - whole-club `rejected` rows in
      `coordinate-reviews.csv`, the Anglo-American Club Zürich way.
    - **Two are left, on purpose**: Società Ginnastica di Torino
      (`Q116949682`, Serie A 1898-1902; its Italian article says only
      that it "was" a club, no end stated) and ACS Voința Limpeziș
      (`Q113573418`, Liga III tag ended 2023; no article at all). Both
      die at the coordinates gate and neither is a confident proposal
      today. A rejection would rest on the tag alone.
    - **Two were on the map at tier 3 and wrong, and were Alexandru's
      call** - *he made it on 2026-09-30 and both are `skip`ped; see the
      2026-09-30 entry. As first written:* CS Lotru Brezoi (`Q141319965`) and Victoria Ineu
      (`Q5014471`), both Liga III tags that ended (2006 and 2023), both
      `extra-not-in-roster`, and their infoboxes say Liga IV Vâlcea and
      Liga VI Arad. Not skipped, because the Liga III article is not a
      complete division list, so the Hermannstadt standard cannot be
      met - the same reason Liga III has been left alone throughout.
    - **Two would be made WRONG by honouring `P582`**: FC Aarau
      (Challenge League tag dated 2010-2013) and BSG Chemie Leipzig
      (Regionalliga tags ending 2018) are both `ok` in their 2026-27
      division - the end date is the stale part, not the tag. VfR
      Garching (tier 7 by hand, no roster) would drop off the map
      entirely, and FC Wil and Smederevo would survive only through the
      hand-named fallback.
    **So the fix is not worth doing now, and the scale is the answer.**
    Switching the club query to honour `P582` would remove about as many
    right clubs as wrong ones outside Serbia, needs the roster check to
    catch the ones it wrongly drops, and interacts with LR Vicenza's
    shape. Per country the remaining bill is two Romanian Liga III clubs
    (Alexandru's) and two off-map items that harm nothing today. If it is
    ever built, it is a report first - name each club whose tier rests on
    an ended tag - not a filter.
  - **The Ub ground stays unplaced, and the monthly run can no longer
    offer it.** FK Zemun is off the map by its hand row's `<clear>` and
    FK Jedinstvo Ub reads `unplaced-no-coordinates`, both confirmed in
    this pass's build and roster check. But nothing stopped
    `propose_coordinates.py` from matching "Ub" in a club's name to one
    of the three unnamed pitches and calling it confident - the
    Gilortul pitch was exactly that shape. Both clubs now have an `open`
    row in `coordinate-reviews.csv`, so any proposal for them reads
    "open - do not paste". The same was done for **Nestos Chrysoupoli**
    (three unnamed pitches, no named ground) and **Hellas Syros** (one
    unnamed stadium, six unnamed pitches).
  - **Greece's top two tiers are on the map: Super League 14 of 14,
    exact; Super League 2 13 drawn for 16, nothing at the wrong tier,
    and the three not drawn are off for a named reason.** Same pipeline
    and standard as the six countries before it; tiers 1 and 2 only.
    - **The league Q-ids were read, not remembered**: `Q235114` Super
      League (enwiki *Super League Greece*) and `Q63980269` Super League
      2 (enwiki *Super League Greece 2*), neither carrying `P3983`. Both
      2026-27 articles are one stadiums-and-locations table, 14 of 14 and
      16 of 16 resolved. StadiumDB's slug is `gre` (29 grounds, only 17
      of them in either division). The box's north, south and east edges
      are Wikidata's `P1332`-`P1334` on `Q41`; its west edge is set by
      hand because Wikidata's westernmost point is on the mainland and
      Corfu lies west of it (written in `COUNTRY_BOX`'s comment).
    - **Greek tags are the best-kept of the seven countries**: most
      clubs carry a dated history with the current league preferred, so
      the truthy tag is usually right. Every item carrying either tag at
      any rank was listed and read. Two exceptions, both the end-date
      shape: **Niki Volos** (`Q3180055`), whose only mapped tag is the
      Super League 1961-1966 and which has no Super League 2 tag, is at
      **tier 2 by a hand row** (the FC Wil shape: both articles complete,
      the club's infobox says Super League 2); and **F.S. Kozani**
      (`Q3292636`), drawn at tier 2 on a Super League 2 tag that ended in
      2024, is **`skip`ped** - both articles complete, neither lists it,
      and its infobox says it was relegated from the Gamma Ethniki to the
      fourth tier.
    - **One more rejected before it was proposed**: Kampaniakos
      (`Q16842502`), Super League 2 tag 2023-2026, no position, infobox:
      relegated in 2025-26, now in the Macedonia FCA First Division.
    - **Not-a-club**: the season item *2016-17 Panionios G.S.S. season*
      carries a Super League tag and would have sat on Panionios's pin;
      the existing net caught it by type.
    - **Duplicates: none.** Every tagged item is one club; the three
      reserve sides (Olympiacos B, PAOK B, Asteras Tripolis B) are their
      own items. Two genuine shared pins: PAOK B with Apollon Kalamaria
      at the Kalamaria Stadium, and Asteras Tripolis B with Asteras.
    - **The roster reader needed a new reserve marker, `b`.** The 2026-27
      Super League 2 table links "Asteras Tripolis B" to the **parent**
      club's article - the Rapid II shape - and without the marker the
      row read as Asteras Tripolis at tier 2. `check_rosters.py` now
      leaves it out and names it. Checked before it went in: no club on
      the map or in any roster had "b" as a word of its name, and no
      other country's verdict moved.
    - **Asteras Tripolis B (`Q135213959`) was on the map but read
      `extra-not-in-roster`, and one line would fix it - Alexandru's
      call.** *He made it on 2026-09-30 and the line is in; see that
      day's entry. As first written:* Its English label was just "Asteras Tripolis"; its Greek
      label is "Αστέρας Τρίπολης Β΄", its description says reserve
      section, its `P831` is the first team. A hand row gives it that
      name, so the shared pin does not read as one club twice. The line
      that would join the table row to it - `2026–27 Super League Greece
      2,Asteras Tripolis B,Q135213959,...` in
      `data/roster-links-manual.csv` - is an identity claim and was not
      written.
    - **Rank blind spot, all three shapes.** No deprecated or preferred
      "no league" Greek item. Query C finds six (Apollon Smyrnis, PAS
      Giannina, PAS Lamia, Makedonikos, Panargiakos, Tilikratis
      Lefkadas), every one a relegated club with its new lower league
      correctly preferred; **bill 0**.
    - **Grounds**: **Panathinaikos** carries two grounds at the same
      rank (the Freiburg shape; the query returned only one row this
      time, so the run report did not name it) and is **pinned to the
      Olympic Stadium, 69,618** - the table, the club's infobox and
      StadiumDB agree; the Leoforos is Kifisia's from 2026 and Kifisia is
      drawn there. **Not placed**: Nestos Chrysoupoli and Hellas Syros
      (above), and **A.P.S. Zakynthos**, `held` on the one OpenStreetMap
      pitch named "Zakynthos Municipal Stadium" - the table and Wikidata
      name that ground, but the club's own infobox names a different one.
    - **Capacities, the UTA Arad rule**: **AEK** 34,000/31,100 (Wikidata
      carries both) → **32,500** (table and StadiumDB); **Asteras
      Tripolis** (and its B side, same ground) 7,616 → **7,423** (table,
      StadiumDB and both infoboxes). **Left alone, contested**: AEL
      (Wikidata and the stadium infobox 17,118 against the table and
      StadiumDB 16,118 - two and two), Atromitos (map 10,200 with
      StadiumDB 10,000, against the table's 9,050), Karditsa (13,000 on
      Wikidata against 3,500 three times, all Wikipedia) and Kallithea
      (4,200 against 6,300, both Wikipedia's figure being one source).
      Marko's is blank: 3,000 appears only on Wikipedia. StadiumDB's
      review adds Panthrakikos (its 3,000 is the outlier against 6,198
      twice) and Apollon Kalamaria (7,000 against 6,500, the map agreeing
      with the table). **Silence is not agreement**: StadiumDB has
      nothing for at least nine of the thirty clubs.
    - **Fixtures: none.** football-data.org's free tier carries no Greek
      competition; the club sheet says so.
    - **Merged on Alexandru's instruction, 2026-09-30, although the
      OpenStreetMap capacity check never came back complete.** Every
      other check on the branch was green. `Cross-check capacities` ran
      six times over two days and each run lost a different country to
      Overpass HTTP 504s (CH; AT, FR and RS; AT; DE; FR; GR and RS), so
      `capacity-review.csv` was left unchanged each time - correctly, and
      not a pass by rule 7, so the merge was his call and he made it.
      Greece was compared in two of the runs, identically both times: 27
      clubs, 3 agree, 0 differ, 20 Wikidata only, 1 neither, 4 no OSM
      ground nearby. **The structural point is the one to act on**: with
      eight countries in one all-or-nothing run, a complete run gets less
      likely with every country added. `coordinate-review.csv` has been
      decided country by country since 2026-09-26; `crosscheck_capacity.py`
      doing the same is the next step, and it is not built. *(Built
      2026-09-30 - see that day's entry.)*

- **The 2026-09-27 pass: the roster check's double count fixed
  properly, Serbia's top two tiers on the map, and the Austrian and
  German questions of 2026-09-26 settled.** Six instructions from
  Alexandru in one session, all run through throwaway probes on a
  GitHub runner (six of them, removed in the same branch) because the
  sandbox still answers 403 to CONNECT for Wikidata, Wikipedia,
  StadiumDB and OpenStreetMap - and WebFetch is refused for Wikidata too.
  - **The double count, and the audit of every hand-row club.** The
    ask: a club present through a hand row and under its real Wikidata
    id should read as ONE club found. Three shapes were doing it, and
    each is now joined id to id (see Conventions and Files):
    - **Rapperswil-Jona and Stade Nyonnais**, the `MANUAL-` shape - now
      under their real Q-ids through the hand-named fallback.
    - **FC Erzgebirge Aue and SV Babelsberg 03**, both with hand rows,
      and **FC Augsburg**, without one - the club-and-men's-team shape.
      Documented, but still two findings each on every run. Joined on
      each team item's own `P831` (parent club).
    - **Young Violets Austria Wien**, a hand-row club reading as one
      false `extra-not-in-roster` (its table row has no link). Joined by
      a hand link.
    **CSC Dumbrăvița was never affected**: its row has carried its real
    Q-id `Q55618976` since the file's first commit, it corrects a club
    the query returns, and its verdict was `ok` throughout. Nothing else
    was silently double-counted. Checked row by row against
    `roster-review.csv`: the other hand-row clubs with a finding
    (FC Ismaning, FC Viktoria 1889 Berlin, FSV Optik Rathenow, Germania
    Egestorf, SV Eichede, SV Heimstetten, TSV 1896 Rain, VfB Auerbach,
    Wuppertaler SV) each carry ONE `extra-not-in-roster` - tier-4 churn,
    a real question about the division, not one club counted twice.
    **Bihor Oradea's pair stays two findings on purpose**: it is two
    items the sources disagree about, the identity question recorded in
    its own entry, and joining them would be deciding it. **CSM Olimpia
    Satu Mare** reads twice under ONE Q-id (`wrong-tier` from Liga II,
    `extra` from Liga III) - two divisions each saying something true,
    no hand row involved; unchanged.
  - **Austria, the seven 2. Liga clubs added** on Alexandru's
    instruction, each confirmed by the complete 2026-27 2. Liga article
    and its ground by **the league's own site**, 2liga.at (robots.txt
    allows everything; one stadium page per team, name, address,
    capacity). SKU Amstetten (Ertl Glas-Stadion, 3,030), SC Schwarz-Weiß
    Bregenz (its own `P115`; capacity contested, 12,000 against the
    league's 5,000, left as Wikidata has it), Floridsdorfer AC (FAC-Platz,
    3,000), ASK Voitsberg (Münzer Bioindustrie Sportpark, the
    Hans-Blümel-Stadion's item for the position; capacity blank), FC
    Hertha Wels (EWW Stadion, 3,000 - the HUBER Arena item sits on the
    same spot), SK Rapid Wien II (Allianz Stadion, Rapid's pin and
    Rapid's 28,600) and SK Sturm Graz II (**Solarstadion Gleisdorf** - the
    league site, the German infobox and article against the English
    table's Merkur Arena; position from OpenStreetMap; capacity blank).
    Rapid II and Sturm II are read by the roster check through hand
    links, because the article links their parent clubs.
  - **The Tivoli carries one figure, 16,008, on WSG Tirol and FC Wacker
    Innsbruck.** The league's own pages for both clubs, the 2026-27
    Bundesliga table and StadiumDB agree exactly. Not taken: 17,000,
    which WSG's own stadium page gives as the total with standing places
    (15,200 seats), and the 2. Liga table and the stadium's articles
    repeat; 17,400, Wikidata's. Both rows say so.
  - **FC Liefering's ground is the Red Bull Arena**, the map's all
    along - the league's own team page is the third source that settles
    the two-to-one split; the Untersberg-Arena was a tenancy in 2014-15
    and 2018-20 (German article). Its capacity now matches Salzburg's
    row for the same ground, 30,188, instead of Wikidata's 31,895.
  - **The five old Vienna clubs are gone, checked rather than left
    open**: FC Wien dissolved in 1973; SC Wacker Wien and SK Admira Wien
    merged in 1971 into FC Admira/Wacker (on the map as Admira Wacker);
    Brigittenauer AC's first team was dissolved in 1933 and the club
    merged away in 2009, its name gone; the Vienna Cricket and
    Football-Club still exists but plays no football. German Wikipedia
    for each, read on a runner. Each has a whole-club `rejected` row in
    `coordinate-reviews.csv`, the Wiener AC way - they have no
    coordinates, so a `skip` is not needed while that holds.
  - **BFC Dynamo is pinned to the Sportforum, capacity blank** -
    Alexandru's decision to prefer Wikipedia's two infoboxes over
    StadiumDB's Jahn-Sportpark listing at a tier where StadiumDB is
    thin. The position is the Sportforum's own item `Q551837`.
  - **Serbia's top two tiers are on the map: SuperLiga 13 of 14 and
    First League 15 of 16 drawn, nothing extra and nothing at the wrong
    tier, and the two not drawn are off for a named reason.** Same
    pipeline and standard as the six countries before it; tiers 1 and 2
    only, the Serbian League and below deliberately untouched.
    - **The league Q-ids were read, not remembered**: `Q235307` SuperLiga
      (`P3983` 1, enwiki *Serbian SuperLiga*) and `Q1813595` First League
      (enwiki *Serbian First League*, **no** `P3983`). Both 2026–27
      articles are one stadiums-and-locations table, 14 of 14 and 16 of
      16 resolved directly, and each has a Team changes table that
      turned out to be the most useful thing on the page. StadiumDB's
      slug is `ser` (`srb` is a 404), 29 grounds - bare coverage, so
      silence there is unchecked, never agreement. The country box's
      north, east and west edges are Wikidata's own `P1332`/`P1334`/
      `P1335` on `Q403`; its south edge sits below Preševo, because
      Wikidata's southernmost point is in Kosovo. Labels are asked in
      English first, then Serbian Latin (Conventions-level reasoning in
      `COUNTRY_BOX`'s comment); Cyrillic is never asked for.
    - **Serbia is where the club query's blindness to end dates bites
      hardest.** Every item carrying either tag at any rank was listed
      (86 statements, about sixty items) and read against both articles,
      `P576` and its own English infobox. Most Serbian league tags carry
      `P580`/`P582` qualifiers, and **the club query does not read
      `P582`**, so a tag that ended in 2013 counts as current. The result
      read before any build: **fourteen items would have been drawn**
      in a division they left - five at tier 1 - and nine more would
      have been offered as coordinate proposals next month.
      - **`skip`ped, fourteen**, each to the Hermannstadt standard (both
        articles complete, neither lists it, an infobox states the
        reason): at tier 1 **FK BSK Borča** (Belgrade First League),
        **FK Budućnost Banatski Dvor** (dissolved 2006),
        **FK Proleter Novi Sad** (dissolved 2022, and it was on
        Vojvodina's pin), **FK Proleter Zrenjanin** (dissolved 2005) and
        **FK Sloboda Užice** (Serbian League West); at tier 2 **FK
        Bežanija**, **FK Inđija**, **FK Mladost Novi Sad** (withdrew),
        **FK Rad**, **FK Sloga Kraljevo** (dissolved 2025), **FK Timok**,
        **OFK Bačka**, **OFK Mladenovac** and **RFK Novi Sad 1921**.
      - **Rejected before they were ever proposed, nine**, whole-club
        rows in `coordinate-reviews.csv`: OFK Bečej 1918, FK Bačinci
        (merged 2010), FK Jedinstvo Putevi, FK Kolubara, FK Radnički
        Nova Pazova, FK Sloga 33, FK Srem, FK Tekstilac Odžaci (relegated
        to the Serbian League, the First League article's own Team
        changes table says) and FK Zlatibor Čajetina.
      - Three more carry `P576` and the gate already drops them: FK
        Hajduk Kula, FK Banat Zrenjanin, FK Sevojno.
      **Whether the club query should honour `P582` is Alexandru's call**
      and is written here rather than built. It would have saved most of
      the fourteen rows. *(Measured 2026-09-29 and that was wrong: five
      of the fourteen skips, and one of the six tier corrections, rest on
      an ended tag; the other nine skipped clubs carry no end date at
      all. See the 2026-09-29 entry.)* It would also change what every country's
      builder sees, and LR Vicenza's shape rests on a preferred tag with
      an end date, so it needs measuring across all seven countries
      before anyone switches it on.
    - **Six tiers corrected by hand, all reviewable**, each on two
      complete division lists plus the club's own infobox, and for five
      of them the Team changes table too - the FC Wil shape: **FK Javor
      Ivanjica, FK Napredak Kruševac, FK Spartak Subotica and FK TSC** to
      tier 2 (relegated from the 2025–26 SuperLiga, their preferred
      SuperLiga tags stale), **FK Smederevo 1924** to tier 2 (a SuperLiga
      tag dated 2009–2013), and **FK Mačva Šabac** to tier 1 (promoted,
      its preferred First League tag stale).
    - **Seven promoted clubs whose tags did not follow reach the map
      through the hand-named fallback**, each under its own Q-id: FK
      Zemun (tier 1), FK Bor 1919, FK Loznica, FK Proleter 023 (a new
      item for a club refounded on 9 July 2026 - not Proleter Zrenjanin),
      GFK Dubočica, OFK Vršac and RFK Grafičar Beograd (tier 2).
    - **Grounds are where the matches are played, read from the leagues'
      own schedules.** superliga.rs and prvaliga.rs (robots.txt allows
      the team and schedule pages) list a venue for every match, and for
      four clubs that settled a disagreement between the club's
      registered ground - Wikidata, the league's team page, the Serbian
      infobox - and the one it actually uses in 2026–27:
      **OFK Beograd** at the Serbian FA's centre in Stara Pazova (both
      home games so far; the Omladinski is its own), **FK IMT** at the
      Lagator in Loznica (sharing FK Loznica's pin, genuinely),
      **FK Bor 1919** at the Mladost in Kruševac, 170 km from Bor (two of
      its three home games, sharing Napredak's pin) and **FK Zemun** in
      Ub, below. **FK Železničar Pančevo** (SC Mladost, all six home
      games), **FK TSC**, **FK Mačva** and **OFK Vršac** were placed from
      their own ground items or OpenStreetMap, and **RFK Grafičar** on
      Red Star's auxiliary pitch, sharing Red Star's pin.
    - **Two clubs are off the map, named, because nobody knows where
      the ground is**: **FK Jedinstvo Ub** and **FK Zemun** play at the
      Stadion "Dragan Džajić" in Ub. Its Wikidata item `Q110045992` has
      no position and OpenStreetMap maps three unnamed full-size pitches
      in Ub and no grandstand, so which is the stadium is a guess, and a
      guess is not a pin. Zemun's hand row clears the position it would
      otherwise take from its own ground in Zemun, where no 2026–27
      match has been played; Jedinstvo has no position anywhere and is
      `unplaced-no-coordinates`. Two halves of one coordinate, from any
      source that names the Ub ground, bring both back.
    - **Duplicates: none.** No men's-team item, no two items for one
      club; three shared pins, each genuine (Lagator, Mladost Kruševac,
      the Rajko Mitić complex). **Hidden leagues**: no preferred
      `<novalue>`; query C's two Serbian candidates, FK Donji Srem and FK
      Jagodina, are named by no roster - bill 0.
    - **Capacities: nothing corrected, and the reasons are written
      down.** StadiumDB's four Serbian rows: **FK Crvena zvezda** 55,538
      (Wikidata) / 51,755 (StadiumDB) / 49,167 (the SuperLiga table) and
      **FK Novi Pazar** 12,000 / 6,900 / 10,000 - no two within 5% in
      either, so contested and unchanged; **FK Javor Ivanjica**, where the
      map's 5,000 agrees with the table and StadiumDB's 3,000 is the
      outlier; and **FK Proleter 023**, where StadiumDB matched the wrong
      ground - its "Proleter" at the Karađorđe in Novi Sad is the
      dissolved Proleter Novi Sad, and the map's Zrenjanin figure stands.
      OpenStreetMap confirms almost nothing, Romania's and Italy's shape:
      of 28 clubs, 1 agrees, 18 have a Wikidata figure only. Five
      capacities are blank on purpose (Mačva, Železničar, OFK Beograd,
      Vršac, Grafičar), each because its only figures are one source's.
      The OpenStreetMap cross-check needed **three runs** on the branch
      before one came back complete - Austria and Germany answered HTTP
      504 on the first, Serbia on the second, and each time the review
      file was rightly left alone. The complete run found no disagreement
      in Austria, Switzerland or Serbia. It did find **no stadium within
      500 m of OFK Beograd's SC FSS pin**, so that position rests on the
      Serbian FA centre's own Wikidata item alone - worth a look. (It
      also found OpenStreetMap's "Stadion im Sportforum" 63 m from BFC
      Dynamo's new pin.)
    - **Fixtures: none.** football-data.org's free tier carries no
      Serbian competition; the club sheet says so.

- **Austria's top two tiers are on the map, 2026-09-26: Bundesliga 12
  of 12, exact; 2. Liga 9 of 16, with nothing extra and nothing at the
  wrong tier, and each of the seven missing is missing for a named
  reason.** Same pipeline and standard as the other five countries, run
  on a GitHub runner through four throwaway probes (removed in the same
  branch). Tiers 1 and 2 only; the Regionalliga and below were
  deliberately not touched.
  - **The league Q-ids were read, not remembered**: `Q219592`
    Bundesliga (`P3983` 1, enwiki *Austrian Football Bundesliga*) and
    `Q650236` 2. Liga (enwiki *2. Liga (Austria)*; it carries **no**
    `P3983`, and its 2025–26 season item's `P3450` points at it).
    StadiumDB's slug is `aut` (`austria`, `at` and `ost` are 404s). The
    2. Liga row in `league-rosters.csv`, parked since the design pass
    under its corrected title, is now live. Both articles are one
    stadiums-and-locations table: 12 of 12 resolved (one through a
    redirect), and 16 rows in the 2. Liga table.
  - **The 2. Liga table links three reserve sides wrongly, and the
    roster check now says so instead of believing it.** Reserve sides
    have no English article, so "SK Rapid II" links SK Rapid Wien,
    "Sturm Graz II" links SK Sturm Graz, and "Austria Wien II" has no
    link at all, so the row's first link was the **city of Vienna**. Read
    as written, that made Rapid and Sturm `wrong-tier` and Vienna a
    division member. `check_rosters.py` now leaves out both row shapes
    and names them in its run summary (see Files). It changed five
    Romanian verdicts too - see the Liga III entry.
  - **What the first build brought, 25 clubs against 28 teams:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 14 | 11 |
    | after this pass | **12** | **9** |
  - **Two tier-1 extras.** **FC Blau-Weiß Linz `Q696525`** is at tier 2
    by a hand row: its only `P118` is the Bundesliga, the complete
    Bundesliga article omits it, the complete 2. Liga article lists it
    and says it was relegated, and its infobox agrees - the FC Wil
    shape, reviewable. **VSE St. Pölten `Q731715`** is `skip`ped: a
    Bundesliga tag dated 1988–1994, no `P576`, drawn at tier 1 at the
    Voithplatz; the German infobox says *aufgelöst 1998*. Shape 4.
  - **Four tier-2 extras `skip`ped** to the Hermannstadt standard (both
    articles complete, neither lists them, an infobox or the article
    states the reason): **FC Gratkorn** `Q697322` (Unterliga Central),
    **FC Juniors OÖ** `Q1387445` (Regionalliga), **FC Lustenau 07**
    `Q692186` (Regionalliga West) and **SK Austria Klagenfurt**
    `Q699184`, relegated to the third tier after an insolvency
    application, which the 2. Liga article itself says.
  - **SV Austria Salzburg `Q22866` placed** at the Max Aicher Stadion,
    1,566 (2. Liga table, StadiumDB and infobox agree; the position is
    the ground's own item, `Q20180568`). It was `unplaced-no-coordinates`.
  - **Young Violets Austria Wien `Q60967849` is Austria Wien II and
    stays.** The roster check will keep calling it `extra-not-in-roster`,
    because its table row has no link and so names no Q-id. A note-only
    row says so. *(Since 2026-09-27 a hand link in
    `roster-links-manual.csv` joins that row to `Q60967849` and the check
    reads one club in its division - see the 2026-09-27 entry.)*
  - **The seven 2. Liga teams still missing, and why** - *all seven were
    added on 2026-09-27, on Alexandru's instruction, through the
    hand-named fallback; see the 2026-09-27 entry. What follows was true
    when written:*
    - **Five promoted clubs whose tags did not follow** - SKU Amstetten
      `Q2206406`, SC Schwarz-Weiß Bregenz `Q699686`, Floridsdorfer AC
      `Q696474`, ASK Voitsberg `Q297832` (each tagged with a Regionalliga
      only) and FC Hertha Wels `Q63168427` (no `P118` at all). The
      Rapperswil-Jona shape exactly: `missing-from-wikidata`, and only a
      no-Q-id add row reaches them, at two false roster findings each.
      **Not added**, because Alexandru's instruction to use that route
      named the two Swiss clubs only. **His call.**
    - **SK Rapid Wien II `Q98228613` and SK Sturm Graz II `Q98217947`**
      exist on Wikidata but carry no 2. Liga tag, and the article links
      their parents, so the roster check cannot name them either. Rapid
      II plays at the Allianz Stadion (German infobox); Sturm II's
      German infobox names the Solarstadion Gleisdorf **and** the
      Stadion Donawitz, so its ground is not settled.
  - **Capacities: seven written, and each note names every figure.**
    By the UTA Arad rule: Red Bull Salzburg 31,895 → **30,188**, Grazer
    AK and Sturm Graz 15,400 → **16,364** (they genuinely share the
    Merkur Arena), TSV Hartberg 4,500 → **5,024**, WSG Tirol 17,400 →
    **16,008**. Filled where Wikidata had none: SK Rapid Wien **28,600**,
    FC Blau-Weiß Linz **5,595** (StadiumDB and infobox; OpenStreetMap's
    5,565 on the first branch run agrees too). **LASK's ground was wrong**: Wikidata's
    `P115` is the old Linzer Stadion (1952, 18,000); the club has played
    at the **Raiffeisen Arena**, rebuilt on the same site, since 2023 -
    19,080 on three sources, its own item `Q116693275` for the position.
    **Left alone**: Admira Wacker (12,000 / 10,600 / 7,010, no two
    agree), SC Austria Lustenau (8,800 on Wikidata against 5,138 on
    English Wikipedia twice - one source), Wolfsberger AC, First Vienna
    and Kapfenberg (the map agrees with one other source), and **FC
    Wacker Innsbruck**, which shares the Tivoli with WSG Tirol: its own
    division's table (17,000) agrees with Wikidata (17,400), so by the
    same rule its figure stands - **one ground now carries two figures on
    two rows**, written down in WSG's note rather than smoothed over.
    *(Settled 2026-09-27 on Alexandru's instruction: 16,008 on both, the
    league's own figure for both clubs - see the 2026-09-27 entry.)*
    **FC Liefering** is drawn at the Red Bull Arena (Wikidata's `P115`,
    a copied first-team ground); the 2. Liga table says the
    Untersberg-Arena in Grödig, its English infobox lists both, and
    StadiumDB has neither for Liefering. Two against one, not
    corrected; worth a look. *(Settled 2026-09-27 by a third source, the
    league's own team page: the Red Bull Arena, so the map was right; its
    capacity now matches Salzburg's row for the same ground.)*
  - **StadiumDB's Austrian page has 27 grounds, and is as thin as
    measured in 2026-09-19.** It has nothing for SC Austria Lustenau,
    Liefering's Untersberg-Arena or Wacker Innsbruck by name. After the
    corrections its review file holds three Austrian rows: Admira
    (contested), First Vienna (map agrees with the table) and Altach (a
    sponsor's name). **Silence is not agreement**, as for Switzerland.
  - **The rank blind spot, all three shapes.** Query C's only Austrian
    candidate is SC Wiener Neustadt `Q134073`, bill 0 (1. Landesliga
    per its infobox). No Austrian item carries a preferred `<novalue>`.
    One carries a tracked league at deprecated rank, ASV Hertha Wien,
    dissolved 1940.
  - **The stale-active-club pattern (shape 6) was looked for.** Every
    item carrying either Austrian tag at any rank was listed (61
    statements, about fifty items) and
    read against both articles, `P576` and its infobox. Three would have
    been offered as coordinate proposals and now have whole-club
    `rejected` rows in `coordinate-reviews.csv`: **SV Horn** `Q689889`
    and **SV Lafnitz** `Q15137936` (alive, in the Regionalliga - the
    relegated relative of shape 6) and **Wiener AC** `Q581990` (no
    longer plays football). **Five more are Alexandru's call** -
    *checked on his instruction on 2026-09-27 and all five are gone
    (dissolved, merged away, or no longer playing football), each now a
    whole-club rejection; see the 2026-09-27 entry. As first written:*
    Brigittenauer AC, FC Wien, SC Wacker Wien, SK Admira Wien and the
    Vienna Cricket and Football-Club carry Bundesliga tags **dated**
    between 1911 and 1971, no `P576`, and no coordinates, so they are
    off the map today and may be proposed next month. Their only
    evidence of being gone is those dates and their absence from both
    articles, and the La Dominante precedent looked for an infobox as
    well - none of them has one that says so. **The club query does not
    read `P582` on a league tag**; that is why a 1930s tag counts as
    current.
  - **Fixtures: none.** football-data.org's free tier carries no
    Austrian competition and OpenLigaDB is German only; the club sheet
    says so.

- **Two truthy grounds on one club item - the SC Freiburg shape - was
  looked for in every country on 2026-09-26, and it is on six clubs on
  the map, not one.** CLAUDE.md said Freiburg's ground "moved" because
  Wikidata was catching up; that was asserted, not checked, and it was
  a flap (see the Italy entry). The question asked this time: which
  club, in any mapped league of all six countries, carries two or more
  `P115` values at its best rank. `fetch_clubs.py` builds a club from
  whichever query row arrives first, and the query service promises no
  order, so such a club's ground can change between rebuilds - and
  worse, the builder can take the **name** from one ground's row and
  the **capacity or position** from the other's. **Two clubs were
  drawing exactly that mixed record** when looked at.
  **Every rebuild now names these clubs** and says whether a hand row
  pins each one. The remedy, as for Freiburg, is a hand row with venue,
  capacity, lat and lon, and only on **three sources agreeing**.

  | club | Wikidata's two grounds | what the map showed | now |
  |---|---|---|---|
  | SC Freiburg | Dreisamstadion; Europa-Park-Stadion | alternated | pinned 2026-09-26 (earlier pass) |
  | Borussia Dortmund II | Rote Erde; Westfalenstadion | Rote Erde's name and capacity (a hand row), **the Westfalenstadion's position** | position pinned to Rote Erde's own item: StadiumDB, infobox and the item agree |
  | VfB Stuttgart II | Robert-Schlienz-Stadion; Waldau | the Waldau, shared with Stuttgarter Kickers | **neither** - the 3. Liga table, StadiumDB and the infobox all say the WIRmachenDRUCK Arena in Aspach, 10,001 |
  | FC Rapid București | Giulești; Regie | **the Regie**, 10,020 | Giulești, 14,047: Liga I table, StadiumDB and infobox |
  | FC Lugano | Cornaredo (ends 2026); AIL Arena (starts 2026) | the Cornaredo | the AIL Arena, whose Wikidata item exists after all (`Q140038602`); capacity still cleared, 8,093 against 8,793 |
  | BFC Dynamo | Sportforum Hohenschönhausen; Jahn-Sportpark | the Sportforum's name and pin **with the Jahn-Sportpark's 19,708** | capacity cleared; ground **pinned to the Sportforum on 2026-09-27**, Alexandru's decision: both Wikipedia infoboxes over StadiumDB, whose coverage at this tier is thin; capacity still blank |

  **Also found, and not a flap today**: Olympique Lyonnais carries the
  Parc OL and the Stade de Gerland (dated 1950–2015) at the same rank
  when the statements are read one by one, but the club query itself
  returned only the Parc OL on 2026-09-26, so nothing was pinned; the
  rebuild report will say so if that changes. Știința Poli Timișoara
  has two grounds and was already pinned by hand. **No Austrian club
  has the shape.** The Waldau is now Stuttgarter Kickers' alone, which
  corrects the old claim that it was genuinely shared.

- **FC Rapperswil-Jona and FC Stade Nyonnais are on the map at tier 2,
  2026-09-26, as hand-added clubs with no Q-id - on Alexandru's
  instruction, and at a cost that is written down.** Switzerland's
  Challenge League is now **10 of 10 drawn**. Both season articles were
  re-read first, as he asked: the complete Challenge League article
  lists both (with 2026-27 results for both), the Super League article
  names neither except Nyon in its navigation box, under the Challenge
  League. Rapperswil-Jona is at the **Stadion Grünfeld** (the ground's
  own item `Q26868807` for the position; capacity **blank** - 2,500,
  2,700, 3,200 and 4,350 in four places, no two independent ones
  agreeing). Stade Nyonnais is at the **Stade de Colovray**, 7,200, the
  ground on its own `P115`.
  **The instruction's premise was not quite right, and it matters for
  the next one.** It said to add them "the same way CSC Dumbrăvița was
  originally added - blank clubQid". Dumbrăvița's row has carried its
  Q-id, `Q55618976`, since the file's first commit: it **corrects** a
  club the query already returned, which is why it costs nothing. A
  row with no Q-id is a different thing - an **add** - and its cost is
  the one the Switzerland entry named: the roster check joins on Q-ids,
  so each club now reads as `missing-from-wikidata` under its real
  Q-id **and** `extra-not-in-roster` under its `MANUAL-` id, on every
  run. `_sameNameOnMap` does fire on the missing side, because the rows
  use the article's exact names, so the pair at least points at itself.
  **A route with no false findings exists and was not built**, because
  it is a design change and his to choose: a third fallback shape that
  surfaces a club a current roster names even when none of its tags is
  mapped, **without a tier**, so that it stays off the map until an
  ordinary `clubQid` hand row gives it one - the Inter Sibiu rule. It
  would reach both Swiss clubs and the five Austrian ones above under
  their own Q-ids.
  **Built on 2026-09-27, on Alexandru's instruction, as the hand-named
  fallback** - the same idea, driven by the hand row rather than by a
  search: the candidates are the Q-ids a hand row names, and the hand
  row gives the tier (Conventions). Both clubs now carry their real
  Q-ids and each reads as one club, `ok`, in its division.

- **Switzerland's top two tiers are on the map, 2026-09-26: Super
  League 12 of 12, exact; Challenge League 8 of 10, nothing extra and
  nothing at the wrong tier, and the two missing are missing for a
  named reason.** Same pipeline and standard as Germany, Romania,
  France and Italy, run on a GitHub runner through four throwaway
  probes (removed in the same branch). Tiers 1 and 2 only; the
  Promotion League and below were deliberately not touched.
  - **The league Q-ids were read, not remembered**: `Q202699` Super
    League and `Q669073` Challenge League, each confirmed by its enwiki
    sitelink and `P3983` 1 and 2. **`Q202699` carries `P17`
    Liechtenstein** as well; nothing depends on it, because tier comes
    from `league-tiers.csv`. StadiumDB's slug is `sui` (`swi`, `che`,
    `switzerland` and `ch` are 404s). The Challenge League article is
    one stadiums table, 10 of 10 resolved (2 through a redirect). **The
    Super League article's stadiums table is laid out with the clubs as
    its header row**, so `check_rosters.py` does not recognise it and
    reads the league table instead: 12 of 12 resolved, but no capacity
    column for that division. The table was read by hand in a probe.
  - **What the first build brought, 24 clubs against 22:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 13 | 11 |
    | after this pass | **12** | **8** |
  - **Five tier-2 clubs carried a stale Challenge League tag and are
    `skip`ped**: FC Biel-Bienne `Q674799`, FC Chiasso `Q668573`, FC
    Gossau `Q690074`, FC Locarno `Q368675`, FC Wohlen `Q583599`. Each has
    one `P118`, Challenge League, normal rank, no `P576`. The standard is
    Orléans/Béziers/Martigues: both articles complete, neither lists
    them, and each club's own infobox names a lower league (Promotion
    League, 2. Liga Ticino, 2. Liga Interregional twice, 1. Liga
    Classic). No tier is written; each row says how to bring the club
    back.
  - **FC Wil `Q187091` is at tier 2 by a hand row, and that one is
    reviewable.** Its only truthy `P118` is Super League, so it arrived
    at tier 1. The complete Super League article does not list it, the
    complete Challenge League article does, and the club's infobox says
    Challenge League. Three reads, two of them complete division lists:
    the Babelsberg shape, not the Farul one, so it was written rather
    than left. Still Alexandru's to overrule; emptying the cell puts it
    back at tier 1.
  - **Both are on the map since 2026-09-26, as hand-added clubs with
    no Q-id, on Alexandru's instruction** - see the entry on the
    Austria pass. What follows is why that was the only route, and what
    it costs; it is kept as written.
  - **The two Challenge League clubs still missing, and why neither is
    fixable by a hand row today.** **FC Rapperswil-Jona `Q681483`**
    carries only `Q672305` 1. Liga; **FC Stade Nyonnais `Q673268`**
    carries only `Q25762` Promotion League. Both were promoted and
    their tags did not follow, so the club query never sees them
    (`missing-from-wikidata`). Mapping either league would be wrong,
    since both are genuinely lower tiers. And `apply_manual` rejects a
    `clubQid` the query did not return, so only an add row with no
    Q-id would reach them, at the cost of two permanent false findings
    each. That is the Farul obstacle before the fallback existed.
    **Alexandru's call**; the roster check names both every run.
  - **The stale-active-club pattern (shape 6) was looked for, not
    waited for, and it is here once.** Every item carrying a Swiss tier
    1 or 2 tag at any rank was listed (112 rows, most of them players,
    which the `Q5` filter already drops) and each club was checked
    against both articles, `P576` and its infobox. **Anglo-American Club
    Zürich `Q339492`**: normal-rank Super League tag, no `P576`, no
    coordinates, infobox *dissolved 1900*. It dies at the coordinates
    gate today and would have been offered as a coordinate proposal on
    the next monthly run; it now has a whole-club `rejected` row in
    `data/coordinate-reviews.csv`. FC Neuchâtel `Q3063128` carries `P576`
    1906 and the dissolution gate already drops it. No other Swiss item
    has the shape.
  - **The rank blind spot, all three shapes.** No Swiss item carries a
    tracked league at deprecated rank, and the preferred-`<novalue>`
    query found nothing. Query C found one: **AC Bellinzona `Q289112`**,
    Challenge League at normal rank under a preferred statement naming
    another league. Its bill is 0: the Challenge League article's team
    changes and its own infobox both say it was relegated to the
    Promotion League, so it stays off, correctly.
  - **FC Vaduz is the Monaco shape** (see Conventions): flagged by the
    country check every run because its `P17` is Liechtenstein, which is
    true, and kept because it plays in the Super League. A note-only row
    says so.
  - **Grounds and capacities.**
    - **FC Lausanne-Sport was on the wrong ground.** Wikidata's `P115`
      is still the Pontaise, at 50,000, which the club left in 2020. It
      is corrected to the **Stade de la Tuilière, 12,544** (Super League
      table, StadiumDB and the ground's Wikidata item agree), at that
      item's own `P625`.
    - **FC Stade Lausanne-Ouchy `Q869907` was placed** at the Pontaise,
      15,850. Its ground was named by the Challenge League table,
      StadiumDB and the Pontaise's own tenant list; the coordinate is
      the Pontaise item's `P625`. It is in the 2026–27 article with no
      `P576`, checked before the row was written. So the Pontaise pin
      moved from one Lausanne club to the other, and neither shares.
    - **FC Sion 16,263 → 14,283**, the UTA Arad rule: the Super League
      table and OpenStreetMap agree exactly; StadiumDB's 20,187 and
      Wikidata's 16,263 are recorded as not taken.
    - **FC Lugano: ground pinned to the AIL Arena on 2026-09-26, capacity
      still cleared** - see the entry on two grounds. What follows was
      true when written.
    - **FC Lugano: capacity cleared, ground open.** No source supports
      Wikidata's 15,000. The club infobox and the Super League table say
      the club now plays at the **AIL Arena**, at 8,093 and 8,793
      respectively (8% apart), and the AIL Arena has no enwiki article
      or Wikidata item this pass found, so no coordinate. The pin and
      venue name stay at the Cornaredo. What settles it is the AIL
      Arena's position and one capacity two sources agree on.
    - **Two figures, no arbiter, unchanged**: SC Kriens (5,360 on
      Wikidata and the stadium's infobox, 3,500 in the Challenge League
      table), Yverdon-Sport (6,600 against 4,200) and Étoile Carouge
      (7,200 on Wikidata against 3,600 in both the table and the
      stadium's infobox, which are one source, Wikipedia, twice).
      **FC Aarau** is the Magdeburg case: 9,249 on the map, StadiumDB
      and the stadium's infobox, against the table's 8,000.
    - **FC Zürich and Grasshopper share the Letzigrund**, and that is
      genuine: StadiumDB and the stadium's tenant list both say so.
  - **StadiumDB covers Switzerland as thinly as measured in 2026-09-19,
    and its silence is not agreement.** 17 grounds on the Swiss page. Of
    the 20 clubs now on the map it has **no figure for eight**: FC
    Lugano, FC Vaduz (Liechtenstein is not on the Swiss page), FC Wil,
    Grasshopper (StadiumDB lists the Letzigrund under FC Zürich and
    "Grasshoppers", and the matcher paired only FC Zürich), SC Kriens,
    Yverdon-Sport, Étoile Carouge and FC Lausanne-Sport. StadiumDB
    does list the Tuilière at 12,544, under the club name
    "Lausanne-Sports", and the matcher, rightly, does not treat
    "Sports" as "Sport"; that figure was read by hand for the row
    above. After the corrections the check reads 20 clubs, 9 agree,
    2 differ (Sion, where StadiumDB is the outlier, and Basel, 38,512
    against 36,000, where the Super League table's 37,994 sides with
    the map), 1 ground-name clash (Thun: Stockhorn Arena against
    Visana Stadion, figures within 5%), 8 not matched. Those eight
    clubs' capacities rest on Wikidata and at most Wikipedia.
  - **OpenStreetMap confirms nothing in Switzerland either**: of 24
    clubs on the first build, 0 agree, 1 differs (Sion, which is what
    settled it), 18 have a Wikidata figure only and 5 have no OSM ground
    nearby. Italy's and Romania's shape, not Germany's.
  - **Fixtures: none.** football-data.org's free tier carries no Swiss
    competition and OpenLigaDB is German only; the club sheet says so.
  - **Found on the way, not Swiss**: SC Freiburg's flapping ground (see
    the Italy entry, corrected), and the OpenStreetMap capacity
    cross-check hitting HTTP 504 on Germany on its first branch run and
    leaving its review file unchanged. It was re-run and came back
    complete before the merge.

- **Italy's top two tiers are on the map, 2026-09-25. Serie A came
  back exact, 20 of 20; Serie B is 18 of 20 with nothing extra since
  LR Vicenza was surfaced later the same day, and each of the two
  still missing is missing for a different, named reason.** Same pipeline and same standard as Germany, Romania and
  France, run on a GitHub runner because the sandbox still answers 403
  to CONNECT for Wikidata, Wikipedia and StadiumDB. Tiers 1 and 2 only;
  Serie C and below were deliberately not touched.
  - **The league Q-ids were read, not remembered**: `Q15804` Serie A
    and **`Q194052`** Serie B, both `P17` Italy. The Serie B id first
    written from memory, `Q15817`, **was wrong** — the second time in
    two countries, after France's Ligue 2. The probe is not optional.
    StadiumDB's slug is `ita` (`italy` and `it` are 404s). Both season
    articles are one stadiums-and-locations table of 20; Serie B needed
    the redirect hop for one title.
  - **Inter and AC Milan: the club pipeline and the ticket files agree,
    and there is no second candidate.** The club query returns
    **`Q631`** for Inter and **`Q1543`** for AC Milan — the ids
    `club-tickets.csv` has carried since 2026-09-24 — and the 2026–27
    Serie A article's links resolve to the same two. To rule out a
    duplicate rather than assume there was none, every item carrying a
    Serie A or Serie B tag **at any rank** whose English or Italian
    label contains "Inter" or "Milan" was listed: four came back, `Q631`,
    `Q1543`, and two clubs that are neither — Internazionale Torino
    (`Q1538737`, 1890s Turin) and US Internazionale Napoli (`Q728986`).
    No shape-5 team item, no shape-1 duplicate. `link_fixtures.py`'s
    ticket read-back now says `Q631 … on the map`, joined by Q-id; the
    only difference it reports is the label, "FC Inter" on Wikidata
    against "FC Internazionale Milano" in the ticket file, which is a
    name and not an identity. The two share the San Siro pin, which is
    right.
  - **What the first build brought, 48 clubs against 40:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 23 | 25 |
    | after this pass | **20** | **17** |
    | after Vicenza, same day | **20** | **18** |
  - **Eight of the extra items were club SEASONS, not clubs** —
    *Palermo Football Club 2026-2027*, *Reggina 1914 2020-2021* and
    six more, each on its club's pin. The Rennes shape in a second
    spelling: the club's name, then a year range. The not-a-club net
    in `fetch_clubs.py` now knows the Italian type word `stagione` and
    a name ending in a year **range** (a club ends in one founding
    year, "Como 1907", never two). Checked against all four country
    files before it went in: those eight and nothing else.
  - **Three were clubs that no longer play at either tier, and are
    `skip`ped** to the Hermannstadt standard — both division articles
    complete (20 of 20 each), neither lists them, and an independent
    statement of the reason: **FC Torinese** `Q534448` (infobox:
    dissolved 1906; its Serie A tag is dated 1898–1900 but the club
    query does not read dates), **ChievoVerona** `Q2037` (a stale
    *preferred* Serie B tag; infobox: Serie D Group B) and **AC La
    Dominante** `Q3626037` (tag dated 1927–1931; no English article,
    so the reason is the **Italian** infobox: *Scioglimento 1931*).
    Chievo was sitting on the Bentegodi beside Hellas Verona, so that
    shared pin went with it.
  - **The three missing Serie B clubs were three different things.
    Two are still missing, and neither is fixable by a hand row today;
    Alexandru has said to leave both as they are:**
    - **Carrarese** `Q650365` has no ground and no coordinates:
      `unplaced-no-coordinates`, the `coordinate-review.csv` route.
    - **Calcio Padova** `Q8428` carries **`P576` 2014**, so the
      dissolution gate drops it — while its own infobox says *2025–26
      Serie B, 10th of 20* and the 2026–27 article links this item.
      A `P576` for a 2014 bankruptcy and refoundation, on the item that
      now describes the refounded club. That gate is working as
      designed and must not be loosened for one club; and
      `apply_manual`'s guard rejects a `clubQid` the query did not
      return, so no hand row reaches it. **Alexandru's call**, and the
      roster check's `missing-from-wikidata` verdict undersells it —
      the club is on Wikidata, the gate that removes dead clubs removed
      it.
    - **LR Vicenza** `Q56542463` was **a new rank shape** and is now
      **on the map at tier 2**, surfaced by the fallback's second
      shape — see the next entry. The roster check reads it `ok`.
  - **The rank blind spot was checked for Italy rather than assumed,
    and the first answer was incomplete.** The diagnostic's queries A
    and B found four Italian items, **all the deprecated shape** and
    none the preferred-`<novalue>` one: AC Cesena and Nocerina
    (dissolved, correctly hidden), Brescia Calcio and Lanciano (no
    `P576`, but in neither 2026–27 article). By those two queries
    Italy's bill was zero. **Vicenza showed it was not** — see below.
  - **Capacities: three corrected, one contested, seven with no
    arbiter.** The UTA Arad rule, exactly: **US Avellino** 10,125 →
    **26,000** (Serie B table; StadiumDB 26,150 agrees), **Venezia**
    10,500 → **12,048** (Serie A table and StadiumDB, identical),
    **Benevento** 25,000 → **16,867** (table and StadiumDB,
    identical). **Mantova** stays contested: 7,367 / 14,884 / 12,000,
    no two within 5%. **Fiorentina** and **Cremonese** are the
    Magdeburg case — the map agrees with a second source and the third
    is the outlier (StadiumDB's 22,000 for the Franchi; the table's
    20,641 for the Zini) — so nothing changed. Seven more differ from
    the league table with no third figure at all: Atalanta, Cesena,
    Pisa, Ascoli, Empoli, Juve Stabia, Hellas Verona. Two figures, no
    arbiter, unchanged.
  - **OpenStreetMap confirms almost nothing in Italy**: of 40 clubs,
    **1 agrees and 38 have a Wikidata figure only**. Italy is Romania's
    shape, not Germany's or France's — StadiumDB and the league table
    are the only second opinions there are.
  - **Fixtures: 20 of 20 Serie A clubs link to football-data.org's SA**
    since the evening of 2026-09-25. Seventeen matched automatically;
    the other three are abbreviations the matcher correctly refuses —
    **Inter** (football-data 108 "FC Internazionale Milano" against
    "FC Inter"), **Atalanta** (102 "Atalanta BC" against "Atalanta
    Bergamasca Calcio") and **Sassuolo** (471 "US Sassuolo Calcio"
    against "Unione Sportiva Sassuolo Calcio") — and each now has a
    `link` row in `fixture-links-manual.csv`, added on Alexandru's
    instruction, the Le Mans way. Checked in the real page: each
    club's sheet lists its Serie A fixtures, and Inter's its Champions
    League ones too, beside the ticket info it already had.
    **The review file still lists all four hand-linked teams** (Le Mans
    too) as `unmatched-team`: `link_fixtures.py` writes that row before
    it applies the hand rows, and does not drop it afterwards. It is
    the same trap as `coordinate-review.csv` offering resolved rows
    again — the link is right, the review row is stale. Not fixed here.
    Serie B has no fixture source; the club sheet says so.
  - **Not Italian, but it moved in the same rebuild**: SC Freiburg's
    ground went from the Dreisamstadion to the **Europa-Park-Stadion**
    (34,700), where it has played since 2021. **This entry first said
    that was Wikidata catching up. That was asserted without being
    checked, and it was wrong.** It was not a move but a **flap**:
    `Q106394` carries two truthy `P115` values with nothing between them
    that the club query reads, and `fetch_clubs.py` keeps whichever row
    the query service returns first, so the ground alternated on every
    rebuild since 2026-09-25 (seven checked). A hand row pins the
    Europa-Park-Stadion, 34,700 (the 2026–27 Bundesliga table, Wikidata's
    figure for the ground and StadiumDB agree). **Freiburg was not the
    only one**: the same shape was looked for in every country on
    2026-09-26 and found on five more clubs on the map, two of them
    drawing a mixed record - see the entry on two grounds under Known
    open problems. The first-row-wins choice is still not changed; every
    rebuild now names each club it touches instead.

- **The 38 confident Romanian rows were judged, 2026-09-26, and the
  judgement is now remembered.** `data/coordinate-reviews.csv` holds 31
  decisions and `clubs-manual.csv` seven placements. Wikidata and
  Wikipedia were read on a runner, the dispatch route, in two probes
  that were removed in the same branch.
  - **Placed, seven clubs, every one of them named by a 2026-27
    roster:** ACS Mediaș 2022, CSO Băicoi and SCM Zalău (Alexandru's
    instruction, the OpenStreetMap ground confirmed against each
    club's infobox), CSM Vaslui (same ground as proposed, confirmed
    by the stadium article's tenant list), and three where the
    proposal was **wrong** and a different ground was placed:
    **FC Bacău** at the Ruși-Ciutea Sportsbase (Liga II stadiums
    table; the proposal was the Stadionul Municipal Bacău, **closed
    since 2014**), **Gloria Bistrița** at the Jean Pădureanu (the
    proposal was right; the coordinate is Wikidata's ground item, so
    it shares one marker with FC Bistrița) and **ACS Înainte Modelu**
    at the Vasile Enache (the proposal was Dunărea Călărași's own
    pin). Capacities only where two sources agree: FC Bacău 700,
    Gloria 7,814.
  - **Rejected, and never proposed again:** ten grounds that were a
    nearby but different town's own ground — six were matcher bugs,
    below — plus Ștefăneștii de Jos's Afumați proposal, which is CS
    Afumați's Comunal, not a shared ground. **CSL Ștefănești stays
    unplaced**: its ground is the Stadionul Dumitru Mătărău (Liga II
    table), whose Wikidata item `Q28230311` has no coordinates.
    Rejected as whole clubs: **CSM Bacău** and **Sparta Râmnicu
    Vâlcea** (both dissolved 2025 per English Wikipedia — the
    Hermannstadt pattern), both Darabani items (the club is in Liga V)
    and `Q74127553`, the thin Înainte Modelu duplicate.
  - **Held, 16 rows:** the seven Batch D clubs, the eight Batch C
    clubs and CS Sporting Juniorul Vaslui. The ground match is kept as
    a lead and no coordinate was written.
  - **Batch A and Batch C were not named in the instruction, and which
    rows they are was inferred.** Batch A is the six rows the two
    matcher bugs explain (ARO Muscelul Câmpulung, Cozia Călimănești,
    Avântul Periam, Gilortul Târgu Cărbunești, Recolta Gheorghe Doja,
    Flacăra Horezu); Batch C is the eight confident rows left over.
    Every row's reason says which batch it was put in. **If the
    inference is wrong, the fix is to edit `decision` on those rows.**
  - **Five held clubs ARE in a 2026-27 roster**, so "no roster behind
    it" does not hold for them: Bradul Putna (Batch D), CS Blejoi,
    CSO Filiași, FC Pucioasa and Oltul Curtișoara (Batch C). They
    are held as instructed. Each row says so. Two Batch C rows also
    look like the rejected shape: Olimpic Zărnești's pitch is in the
    **Buzău-county** Zărnești, and Oltul Curtișoara's is the
    neighbouring village of Moșteni's pitch. The roster check also
    labels `Q39058326` "FC Aninoasa", not FC Pucioasa.
  - **Rejected is not the end for two clubs that are playing**: ARO
    Muscelul Câmpulung and Recolta Gheorghe Doja are in the 2026-27
    Liga III article and still need their real ground.
  - **Two matcher bugs, fixed in `propose_coordinates.py`.** (1) A
    place whose name was only **partly** in the club's name was
    accepted on its first word: Periam Port, Târgu Jiu, Gheorghe
    Lazăr, Câmpulung Moldovenesc. A partial match now counts only where
    the rest of the place name is a German qualifier (`bei`, `am` …,
    the Garching bei München case it was written for) or in brackets.
    Romanian and French place names are deliberately **not**
    shortened: Galda de Jos and Galda de Sus are two villages. (2) A
    sports hall tagged `leisure=stadium` ("Sala de sport Treapt") was
    accepted as a ground. An object whose `sport` tag names only other
    sports, or whose name says hall, pool or rink, is now left out and
    listed in the run summary. **`athletics` is not one of the "other
    sports"**: the first real run left out 488 German, 291 French, 211
    Italian and 13 Romanian objects, and athletics-only stadiums among
    them, which is often a football ground with a track. Leaving the
    true ground out can make a wrong one the only candidate, so
    athletics now counts as possibly football.
  - **What the rejections turned up on the real run.** With the wrong
    grounds out of the way, two clubs got a new confident proposal:
    **ARO Muscelul Câmpulung → Stadionul Muscelul** (OpenStreetMap links
    that ground to the club's own Q-id — the strongest evidence the tool
    has) and **Gilortul Târgu Cărbunești → a "Teren de Fotbal" in
    Târgu Cărbunești**. Three rows are confident for the first time:
    KSE Târgu Secuiesc, Șoimii Gura Humorului and Lotus Băile Felix,
    and the last is a **"Teren Minifotbal"**, a small-sided pitch, which
    is very probably not a club's ground. None of the five was applied;
    they are new rows to judge.
  - **Merged on Alexandru's instruction, 2026-09-26, although France
    did not come back — the session had stopped short of merging.** Both proposal runs on the branch (2026-09-26, 11:01 and
    11:52 UTC) wrote Germany, Romania and Italy and left France
    `UNCHANGED`: the same batch of **19 French place names** timed out
    at Overpass both times (HTTP 504, then a read timeout, on both
    attempts of each run). The French place lookup runs before any code
    this branch changed and asks the same names as before, so it is not
    this branch's failure — but a review file left unchanged because a
    fetch failed is not a pass, so the merge was his call, and he made
    it. France's three rows are still run #10's. Twice
    in a row is not a flake; if it recurs on the monthly run, the next
    step is splitting France's place lookup into smaller requests, the
    way Romania's pitch lookup was split.
    **That next step was the wrong one, and France came back on
    2026-09-26 — but not cleanly, and the cause is not proven.** Run
    #13's log showed the failing step was one request of **19 names**,
    while Germany's single request of 17 names came back in two
    minutes, so a smaller batch would only have repeated it. The
    change made instead: the place lookup also stays inside
    `COUNTRY_BOX` from `fetch_clubs.py`, because France's national
    boundary includes the overseas departments and its bounding box
    spans half the globe. On the branch run (15:07 UTC) France was
    **`WRITTEN`** and all four countries were complete, the first time
    since run #10. **But France's lookup still timed out four times**
    (three on the first pass, one on the retry) and came back on the
    fifth attempt, 17 minutes in. So the box did not make the request
    fast; it may have made it possible, or Overpass may simply have
    been less busy. **One success after five attempts is not a fix
    confirmed.** France's rows were written and are unchanged in
    content from run #10. If the monthly run leaves France `UNCHANGED`
    again, one untried idea is to ask for the place lookup with the box
    alone and no country area. Nobody has measured whether the area is
    the slow half, and without it a same-named place just over a border
    could come back as a candidate, so it needs checking before it is
    built.
    **Run #16 (the push to `main` after PR #37, 15:18–16:00 UTC) made
    two more findings, and together they point away from France.**
    (1) **France came back complete a second time in a row** — `WRITTEN`
    on #15 and again on #16, the first two in a row since run #10. It
    was still not clean: the 19-name place request timed out twice
    (15:38 and 15:42) and came back on the retry pass, 14 minutes in.
    (2) **Germany's place lookup failed in the same run.** 17 names,
    inside Germany's box (47.15–55.15 N, 5.75–15.15 E), a compact
    request with no overseas departments in it: one HTTP 504, then a
    read timeout, then "17 name(s) did not come back". It came back on
    the retry pass and Germany was `WRITTEN`, so it failed the first
    pass and not the run. In run #13 the same German request had come
    back in two minutes. **It was not only those two**: Romania's
    whole-country stadium request got three 504s and Romania was left
    `UNCHANGED` (95 rows kept from the last good run). Italy hit two
    504s on its place lookup and three on its pitch lookup before
    finishing. Every country's Overpass steps struggled in that run.
    **What this changes.** The earlier idea was that France's request
    shape was the cause: its national area, its overseas bounding box,
    its 19 names. A German request of about the same size and a much
    smaller area failing the same way, in the same run, **weakens that
    idea a lot**. The better-supported explanation is general Overpass
    server load in a long, heavy run, which hits whichever country is
    asking at the time. That is better supported, not proven: it rests
    on one run's log. **So the next look at this tool should be at its
    retry and backoff behaviour as a whole, not another per-country
    fix aimed at whichever country failed last.** Three things in
    `propose_coordinates.py` are worth that look, none of them changed
    here: the waits are fixed (60 s after a busy answer, 30 s after a
    timeout, `MAX_RETRIES` 3, a single retry pass) with no growing
    backoff and no jitter; the client gives up after
    `TIMEOUT_SECONDS` 180 s while the queries ask Overpass for
    `[timeout:240]`, so an answer Overpass would deliver between 180
    and 240 s is thrown away; and there is only one Overpass instance,
    `overpass-api.de`. Whether any of these is the real limit has not
    been measured. **The "box alone, no country area" idea above is
    now less promising**, because it was aimed at France's shape.
  - **New open questions this turned up, all Alexandru's:**
    **FC Bistrița `Q24895825` is on the map at tier 3 and dissolved in
    2017** (English Wikipedia; `roster-review.csv` already reads it
    `extra-not-in-roster`). Shape 4: the next `skip`, once two division
    articles and the infobox are read to the Hermannstadt standard.
    It now shares its marker with Gloria Bistrița, the club really
    playing there. **Q74127553** is a `skip` candidate (shape 1).
    **CS Afumați** is drawn at its Comunal ground, but the Liga II
    table says it plays 2026-27 at the CNAF in Buftea while the Comunal
    is renovated. That is not changed here.
  - **Second pass, same day, a separate session on Alexandru's
    instruction — and what was already done before it.** Checked
    first, from the files: FC Bistrița was **still in `RO.json` at
    tier 3** with no hand row, and Q74127553 had its whole-club
    `rejected` row in `coordinate-reviews.csv` (line 27) but **no
    `skip` row** in `clubs-manual.csv`. So neither had been done as
    asked. Everything below was read on a runner through a throwaway
    probe, removed in the same branch.
    - **`skip` rows added for both.** FC Bistrița: its English
      infobox says *dissolved 2017*; no `P576`; neither 2026-27 Liga II
      nor Liga III names it. The Liga III article is not a complete
      division list, so this is **weaker than the Hermannstadt
      standard** and rests on the infobox date, on Alexandru's
      instruction — the row says so. Gloria Bistrița is now alone on
      the Jean Pădureanu pin. Q74127553: 0 sitelinks, no `P159`, and
      the Liga III article links `Q55864953` — shape 1.
    - **Placed: ARO Muscelul Câmpulung** (Stadionul Muscelul; the OSM
      way carries the club's own Q-id, and infoboxes, Wikidata's `P115`
      and the Liga III map pin agree), **KSE Târgu Secuiesc** (Dr.
      Sinkovits; infoboxes and map pin agree) and **Oltul Curtișoara**
      (Stadionul Tineretului; the stadium article's coordinate and an
      OSM pitch agree within 10 m). All three are in the 2026-27 Liga
      III article with no `P576` and no withdrawal. Capacities blank:
      each figure came from English and Romanian Wikipedia only.
    - **Not placed, though asked for: Gilortul Târgu Cărbunești** —
      *"Relegated to Liga IV"* in the 2026-27 Liga III article, so the
      pitch would have drawn a Liga IV club at tier 3. **Șoimii Gura
      Humorului** — *"had withdrawn and were formally excluded by the
      FRF"*, and the article links a different item, `Q140089397`,
      whose ground is the Areni in Suceava. Both are whole-club
      rejections; Șoimii is the third instance of shape 6. **Lotus
      Băile Felix**'s mini-pitch is rejected as a ground; the club
      itself is fine.
    - **Held → rejected, both.** Olimpic Zărnești's held pitch is in
      Buzău county; the Liga III article (Series II) pins the club in
      the **Brașov** Zărnești. So the earlier "held with roster
      support" was half right: the club **is** in the 2026-27 article —
      linked as a red link, which is why `roster-review.csv` never
      resolved it and the list above missed it — and the ground is
      wrong. Its real ground is **not known**: OSM has several unnamed
      pitches in the Brașov town and nothing ties the club to one.
      Oltul Curtișoara's Moșteni pitch is rejected and the club placed
      at its real ground, above. **A Wikipedia map pin can be wrong**:
      the Liga III article pins Oltul on the Curtișoara in Dolj, 30 km
      from the Olt one where it plays.

- **`coordinate-review.csv` is current again, 2026-09-26: all four
  countries, 115 rows, from run #10.** It had been the 2026-09-18
  German and Romanian file through four runs. #6 and #7 (after PR #31
  fixed the crash on `build_clubs`' fifth return value), #8 and #9 all
  went green and left the file alone, because Overpass did not answer
  everything and the guard then discarded the whole run. What each run
  missed was different except for one step: **Romania's pitch lookup
  failed in every run that reached it** (#6, #7, #9), while Germany,
  France and Italy sent one small pitch request each and got answers.
  **Two changes, both in `propose_coordinates.py`:**
  - `PLACES_PER_REQUEST` went from 50 to **10**, and a pitch batch that
    does not come back is asked once more, the way the place lookup
    already worked. In run #10 Romania's 53 places went as 6 requests
    and **all 6 came back** — but batch 2 needed its third and last
    attempt after two 504s. That is one run under visible load, not
    proof the step can no longer fail. If it fails again, the next
    change is a smaller batch or a longer wait. More retries would be
    the wrong fix.
  - The file is now **decided country by country** (see Conventions).
    Run #10 did not exercise that path, because every country came
    back. It was checked offline with Overpass mocked: a failing
    Romanian pitch step left Romania's 107 old rows byte-identical and
    wrote Germany, France and Italy; every country failing left the
    whole file byte-identical.
  **What the file now says:** Germany 3 (0 confident / 2 ambiguous /
  1 nothing), Romania 106 (**38** / 31 / 37, against 31 / 32 / 44 in
  the 2026-09-18 file), France 3 (0 / 2 / 1), Italy 3 (0 / 1 / 2).
  Nothing was applied to any club file. Every confident row still
  needs a person to read it before it goes into `clubs-manual.csv`.
  Some rows describe clubs already dealt with elsewhere. Torgelower FC
  Greif and Teutonia Watzenborn-Steinberg are the merged-away shape 4
  and are Alexandru's call. TSV 1860 München II's ground was cleared
  on purpose. Carrarese is the Italian club still missing from Serie B.
  So the file is a list to judge, not a to-do list.

- **A mapped league can be hidden under a preferred statement naming a
  DIFFERENT league. That is a third rank shape, the diagnostic could
  not see it until 2026-09-25, and it is much the biggest of the
  three.** LR Vicenza `Q56542463` carries Serie B at **normal** rank
  twice, and **Serie C Group A at preferred rank** (2022–2026, with an
  end date). `wdt:P118` therefore yields Serie C, which is not mapped,
  and the club never reaches the map — though its infobox reads
  *2025–26 Serie C Group A, 1st (promoted)* and the 2026–27 Serie B
  article lists it. It is not a `<novalue>`, so the novalue fallback
  does not touch it, correctly; and query B asked only about clubs
  with **no** truthy `P118` at all, so the diagnostic was blind to it
  by construction.
  **Query C now measures it, and the number is 63** — across all four
  countries, 89 statements, answered in 2.5 s. Nearly all are exactly
  the Vicenza pattern: a club promoted or relegated, the new league
  added at normal rank, the old one left preferred. Italy (Perugia,
  Reggiana, Reggina, Cittadella, Cosenza, Pescara, Bari, Spezia,
  Ternana, Salernitana, Pordenone, SPAL and Vicenza), **France** (Ajaccio,
  Amiens, Bordeaux, Caen, Bastia, Nîmes, Valenciennes, Gazélec
  Ajaccio), **Germany** (KFC Uerdingen 05, no position) and some forty
  Romanian clubs, most at Liga III.
  **What it costs, measured against the rosters and not guessed: three
  clubs, one of them in scope.** Of the 63, only three are named by a
  2026–27 season article this project reads: **LR Vicenza** (Serie B),
  and **FC Inter Sibiu** and **FCSB II** (Liga III — untouched
  territory, and FCSB II has no position anyway). The eight French
  clubs are absent from both complete Ligue articles, so France's
  "exact" still holds for current clubs — **but "France measured a
  clean absence at tiers 1–2" was a statement about queries A and B,
  and the shape was there all along.** A clean result from a query is
  a clean result for the question it asked.
  **Alexandru chose the first option later on 2026-09-25**: the
  fallback now reads through this shape under the same three
  conditions (see the Conventions entry on the novalue fallback), and
  Vicenza is on the map at **tier 2**, which its normal-rank Serie B
  tags give and the Serie B roster agrees with. His instruction called
  it "the same resolution as shape 5"; it is the same *outcome* — the
  live league wins — by a different mechanism, since Augsburg needed
  nothing read through. Of the 63, the roster confirms exactly
  **three**: Vicenza, **FCSB II** (surfaced, but it has no position,
  so still off the map) and **FC Inter Sibiu** `Q533005` — below.
  **FC Inter Sibiu is left off, and its tier is Alexandru's call.**
  The first build with the new shape drew it at **tier 2**, because its
  normal-rank tags include Liga II — while the 2026–27 Liga III article
  lists it and the Liga II one does not. Drawing a club at a tier its
  own division contradicts is a wrong fact on the map, and writing
  tier 3 off one table is the Farul decision, which was his. So the
  fallback gained one rule the same day: **a surfaced club whose
  ordinary-rule tier the roster contradicts stays off the map until a
  hand row in `clubs-manual.csv` gives it a tier.** Farul has that row,
  so nothing changed for it. For Inter Sibiu, one row — `Q533005`, tier
  3 or whatever he decides — puts it on the map; the run summary names
  it every run until then. Note also that the Liga III union is not a
  clean division list (see the Liga III entry below), so tier 3 rests
  on a weaker table than Farul's tier 1 did.

- **Romania's Liga II moved between 2026-09-20 and 2026-09-25, and it
  was Wikidata, not this project.** The figures above say seven
  `unplaced-no-coordinates` and no wrong tier; the roster check now
  says **six and one `wrong-tier`**. It is one club changing verdict:
  **CSM Olimpia Satu Mare `Q99446805`**. Between the two runs Wikidata
  gained a ground for it, the Stadionul Daniel Prodan, so the
  coordinates gate let it through and the 2026-09-25 rebuild put it on
  the map — **at tier 3**, because its truthy `P118` is Liga III only,
  while the Liga II article lists it. (Its Liga II tag is not truthy;
  query C does not list it, so the Liga III statement is not the
  preferred-over-normal shape either — the rank detail was not read.)
  **Nothing was corrected**, because both remedies are judgements: a
  tier 2 would be written off one table, which Farul's row shows is
  Alexandru's to write; and it now **shares a pin** with `Q629277`
  "Olimpia MCMXXI Satu Mare", another tier-3 item on the same ground
  that the Liga III article does not list either. Two items, one name,
  one ground: shape 1, 2 or 4, and the shapes list says to find out
  which before touching either. Worth a look; not urgent — the map is
  no less right than it was, it shows one more club.

- **France's top two tiers are on the map, 2026-09-25, and came back
  exact: Ligue 1 18 of 18, Ligue 2 18 of 18, nothing missing, nothing
  extra, nothing at the wrong tier.** Same pipeline and same standard
  as Germany and Romania, all of it run on a GitHub runner because the
  sandbox still answers 403 to CONNECT for Wikidata, Wikipedia and
  StadiumDB. France is tiers 1 and 2 only; Ligue 3 and below were
  deliberately not touched.
  - **The league Q-ids were read, not remembered**: `Q13394` Ligue 1
    and **`Q217374`** Ligue 2, both `P17` France. The Ligue 2 id first
    written from memory was wrong, which is why a probe went first.
    StadiumDB's slug is `fra` (`france`, `fr` and `fre` are 404s).
    Both season articles are one stadiums-and-locations table of 18
    clubs; Ligue 2 needed the redirect hop for one title.
  - **What the first build brought, 40 clubs against 36:**
    | | tier 1 | tier 2 |
    |---|---|---|
    | first build | 19 | 21 |
    | after this pass | **18** | **18** |
  - **The nineteenth tier-1 item was not a club.** *saison 2016-2017
    du Stade rennais FC* (`Q24937450`) carries `P118` Ligue 1 and
    borrowed Roazhon Park's coordinates, so it sat on Rennes' own pin.
    It is the squad-list class, not one of the five duplicate shapes,
    and the not-a-club net in `fetch_clubs.py` now names **seasons**
    as well as lists, by type word and by a title anchored to "season"
    plus a year. Checked against all three country files: it drops
    that one item and nothing else.
  - **Three tier-2 clubs carried a stale Ligue 2 tag and are
    `skip`ped**: US Orléans (`Q369349`, now Ligue 3), AS Béziers
    (`Q2619514`, Régional 1 Occitanie) and FC Martigues (`Q1132418`,
    administratively relegated in 2024-25, now Départemental 3). Each
    has exactly one `P118`, Ligue 2, normal rank, no dates. The
    standard is the one Hermannstadt and Politehnica Iași were held
    to: **both** division articles complete (18 of 18 resolved each),
    **neither** lists them, and **each club's own infobox** states the
    reason. No tier is written for any of them — France is tracked at
    tiers 1-2 only and a tier is not written off one Wikipedia table —
    and each row says how to bring the club back.
  - **The rank pattern was looked for, and it does not recur in
    France.** `diagnose_p118_rank.py` now counts France: no French item
    is in the worldwide census of preferred-rank no-league statements,
    no club in Ligue 1 or Ligue 2 is hidden by a deprecated or
    suppressed `P118`, and the novalue fallback found no French
    candidate, so no roster was fetched on its account. That is a
    measurement for tiers 1-2 on 2026-09-25, not a promise about
    Ligue 3. **It was also a measurement of queries A and B only**:
    query C, added the same day in the Italy pass, found eight French
    clubs hidden by a stale *preferred* league tag. None of the eight is
    in either 2026–27 Ligue article, so France's 18 and 18 still stand.
  - **No duplicate shape appeared.** No ground carries two French
    clubs, no two pins are within a kilometre, and the roster check
    reports no club twice, so there is no shape-5 club/men's-team
    pair either. Three items with Ligue 1 or 2 tags die at the
    coordinates gate and none is current: Sporting Club fivois, the
    wartime *équipe fédérale Reims-Champagne*, and SC Bastia B.
  - **AS Monaco is flagged by the country check on every run, and
    that is correct and left alone.** Its `P17` is Monaco and its
    ground is in Monaco; it is in `FR.json` because it plays in
    Ligue 1. A note-only row in `clubs-manual.csv` says so, the Bihor
    way. The file is France's league pyramid, not France's territory.
  - **Capacities: eight corrected, three contested, one blank.** The
    league's stadiums table is now the fourth figure beside Wikidata,
    OpenStreetMap and StadiumDB, and the UTA Arad rule was applied
    exactly. **Corrected**, each with every figure in its note: Angers
    19,800, Clermont 11,980, Troyes 21,877, Metz 28,786, Red Star
    10,000, Laval 18,607 (Wikidata said 11,107), Dunkerque 4,933, and
    Pau 4,031 where Wikidata had nothing. **Contested, nothing
    changed**, because no two sources agree: AS Monaco (18,523 against
    the table's 16,360, and neither OpenStreetMap nor StadiumDB looks
    in Monaco), RC Strasbourg (26,109 / 29,000 / 32,000 — the Meinau is
    being rebuilt) and US Boulogne (6,600 / 15,034 / 9,534).
    **Rodez** has only the table's 5,955 and stays blank: one source
    is not two — and OpenStreetMap's nearest stadium to Rodez's pin is
    8.8 km away, so either the Stade Paul-Lignon is untagged there or
    the pin is off; nobody has looked. Auxerre, Lorient, Nantes and Reims show up in the
    review files but the map's figure agrees with the table, so the
    outlier is the other source. StadiumDB could not choose between two
    Lille grounds and says so.
  - **Fixtures: 17 of 18 Ligue 1 clubs link to football-data.org's
    FL1**, which was already being fetched. **Le Mans is the
    eighteenth**: football-data calls it "Le Mans FC", Wikidata "Le
    Mans Football Club", and an abbreviation is not an equality. One
    `link` row in `fixture-links-manual.csv` (football-data team 535)
    settles it, and that file's entries are Alexandru's call. **He
    made it on 2026-09-25 and the row is in**: Ligue 1 is now 18 of 18
    linked. Ligue 2 has no fixture source; the club sheet says so.
  - **Found on the way, and on `main` before this pass:** since
    `fixture-links.json` landed in `data/clubs/` on 2026-09-25,
    `check_tickets.py`, `check_rosters.py`, `crosscheck_capacity.py`
    and `crosscheck_stadiumdb.py` all crashed on it, because each read
    every `.json` in that folder as a country file. They now read only
    two-letter country files (`check_tickets.py` skips anything whose
    `clubs` is not a list). The scheduled runs of all four would have
    gone red on their next run.

- **Where `football-rules.json`'s Inter and Italy figures come from,
  read 2026-10-03 and not changed.** The Italy-related content is the
  `inter` and `milan` club entries, the `derby-madonnina` bucket item
  (two confirmed fixture dates, 1 Nov 2026 at Milan and 14 Feb 2027 at
  Inter, each with a `saleRoute`), and two ticket events, `milan-derby-
  sale-nov` (inferred, 2026-10-01, "approx one month before the 1 Nov
  fixture") and `inter-derby-phase1` (disputed: its own warning says the
  source gave 13/21/24 August with no year, matching 2026 and 2015). **The
  file names no source for any single Inter figure** - not the four
  phases, not "up to 4 tickets", not "EUR 70-75" or "up to EUR 230".
  What it does say is in `provenance`: facts from "the conversation" were
  "established by checking club/UEFA/league sources directly", and
  anything from "the bucket-list and derby documents" is "INSPIRATION,
  NOT FACT" and enters as `verified:false`. Both Italian entries carry
  `ageRules.verified: false`; neither says which of the two routes its
  procedure came by. Since 2026-10-03 the Inter sheet shows these notes
  beside the researched rows, unreconciled, so the disagreements below
  are visible in the app.
- **The derby PDF contradicts `football-rules.json` on Inter, and
  nothing has been changed on either side.** Found 2026-09-23 while
  incorporating the PDF. `football-rules.json` is hand-written and no
  tool writes to it, so the contradictions are listed here for
  Alexandru to settle:
  - **Phase 1.** `football-rules.json` says Inter's home-derby phase 1
    is *"OPEN TO EVERYONE WORLDWIDE, primo anello rosso/arancio only.
    The route from abroad"*, and the `derby-madonnina` fixture's
    `saleRoute` repeats it. The PDF's 2025-26 sequence, from the club's
    own announcement (I2), has **four season-ticket-holder phases
    first** and no open-to-everyone phase until open sale on the eighth.
  - **The Siamo Noi phase.** `football-rules.json`: *"In 2025 the
    allocation sold out after phase 2, so the SiamoNoi phase never
    opened"*, *"up to 4 tickets"*, and *"the free card"*. The PDF: the
    Siamo Noi phase ran 24–26 Oct 2025 with **2** tickets per holder,
    the card costs **EUR 15** (I-4), and in 2024-25 the Siamo Noi
    allocation ran out five days before that phase was due to close,
    so it did open.
  - **Name changes.** `ageRules.note` says no name changes for the
    derby; I-16 says season-ticket holders could not transfer but
    single PLUS tickets could change user once from 48 h before kickoff
    (2025-26).
  - **Prices.** `procedure.pricing` gives *"primo rosso centrale up to
    EUR 230"*; the PDF's 2025-26 figures are Secondo Arancio Centrale
    230, Primo Rosso Laterale 240 and Poltroncina Rossa 420–440, all
    unverified and third-party.
  - **The Frankenderby window.** `frankenderby.nextFixture` estimates
    30 Jan–1 Feb 2027; the PDF's fixture table says 29–31 Jan 2027,
    citing the DFL schedule (N1). Small, but they are not the same.
  **The PDF also disagrees with itself once**, and both halves are kept:
  I-20 says the 2025-26 Inter derby sold out before open sale, while its
  own price table heads the 2025-26 column *"free sale, sectors still
  available"*.
  **The two Q-ids that rested on memory are verified, 2026-09-24.**
  Inter `Q631` and AC Milan `Q1543` were written on 2026-09-23 without
  being read from Wikidata. A throwaway probe dispatched through
  `build-clubs.yml` read them on a runner: enwiki *Inter Milan*
  resolves to `Q631` and *AC Milan* to `Q1543`, both typed association
  football club (AC Milan also carries men's football team), `P17`
  Italy, `P115` `Q133566` San Siro. Every Inter row's note now says
  verified and how. The probe and its temporary job were removed in
  the same branch.

- **Both new checks are built and have run for real, 2026-09-20. These
  are the numbers they left behind.** `crosscheck_stadiumdb.py` and
  `check_rosters.py` are described under Files and Code; what follows is
  what the first pass over Germany and Romania actually did.

  | | tier 1 | tier 2 | tier 3 | tier 4 | 6 | 7 | 8 | on the map |
  |---|---|---|---|---|---|---|---|---|
  | **Germany** before | 18 | 18 | **22** | 83 | 3 | 1 | 1 | 146 |
  | **Germany** after | 18 | 18 | **20** | 88 | 3 | 1 | 1 | **149** |
  | **Romania** before | 16 | 16 | 32 | — | — | — | — | 64 |
  | **Romania** after the tier 1/2 pass | 16 | **15** | 32 | — | — | — | — | **63** |

  **Against the leagues' own membership, after the corrections.** The
  Romanian rows are the second pass of 2026-09-20 — the tier 1 and
  tier 2 one — and the figures the first pass left are kept beside them
  because the difference is the point:

  | division | roster | on the map | ok | extra | missing | wrong tier | unplaced |
  |---|---|---|---|---|---|---|---|
  | Bundesliga | 18 | 18 | 17 | 1 | 1 | — | — |
  | 2. Bundesliga | 18 | 18 | **18** | — | — | — | — |
  | 3. Liga | 20 | 20 | **20** | — | — | — | — |
  | Regionalliga | 87 | 88 | 55 | 33 | 29 | 3 | — |
  | Liga I *(first pass)* | 16 | 16 | 15 | 1 | — | 1 | — |
  | **Liga I** | 16 | 16 | **16** | — | — | — | — |
  | Liga II *(first pass)* | 22 | 16 | 14 | 2 | 1 | — | 7 |
  | **Liga II** | 22 | **15** | 14 | 1 | 1 | — | 7 |
  | Liga III *(unchanged)* | 69 | 32 | 18 | 14 | 13 | 4 | 34 |

  **The 3. Liga is the headline.** It began this pass at 22 clubs
  against a real 20 — the gap that motivated the whole design — and it
  is now **20 of 20, nothing missing and nothing extra**. Six clubs were
  sitting at tier 3 on a stale `P118`, two belonged there and were at
  tier 4, and two were invisible to the club query altogether. The
  2. Bundesliga is likewise exact.
  **Romania's counts did not move in the first pass, and that was the
  honest outcome at the time.** Liga II was 16 on the map against 22,
  Liga III 32 against 69, and the reason is coordinates rather than
  tags: 41 of those clubs are `unplaced-no-coordinates`, which is the
  route `coordinate-review.csv` and europlan-online already exist for.
  Nothing was trimmed to make a count look better.
  **The second pass of the same day moved the tier 1 and tier 2 rows,
  and the direction is worth reading carefully.** `Liga I` is now
  **16 of 16, nothing extra, nothing missing, nothing at the wrong
  tier** — the first Romanian division to come back exact. It took
  three changes, not one: Farul surfaced by the novalue fallback,
  Farul's tier hand-corrected to 1, and Hermannstadt removed because
  the club no longer exists.
  **`Liga II` went DOWN, from 16 on the map to 15, and that is an
  improvement.** Politehnica Iași left because the division says it is
  not in it. The `ok` count is unchanged at 14 and the seven
  `unplaced-no-coordinates` are untouched, so nothing was gained or
  lost in the part of the gap that is real; what changed is that the
  map stopped claiming a club plays in a division it is out of. **A
  count going down can be the map getting more accurate**, which is
  the same lesson the 3. Liga's 22-against-20 taught from the other
  direction.
  **Liga III and everything below were deliberately not touched.**
  **What the capacity pass changed:** eleven figures, every one of them
  a case where two independent sources agreed against what the map held,
  plus one copied ground. The StadiumDB review went from **27 rows to
  19**. The template for recording a contested figure is in Conventions
  above and UTA Arad is the worked example.

- **What stayed contested after all three sources, and why.** Nineteen
  rows survive in `stadiumdb-review.csv`, and they are not all the same
  kind of thing.
  - **Three where the map is corroborated and StadiumDB is the
    outlier**, because StadiumDB matched a ground the club does not play
    at: **1. FC Magdeburg** (30,098 on the map and on Wikipedia against
    StadiumDB's 25,910), **FC Viktoria Köln** (8,343 twice against
    10,000) and **FC ASA Târgu Mureș** (8,200 twice against 3,500 — and
    StadiumDB's is the Stadionul Municipal while ours is the Stadionul
    Trans-Sil). The tool's own `?ground-unchecked` marker flagged the
    last of these before anyone looked. **A third opinion is a third
    opinion, not a tie-breaker.**
  - **Three where no two sources agree and nothing was changed**:
    **FC Botoșani** 12,000 / 8,500 / 7,782, **SC Fortuna Köln** 13,750 /
    14,944 / 11,748, and **VfB Oldenburg** 32,000 against 15,200, which
    only became visible because `Q2188121` put the club on the map that
    same day.
  - **Seven with one source each way and no third**, all tier 4 or
    below where Wikipedia has no stadiums table: BSG Chemie Leipzig,
    FC 08 Homburg, FC Carl Zeiss Jena, TuS Koblenz, VfB Lübeck, VfR
    Aalen, FC Hermannstadt. Two figures, no arbiter.
  - **One with a single source at all**: Avântul Reghin, where only
    StadiumDB has a figure (3,000) and neither Wikidata nor
    OpenStreetMap has one.
  - **Four that are not disagreements**: FSV Zwickau, SpVgg
    Unterhaching, Jiul Petroșani, Sepsi OSK and UTA Arad, where the
    figures agree and only the ground NAMES differ — a sponsor's name
    against the old one. They stay in the file because a name clash is
    worth one look, not because a number is in doubt.

- **A Wikidata statement's RANK can hide a league from the club query
  entirely, and until 2026-09-20 nothing here could see it.** This is
  the most important thing the roster check found on its first real
  run, and it is a new shape of invisibility rather than a new instance
  of a known one.
  `CLUB_QUERY` joins on `wdt:P118`. The `wdt:` prefix yields only
  **truthy** statements: the preferred-rank ones if the item has any,
  otherwise the normal-rank ones, and **never a deprecated one**. So a
  club can carry exactly the right league and still never reach the map.
  Two cases, both read from Wikidata on a runner:
  - **FC Augsburg `Q15755`** has `P118` = `Q82595` Bundesliga at
    **deprecated** rank. One statement, the right league, invisible.
  - **SSC Farul Constanța `Q368104`** has `P118` = `Q1707697` Liga III
    and `Q386384` Liga II, both at **normal** rank, and a third
    statement with **no value at all** at **preferred** rank. The
    preferred one suppresses both of the others, so `wdt:P118` yields
    nothing and the club is invisible even though two mapped leagues sit
    on the item.
  **Neither leaves a trace anywhere else in the pipeline.** They are not
  in `data/clubs/`, so no review file mentions them; the club query
  simply never returns them. That is precisely the blind spot the roster
  check exists for, and it is the first thing it found.
  **HALF OF THIS IS NOW FIXED, and the half that is not is the half
  that should not be.** Written when nothing had been changed for
  either club; the novalue fallback was built later the same day and
  the Conventions entry above is its rule. What changed:
  - **Farul is on the map**, surfaced by the fallback, because a
    preferred `<novalue>` suppressing two true tags on a club the
    2026-27 Liga I article names is a mistake on Wikidata's side. Its
    tier is hand-written, not read through — see its own entry below.
  - **Augsburg is untouched and must stay untouched.** Its shape is
    **deprecated**, not `<novalue>`, and the fallback is narrow to
    `<novalue>`/`<somevalue>` precisely so that it cannot reach a
    deprecated statement. Augsburg is on the map already under
    `Q97905916`, and the remedy there would make it worse rather than
    better; see the entry on the club-and-team shape below.
  **The general fix is still not attempted, and the narrow one is not
  a step towards it.** Dropping `wdt:` for `p:`/`ps:` would see every
  statement including the deprecated and historical ones, which is how
  a club gets put in a league it left in 1994 — the exact problem
  `league-tiers.csv` and the truthy join exist to avoid. What the
  fallback does instead is read through **one** shape of suppression,
  **only** where a division's own membership list says the club is
  playing, and **only** to decide whether the club is drawn at all.
  Deciding what a deprecated league tag means is still Alexandru's,
  and is still not a query change to slip in.

- **The rank blind spot has been measured, 2026-09-20. It is 20 clubs,
  and it costs this project exactly two of them.** The entry above was
  written from two clubs found by accident. `tools/diagnose_p118_rank.py`
  now asks the question deliberately, and the first two real runs are
  what follows. It was run from a GitHub runner, because the sandbox
  still answers 403 to CONNECT for `wikidata.org`.
  **Two queries, because one question is a census and the other is a
  bill.**
  - **Query A, the census**: every item **anywhere** carrying a
    preferred-rank `P118` that asserts no league. It is deliberately
    **not** bounded by country — `P17` is exactly the field the missing
    clubs already lack, so a country filter would drop the clubs the
    query exists to find. **43 items worldwide**, in 168.2s with one
    timeout and retry.
  - **Query B, the bill**: clubs carrying one of the twelve leagues
    `league-tiers.csv` maps, on a statement `wdt:P118` will not yield —
    for any reason, a deprecated rank or a preferred `<novalue>` on top.
    Bounded by the mapped leagues, so it needs no `P17` at all: the
    league is the country signal. **18 clubs**, in 82.0s with one 504
    and a retry.

  **Twenty clubs in Germany and Romania are hidden from the club query
  by rank.** Eighteen by a preferred `<novalue>`, two because every
  statement on the item is deprecated.
  **Every one of the eighteen is Romanian. Not one is German.** The
  German half of this blind spot is the deprecated shape and FC
  Augsburg is still its only instance. The remaining 25 of the
  worldwide 43 are somebody else's problem — mostly American college
  athletics programmes, a few Polish and Dutch clubs.
  **Seventeen of the twenty leave no trace anywhere in the pipeline.**
  Only three appear in `roster-review.csv` at all — Augsburg, Fotbal
  Comuna Recea and Farul — and none of the twenty is in `data/clubs/`,
  because none has a truthy `P118`. That is the blind spot stated as a
  number rather than as a worry.

  **A preferred `<novalue>` is NOT automatically an error, and treating
  all eighteen as one would be the mistake this entry exists to
  prevent.** Wikidata's `<novalue>` means *this item has no value for
  this property*, and on a club that folded that is the **correct**
  statement: the club is in no league because there is no club, and the
  normal-rank league tags underneath it are history. Reading through
  those would put a dead club on the map at the tier it last played in,
  which is precisely what the truthy join exists to prevent. `P576` is
  what separates the two, and the tool reads it.
  **Twelve of the twenty carry `P576`**, with dissolution years from
  1946 to 2026: ACS Poli Timișoara 2021, CA Câmpulung Moldovenesc 1953,
  CS Mioveni 2025, Chinezul Timișoara 1946, FC Brașov Steagul Renaște
  2023, FC Gloria Buzău 2025, FC Politehnica Iași 2026, FC Politehnica
  Timișoara 2012, Fotbal Comuna Recea 2021, Gloria Bistrița 2015,
  Turris-Oltul Turnu Măgurele 2021, Viitorul-Pandurii Târgu Jiu 2024.
  On every one of them the `<novalue>` is right, and `CLUB_QUERY`
  excludes dissolved clubs anyway, so nothing is owed.
  **Two more have no position**: AFC Câmpulung Muscel `Q113816215`
  (the second deprecated-only case) and FC Carmen București
  `Q62562381`, which also hides nothing this project maps. Reading
  their rank would not place them.

  **Six are left**, and they are the only ones where reading the rank
  would put a club on a map: FC Augsburg `Q15755` (hides tier 1 DE),
  CS Balotești `Q12723213` (tier 2 RO), CS Gaz Metan Mediaș `Q856790`
  (tier 1 RO), CSM Focșani `Q4683096` (tier 2 RO), FC Astra Giurgiu
  `Q750322` (tier 1 RO) and SSC Farul Constanța `Q368104` (tier 2 RO).
  **A missing `P576` is not evidence that a club is playing**, and this
  is where that matters. It means only that nobody has recorded a
  dissolution. The thing that says whether a club is in a division
  **now** is the roster check, and of these six exactly **two** are
  named by any 2026-27 season article this project reads: **FC
  Augsburg**, in the Bundesliga article, and **SSC Farul Constanța**,
  in the Liga I one. The other four are listed by no current-season
  article at all, so nothing here says they are in a division, and
  nothing should be written for them on the strength of an absent
  property.
  **So the rank blind spot costs this project two clubs today, and they
  are the two that were already known.** That is a good outcome rather
  than a dull one: the pair found by accident turns out to be the whole
  current bill, it is now known rather than hoped, and the other
  eighteen are written down so that the next run can tell a new one
  from these.
  **The bill is now ONE, and this list is what the fallback's third
  condition was written against.** Of the six, Farul is the only
  `<novalue>` case the roster confirms, and it is on the map from
  2026-09-20. Augsburg is the other confirmed one and is the
  **deprecated** shape, which the fallback deliberately does not
  reach. **Balotești, Gaz Metan Mediaș, Focșani and Astra Giurgiu are
  exactly the clubs condition 3 exists to leave out** — they carry no
  `P576`, their `<novalue>` may well be wrong, and no current-season
  article this project reads names any of them. The fallback finds all
  five Romanian candidates on every run, surfaces the one the roster
  confirms and **names the other four in the run summary as left
  out**, so they stay visible as an open question rather than becoming
  either a silent inclusion or a silent omission.

  **Farul's `<novalue>` is being treated as an error rather than as
  authority, and that decision is Alexandru's, taken on 2026-09-20.**
  `Q368104` carries Liga III and Liga II at normal rank, both of them
  true statements about a club that exists and is playing, and a
  preferred-rank statement asserting no league sitting on top of them
  and suppressing both. A statement that overrides two true ones with
  an assertion that the club is in no league, about a club the Liga I
  article lists this season, is a mistake on Wikidata's side. **The
  suppressed tags are what this project reads for Farul.**
  **What that does not settle is the tier, and it is worth being exact
  about why.** Read through the `<novalue>` and the two tags give
  **tier 2**, because the builder takes the most senior mapped league
  and Liga II is it. The 2026-27 Liga I article says **tier 1**. So the
  `<novalue>` is an error *and* the statements under it are stale, both
  at once — correcting the first does not correct the second, and
  reading the rank would put Farul on the map one division below where
  it plays. Neither number may be written: tier 2 is contradicted by
  the roster, and tier 1 rests on the English Wikipedia table alone.
  **Asked directly on 2026-09-20, Alexandru's first answer was to leave
  Farul off the map and settle the identity question first**, and the
  reason was the right one: the tier is the *second* question. The
  first is which club `Q368104` actually is — the old Farul, the 2021
  Viitorul merger that took the name, or both depending on who edited
  the item — and a tier written before that is a number attached to a
  club nobody has identified.
  **Later the same day he reversed that, and Farul is on the map at
  tier 1.** The reversal is his and is recorded here so the two
  decisions are not read as a contradiction: the earlier one was made
  when putting Farul on the map at all meant either writing a tier the
  roster contradicts or losing the Q-id, and the fallback removed both
  of those costs. **The identity question is NOT settled by this** and
  is unchanged — which club `Q368104` is remains open, and the row in
  `clubs-manual.csv` says so in its own note.
  **The mechanical obstacle that used to stand in the way is gone, and
  how it went is the point.** `apply_manual` in `fetch_clubs.py`
  **rejects** a row whose `clubQid` is not in the country's fetched
  clubs — verified at the time by running it against a Farul-shaped
  row, which came back *"Q368104 is not in this country's fetched
  clubs"*. That is the right guard for a typo and it was exactly wrong
  here, because not being in the fetched clubs was the whole problem.
  The only row that worked then was an **add** row with no `clubQid`,
  and it cost the Q-id: a synthetic `MANUAL-…` id, and
  `check_rosters.py` joins on Q-ids, so the roster's `Q368104` would
  have gone on reading as missing while the hand-added club read as
  `extra-not-in-roster` — **two permanent false findings in place of
  one true one**.
  **The fix was not to weaken the guard.** The novalue fallback puts
  `Q368104` into the fetched clubs, under its own Q-id, so an ordinary
  `clubQid` correction row now finds it and `apply_manual` is
  unchanged. That is the shape worth keeping: a club that could not be
  corrected by hand because it was not there is fixed by **making it
  be there**, not by letting a hand row invent a club the query never
  saw. Every other rank-hidden club is still refused by the same
  guard, and should be.

- **Two Romanian clubs are one club's identity question each. One is
  now drawn and still unidentified; the other is unchanged.** Both came
  out of the roster check on 2026-09-20 and both are shape 2 — two real
  items, not a duplicate — so `skip` is the wrong tool for either.
  - **Farul Constanța.** The 2026-27 Liga I article lists a club whose
    Wikidata item is `Q368104`, labelled "SSC Farul Constanța", English
    sitelink "FCV Farul Constanța", 29 sitelinks. It used to be **not on
    the map at all**, for the rank reason above: a `<novalue>` `P118` at
    preferred rank hides its Liga II and Liga III tags. Meanwhile the
    map's sixteenth Liga I club was **FC Hermannstadt `Q24884611`**,
    which the Liga I article does not list. So the top flight had the
    right *count* and one wrong *member*, which is exactly the failure a
    count cannot see and this check was built to catch.
    **Both halves of that swap are now done**: Farul is surfaced by the
    novalue fallback and hand-corrected to tier 1, and Hermannstadt has
    a `skip` row because the club was dissolved on 1 August 2026 — see
    its own entry below.
    **What is STILL not established** is which club `Q368104` is: the
    old Farul, the Viitorul merger that took the name in 2021, or both
    depending on who edited the item. Drawing it does not answer that,
    and the hand row says so out loud rather than letting a pin imply
    the question was settled.
  - **Bihor Oradea is two clubs with one name**, and the two sources
    disagree about which is in Liga II. `Q1386940` is "established in
    1958", 12 sitelinks, and carries Liga II at **preferred** rank — so
    Wikidata says it is the Liga II club, and it is the one on the map.
    `Q113541238` is "established in 2022", 2 sitelinks, **no `P118`, no
    ground, no coordinates and no inception date** (re-read 2026-09-20),
    and it is the one the Liga II article links.
    **Neither source is obviously wrong** and acting on either loses
    something: removing the 1958 club takes Bihor off the map entirely,
    because the 2022 one has no coordinates. Left as it is, and now
    **recorded on the club itself** — `clubs-manual.csv` carries a
    note-only row for `Q1386940` that changes no value and explains why
    nothing was changed, so the note travels into `RO.json` and is
    there the next time somebody sees the two findings and reads them
    as two errors.
    **It is one of the two tier-2 extras and it is NOT the same kind of
    thing as the other.** Both sources agree a club called Bihor Oradea
    is in Liga II; they disagree only about which item it is. That is
    the opposite of Politehnica Iași below, where the division itself
    says the club is not in it.
    **`_sameNameOnMap` does NOT fire for this pair, and that is a
    shortcoming of the annotation rather than of the finding.** The
    column exists exactly so that one club appearing twice does not
    read as two errors, and here it is blank on both rows: the roster
    calls the club **"FC Bihor Oradea"** and the map calls it
    **"Bihor Oradea"**, because the map takes Wikidata's *Romanian*
    label and the article links the English one. `same_name_on_map()`
    compares folded names for **exact equality**, so a missing "FC"
    is enough to miss it. It was left alone on purpose: loosening the
    comparison is how Eutin 08 scored against FC 08 Homburg on a shared
    "08", and renaming the club to make the annotation fire would be
    engineering a weak signal to produce an answer already known. **The
    note-only row is what carries the explanation instead**, and it
    travels into `RO.json` where the annotation would have been read.
    Worth fixing properly if a second pair turns up; not worth a fuzzy
    matcher for one.
    **The other blank is structural**: the `extra-not-in-roster` branch
    of `check_rosters.py` hardcodes `_sameNameOnMap` to empty and never
    looks, so even an exact name match would only ever annotate the
    `missing-from-wikidata` side of a pair, never both.

- **Two clubs were holding Romanian tier-1 and tier-2 slots they had
  left, and in both cases Wikidata had simply not been told. Found and
  removed 2026-09-20.** These are the two `skip` rows of that day's
  Romanian pass, and they are worth keeping together because they are
  the same failure arriving by two different routes: **a club stops
  playing, its `P118` does not change, and nothing in the pipeline can
  see the difference.**
  - **FC Hermannstadt `Q24884611` no longer exists, and the direction
    was not the one anybody expected.** It sat at **tier 1** because
    Wikidata gives it `Q237753` SuperLiga and `Q386384` Liga II at
    normal rank and the builder takes the most senior. The obvious
    reading was a relegation, tier 1 down to tier 2 — and that reading
    is **wrong**. All three tracked Romanian season articles were read
    on 2026-09-20 and **none** of them lists the club: not
    `2026–27 Liga I`, not `2026–27 Liga II`, not `2026–27 Liga III`.
    The club's own English Wikipedia infobox says
    *"2025–26 Liga I, 14th of 16 (relegated via play-offs)"* and then
    **"Dissolved 1 August 2026"**, and the Liga II article cites
    gsp.ro of 31 July 2026, *"Șoc! Hermannstadt s-a retras din noul
    sezon de Liga a 2-a"* — Hermannstadt **withdrew** from the new
    second-division season. So it was relegated and then ceased to
    exist. **No tier is right, and tier 2 would have been an
    invention.**
    **Wikidata carries no `P576` on the item**, which is exactly why
    nothing here could see it: `CLUB_QUERY`'s dissolution gate never
    fired, and a club with a live league tag and no dissolution date is
    indistinguishable from a club that is playing. Only the roster
    could tell them apart.
  - **Politehnica Iași `Q1024390` is out of Liga II on certification,
    not relegated.** It sat at **tier 2** on a **preferred**-rank
    `Q386384` Liga II tag — so this was not a stale normal-rank tag
    being outvoted, it was the item's own best statement. The 2026-27
    Liga II article does not list it. CLAUDE.md had left one innocent
    explanation open — that the article links the club under a title
    the sitelink hop could not resolve — and that is now **ruled out
    rather than doubted**: the article's 22 linked titles resolved
    **22 of 22** to Q-ids on 2026-09-20, a complete division with no
    slot unaccounted for. The Liga I and Liga III articles do not list
    it either.
    The reason is in the Liga II article itself, which says its
    participants *"were admitted through the FRF certification or
    Liga I licensing procedures"* and cites frf.ro of 14 July 2026 on
    certification for the 2026-27 Liga II together with sport.ro of
    17 July 2026, *"Poli Iași, out din Liga 2!"*.
    **Two items, and the useful one is the sibling.** `Q1024390`'s own
    English sitelink is *FC Politehnica Iași (2010)*; `Q926152` is
    *FC Politehnica Iași (1945)*, the same ground `Q2262973`, and it
    **does** carry `P576` 2026. So the dissolution evidence exists on
    Wikidata, on the wrong item of the pair.
  **The shape to carry forward: a club that has stopped playing looks
  exactly like a club that is playing, from inside this pipeline.**
  Every gate `CLUB_QUERY` has — not a person, not dissolved, league in
  `league-tiers.csv` — passes for both. The roster check is the only
  thing that can tell them apart, and it can only do it for the tiers
  that have a season article in `league-rosters.csv`. **Expect more of
  these, and expect them to be invisible until a roster is read.**
  **A single article saying a club is absent is still not evidence, and
  neither of these rests on one.** The rule CLAUDE.md already had is
  intact: what made these two actionable was a **complete** division
  list (16 of 16 and 22 of 22 resolved, so there is no unaccounted
  slot), **three** articles agreeing on the absence, and an independent
  statement of the reason — an infobox dissolution date for one, the
  league's own certification note and a cited report for the other.
  Absence from one table on its own would still not have been enough.

- **Three of the roster check's own bugs are worth keeping, because all
  three failed SILENTLY and two were the same mistake.** Found and fixed
  on 2026-09-20, on the first three runs.
  1. **`props=sitelinks` under `formatversion=2` returns sitelinks as a
     LIST**, `[{site, title}]`, not a dict keyed by site. The reader
     expected the dict. Every title resolved to nothing, and the check
     reported all 246 roster clubs as having no Wikidata item and all
     205 mapped clubs as absent from their own division — **with a green
     tick**.
  2. **`wbgetentities` accepts `normalize` only when exactly one title
     is given.** Sent with a batch of 40 it refuses the whole call and
     answers HTTP 200 with an `error` object and no entities. With no
     error check on that call, a refusal read as "Wikidata has never
     heard of any of these clubs".
  3. **A season article often links a club through a REDIRECT** — the
     Liga II page links "FC Chindia Târgoviște", which redirects to
     "Chindia Târgoviște". A redirect has no Wikidata item of its own,
     so 15 clubs read as having no item. They now go through Wikipedia's
     own redirect table and are tried again under what they point at;
     **all 15 resolved**, and the `no-wikidata-item` verdict went to
     zero.
  **The lesson is the shape, not the three APIs.** The rule this project
  already had — *a source that returns nothing is a failed fetch, not an
  empty answer* — was written for the article fetch and had not been
  applied to the two steps after it. It is now on all three: a batch
  that resolves zero titles, and a call that returns no usable entity
  for items Wikidata itself just named, are both failures, and a failure
  keeps the last good review file. That guard is what caught bug 2 -
  the run said which step had failed and left the file alone instead of
  overwriting it with 455 wrong rows.
  **And an API that answers 200 with an error object needs that object
  read.** Two of the three bugs looked identical from the outside -
  "zero results" - and only one of them was a shape problem. Printing
  the error turned the second into a one-line fix.

- **Germany's tier 4 is not a gap, it is churn, and the roster check
  measured it for the first time on 2026-09-20.** Against the 2026-27
  Regionalliga article's 87 clubs, the map had **49 of them right**, 34
  clubs at tier 4 that the division does not list, and 30 of the
  division's clubs missing. After that day's corrections it is **54
  right**. The two directions are the same problem seen from both ends:
  Wikidata's `P118` on German lower-league clubs is largely last
  decade's.
  **What the 30 missing ones actually carry was read rather than
  guessed**, and it settles how to fix them: their `P118` names an
  **Oberliga or a Landesliga**, not a Regionalliga. `Q878642` Oberliga
  Baden-Württemberg has four of them, `Q15735` Fußball-Bayernliga three,
  `Q316113` Oberliga Westfalen three, `Q316686` NOFV-Oberliga and
  `Q317868` Oberliga Niedersachsen two each, and so on down. Those are
  genuinely tier-5 leagues, so **adding them to `league-tiers.csv` would
  be wrong** — the clubs were promoted and their tags did not follow.
  The remedy is a per-club row in `clubs-manual.csv`, thirty of them,
  each needing a look. That is not done here.
  **Two of the unmapped league items are traps worth naming.**
  `Q1477024` "Fußball-Regionalliga Süd" is described by Wikidata as a
  ***women's* association football league** — mapping it would put this
  project in breach of rule 6, and it is TSV Schwaben Augsburg's only
  tag. `Q283009` DDR-Liga and `Q6954881` NOFV-Oberliga Süd are history,
  not a current division.
  **One of them was mapped, on purpose, and the cost was measured
  rather than assumed.** `Q2188121` is the **generic** "Regionalliga"
  item — Wikidata's own description is "fourth division of men's
  association football in Germany" — and **eight** clubs carry it and
  nothing else. It is now in `league-tiers.csv` at tier 4.
  Of the eight, three are right: **VfB Oldenburg** really is in the
  Regionalliga, and **SV Meppen** and **TSV Havelse** are in the 3. Liga
  and have hand rows saying so. That closes the 3. Liga completely — it
  now reads **20 of 20, nothing missing and nothing extra**.
  **The other five arrived at tier 4 with nothing to support it**, and
  they are `skip`ped: 1. FC Union Berlin II, BV Cloppenburg, FC
  Oberneuland, SV Wilhelmshaven and Viktoria Aschaffenburg. The 2026-27
  Regionalliga article lists none of them and the roster check found no
  second Wikidata item for any of them, so tier 4 would have been an
  invention — rule 2. They are off the map until somebody finds their
  real tier, which is exactly where TSV 1860 München II is and for the
  same kind of reason, and each row says how to bring the club back.
  **A generic item is a league HISTORY, not a current division.** It
  says a club has played at that level at some point and nothing about
  now, which is why five of eight were wrong. Expect to have to say this
  again for the next club that carries one, and expect the same split:
  the item is worth mapping for the clubs it places correctly, and every
  club it places has to be checked against a roster before it is
  believed.
  This closes the 3. Liga gap: CLAUDE.md has recorded since 2026-09-16
  that "SV Meppen and 1. FC Schweinfurt are missing from the German
  layer entirely ... there is no way to see which league Q-id they do
  carry". Meppen's is `Q2188121`; Schweinfurt's is `Q15735`, the
  Bayernliga.

- **Romania's hole is coordinates, not tags, and it is much the bigger
  one.** Of Liga III's 69 clubs the map has 18; **34 of the other 51 are
  `unplaced-no-coordinates`** — the club query can see them, and neither
  they nor their grounds have a position, so they are dropped at the
  coordinates gate. Liga II adds seven more. That is the route
  `coordinate-review.csv` and europlan-online already exist for, and it
  matches what was already written down: 107 Romanian clubs have a tier
  and no coordinates, against 64 on the map.
  **The Liga III article's union is not a clean division list**, and the
  check says so rather than pretending otherwise. The page has 20
  standings tables — series plus play-off and play-out groups — and the
  union comes to 69 clubs, fewer than Liga III actually fields, while
  also picking up four clubs that are plainly not in it: FC Voluntari
  and Sepsi OSK are in Liga I and come back `wrong-tier`, Știința Poli
  Timișoara is in Liga II. Their own division's article gets them right,
  so no harm is done - but a `wrong-tier` from the Liga III row alone is
  not evidence, and nothing should be changed on the strength of one.
  **Since 2026-09-26 those rows are no longer read at all.** The
  Austria pass taught the roster check to leave out a row whose team
  cell has no link of its own, and five Liga III rows had exactly that
  shape: FC Voluntari, Sepsi OSK, SC Oțelul Galați, Știința Poli
  Timișoara and FC Bacău, whose `wrong-tier` findings are gone. Checked
  against the previous `roster-review.csv`: those five verdicts and
  nothing else changed in Romania.

- **Liga II's shortfall, taken apart club by club on 2026-09-20: it is
  coordinates, and the figure of six hides how it is made.** The table
  above reads 22 in the division against 16 on the map, and six is what
  you get by subtracting. Six is not six clubs.
  **Eight of the division's 22 are absent from the map, and two clubs
  the division does not list are on it at tier 2. Those cancel to six.**
  That is the arithmetic this whole check was built to distrust — a
  count can come out nearly right while the membership is wrong, and
  here it comes out two clubs closer to the truth than it should.
  **Seven of the eight are coordinate-only, and nothing about their
  tags needs touching.** Every one of them carries `Q386384` Liga II on
  a statement `wdt:P118` yields, so the club query sees them and the
  tier they would land at is right; they die at the coordinates gate
  because neither the club nor its ground has a position:

  | club | Q-id |
  |---|---|
  | CSA Steaua București | `Q39487082` |
  | CSC 1599 Șelimbăr | `Q66424141` |
  | CSL Ștefăneștii de Jos | `Q18539440` |
  | CSM Olimpia Satu Mare | `Q99446805` |
  | FC Bacău | `Q106779019` |
  | Gloria Bistrița | `Q56677281` |
  | SC Popești-Leordeni | `Q55593565` |

  **The eighth is a tagging problem that fixing would not place.** FC
  Bihor Oradea `Q113541238` comes back `missing-from-wikidata` because
  it carries **no `P118` at all** — but it carries no ground and no
  position either, so giving it a league would move it from one kind of
  missing to the other and it would still not be drawn. It is also half
  of the Bihor identity question recorded below: the club on the map at
  tier 2 is `Q1386940`, the 1958 item, which carries Liga II at
  preferred rank, and it is one of the two extras.
  **So the answer to "how many of the six are a tagging problem the
  roster check should resolve" is none of them.** Seven are the
  coordinates gate and the eighth is blocked by the coordinates gate
  underneath an identity question that is Alexandru's to settle. The
  roster check has already done its job here: it named all eight and
  said which kind each one is.
  **The two extras are not one thing either, and they have now been
  taken apart.** Both were named and settled later on 2026-09-20 — see
  the entry on the two clubs holding slots they had left.
  `Q1386940` **Bihor Oradea** is the other half of the identity
  question and is **not** a spurious club — read the two Bihor items as
  one club and the genuine absence is seven, all coordinate-only,
  against one genuine extra. It keeps its pin and gains a note-only row
  saying why nothing was changed.
  The genuine one is **`Q1024390` Politehnica Iași**, and this entry
  used to say of it: *"Either its `P118` is stale or the article links
  it under a title the sitelink hop did not resolve. Nothing has been
  changed for it, because a single article saying a club is absent is
  not evidence that it is."* **The second half of that disjunction is
  now ruled out** — the Liga II article's 22 titles resolved 22 of 22,
  a complete division with no unaccounted slot — and the absence is
  corroborated by the Liga I and Liga III articles and by the league's
  own certification note. So the `P118` is stale, the club has a
  `skip` row, and the caution the entry was written with was right to
  hold until there was more than one source. There is now.
  **The remedy already exists and has already worked once at this
  tier.** CSC Dumbrăvița `Q55618976` is on the map at tier 2 only
  because a hand row in `clubs-manual.csv` carries coordinates Wikidata
  does not have — its `roster-review.csv` row still says
  `_hasCoordinates: no` and its verdict is `ok`. That is exactly the
  shape the other seven need: `coordinate-review.csv`, a second source,
  then a hand row. How much of Romania europlan-online covers has never
  been measured — the 20 clubs it settled were all German — so whether
  it is the second source for these seven is an open question rather
  than an assumption.
  **Liga III and below stay where they are**, in the coordinate-review
  queue at its current standard. The 34 Liga III clubs above are the
  same coordinates gate and a much bigger pile of it, and a decision
  taken here for 22 clubs in the second tier is not a decision about
  69 in the third.

- **Romania's top flight WAS roster-checked this pass, and it did not
  come back 16 of 16.** Asked directly on 2026-09-20 and answered from
  the file rather than from the counts: `roster-review.csv` holds **17
  rows** for `SuperLiga Romaniei`, every one of them against
  `2026–27 Liga I`, season `2026-27`. So the division was fetched,
  parsed and compared like the others — it was not skipped, and it was
  not merely left unflagged because nothing about it had changed.
  **What it came back with is 15 of 16.** Fifteen `ok`, one
  `wrong-tier` and one `extra-not-in-roster`. The roster's sixteenth
  club is **SSC Farul Constanța `Q368104`**, which is not on the map at
  all; the map's sixteenth tier-1 club is **FC Hermannstadt
  `Q24884611`**, which the Liga I article does not list.
  **The count is right and one member is wrong**, which is precisely
  the failure a count cannot see and precisely why this check exists.
  The table above already says so — `ok` 15, `extra` 1, `wrong tier` 1
  — and the **16** in its "on the map" column is the size of the tier,
  not a number of matches. Reading that 16 as agreement is the one
  misreading the table invites, and it is worth saying out loud once.
  **FIXED THE SAME DAY, and the fix needed three changes rather than
  the one the "one wrong member" framing suggests.** Liga I now reads
  **16 of 16, sixteen `ok` and nothing else** — no extra, nothing
  missing, nothing at the wrong tier. It took: the **novalue
  fallback** to make `Q368104` visible at all; a **hand row** to
  correct its tier from the 2 its Wikidata tags give to the 1 the
  roster says; and a **`skip` row** for `Q24884611`, because
  Hermannstadt was not a club at the wrong tier, it was a club that
  had ceased to exist. **Two of those three were invisible to the
  count and to the tier column alike** — the count said 16 both before
  and after, and it was wrong before and right after.
  **The same 16 is still the size of the tier and not a number of
  matches.** What makes it agreement now is the `ok` column reading 16
  beside it, which is exactly the reading this entry was written to
  insist on.

- **Wikidata keeps a CLUB item and a MEN'S FIRST TEAM item for many
  German clubs. That is a fifth shape, and it wants a different remedy
  from all four above.** Found 2026-09-20 by the roster check, which
  reported three German clubs twice each — once as missing from
  Wikidata, once as extra on the map.
  The two items split the facts between them:

  | | club item | men's first team item |
  |---|---|---|
  | FC Augsburg | `Q15755`, **75 sitelinks**, `P118` Bundesliga at deprecated rank | `Q97905916`, **0 sitelinks**, `P118` Bundesliga at normal rank |
  | FC Erzgebirge Aue | `Q141882`, 38 sitelinks, **no `P118` at all** | `Q97927365`, 0 sitelinks, eleven `P118` values |
  | SV Babelsberg 03 | `Q571553`, 21 sitelinks, **no `P118` at all** | `Q97927380`, 0 sitelinks, `P118` Nordost + 3. Liga + DDR-Liga |

  `P31` is what names the shape: the club item is an *association
  football club*, the team item is a ***men's association football
  team*** (`Q103229495`). Wikipedia links the **club** item; the map can
  only see the **team** item.
  **The remedy is to do nothing to the club files, and that is the
  point.** `skip` on the team item would take Aue and Babelsberg off
  the map for good, because their club items carry no league and would
  never come back. This is the SSV Ulm lesson pointing the other way:
  there the parent was the one to skip, here the "duplicate" is the only
  one that works. **Getting the shape wrong deletes a real club.**
  **The rule that decides which of the two items wins, written down so
  a later cleanup pass cannot get it backwards: an item with a LIVE
  `P118` beats a sibling item whose league tag is deprecated or absent
  altogether. Never the reverse.** A live league tag is the only thing
  that puts a club on the map at all, so the item carrying one is the
  only item that works; an item with no usable league is not a tidier
  copy of it, it is a copy that cannot be drawn. That holds whichever
  item Wikipedia writes about, whichever is older, and whichever has
  the fuller description.
  **The sitelink count points the wrong way in all three pairs, and
  that is the trap.** 75 against 0 for Augsburg, 38 against 0 for Aue,
  21 against 0 for Babelsberg. The shapes list below already says to
  use the sitelink count only to break a tie *after* the shape is
  settled; this is the shape where using it to settle anything deletes
  the club.
  **These three pairs are verified correct as they stand, and they are
  protected from any future duplicate cleanup pass.** That is a
  standing instruction, not an observation:

  | club | the item that must stay | the item that must NOT be preferred over it | why |
  |---|---|---|---|
  | FC Augsburg | `Q97905916`, the men's team item | `Q15755`, the club item | `Q15755`'s only `P118` is Bundesliga at **deprecated** rank, so `wdt:P118` yields nothing and the club query cannot see it. `skip` the team item and Augsburg leaves the map with nothing to bring it back |
  | FC Erzgebirge Aue | `Q97927365`, the men's team item | `Q141882`, the club item | `Q141882` carries **no `P118` at all** |
  | SV Babelsberg 03 | `Q97927380`, the men's team item | `Q571553`, the club item | `Q571553` carries **no `P118` at all**; the team item is the one whose tier is corrected by hand to 4 |

  **None of the three needs a `skip` row and none may be given one.**
  What makes them look like duplicates is not two pins on one ground —
  the club item never reaches the map, so nothing on the map can show
  it. It is the roster check reporting each club twice, once as missing
  from Wikidata under the club item Wikipedia links and once as extra
  on the map under the team item, and `_sameNameOnMap` exists exactly
  so that one club appearing twice does not read as two errors.
  **Rule 6 is satisfied rather than threatened by these items** — they
  are explicitly the men's team, which is what this project wants.
  **What did change is one tier.** SV Babelsberg 03's team item carries
  both `Q548937` and `Q154069`, and the builder takes the lowest mapped
  tier, so it arrived at 3. The 2026-27 Regionalliga article lists the
  club and the 3. Liga article does not, so `clubs-manual.csv` now says
  tier 4.
  **And `roster-review.csv` now says so on the row.** A
  `_sameNameOnMap` column names the other Q-id when a club of the same
  name sits on the map at that tier. It is an **annotation and never a
  decision** — the whole value of the sitelink hop is that the
  comparison is id-to-id, and a name is too weak to join on. It is there
  so one club appearing twice does not read as two errors.
  **Since 2026-09-27 the three pairs read as one club each, `ok`, and
  the join is id to id after all.** Read on a runner that day: each team
  item names its club item in `P831` (parent club) - `Q97905916` →
  `Q15755`, `Q97927365` → `Q141882`, `Q97927380` → `Q571553` (the last
  in `P361` too). The club items point at nothing. `check_rosters.py` now
  takes a map club the roster does not name, whose `P831` is a roster
  club not on the map, with the same reserve marker, as that club. The
  protection above is unchanged: nothing about which item stays moved.


- **Both cases found by grouping clubs on their coordinates are now
  closed.** Of the 10 shared grounds, two looked like one club entered
  twice. Neither turned out to be an ordinary duplicate, and the two
  went opposite ways. Both were settled on 2026-09-19 by reading
  Wikidata from a **GitHub runner**, because the session doing the work
  could not reach `wikidata.org` at all — see the entry on the
  Actions-dispatch route below.
  - **Dinamo București is two real clubs, and they are two pins at
    last.** `Q204237` is the Liga 1 club at Stadionul Dinamo.
    `Q113577526` is **CS Dinamo București**, a separate club currently
    in Liga 2. What was wrong was Wikidata's data, not the item:
    `Q113577526` carries `P115` `Q1226240`, the senior club's ground,
    and its capacity and coordinates followed from that.
    `clubs-manual.csv` corrected the name, venue and capacity on
    2026-09-18, and now carries the coordinates too: **44.5481 /
    25.9811**, which is `Q7596368` Stadionul Buftea's own `P625`. That
    is **14.1 km** from Stadionul Dinamo, so the shared pin is gone.
    **One thing was deliberately not resolved.** `Q7596368` says the
    capacity is **450**; the file says **1,600**, which is Alexandru's
    figure and wins, as hand-written data always does. The disagreement
    is written into the row rather than argued away, because it may not
    be a wrong number at all — it may mean `Q7596368` "Stadionul
    Buftea" and the CNF Buftea pitch the club actually uses are two
    different grounds in the same town. The coordinate is still trusted,
    because that row had already named `Q7596368` as its source before
    anyone could read it.
    **There is now a theory for the 450, and it is a theory, not a
    finding.** CNF Buftea is not a stadium, it is the federation's
    national training centre: a complex of several pitches on one site.
    Romanian sources give its main stadium **800 on each side**, which
    is the **1,600** already in the row — so the hand-written figure and
    the main stadium agree, and `Q7596368`'s 450 would then be a
    *different pitch in the same complex*, not a contradiction of
    anything. That would explain the gap without either number being
    wrong, and it would explain why the coordinate can be right while
    the capacity beside it is not.
    **Nobody has verified it, so nothing has been changed.** What would
    settle it is reading which ground `Q7596368` actually names, and
    which pitch of the complex CS Dinamo plays on, from the federation
    or the club rather than from a number that fits. Until then the
    1,600 stands because it is hand-written, not because this theory is
    right — and if the theory turns out to be right, the row still does
    not change, it just stops looking like a disagreement.
  - **SSV Ulm 1846 is decided, and it is not a duplicate either.** The
    sitelink test prepared for it was run: **`Q14551982` has 21
    Wikipedia sitelinks, `Q701290` has 14**, so the second of the two
    prepared branches applies — the `tier 4` correction on `Q14551982`
    stays, because its own tag is still the 3. Liga one, and `Q701290`
    now has the `skip` row.
    **The reason the test gave the right answer is not the reason the
    entry assumed**, and that matters more than the answer. These are
    not one club entered twice. `Q701290` is labelled "SSV Ulm 1846"
    and typed *sports club* and *multisports club*; `Q14551982` is
    labelled "SSV Ulm 1846 Fußball" and typed *association football
    club*. That is a parent club beside its football department, which
    is how a great many German clubs are organised — so expect this
    shape again, and expect the sitelink count to keep pointing at the
    football item simply because that is the one the Wikipedias write
    about. On a football map both readings give the same instruction:
    keep the football item, skip the parent.

  **So there were never three duplicates, only two.** Hamburger SV and
  1. FC Lokomotive Leipzig are genuine duplicate items and still have
  their `skip` rows. Dinamo was a copied *coordinate*, Ulm is a parent
  club beside its department. The lesson that survives all three
  shapes: two pins on one ground is a *symptom*, not a diagnosis, and
  the "2" marker is what makes the symptom visible at all. Before it,
  the second pin sat exactly under the first and nothing counted it.

  **The six shapes have names now, because the next one will not
  arrive with a label on it.** The first three look identical on the
  map — two items, one name, one ground — and each wants a different
  remedy. The fourth and fifth never appear as two pins at all, because
  one item of the pair never reaches the map: only the roster check can
  see them, and it sees them as one club reported twice. The sixth
  never reaches the map either, and arrives by a third route: as a
  confident coordinate proposal.
  Getting the shape wrong is not a cosmetic mistake: `skip` the wrong
  item in the second shape and a real club disappears from the map for
  good, with nothing to notice it had gone, and `skip` the wrong item
  in the fifth and the same thing happens for the same reason.

  1. **One club, two items — a true duplicate.** *Hamburger SV,
     1. FC Lokomotive Leipzig.* Same name, same league, same ground,
     same capacity, same coordinates, and one of the two items carries
     almost no Wikipedia sitelinks. **Remedy: `skip` the thin item.**
  2. **Two clubs, one name — separate real clubs.** *Dinamo București:
     `Q204237` in Liga 1, `Q113577526` in Liga 2.* Both items are real
     and both belong on the map. They landed on one pin because one
     item was given the other's ground — `Q113577526`'s `P115` points
     at Stadionul Dinamo, and the coordinates and capacity followed.
     **Remedy: correct the wrong club's ground and coordinates in
     `clubs-manual.csv`. Never `skip`.**
  3. **One club, two items — parent and department.** *SSV Ulm 1846:
     `Q701290` the multi-sport parent, `Q14551982` the football
     department.* One organisation, two Wikidata items by design, which
     is how a great many German clubs are structured. **Remedy: keep
     the football item, `skip` the parent.**
  4. **One club that is no longer a club — merged, dissolved or thrown
     out of its division.** *Torgelower FC Greif `Q566179`, Teutonia
     Watzenborn-Steinberg `Q21175456`, FC Hermannstadt `Q24884611`,
     Politehnica Iași `Q1024390`.* The club stopped existing, or
     stopped playing at any tracked level, and Wikidata still tags it
     with the division it was in. **Remedy: Alexandru's, and it is a
     `skip` or a rename, never a coordinate** — writing the merged
     club's ground would put a club that has not existed since 2018 or
     2022 onto the map at a tier it left.
     **The two German ones never reached the map and the two Romanian
     ones were ON it, which is the difference that matters.** Torgelow
     and Teutonia have no coordinates, so they die at the coordinates
     gate and no marker could ever reveal them. Hermannstadt was drawn
     at **tier 1** and Politehnica Iași at **tier 2**, with grounds,
     capacities and pins, looking exactly like checked facts. **Nothing
     on the map can show this shape**, because a dead club's pin is
     indistinguishable from a live one's — only a roster can, and only
     where `league-rosters.csv` has an article for that tier.
  5. **One club, two items — club and men's first team.** *FC Augsburg
     `Q15755` / `Q97905916`, FC Erzgebirge Aue `Q141882` /
     `Q97927365`, SV Babelsberg 03 `Q571553` / `Q97927380`.* Wikidata
     keeps an *association football club* item and a ***men's
     association football team*** item (`P31` = `Q103229495`) and they
     split the facts between them: Wikipedia links the club item, the
     usable league tag lives on the team item. **Remedy: keep the item
     with a live `P118` — the team item in all three — and `skip`
     neither. Never the reverse.** The entry above names these three
     pairs as verified and protected from cleanup.
  6. **A club recently gone, offered as a coordinate proposal.** Named
     2026-09-26, at Alexandru's instruction. *Sparta Râmnicu Vâlcea
     `Q130235269` (dissolved 2025), CSM Bacău `Q66423967` (dissolved
     2025), Șoimii Gura Humorului `Q130234791` (withdrew and was
     excluded by the FRF before 2026-27).* The club stopped playing in
     the last season or two; Wikidata still carries its Liga III tag
     and **no `P576`**, so the club query keeps it; it has no
     coordinates, so it never reaches the map; and
     `propose_coordinates.py` then finds it a perfectly plausible
     ground and calls the row **confident**. Nothing about the row
     looks wrong — the ground is usually real and in the right town.
     **What is wrong is the club.** Applying the proposal is what would
     create the error: a dead club drawn at tier 3 with a real pin.
     **How it differs from shape 4.** Same underlying fact — a club
     that stopped, a tag that did not — but shape 4's clubs were on the
     map or hidden at the coordinates gate and needed a `skip`. These
     are caught one step earlier, at judging time, and the remedy is a
     **whole-club `rejected` row in `data/coordinate-reviews.csv`**
     (blank `osmRef`), which stops the tool proposing anything for
     them. A `skip` is not needed while they have no coordinates.
     **A close relative, not the same thing:** a club *relegated* below
     every tracked tier with the old tier still preferred on Wikidata —
     Gilortul Târgu Cărbunești `Q20647345`, *"Relegated to Liga IV"* in
     the 2026-27 Liga III article — is alive, just out of scope. Same
     remedy, different reason, and the row says which.
     **Standing practice from 2026-09-26: every `confident` or `held`
     proposal is checked for dissolution before it is applied**, the
     same way a `skip` is checked before it is written. Three reads, in
     this order: the item's `P576`; the club's own Wikipedia infobox
     (`dissolved`, and `league`/`season`/`position` for a relegation or
     withdrawal); and the current-season division article, **including
     its Team changes section** — that is where *withdrew*, *excluded*
     and *relegated to* are written, and a club listed there is not in
     the division even though its name is on the page. **A missing
     `P576` proves nothing**: none of the three clubs above has one.

  **What to look at, in this order.** `P31` first: *association
  football club* on one item and *sports club* or *multisports club* on
  the other is shape 3 and is nearly conclusive — a label ending in
  "Fußball" says the same thing. Then the league and the tier: two
  items in **different** divisions of the same pyramid, each with its
  own history and its own current season, is shape 2. Only when both
  items claim the same club in the same division is it shape 1.
  `P31` names shape 5 just as plainly: ***men's association football
  team*** (`Q103229495`) on one item against *association football
  club* on the other. Where that is what you have, stop comparing the
  items and read the **rank** of each one's `P118` instead — an item
  can carry exactly the right league and still be invisible to the club
  query, which is what `tools/diagnose_p118_rank.py` exists to say.

  **The sitelink count is not the test it looks like.** It answers
  "which item do the Wikipedias write about", which happens to be the
  right question in shapes 1 and 3 and is the **wrong question in
  shapes 2 and 5**. In shape 2 both items are real clubs and the senior
  one always wins on sitelinks; in shape 5 the club item wins every
  time — 75 to 0, 38 to 0, 21 to 0 — and it is the item that cannot be
  drawn. It pointed at the football item for SSV Ulm for a
  reason that had nothing to do with duplication. Use it to break a tie
  *after* the shape is settled, never to settle the shape.

  The remaining shared grounds are genuine. FCU Craiova and
  Universitatea Craiova really do share the Stadionul Ion Oblemenco.
  **This line used to say the Waldau-Stadion really is Stuttgarter
  Kickers and VfB Stuttgart II. It was not**: the Waldau was one of two
  truthy `P115` values on VfB Stuttgart II's item, and the club plays
  its 2026-27 home games in Aspach (corrected 2026-09-26). The rest are a first team with its own reserve side.
  The Grünwalder was three at once — TSV 1860 München, TSV 1860 München
  II and FC Bayern München II — until TSV 1860 München II's ground was
  cleared; it is two now, and the third was never really there, only
  copied from the senior club.

- **The Franz-Kremer-Stadion is in the data now.** It was not, when
  this entry was written, and the rest of the entry explains why the
  bug report that named it was not a marker problem. 1. FC Köln II now
  has the ground by hand in `clubs-manual.csv`, from europlan-online —
  see the entry on the 22 coordinate rows below. The women's team and
  the U19s named in that bug report are still not in the data, and the
  ground still carries exactly one club, so there is still nothing here
  for the shared-marker feature to show.
  What the original entry said, and it still holds as the reasoning:
  the bug report that prompted the change named 1. FC Köln II, the
  women's team and the U19s as three clubs sharing it, and at the time
  none of the three was in `data/clubs/DE.json`. Only three
  clubs in the German file have "Köln" in the name — 1. FC Köln at the
  RheinEnergieStadion, SC Fortuna Köln at the Südstadion and FC Viktoria
  Köln at the Sportpark Höhenberg — and no club anywhere in either file
  had a Franz-Kremer venue. 1. FC Köln II was one of the 31
  Regionalliga clubs listed below that Wikidata cannot place, so it
  never reached the map to collide with anything. It was a candidate
  for `clubs-manual.csv` by way of `coordinate-review.csv`, not a
  marker problem — and that is exactly the route it took.

- **The Actions-dispatch route to Wikidata still works, and it is the
  only route this sandbox has.** Checked first thing on 2026-09-19. The
  session's egress proxy answers **403 to CONNECT** for
  `wikidata.org`, `query.wikidata.org`, `overpass-api.de` and
  `europlan-online.de` — and also for `unpkg.com` and
  `tile.openstreetmap.org`, so the app's own CDN and map tiles cannot
  be loaded from here either. `api.github.com` **is** reachable.
  GitHub's runners are not behind that proxy, so a
  `workflow_dispatch` of `build-clubs.yml` against a working branch
  reaches Wikidata normally. That is how the Dinamo coordinates, the
  SSV Ulm sitelink counts and the Triesenberg confirmation were
  obtained, and how europlan-online.de was read for the go/no-go
  question below. The pattern, used repeatedly on 2026-09-19: add a
  throwaway script plus a temporary step to `build-clubs.yml` **on the
  working branch**, dispatch it with `ref` set to that branch, read the
  answers out of the job log, then remove the script and the step in
  the same branch.
  **Two practical lessons from the europlan runs.** Put a temporary
  job's own `if: false` on the `clubs` job while the probe runs, or the
  dispatch also rebuilds and commits the club layer as a side effect of
  asking a question. And **keep the printed output small**: the first
  europlan probe dumped the site's ~1,000 homepage links, and the log
  that could be read back no longer reached as far as the answer at the
  top of it. Print the thing you are asking about first, and print it
  again last.
  **The one constraint worth writing down:** `workflow_dispatch` only
  works for a workflow file that already exists on the **default
  branch**. A brand-new workflow on a working branch cannot be
  dispatched, which is why the temporary step goes inside
  `build-clubs.yml` rather than into a file of its own.
  Wikidata itself was slow but fine: the German discovery query took
  180.8s across retries on the first run of the day (one 502, one
  timeout) and 2 minutes total on the second.

- **The Actions-dispatch route does not reach fcbayern.com, and that was
  measured rather than assumed.** Established 2026-09-19 while writing
  the first row of `club-tickets.csv`. The club's site sits behind
  Akamai and refuses this infrastructure outright:
  `fcbayern.com/robots.txt`, `fcbayern.com/de/tickets/info/preise-und-ermaessigungen`
  and `tickets.fcbayern.com/documents/de/preisliste.pdf` all answer
  **HTTP 403 with `server: AkamaiGHost`** and a 3,823-byte "FC Bayern
  München - Support" page carrying `<meta name="robots"
  content="noindex,nofollow">`.
  **The control is what makes this conclusive.** From the same runner,
  in the same step, `www.bundesliga.com` answered **HTTP 200 in 0.13s**
  with 1.1 MB of HTML. So it is not the runner's network, not its
  region (Azure westus), and not a transient failure. It is that site
  refusing that traffic.
  **Two shapes of the same refusal, and the first one wastes eight
  minutes if you do not know about it.** With a scripted `User-Agent`,
  Python's `urlopen` does not get a 403 at all - the TCP connection
  opens and then no bytes ever arrive, so every request dies on the
  read timeout. It was only switching to `curl` with an ordinary
  browser `User-Agent` that turned the silence into a legible 403. If
  a fetch against this site hangs rather than failing, that is the
  block, not a slow page.
  **`robots.txt` is itself a 403**, so unlike europlan-online - where
  the missing file meant there were no path rules to obey - there is no
  readable crawl policy here at all. What there is instead is an
  explicit refusal, and it was not worked around. Rotating user agents,
  residential proxies or TLS fingerprint spoofing would be evading an
  access control the site operator deliberately put up, which is a
  different thing from reading a page that is simply slow.
  **What this cost, practically** - written when it was still the whole
  story: the ticket facts in `club-tickets.csv`,
  `club-ticket-windows.csv` and `club-ticket-prices.csv` for Bayern were
  hand-written by Alexandru and corroborated only by search-engine
  results quoting the club's pages, never by the pages themselves.
  **That is no longer true of most of them.** The next entry is how the
  pages were read - from the Internet Archive, which does not touch the
  refusing server - and the price and window rows now rest on the club's
  own words with a capture date on them. What is still uncorroborated
  says so in its own note: the DFB-Pokal prices, and the
  `bundesliga-away-block` window whose club page has no snapshot at all.
  The URLs in the `source` columns are real and open normally in an
  ordinary browser - which is still the route to confirming any of it.

- **The club's pages have now been read, from the Internet Archive, and
  that is a different thing from getting past Akamai.** Done on
  2026-09-19. `fcbayern.com` was **not** retried: it answers 403 and a
  bot-management refusal is a stop, not something to work around. What
  was fetched instead is the Wayback Machine's own public copies, which
  is the same category of source as the search-engine results this
  project already leans on, only far better - the club's exact words,
  with a capture date on them.
  **This is now standing policy rather than a call made once**, and it
  lives in Conventions above: a bot-management 403 is a stop, the
  archive is a different source and not a way round it, and every
  archive-sourced row carries the original URL in `source` and the
  capture date in its note.
  **What exists and what does not**, checked rather than assumed:
  `/de/tickets/jahreskarten` (captured 2026-06-08),
  `/de/tickets/faq-jahreskarten` (2026-06-14),
  `/de/tickets/auswaerts-dauerkarte` (2026-06-13) and
  `/de/tickets/info/preise-und-ermaessigungen` (2025-09-02, and three
  older ones). The one page most wanted -
  `/de/tickets/info/anfragen-fuer-die-neue-saison-2026-2027` - has **no
  snapshot at all**; the CDX index answered HTTP 200 with an empty list.
  So the page dated 2 June 2026 is still unread and probably always will
  be.
  **Two practical notes for next time.** The CDX index is slow and
  flaky from a runner: several queries needed three attempts at a
  70-second timeout, and one run spent seventeen minutes on five URLs.
  And a `.../<timestamp>id_/<url>` fetch sometimes fails where the same
  capture succeeds on a plain `.../<timestamp>/<url>` retry, so retry
  without `id_` before believing a snapshot is unreadable.

- **The Champions League price sets differ by OPPONENT, not by round,
  and the theory that said otherwise was wrong.** This is the
  correction worth keeping from 2026-09-19.
  `club-ticket-prices.csv` used to argue that its 100/80/60/50/19 rows
  were the league phase and that a higher 150/120/100/70/19 set search
  results kept returning was a later knockout round - reasoning from
  category 5 agreeing at 19 EUR in both. The archived price page shows
  **two league-phase tables side by side**: "PREISE UEFA CHAMPIONS
  LEAGUE GRUPPENPHASE FC BAYERN - CHELSEA FC" at 120/100/70/60/19, and
  "... FC BAYERN - BRÜGGE / SPORTING LISSABON / SAINT-GILLOISE" at
  100/80/60/50/19. Same round, different visitors.
  **Both tables are now in the file**, as of 2026-09-19, under a new
  `opponentTier` column that is part of the price key - see the
  Conventions entry. Until then the file held only the cheaper set and
  read like *the* Champions League league-phase price. **A single flat
  figure for a club that prices by opponent was always going to be
  incomplete**, and nothing in the file said so, which is the part worth
  remembering: it was not wrong about a number, it was silently missing
  half the answer.
  **The category-5 clue was worthless and it is worth knowing why.**
  19 EUR is the Südkurve standing price on *every* Champions League
  table on that page, and 15 EUR on every Bundesliga one. Two Champions
  League sets agreeing on category 5 therefore says only that both are
  Champions League - it would have matched whatever the two sets were.
  A constant is not a fingerprint. Use it to confirm a competition,
  never a round.
  **Prices do rise by round, so half the theory was right**, and the
  archived Jahreskarten page proves it for the season-ticket add-on:
  UCL Ligaphase 80/60/40/30/15, Achtelfinale 110/90/70/40/15,
  Viertelfinale and Halbfinale both 160/120/80/60/15. Those are
  Jahreskarten prices - a per-match add-on for season-ticket holders -
  and **a different product from a day ticket**, so they do not belong
  in the day-ticket rows. Bayern quotes at least three price families
  for the same seat, and mixing them is the easy mistake here.
  **The Bundesliga rows are confirmed exactly** against the same page:
  80/70/50/40/15 for categories 1 to 5, Vollzahler, member discount
  2,50 EUR.
  **The season was the open problem and it is closed by relabelling,
  not by research.** The page that matches every one of those rows is
  the **2025|26** one and the rows said `2026-27`;
  fussball-tickets-kaufen.de, read directly, says the club has not
  published 26/27 prices at all. So the rows confirmed against that
  page - the Bundesliga set and both Champions League sets - now say
  `2025-26`, the season they were actually confirmed for. That is not a
  downgrade: they are confirmed more firmly than before, against the
  right year.
  **What the file therefore no longer claims is a 26/27 Bundesliga
  price**, and that gap is the honest state of things rather than
  something to fill. The only rows left at `2026-27` are the DFB-Pokal
  ones, whose sole source is Alexandru and which say so - the archived
  price page carries no Pokal table at all, so there was nothing to
  check them against.
  The 150/120/100/70/19 set was on no page read and is still
  unaccounted for.
  **`priceBasis` is corrected too.** It said `excl-vat-fees`, which is
  wrong twice over: a German consumer price includes VAT by law, and
  the 1 EUR Vorverkaufsgebühr and 2-8 EUR Systemgebühren are added *on
  top*. Neither of the two values that existed could say that, so
  `incl-vat-excl-fees` was added to the closed vocabulary and the
  confirmed rows carry it. The Pokal rows now say `unknown`, because
  nothing was ever read for them.
  **And the 120 EUR resale row has a likely explanation at last**,
  which is the thing this correction bought. Alexandru's sighting was
  FC Bayern v **RB Leipzig**, 24/25, on the club's member-only
  Zweitmarkt, against an 80 EUR category 1 face value - which read as a
  breach of the club's own no-more-than-face-value rule. If Bayern
  tiers domestic prices by opponent the way it demonstrably tiers
  Champions League ones, the face value for that fixture was probably
  above 80 EUR and nothing was breached. **That is inferred and the row
  says so**: the tiering actually read is Champions League, no
  Bundesliga table showing two price sets has been seen, and no price
  table for that match has been read at all. The 120 EUR matching the
  top Champions League category 1 exactly is a coincidence worth
  noting and is not evidence - different competition, different season.
  `opponentTier` is left **blank** on that row for the same reason.

- **The Bayern request windows were two clocks read as one, and that is
  settled.** The `bundesliga-home` and `bundesliga-away` rows of
  `club-ticket-windows.csv` used to end "Both cannot be right. Nothing
  here picks a winner", over an apparent contradiction: a request page
  dated 2 June 2026 against a DFL fixture list published 2 July 2026.
  Both were right, about different products.
  **The season-ticket clock** runs on the season ending, not on the
  fixture list. From the club's own pages: the ADK order deadline for
  26/27 "endete ... am 28.05.2026" with answers "Anfang Juni"; the
  Reservierungsanschreiben goes out "ca. Anfang bis Mitte Juni", and
  for 26/27 "voraussichtlich Mitte Juni 2026"; and "alle Änderungen für
  die Jahreskarte können immer in der Saisonvorbereitung durchgeführt
  werden, ca. Anfang Juni bis Ende Juni, dies hängt vom Saisonende ab".
  A season runs 1 July to 30 June.
  **The single-match clock** is the Ticket-Anfrageportal, "bereits vor
  einer Saison für die Spiele Ihrer Wahl", with the lottery "ca. 6
  Wochen vor jedem Spiel" - which also pins down the "four to six
  weeks" in `club-tickets.csv` at about six. A request can be lodged
  before the opponent is known, which is exactly the blind matchday
  slot `football-rules.json` describes; a **match-specific** request
  needs the schedule, which is why 26/27 league-phase requests opened
  on 29 August 2026, two days after the draw.
  **The single `late June` estimate has now been split, 2026-09-19**,
  because one cell cannot answer for two clocks and leaving it whole
  meant it was wrong for at least one of them. The file now carries
  **five** window rows instead of three:
  - `season-ticket-renewal` — the Jahreskarte cycle, `early to mid
    June`, `inferred` / `observed-past-cycle`. It follows the season
    ending, so the DFL's fixture list is irrelevant to it.
  - `bundesliga-single-match` — the per-match home clock, `about six
    weeks before each match`, `inferred` / `published`. **It has no
    calendar date at all**, which is the point: a reminder built from
    this row hangs off a fixture, never off a month.
  - `bundesliga-away-block` — all away fixtures in one pre-season
    window, moved from `late June` to `early July`, `inferred` /
    `user-supplied`. A match-specific away request needs the schedule,
    and Alexandru's own `football-rules.json` says the same from the
    other side: check "from early July 2027", close 27 July. **That
    cell is his figure moved across, not a new one invented here** —
    rule 1 — and if he disagrees it is his to change.
  - `away-season-ticket` — the ADK, `late May`, and the **only**
    `confirmed` / `published` row in the file. The ADK page states its
    own next cycle: "Ende Mai 2027 informieren wir Sie dann gerne
    wieder über Bestellmöglichkeiten für die Saison 2027/28." A
    published claim about a *future* window is exactly what `confirmed`
    means, and nothing else in the file has one.
  - `ucl-league-phase` — unchanged.
  **One nuance the six-weeks row carries and nobody should lose**: the
  club's "ca. 6 Wochen vor jedem Spiel" is when the **lottery draws**,
  not when requests open. The portal takes them before the season
  starts. So six weeks is the deadline side of that window and the
  request has to be in *before* it, not made at it.
  **What is confirmed about the ADK is narrower than the row looks.**
  The club says it will *inform* members at the end of May 2027. It
  does not say the ordering window opens then and does not say when it
  closes, so `late May` is when to start watching and no deadline is
  written anywhere in these files.

- **TSV 1860 München II is off the map until somebody finds its real
  ground, and that is the right place for it.** `Q7671747` is corrected
  to **tier 5, Bayernliga Süd**, in `clubs-manual.csv` — Wikidata still
  tags it `Q340179` Regionalliga Bayern, which is why it arrives at
  tier 4 and needs the correction. Its **venue, lat and lon now read
  `<clear>`**, which deletes Wikidata's `P115` `Q254903`, the
  Grünwalder, and the coordinates that came with it. Those were the
  senior club's, copied onto this item — the same shape of error as CS
  Dinamo's, and none of it ever verified.
  Until 2026-09-19 those cells were blank instead, and a blank leaves
  the fetched value alone, so the club went on displaying the senior
  club's ground as fact. That was the case that produced the `<clear>`
  sentinel.
  **The Grünwalder collision is gone.** Confirmed against the rebuild
  of 2026-09-19, which was run on a GitHub runner because this sandbox
  cannot reach Wikidata: `Q7671747` is no longer in `data/clubs/DE.json`
  at all, Germany went from 127 clubs on the map to 126, tier 5 is now
  empty, and the Grünwalder is a **"2"** — TSV 1860 München and FC
  Bayern München II, both tier 4 — from z11 and at every zoom above it.
  It never becomes a "3" again.
  **The capacity cell was deliberately left alone.** 15,000 is the
  Grünwalder's and just as wrong, but a club with no coordinates is not
  written to `DE.json` at all, so that figure now reaches nothing.
  Clear it too if the club ever comes back without a confirmed one.
  **What is still not known is the ground itself.** Nothing here
  establishes where this team plays; it says only that the map has
  stopped claiming to know. Fill the three cells in with a real ground
  and it returns.

- **A blank cell still cannot clear a fetched value, and now it does
  not have to.** This used to be an open problem: a blank said *leave
  the fetched value alone* and nothing said *remove what Wikidata
  claims here*, so a ground known to be wrong had to go on being
  displayed. The sentinel that was sketched here is **built** — a cell
  reading `<clear>` deletes the fetched value and puts nothing back.
  The rules, the four cells that accept it and the reason a position
  needs it in both `lat` and `lon` are in Conventions above. A blank
  cell means exactly what it always meant; nothing already in
  `clubs-manual.csv` changed meaning.
  **What is still open is not the mechanism.** Nothing detects a
  copied ground on its own. `<clear>` is how you act on one once a
  person has spotted it, and the only thing that makes them visible is
  still the shared-ground marker — which cannot help when the copied
  ground belongs to a club that is not on the map at all.

- **The map lag was profiled, and `drawClubs()` is not where it is.**
  Measured on 2026-09-19 in headless Chromium at a 390x844 phone
  viewport with **4x CPU throttling**, against the real `index.html`
  (Leaflet served from a local copy and map tiles stubbed, because the
  proxy blocks both). Numbers, not impressions:
  - **Panning never calls `drawClubs()` at all.** Eight pans, zero
    calls. The app binds it to `zoomend` and to nothing else, so the
    premise that it runs on every pan is simply not true.
  - `drawClubs()` costs **17–25 ms** per zoom change, worst case at z11
    where all 182 markers are on. The whole call was 32.8 ms in a tight
    loop.
  - **The coordinate grouping is not the expensive part**: filtering by
    tier and grouping 193 clubs by coordinate takes **0.32 ms**. It is
    about 1% of the redraw.
  - The rest is Leaflet adding and removing markers, not the app's own
    code. Eager popup building — an HTML string for each of 172 solo
    clubs and a full DOM subtree with a click listener for each of the
    10 shared grounds, on every redraw, for popups that are mostly
    never opened — accounts for **3.1 ms** of it. Waste, but not lag.
  - Twenty pans at z11 cost **15.8 ms each**, and a 30-pan drag
    produced **no long task over 50 ms**.
  So at today's 191 clubs there is no lag in the drawing code to fix.
  If the app feels slow on a phone, the remaining suspect is **tile
  loading from `tile.openstreetmap.org`**, which is network and could
  not be measured from here because the proxy blocks it.

- *(2026-10-03: since every club is drawn from z9, all 556 are SVG
  paths at z9 - 531 markers - where the old rule had 443. Still under
  the crossover below; the timing is in Conventions, "Tier zoom
  bands".)*
- **The canvas renderer in `initMap()` has never been in effect.** The
  line `L.layerGroup([], {renderer: L.canvas({padding:.5})})` does
  nothing: `L.LayerGroup` has no `renderer` option and does not pass
  its options to its children. Verified by inspecting the live map —
  every club circle resolves to **`L.SVG`** with the default padding of
  **0.1**, there are **172 SVG `<path>` elements** in the DOM and
  **zero canvases**, and the `L.canvas()` object that is created is
  thrown away. The comment above it claims a protection the map does
  not have.
  **It has not been fixed, and the measurement is why.** At today's
  size canvas is *slower*: 20 pans cost 15.4 ms each on SVG against
  18.4 ms on a real canvas. The crossover, measured by cloning the club
  list:

    | clubs | `drawClubs()` | per pan, SVG | per pan, canvas |
    |---|---|---|---|
    | 191 | 22 ms | 15.4 ms | 18.4 ms |
    | 500 | 38 ms | 15.7 ms | 21.9 ms |
    | 1,000 | 58 ms | 18.3 ms | 19.6 ms |
    | 2,000 | 122 ms | 32.0 ms | 19.2 ms |
    | 4,000 | 278 ms | 68.5 ms | 23.3 ms |

  Canvas only starts winning somewhere between **1,000 and 2,000**
  clubs. **Tier 5 does not get there**: the German leagues in
  `unmapped-leagues.csv` that look like tier 5 carry about **254**
  football clubs between them before the roughly one-in-three that have
  no coordinates are dropped, so tier 5 in Germany would take the map
  to something like 350–400. So this is a real bug that is currently
  harmless, and fixing it today would make panning slightly worse. It
  is recorded here so that whoever expands past about a thousand clubs
  knows exactly which line to change and what it buys.

- **The city field is always null.** `CLUB_QUERY` in `tools/fetch_clubs.py`
  selects `?cityLabel` but never binds a `?city` variable anywhere in its
  `WHERE` clause — there is no `?club wdt:P159 ?city` or similar triple, so
  `SERVICE wikibase:label` has nothing to label and `?cityLabel` comes back
  unbound on every row. `city = cell(row, "cityLabel")` is therefore always
  `None`, and every club in `data/clubs/DE.json` and `data/clubs/RO.json`
  carries `"city": null`, confirmed by inspecting both files directly.
  `propose_coordinates.py`'s own `CITY_QUERY` binds `?city` correctly (via
  `?club wdt:P159 ?city` / `wdt:P131 ?city`), so the fix pattern already
  exists in this codebase — it was just never carried over to `CLUB_QUERY`.
  Not fixed here; recorded only.
- SV Meppen and 1. FC Schweinfurt are missing from the German layer
  entirely: neither comes back from the club query at all, and until the
  discovery query finishes there is no way to see which league Q-id they
  do carry. Erzgebirge Aue is a different case — it does come back, as
  `Q97927365`, and is dropped for the reason below.
- **Two coordinate proposals were wrong and must not be pasted in.**
  OpenStreetMap puts SV Heimstetten (`Q324983`) at "Sporttraum München"
  (`way/388183624`), a commercial sports centre 0.8km from the club's own
  Stadion im ATS-Sportpark; and ETSV Weiche (`Q831867`) at the
  "GP JOULE Arena" (`way/25020637`), 3.3km from its Manfred-Werner-
  Stadion. Both were checked against independent sources by Alexandru and
  both are now corrected by hand in `clubs-manual.csv`, from
  europlan-online, with the addresses and capacities in the note column.
  That row also carries the club's current name, SC Weiche Flensburg 08 —
  Wikidata still labels it ETSV Weiche.
  Nothing in `propose_coordinates.py` remembers a rejection, so
  `coordinate-review.csv` will offer both wrong grounds again next month.
  The manual rows win, so the map is safe either way; the risk is only
  that the review file still reads "confident" for two rows that are not.
- FC Unirea Dej has plainly wrong coordinates in Wikidata — placed near
  Bucharest, roughly 300km from Dej. FK Csíkszereda is the same kind of
  error, 31km from the nearest ground OpenStreetMap knows about.
- Wikidata carries two items for the same club more often than expected.
  Hamburger SV was the first, 1. FC Lokomotive Leipzig the second:
  `Q162317` with 39 Wikipedia sitelinks against `Q28936927` with 2, same
  league, ground, capacity and coordinates. Both duplicates now have a
  `skip` row in `clubs-manual.csv`. Nothing detects this automatically,
  so the next one will again show up as two pins on one ground.
- The cross-check has now been run for real. Of 185 clubs it compared,
  20 agreed and 7 disagreed; the rest could not be compared because only
  one source has a figure. Fortuna Düsseldorf (Wikidata 9,917 against
  OpenStreetMap 54,600) and 1. FC Saarbrücken (35,303 against 16,003)
  are the two worst. Preußen Münster was not among them — OpenStreetMap
  has no capacity for its ground, so nothing could be checked.
  **That 7 was 6 clubs, not 7.** Checked on 2026-09-19 against the run
  that produced it: the 2026-09-16 file carried 1. FC Lokomotive Leipzig
  twice, once as `Q162317` and once as `Q28936927`, the duplicate item —
  same club, same two figures, counted twice. Since the `skip` row for
  `Q28936927` the file has held **6** disagreements, and that is the
  real number. Nobody has recounted the 20 agreements or the 185
  comparisons the same way, so treat those two as upper bounds until a
  run after the duplicate removals is counted. The lesson is worth more
  than the arithmetic: a duplicate Wikidata item does not only put two
  pins on one ground, it quietly inflates every count taken downstream
  of the club layer.
- Romanian capacities cannot be corroborated. OpenStreetMap has a usable
  capacity for exactly one Romanian ground out of the 404 it knows about,
  so the cross-check confirmed nothing there: 0 agreements, 0
  disagreements, 0 figures OpenStreetMap could supply on its own. Every
  Romanian capacity on the map is therefore either hand-entered or
  single-sourced from Wikidata, and no second source exists to catch a
  wrong one. Germany is only better by degree — 71 usable capacities out
  of 2,960 grounds.
- Both queries now exclude people with
  `FILTER NOT EXISTS { ?club wdt:P31 wd:Q5 }`. That worked for what it
  was aimed at: the German club count is unchanged apart from the
  duplicate removed on purpose, and the "in more than one mapped tier"
  figure fell from 4,104 to 3 for Germany and 1 for Romania. It did not
  fix the discovery query. That was fixed separately — see the next
  entry — and `unmapped-leagues.csv` now carries 108 German leagues.
- **The discovery query has been turned round, and Germany is in the
  seed list at last.** `unmapped-leagues.csv` carried no German league
  at all until 2026-09-18; it now carries 108, alongside Romania's 53.
  What the tool asks is now: which leagues does Wikidata place in this
  country, and how many clubs does each have. The counting happens in a
  subquery and the labels are added outside it, because the label
  service cannot run inside an aggregate.
  - **The trade-off, and it is a real one.** This finds leagues LOCATED
    IN a country, not leagues that country's clubs PLAY IN. A club
    playing in a league Wikidata places abroad no longer puts that
    league in the seed list, and a domestic league with no `P17` at all
    disappears from it too. The run summary prints this every time.
  - Measured, not assumed: four Romanian leagues that were in the old
    seed list are gone from the new one. Two are the trade-off exactly —
    `Q257400` ABA League and `Q456092` Eurocupa ULEB, foreign basketball
    competitions Romanian clubs take part in. One, `Q5282797`
    "dizolvare", is junk and no loss. The fourth, `Q55452861` Liga a V-a
    Dolj, is the case that should worry anyone extending this: a real
    Romanian league that the new question cannot see because its
    Wikidata item carries no country. One league arrived that was never
    there before, `Q18417282` Cupa României. Net: 56 Romanian rows
    became 53.
  - No mapped league was lost. All 11 leagues in `league-tiers.csv`
    came back, and the club layer was unchanged at 129 German and 64
    Romanian clubs on the map.
  - **It is not as fast as the probe suggested and it is not reliable
    yet.** The probe measured 6.9 seconds; inside the tool the German
    query took 23.7 seconds, and the run before that one failed
    outright — HTTP 502, then 504, then 504, three attempts, no German
    leagues. The ceiling is 60 seconds, so there is room but not much,
    and the summary now prints how long the query took on every run.
    When it does fail the seed file is left alone rather than
    half-written. If this keeps failing, the next thing to try is
    splitting it: the league list in one query, the club counts in a
    second one bounded by `VALUES ?league`, with `clubsSeen` left blank
    and reported when the count cannot be had. That has not been
    measured and has not been built.
- **What the 2026-09-16 probes measured**, kept because it is the
  evidence the rewrite rests on. 20 timed probes. Stripped of
  `SERVICE wikibase:label` the German query finishes in 8.9 seconds and
  returns 967 rows. Exactly the same query with the label service put
  back dies at the query service's 60-second ceiling, having streamed
  324KB of a half-written answer. The German answer was never large:
  967 rows, 138 different leagues. Romania's is 308 rows and 56 leagues
  and takes 5.8 seconds, labels and all — Germany sits just over a line
  Romania sits just under.
  - Paging is the wrong remedy. The whole German answer is one page of
    1,016 rows; `LIMIT 10000` returned all of it, and adding
    `ORDER BY` made it slower (27–30s against 4.6s), not faster.
  - Splitting by tier cannot be done: tier is what the discovery query
    exists to find out. Splitting by region needs `P131` on the club,
    which is exactly the data the missing clubs do not have.
  - Forcing the join order with `hint:optimizer "None"` made it worse:
    HTTP 504 after 65 seconds.
  - What did work, measured: asking which leagues have Germany as their
    country, counting clubs per league, instead of asking which clubs
    are in Germany and collecting their leagues. 6.9 seconds, 118
    leagues, labels included. This is the shape that was built.
    The note here used to add that the same shape returns Romania's 56,
    "the same 56 already in `unmapped-leagues.csv`, which is the
    evidence that it loses nothing." That reading was wrong: 56 is the
    total including the three leagues already mapped, so it was 53
    unmapped against the file's 56, and the real run confirmed exactly
    that. It loses four and gains one — named in the entry above.
  - Adding a "is a football club by type" filter is faster still (3.5s)
    but returns 74 leagues against 118. It drops 44, so it would undo
    the deliberate decision not to filter by type. Not worth it.
  - The trade-off in the turned-round version: it finds leagues *in*
    Germany rather than leagues *German clubs play in*, so a German club
    in a foreign league would no longer put that league in the seed
    list. That was a measurement when it was written; it is now the
    behaviour, and what it actually cost is listed above.
- **Twenty of the 22 unresolved German coordinate rows are settled,
  from europlan-online.** Done on 2026-09-19 through the
  Actions-dispatch route, because the sandbox still answers 403 to
  CONNECT for europlan-online.de. The 22 were the 19 `ambiguous` rows
  and the 3 `no match` rows of `coordinate-review.csv`, once the five
  Wikidata squad lists and SC Veltheim are set aside. Scale: 13 league
  pages, 7 searches and 38 ground pages, which is the "few dozen pages"
  end of the question left open above, not a country's worth.
  **What settled them is the site's own club-to-ground link**, not a
  ground name. A league page's table row pairs a club with its ground,
  and the ground page's "Vereine, die in diesem Stadion spielen" says
  the same thing from the other side, with the club's current league
  and level. Both were required to agree before a row was written, and
  the ground's own town was checked against the town Wikidata gives the
  club. That last check earned its place immediately: **Eutin 08 scored
  0.5 against FC 08 Homburg** on the shared "08" alone, and only the
  town told them apart.
  **The 14 found on league pages**: 1. FC Köln II (Franz-Kremer-
  Stadion), 1. FC Nürnberg II (Max-Morlock-Platz), Borussia
  Mönchengladbach II (Grenzlandstadion), FC Augsburg II
  (Rosenaustadion), FC Erzgebirge Aue (eins Erzgebirgsstadion),
  FC Ismaning (Prof. Erich Greipl Stadion), FC Schalke 04 II
  (Parkstadion), FSV Optik Rathenow (Stadion Vogelgesang), Germania
  Egestorf (Stadion An der Ammerke), SG Barockstadt Fulda-Lehnerz
  (Stadion der Stadt Fulda), SpVgg Greuther Fürth II (Konrad-Ammon-
  Platz), VfB Eichstätt (HIRSCH Sportpark), Hertha BSC II (Stadion auf
  dem Wurfplatz) and TSV Steinbach Haiger (SIBRE-Sportzentrum
  Haarwasen).
  **The 6 found through the site's search**: Eutin 08 (Thies Hahn
  Arena), FC Kray (KrayArena), Lupo Martini Wolfsburg (Lupo Stadio),
  VfB Hüls (EVONIK Sportpark), VfR Garching (Sportplatz Schleißheimer
  Straße) and FC Viktoria 1889 Berlin (Stadion Lichterfelde).
  **Two of the three clubs OpenStreetMap could not place at all are
  now placed**: Hertha BSC II and TSV Steinbach Haiger.

- **A club can be unplaceable because it no longer exists, and nothing
  here was looking for that.** The two of the 22 that did not resolve
  are not missing data. Both clubs were merged out of existence, and
  europlan says so on the ground page itself:
  - **Torgelower FC Greif** (`Q566179`). The Gießerei-Arena in Torgelow
    lists **SpVgg. Torgelow-Ueckermünde 22**, "Fusion 2022 aus
    Torgelower FC Greif 1919 und FC Einheit Ueckermünde 1949", and
    names Torgelower FC Greif 1919 under *former* clubs.
  - **Teutonia Watzenborn-Steinberg** (`Q21175456`). The Waldstadion in
    Gießen lists **FC Gießen 1927 Teutonia/1900 VfB**, "Fusion 2018 aus
    VfB 1900 Gießen / SC-Teutonia Watzenborn-Steinberg". The club's old
    ground, the Sportplatz an der Neumühle in
    Pohlheim-Watzenborn-Steinberg, is still there and is now a side
    pitch of the merged club.
  **Neither was given coordinates, on purpose.** A ground is known for
  both, and writing it would put a club that has not existed since 2018
  or 2022 onto the map, at the Regionalliga tier Wikidata still tags it
  with. That is a `skip` decision or a rename, and it is Alexandru's,
  not something to settle by filling in a coordinate. Note that this is
  a *fourth* shape to add to the three duplicate shapes above, and it
  is the only one that a shared-ground marker can never reveal, because
  the club never reaches the map at all.

- **Six of the 20 are nowhere near the tier Wikidata gives them, and
  the tier was deliberately not corrected.** europlan names each club's
  current league and level on the ground page, and for these six it is
  far below the Regionalliga tag that brought them into
  `coordinate-review.csv` in the first place: FC Kray and Lupo Martini
  Wolfsburg at level 6, Eutin 08 at level 6, VfR Garching at level 7,
  VfB Hüls at level 8, and FC Viktoria 1889 Berlin's men's team not
  found in any league page read. Each row says so in its note.
  **Why nothing was changed.** `TIER_FROM_ZOOM` in `index.html` is
  `{1:0, 2:7, 3:9, 4:11, 5:12}`, and `drawClubs()` skips a club whose
  tier is not a key in it. So writing tier 6, 7 or 8 does not move a
  club down the map, it **removes the club from the map entirely**, the
  same way TSV 1860 München II left it. Leaving the tier blank instead
  leaves Wikidata's stale tier 4, so these six will now appear at z11
  among the Regionalliga clubs. Both are wrong in different directions
  and the choice is a real one, so it is being put to Alexandru rather
  than taken here.

- **OpenStreetMap has now been asked where the unplaced clubs are**, by
  `propose_coordinates.py`, first real run 2026-09-16. Of the 31
  Regionalliga clubs with no coordinates: 9 got a confident proposal,
  19 are ambiguous, 3 got nothing. **All 22 of the ambiguous and the
  unplaceable have since been taken to europlan-online and 20 of them
  settled** — see the entry above. What is left in this file for
  Germany is therefore evidence that has been acted on, not evidence
  waiting to be judged, and `propose_coordinates.py` will offer every
  one of those rows again next month, because nothing in it remembers
  that a row was resolved elsewhere. Same standing trap as the two
  rejected rows below: the manual rows win, so the map is safe, and the
  risk is only that the review file goes on reading "ambiguous" for
  rows that are not. Five of the nine are certain enough
  to be worth reading first — the OpenStreetMap ground names the club in
  its `operator` tag (DJK Vilzing, SSV Jeddeloh, SV Rödinghausen,
  TSV 1896 Rain, VfB Auerbach). The other four rest on a town match and
  deserve a harder look. Six of the seven reserve teams are ambiguous on
  purpose: their town is the first team's town and says nothing about
  which of the club's grounds they play on — which is the question
  europlan's club rows turned out to answer directly. Nothing had been
  applied to any club file when this was written;
  `data/clubs/coordinate-review.csv` is a list to judge, and its German
  half has now been judged.
- Romania turns out to be the bigger hole, and it was never written
  down: 107 Romanian clubs have a tier and no coordinates, against 64 on
  the map. 31 confident, 32 ambiguous, 44 nothing. Most of the 44 are
  villages where OpenStreetMap has no named ground at all, which no
  amount of matching can fix.
- Romanian club names are full of words that are also village names —
  Unirea, Progresul, Viitorul, Cetate, Petrolul. The town match finds
  the wrong village and the club's town from Wikidata throws it out
  again, which is what that check is for. A club with no town in
  Wikidata has no such guard, so a row like that is worth more
  suspicion than its wording suggests.
- Four Romanian grounds are proposed for two clubs at once (Bacău,
  Vaslui, Darabani, Modelu). Sharing a municipal ground is normal, so
  the rows say so rather than being dropped — but "ACS Înainte Modelu"
  and "Înainte Modelu" are almost certainly one club with two Wikidata
  items, the same problem as Hamburger SV.
- **The squad lists are filtered out now, by type.** Five German items
  with a tier were Wikidata squad lists — "Kader der 2.
  Fußball-Bundesliga 2019/20", "Mannschaftskader der deutschen
  Fußball-Bundesliga 2013/14" and so on. They carry `P118` exactly as a
  club does and are not people, so the `wdt:P31 wd:Q5` filter never
  touched them, and they stayed off the map only because they happen to
  have no coordinates — luck, not a rule.
  The club query now asks for `P31` as well, which costs nothing there
  because that query is bounded by the leagues in `league-tiers.csv`,
  and an item whose type is a list is thrown out and named in the run
  summary. In the real run of 2026-09-18 all five were caught by the
  type, none needed the name fallback: four are a "list of participants
  in sport tournament" and one is a "Mannschaftskader". The name
  fallback exists for an item whose type says nothing, and it only
  matches the shapes a list title has ("Kader …", "Mannschaftskader …",
  "Liste …") and a club name does not.
  This is not the "is a football club by type" filter that was
  deliberately not added. That one would have said which items to keep
  and dropped every club whose type is simply not filled in. This one
  says what to throw out, and an item with no type at all passes
  untouched.
  They will keep their rows in `coordinate-review.csv` until
  `propose_coordinates.py` next runs, which is monthly.
- **SC Veltheim is not German.** It came through the club query
  carrying the German 3. Liga item `Q154069`, and the map has no
  country filter to stop it: the club query is bounded by league, not
  by country, so any foreign club whose league tag points at a German
  league item arrives as a German club. Two searches on 2026-09-18
  agree it is the Swiss SC Veltheim, from the Veltheim district of
  Winterthur, registered with the Fussballverband Region Zürich and
  playing in the Swiss 2. Liga — so its tag most likely means the Swiss
  3. Liga and is a wrong link. It is now removed by hand with a `skip`
  row in `clubs-manual.csv`. Adding a country filter to the club query
  was considered and not done: `P17` is exactly the kind of field the
  missing clubs already lack, and a filter on it would quietly drop
  real ones. Nothing detects the next case automatically.
- **FC Triesenberg was not German and is now off the map.** `Q1387764`
  sat in `data/clubs/DE.json` at tier 3, venue Sportanlage Leitawis,
  capacity 800, coordinates 47.1145 / 9.5401 — which is in
  **Liechtenstein**. It reached the German map the same way SC Veltheim
  did: the club query is bounded by league rather than by country, and
  its item carries `Q154069`, the German 3. Liga.
  On 2026-09-19 the inference recorded here was **confirmed from the
  item itself**, read on a GitHub runner: `P17` is `Q347`,
  Liechtenstein; `P118` carries `Q24448` "2. Liga" alongside `Q154069`;
  and the coordinates come from its ground `Q2135126` Sportanlage
  Leitawis. Liechtenstein has no league of its own and its clubs play
  in the Swiss pyramid, so `Q154069` is a wrong link — most likely the
  Swiss 3. Liga, the same confusion as Veltheim's. That last step is
  still inference, and the `skip` row does not depend on it: whichever
  Swiss league is meant, the club does not belong on a German tier-3
  map. It now has a `skip` row in `clubs-manual.csv`.
- **Romania was checked for the same mistag pattern and came back
  clean.** Every one of the 64 clubs in `data/clubs/RO.json` has
  coordinates inside Romania, so no foreign club has arrived through a
  Romanian league tag the way Veltheim and Triesenberg arrived through a
  German one. Moldova was the case to worry about, because a crude
  bounding box for Romania also covers Chișinău and Moldovan clubs have
  Romanian-language names; the easternmost club in the file is
  CS Medgidia at 28.2575, well inside Dobrogea, so nothing came through.
  No club Q-id appears in both country files.
  **What that check cannot see**, and nobody should read it as covering:
  the other direction — a Romanian club tagged onto a *foreign* league.
  The club query is bounded by the leagues in `league-tiers.csv`, so a
  Romanian club carrying, say, a Hungarian league tag simply never
  appears through that tag and leaves no trace in the output to find.
  There is already evidence this direction is real: the old discovery
  query put `Q257400` ABA League and `Q456092` Eurocupa ULEB into the
  seed list precisely because Romanian clubs take part in them. Ruling
  it out needs a Wikidata query listing every `P118` value on Romanian
  clubs, which could not be run on 2026-09-19.
  **The country check now watches this, within its limits.** Run against
  the rebuild of 2026-09-19 it flags **nothing** in either country - but
  that is because both known offenders have `skip` rows by then, so the
  empty `country-review.csv` is the check agreeing with the hand
  corrections, not evidence that it would catch anything. That it works
  was established separately, against the files as they stood: the box
  alone flags FC Triesenberg and nothing else, and the `P17` signal
  flags SC Veltheim on Switzerland. The check runs on what actually
  reaches the map, so a club removed by hand is not reported again
  forever.
- **Editing `clubs-manual.csv` now does rebuild the club layer — and
  this entry claimed that a day before it was true.** The entry below
  was written on 2026-09-19 saying `data/clubs-manual.csv` was in the
  workflow's `paths`. It was not: `build-clubs.yml` on `main` still
  listed only `league-tiers.csv`, `fetch_clubs.py` and the workflow
  itself, and it was put in on **2026-09-20**. So for a day this file
  described a fix that had been decided and not made.
  **Two things went in at the same time, both of them the project's own
  rules applied to a file that was breaking them.** The `paths` entry,
  and `set -o pipefail` on the `Fetch clubs from Wikidata` step, which
  pipes to `tee` and had no `pipefail` — exactly the shape the
  Conventions entry says "has already caused one silent failure".
  The original entry, still true in everything else it says:
  Until 2026-09-19 `.github/workflows/build-clubs.yml` reran on a push
  that touched `league-tiers.csv`, `fetch_clubs.py` or the workflow
  itself — but not `clubs-manual.csv`, even though a hand correction
  decides what is on the map just as directly. A correction therefore sat inert
  until the Sunday 04:23 UTC cron or a manual "Run workflow". This was
  not theoretical: the CS Dinamo correction was committed on 2026-09-18
  and the map still did not show it a day later. `data/clubs-manual.csv`
  is now in the workflow's `paths`, so a push that touches it rebuilds.
  **What this does not cover**, and it is worth knowing: the `paths`
  filter only applies to pushes on `main`. A correction pushed to a
  working branch still needs a `workflow_dispatch` against that branch.
- **The country sanity check is built, and the claim that used to sit
  here was wrong.** This entry used to say that a bounding box would
  have caught both SC Veltheim and FC Triesenberg automatically. It
  would not have, and that was measured rather than argued before the
  check was written.
  `tools/fetch_clubs.py` now runs a country check over every club that
  reaches the map and writes `data/clubs/country-review.csv`. It
  **reports and never removes**, the same shape as
  `capacity-review.csv`, and the run summary pastes it. It uses **two
  signals, because one of them is not enough**:
  1. **A hand-written rectangle** round each country, taken from the
     country's own extreme points with a small margin (`COUNTRY_BOX` in
     the tool). This catches FC Triesenberg, at 47.11°N, because
     Liechtenstein lies south of Germany's southernmost point
     (47.2701°N, the Haldenwanger Eck).
  2. **Wikidata's own `P17`** on the club, compared against the country
     file it is being written into.
  **Why the box alone is not enough.** SC Veltheim is in Winterthur, at
  roughly 47.51°N 8.72°E. Any rectangle wide enough to hold Germany
  also holds northern Switzerland, western Austria and the whole of
  Liechtenstein, and tightening it enough to exclude Winterthur would
  cut off real German clubs in the far south. Run against the current
  files, the box alone flags exactly **one** club — Triesenberg — and
  flags Veltheim **not at all**. Signal 2 is what catches Veltheim: its
  `P17` is `Q39`, Switzerland.
  **Why using `P17` here does not contradict the decision not to filter
  on it.** That decision stands and is still right: `P17` is exactly
  the field the missing clubs already lack, so a *filter* on it would
  quietly drop real clubs. A *report* cannot drop anybody — a club with
  no `P17` whose coordinates sit inside the box is never mentioned at
  all. That is also the check's blind spot, and the run summary prints
  it every time: **nothing flagged does not mean nothing is wrong.**
- The missing Regionalliga clubs are not a query problem, and the type
  filter was never what stood in the way. The club query returns 95 clubs
  tagged with one of the five mapped Regionalliga items. 31 of them have
  no ground (`P115`) and no coordinates (`P625`) anywhere on the item, so
  they are dropped at the coordinates gate; 64 survive, and 61 reached
  the map once two were moved to tier 3 by hand and one duplicate was
  skipped. That was the 2026-09-18 figure. Since the `skip` row for
  `Q701290`, the second SSV Ulm item, the German file holds **68 clubs
  at tier 4** - the Regionalliga survivors plus the ones given
  coordinates by hand from `coordinate-review.csv` and europlan-online.
  The 31 are seven reserve teams (1. FC Köln II, FC Schalke 04 II,
  Hertha BSC II, Borussia Mönchengladbach II, FC Augsburg II,
  1. FC Nürnberg II, SpVgg Greuther Fürth II) and 24 first teams,
  including SV Rödinghausen, TSV Steinbach Haiger, FC Viktoria 1889
  Berlin, SV Heimstetten and FC Erzgebirge Aue. The gap is missing data
  in Wikidata, not a filter, so no change to the query will close it.
  What can close it is a second source, which is what
  `coordinate-review.csv` above offered for 28 of the 31 — and what
  europlan-online has now actually closed for 20 of them, two of which
  the review file could not place at all. Two more turned out to be
  clubs that no longer exist. See the entries above.
- **europlan-online as a second stadium source: the site has been read
  at last, and what it says about automated access is nothing.** Two of
  the three go/no-go questions are answered as of 2026-09-19, from the
  site itself, through the Actions-dispatch route — the sandbox still
  answers 403 to CONNECT for europlan-online.de, so a throwaway probe
  went into `build-clubs.yml` on a working branch and was dispatched
  three times. The probe read the legal and informational pages, plus
  the homepage and one country, league and ground page to see what
  robots directives those carry; it extracted no club or ground data
  and kept nothing. Both it and the temporary job were removed again in
  the same branch.
  - **There is no `robots.txt`. It is a 404.** Both
    `europlan-online.de/robots.txt` and
    `www.europlan-online.de/robots.txt` return **HTTP 404** with the
    server's generic 964-byte "404 Not Found" page — not an empty file,
    not a file with no rules in it, no file at all. So there is **no
    `User-agent` group, no `Disallow`, no `Allow`, no `Crawl-delay` and
    no `Sitemap` line**, for any user agent, because there is no file
    for them to be in. There is also no `sitemap.xml`.
  - **There is no terms-of-use page, and this was proved rather than
    assumed.** The site has exactly **four** pages that are not content:
    Impressum, Datenschutz, FAQ and Kontakt. Everything else guessed at
    — `?s=agb`, `?s=nutzungsbedingungen`, `?s=terms`, `?s=lizenz`,
    `?s=copyright`, `?s=disclaimer`, `?s=info`, `?s=hilfe`, `?s=regeln`
    — returns **HTTP 200 with the homepage**, and so does
    `?s=thisdefinitelydoesnotexist`. That is the site's fallback, not a
    page. The words "AGB", "Nutzungsbedingungen" and "Terms" appear
    **zero** times in the homepage HTML, and the footer links only to
    Bilder/Grounds hinzufügen, Fehler melden, FAQ, Presse, Kontakt,
    Impressum and Datenschutz. So the earlier session was right that
    `index.php?s=impressum` is generic legal boilerplate — and right to
    keep looking, because now we know there is nowhere else to look.
  - **Nothing on the site addresses automated or repeated access.** The
    **complete** text of all four pages was swept — 6,888 characters of
    Impressum, 42,931 of Datenschutz, 5,622 of FAQ, 4,436 of Kontakt —
    for some forty German and English terms: *untersagt, verboten,
    nicht gestattet, unzulässig, dürfen nicht, keine automatisierte,
    systematisch, massenhaft, Roboter, crawl, scrap, spider, harvest,
    data mining, rate limit, Zugriffsbeschränkung, nur für den
    persönlichen Gebrauch, gewerblich, kommerziell* and the rest.
    **Not one of them is there.** The handful of matches were substrings
    inside unrelated German words — "agb" inside
    *Datenübertragbarkeit*, "bots" inside *Botswana* in the country
    dropdown — and GDPR boilerplate about processing personal data.
  - **What the site does say is about copyright, not about access.** The
    Impressum carries the standard eRecht24 paragraph: content created
    by the operators is under German copyright, and "die
    Vervielfältigung, Bearbeitung, Verbreitung und jede Art der
    Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der
    schriftlichen Zustimmung des jeweiligen Autors". The Kontakt page
    says the usage rights in the photographs belong **exclusively to
    the person who submitted them** and that Europlan is not authorised
    to license them on. Both are about republishing, neither is about
    reading.
  - **The one robots instruction that does exist says "index, follow",
    and it must not be over-read.** Every page checked — homepage,
    country page, league page and a ground page — carries
    `<meta name="robots" content="index, follow">` and **no
    `X-Robots-Tag` header**. That is an instruction to search engines to
    index the page. It is not a grant of permission for anything else,
    and nobody should cite it as one.

  **So: it is silence, and silence is what it is.** The site expresses
  no rule about automated reading — it neither permits it nor forbids
  it, and there is no document on it that speaks to the question at
  all. A missing `robots.txt` conventionally means a crawler has no
  path-level rules to obey (RFC 9309), but that is a convention among
  crawlers, not permission given by this site. Do not write "the site
  allows it" anywhere. What is true is: **nothing there says not to.**

  **What silence does not settle, and it is the real question.** German
  law gives a database maker a right of its own (`§ 87a-b UrhG`,
  *Datenbankherstellerrecht*) against extracting a **substantial part**
  of a database, whether or not the individual facts in it are
  copyrightable — and a ground's coordinates and capacity are facts.
  Reading a few dozen pages to settle the 19 ambiguous coordinate rows
  and the 3 unplaceable clubs is a different thing from taking a
  country's worth of grounds for tier 5, and the difference is exactly
  what that right is about. Nothing found on the site answers it,
  because the site says nothing. This is flagged here as an open
  question and is **not** a finding — nobody involved is a lawyer, and
  it should not be settled by anybody guessing which side of "a
  substantial part" a plan falls on. The cheap way past it is to ask:
  the Kontakt page gives `info@europlan-online.de`, the site is run by
  four named people, and a short mail describing exactly what is wanted
  would replace all of this reasoning with an answer.

  **The third go/no-go criterion is answered, and the answer is yes.**
  Checked on 2026-09-19 across 38 ground pages read while settling the
  22 clubs below. Every ground page carries its position in the same
  place and the same shape — a Google Maps link,
  `maps.google.de/maps?q=(<lat>, <lon>)` — and a second, rounded copy
  in an `index.php?s=umkreis&lat=…&lon=…` link beside it. Precision is
  not the problem: most are 14–15 decimal places, which is a click on a
  map rather than a survey, and the four or five that matter are all
  there. Capacity is `Kapazität: 12.345` in the Stadiondaten block,
  German thousands separators, and the address sits above it under
  Anschrift with a postcode and town. Layout did not vary once across
  the 38.
  **What the pages do NOT carry is a coordinate for the club** — only
  for the ground. That is the right way round for this project, but it
  means the club-to-ground link is what everything rests on.

  **Notes for whoever does build the fetcher**, all measured on
  2026-09-19:
  - Everything redirects to `www.europlan-online.de`. nginx, PHP
    7.4.33, a `PHPSESSID` cookie on every response, and
    `Cache-Control: public, max-age=600`.
  - **A 200 from this site does not mean the page exists.** An unknown
    `?s=` value silently serves the homepage with HTTP 200. Any fetcher
    must check the content, never the status code.
  - The country page `index.php?s=land&id=1` is **504 KB** in one
    response and the homepage is 176 KB. Whatever is built should be
    slow and few-requests by design; there is no `Crawl-delay` to obey
    precisely because there is no file to put one in.
  - A real ground URL, confirmed live:
    `/stadion-gladbeck-vestische-kampfbahn/stadion-5093.html`.

  What was established earlier from a search engine's index of the
  site's own pages rather than from the pages has now been checked
  against the pages, and it was half right:
  - The URL shapes are real. A ground is `/<name>/stadion-<id>.html`,
    a league is `index.php?s=liga&id=<n>`, a country is
    `index.php?s=land&id=1`, and leagues go down to Kreisliga level.
    Germany's country page lists **2,382** league links, each labelled
    with its level in brackets — `NOFV-Regionalliga Nordost (4)` — so
    the level comes from the site rather than from reading a name.
  - **`/<ground>/verein/<clubId>` does not exist.** It was the one
    thing this entry was most confident about and it is wrong. Counted
    on 2026-09-19: **zero** links of that shape on the homepage, on the
    country page, on a league page or on a ground page. It was an
    artefact of a search engine's index, which is exactly why this
    entry said it was unverified — and the lesson is that an index can
    show you a URL the site does not itself link, or does not serve at
    all.
  - **The real club-to-ground link is better, not worse.** A league
    page is a table and every row pairs a club with the ground it plays
    at. In the row: the club is a `<span translate="no">`, the ground
    is a `<td class="liste_stadt">` link, the capacity is a
    `<td class="kapazitaet">`, and the row's own map-zoom control
    carries the position as `ol.proj.fromLonLat([lon, lat])`. So one
    league page gives club, ground, capacity and coordinates for every
    club in that division at once. A ground page then closes the loop
    from the other side: **"Vereine, die in diesem Stadion spielen"**
    names the clubs based there, with each one's current league and
    level. Both are the site's own assertion, not a name match.
  - **There is a search, and the form field is called `search`.**
    `index.php?s=search&search=<term>` — a plain GET, placeholder
    "Stadion / Verein suchen". It searches grounds, not clubs, so it
    answers "which grounds are in this town" and the ground page's
    club list is what picks between them. Five other parameter names
    were guessed first and every one of them returned the search page
    with no results rather than an error, which is the same trap as the
    `?s=` fallback: **this site answers a wrong question with a page,
    not with a 404.** Use a control term whose answer you already know.
  - The eight clubs the index had named were all confirmed against the
    site, and **the two it could not name are now named too**.
    FC Schalke 04 II is at the **Parkstadion** in Gelsenkirchen-Buer —
    the small current one, not the demolished 70,000 ground of the same
    name. 1. FC Nürnberg II is at the **Max-Morlock-Platz**, which is
    the one of the four Valznerweiher pitches that the club row points
    at. The index could not choose between the four; the club row does
    not have to, because the site itself made the link.
    Two of the eight also needed correcting in passing: Eutin 08's
    ground is the **Thies Hahn Arena**, which is the Eutina-Platz
    renamed and still at that URL, and Aue's is the **eins
    Erzgebirgsstadion**, whose URL still says `sparkassen-`.
  - Two of those eight are grounds OpenStreetMap never offered at all.
    The Gladbach II row proposed Borussia-Park and SparkassenPark, not
    the Grenzlandstadion; the Viktoria Berlin row offered ten Berlin
    stadiums, none of them Stadion Lichterfelde. If the site is right,
    it settles rows that no amount of name-matching against
    OpenStreetMap could settle.
  - The same breadth is also the risk: side pitches, old grounds and
    sports halls are separate entries — Aue alone returned six, and
    Valznerweiher four. Matching on a ground's name would be exactly as
    ambiguous as OpenStreetMap is. Only the club-to-ground link is
    worth anything here.
- **StadiumDB.com was evaluated as a second, OpenStreetMap-independent
  capacity source on 2026-09-19, to the same standard europlan-online
  got. It passes on terms and on format, and it fails on coverage —
  so it is not the tier-2 cross-check that was wanted.** Everything
  below was read from the site through the Actions-dispatch route; the
  sandbox answers 403 to CONNECT for `stadiumdb.com` the same way it
  does for Wikidata and europlan. **That 403 is this sandbox's egress
  policy, not the site refusing anything**, which is the opposite of
  the fcbayern.com case and must not be confused with it.
  - **There is a real `robots.txt`, and it permits this.** 33 bytes,
    `text/plain`, byte-identical on `stadiumdb.com`,
    `www.stadiumdb.com`, `stadiony.net` and `www.stadiony.net` (the
    www hosts redirect to the apex). In full:
    `User-agent: *` / `Disallow: /lay-gfx/`. One disallowed path, and
    it is the layout graphics directory. No `Crawl-delay`, no
    `Sitemap` line, and `sitemap.xml` and `sitemap_index.xml` are both
    404.
    **This is a stronger answer than europlan gave and the difference
    matters.** europlan has no `robots.txt` at all, so there were no
    path rules to obey and the conclusion had to be "nothing there says
    not to". StadiumDB *has* a crawl policy, and that policy allows
    every content path. That is permission of a narrow and specific
    kind — for crawling, under the robots convention — and it should
    not be stretched into permission for anything else.
  - **It 404s honestly, which europlan does not.** A bogus path returns
    a genuine HTTP 404 with an 11.5 KB error page, clearly distinct
    from the 54 KB homepage, at both `/xxx` and `/stadiums/xxx`.
    europlan answers an unknown `?s=` with the homepage and HTTP 200,
    so any fetcher there has to check content rather than status.
    Here the status code can be trusted.
  - **No `<meta name="robots">` on any page checked and no
    `X-Robots-Tag` header**, on the homepage, the stadium index or
    the about page. europlan carried `index, follow`; this carries
    nothing at all.
  - **There is no terms-of-use page, and the copyright page is empty.**
    The footer links to Copyrights on both sites. The English
    `/copyrights` is a **404**. The Polish `/prawa_autorskie` returns
    **HTTP 200 with no body text whatsoever** — 1,324 characters, every
    one of them navigation, the standard site blurb and the footer.
    `/faq` is the same: HTTP 200, no FAQ on it. `/privacy_policy` is a
    404 despite being linked, because those nav entries sit inside HTML
    comments in the markup, which is why a link-scrape finds URLs the
    site does not serve. `/contact_us` is real and names Grzegorz
    Kaliciak as founder and owner. `/o_serwisie` is real and is the
    site's history.
  - **The only statement of rights anywhere is the footer line**:
    "© 2001-now StadiumDB.com. All rights reserved." and its Polish
    twin "Wszelkie prawa zastrzeżone." A sweep of the full text of
    every non-content page on both sites for some forty English and
    Polish terms — *prohibit, forbidden, not permitted, automated,
    scrap, crawl, spider, harvest, data mining, systematic, bulk,
    rate limit, personal use, commercial, zabronione, niedozwolone,
    automatyczn, masowe, systematyczn, komercyjn, użytek osobisty,
    baza danych* and the rest — matched **nothing about access**. The
    two Polish hits were a gambling-licence disclaimer that appears in
    the footer of every page.
  - **So the open legal question is the same one europlan left open,
    and it is not settled here either.** The operator is Polish, and
    Poland implements the EU sui generis database right just as
    Germany does, so extracting a substantial part of the database is
    a different question from reading some pages, and `robots.txt`
    does not speak to it. Nobody involved is a lawyer and this is not
    a finding. The cheap way past it is the same: the contact page
    names the owner, and a short mail describing exactly what is
    wanted would replace the reasoning with an answer.
  - **The page format is the most consistent this project has
    evaluated.** 27 stadium pages were sampled across nine countries.
    Capacity, Country, City and Clubs were present on **27 of 27**.
    Inauguration on 23, Address on 21, Floodlights on 5. Layout did
    not vary.
    Better still, every page carries a single meta tag that holds the
    whole record:
    `<meta name="Description" content="Stadium: Stade des Costières,
    Nîmes, France, capacity: 18482, club: -." />`
    One regular expression over that line gives name, city, country,
    capacity and club, with no HTML parsing at all. The capacity in
    the page body uses non-breaking spaces as thousands separators
    ("18 482"); the meta tag gives it as a bare integer.
    A country page is even cheaper: it is one table,
    **Name | City | Clubs | Capacity**, and **every row named a club**
    — 69 of 69 for France, 109 of 109 for Germany, 314 of 314 for
    Poland. One request per country gives the whole country.
  - **What the pages do NOT carry is a coordinate. Zero of 27.** This
    is the structural problem, not a detail. `crosscheck_capacity.py`
    matches a club to a ground **by position, within 500 m,
    deliberately not by name**, and this project has already been
    bitten by name matching — Eutin 08 scored 0.5 against FC 08
    Homburg on the shared "08" alone. A StadiumDB cross-check cannot
    use the existing matcher and would have to match on club name plus
    city, which is the technique the coordinate matcher exists to
    avoid.
  - **Coverage is where it fails, and the numbers are the answer.**
    Counted from each country's own listing page:

    | country | stadiums | under 6,000 | under 12,000 | under 20,000 |
    |---|---|---|---|---|
    | France | 69 | 5 | 15 | 40 |
    | Italy | 69 | 7 | 18 | 36 |
    | Switzerland | **17** | 2 | 7 | 12 |
    | Austria | 27 | 8 | 17 | 23 |
    | Serbia | 29 | 11 | 20 | 26 |
    | Greece | 29 | 5 | 15 | 20 |
    | Germany | 108 | 5 | 18 | 63 |
    | Romania | 40 | 7 | 17 | 33 |
    | Poland | **314** | 246 | 278 | 302 |

    The whole database is **2,501 stadiums worldwide**, a figure the
    site prints on its own pages. Poland having 314 of them, against
    108 for Germany and 17 for Switzerland, is the shape of a Polish
    site that grew out of `stadiony.net` in 2001 and added an English
    edition in 2012. **Coverage is deep at home and thin abroad**, and
    that is the finding.
  - **Switzerland fails on arithmetic alone.** Seventeen stadiums in
    the whole country is fewer grounds than the Super League and
    Challenge League have clubs between them, so the second tier
    cannot be complete no matter which 17 they are. Austria at 27,
    Serbia at 29 and Greece at 29 are all in the same range as their
    top two divisions' club counts, which means at best bare coverage
    with no margin, and in practice less than that.
  - **A name-based smoke test agrees, and it was the author's own
    recollection rather than a source**, so it is corroboration and
    not evidence: second-tier club and town names were found for
    France 10 of 12 and Italy 10 of 12, but Switzerland 5 of 11,
    Serbia 4 of 10, Austria 3 of 7 and **Greece 2 of 10**. The two
    countries that pass the arithmetic are the two that pass the name
    test, which is what makes the pattern worth reporting.
  - **IT IS BUILT FOR GERMANY AND ROMANIA, 2026-09-20, and it earned
    its place immediately.** `tools/crosscheck_stadiumdb.py` reads
    `/stadiums/ger` and `/stadiums/rou` — both confirmed, and
    `/stadiums/germany`, `/stadiums/de`, `/stadiums/rom`,
    `/stadiums/romania` and `/stadiums/ro` are all genuine 404s — and
    writes `data/clubs/stadiumdb-review.csv`. First run: **109 German
    grounds against 146 clubs and 40 Romanian grounds against 64**,
    producing 27 rows needing an eye. Coverage is exactly as thin as
    this entry predicted: 81 of the 210 clubs matched at all.
    **What it caught that nothing else could.** Preußen Münster was on
    the map at **45,000** against a real 14,300 — and this entry already
    recorded that OpenStreetMap has no capacity for that ground, so the
    existing cross-check could never have found it. FSV Zwickau had no
    Wikidata figure at all and OpenStreetMap and StadiumDB agree exactly
    on 10,134. Borussia Dortmund II was carrying the first team's Signal
    Iduna Park and its 81,359, which StadiumDB exposed by naming Stadion
    Rote Erde for the reserve side separately.
    **And it was wrong three times in a way worth knowing about**, all
    three where StadiumDB matched a ground our club does not play at:
    FC ASA Târgu Mureș, 1. FC Magdeburg and FC Viktoria Köln, where our
    figure and Wikipedia's agree and StadiumDB is the outlier. The
    tool's own `?ground-unchecked` marker flagged the first of them
    before anyone looked. **A third opinion is a third opinion, not a
    tie-breaker.**
  - **So the verdict is: yes for France and Italy, no for
    Switzerland, Austria, Serbia and Greece.** (Switzerland and Austria
    were added to `crosscheck_stadiumdb.py` anyway on 2026-09-26, slugs
    `sui` and `aut`, each as a thin third opinion, never as agreement by
    silence - see their entries under Known open problems. Serbia
    followed on 2026-09-27, slug `ser`, and Greece on 2026-09-29, slug
    `gre`, on the same terms. **Spain, slug `esp`, 2026-09-30, was
    measured for itself rather than assumed, and is the other way
    round**: 89 grounds, and a StadiumDB ground for 40 of the 42 clubs in
    its two 2026-27 divisions - see the Spain entry. **England, slug
    `eng`, 2026-09-30, measured too, and as full**: 125 grounds, 41 of
    the 44 clubs in its two divisions, and the other three - the Welsh
    clubs - on `wal`, which the tool now reads for GB as well. **The
    Netherlands, slug `ned`, 2026-10-01, measured too, and as full**: 45
    grounds in two tables, a ground for 18 of 18 Eredivisie clubs and 16 of
    20 Eerste Divisie clubs, the four without being the Jong sides. **Belgium,
    slug `bel`, 2026-10-01**: 37 grounds; the matcher pairs 12 of the 31
    clubs and 19 go unmatched on short names, all read by hand in the
    Belgium pass.) As a second opinion on
    a ground StadiumDB happens to hold it is excellent — clean to
    parse, independent of both OpenStreetMap and Wikidata, and
    editorially curated rather than crowd-sourced. As the systematic
    tier-2 capacity cross-check for those six countries it does not
    have the data, and no amount of parsing will conjure it.
  - **What would fill the gap is already in hand.** The Wikipedia
    current-season article for a league carries a "Stadiums and
    locations" table with a capacity column, and its coverage is
    exactly the league being checked, by construction — there is no
    country where it is thin, because the table is the league. The
    roster check described under "Planned, not built" reads those
    tables anyway, so the capacity column is free once it exists: one
    source doing two jobs. europlan-online remains the deeper source
    for Germany and OpenStreetMap remains the position-matched one.
    StadiumDB is worth keeping as a third opinion for the top flights
    and for France and Italy, and is not worth building a pipeline
    around.
- Wikidata's Regionalliga season items carry no participant list
  (`P1923`) for any of the five divisions, so there is no way inside
  Wikidata to enumerate who should be in a division and compare it
  against what came back.
  **That was measured across seven countries on 2026-09-19 and it is
  worse than the Regionalliga note suggested.** The latest season item
  of each league was found through `P3450` and its `P1923` count
  taken. **Zero participants** on the current season of the
  Bundesliga (`Q138320695`, starts 2026-08-28), the Romanian SuperLiga
  (`Q140134051`), Liga II, Liga III, the Austrian Bundesliga
  (`Q138946873`), the Serbian SuperLiga, the Swiss Super League
  (`Q138975892`) and the Challenge League. The only two leagues with
  any participants at all are stale: 2. Bundesliga last has 18 on a
  **2022-07-15** season, 3. Liga 19 on a **2024-08-02** one.
  So `P1923` cannot be the roster source for any tier, in any of these
  countries. This is a shame rather than a detail, because it is the
  only candidate that would have returned **Q-ids** and so joined to
  the club layer with no name matching at all.
  `P3983` (league level) is no better as a way in: asked for every
  league in France, Italy, Switzerland, Austria, Serbia and Greece at
  level 1 or 2, it returns **six leagues**, none of them French or
  Italian, and **two of the six are women's competitions**, which rule
  6 excludes anyway.
- Wikidata's `P3983` (league level) is not set on Bundesliga, so it
  cannot be the sole source of tier data. It can generate a draft of
  `league-tiers.csv` for review, which is the plan for expanding beyond
  Germany and Romania.
- **OpenLigaDB is wired up, 2026-09-24, and it covers less of the
  Regionalliga than this file used to assume.** This entry used to say
  it "would cover 2. Bundesliga, 3. Liga, DFB-Pokal and Regionalliga".
  Three of the four are true. The fourth is **two of five divisions**.
  Read from the API on a GitHub runner, because the sandbox answers 403
  to CONNECT for `api.openligadb.de` the same way it does for Wikidata.
  - **The API.** Base `https://api.openligadb.de` (the old
    `https://www.openligadb.de/api` still answers identically).
    `getavailableleagues` lists every league (832 on the day);
    `getmatchdata/<shortcut>/<season>` gives one league-season's
    matches; `getavailableteams/<shortcut>/<season>` its teams. Season is
    the **start year**: `2026` is 2026/27. Keyless.
  - **The shortcuts used, and what came back on 2026-09-24:**

    | shortcut | OpenLigaDB's name | matches | played | teams | crests |
    |---|---|---|---|---|---|
    | `bl2` | 2. Fußball-Bundesliga 2026/2027 | 306 | 54 | 18 | 18 |
    | `bl3` | 3. Liga 2026/2027 | 380 | 69 | 20 | 20 |
    | `dfb` | DFB Pokal 2026/2027 | 48 | 32 | 64 | 64 |
    | `rln` | Fußball-Regionalliga Nord | 306 | 90 | 18 | 18 |
    | `rlno` | NOFV Regionalliga NordOst | 306 | 90 | 18 | 18 |

    The Pokal's 48 is the first round (32, played) and the second (16,
    scheduled); later rounds appear once they are drawn.
  - **The Regionalliga is five divisions and OpenLigaDB carries two of
    them this season.** Nord and Nordost are complete. **Bayern** is a
    stub, `regio-bayern`: four teams, no matches — the tool watches it
    and says so, and starts writing a file the day it fills.
    **West and Südwest are not there under any name** — the full 2025
    to 2027 league list was read, not searched for a guessed code.
    West was carried in some past seasons (`rlw` 2023, `RLW` 2024) and
    not in others, which is the shape of this site: its leagues are
    maintained by volunteers, season by season.
  - **Its league list is community-edited, and that is the founding
    assumption that was most wrong.** Anyone can create a league: the
    list carries test leagues, darts, ice hockey, and **copies** — `bl2h`
    is a second 2. Bundesliga 2026/27 with the same 306 fixtures and no
    results entered. So the tool **names its shortcuts by hand** and
    never picks one by matching a league name.
  - **"Nothing" looks like success.** `getmatchdata` answers **HTTP 200
    with `[]`** for a shortcut that does not exist at all. So an empty
    answer is a failed fetch, the last good file is kept, and the run
    goes red — exactly the rule this project already had, applied to an
    API that would otherwise make it easy to break.
  - **A missing kickoff is written as `1970-01-01`.** Seen in a women's
    league, not in any of ours today; the tool reads it as "no date",
    leaves the field blank and counts it.
  - **There is no match status**, only `matchIsFinished`, so the files
    say `finished: true/false` and nothing is invented to fill
    football-data.org's `SCHEDULED`/`POSTPONED`. The final score is the
    result OpenLigaDB labels `Endergebnis` and nothing else.
  - **Stadium is mostly absent**: 0 of 380 3. Liga matches carry one.
  - **Crests: a URL on every team, and not a licensing answer.** 138
    team entries, 138 with a crest. They are hotlinks to wherever each
    image was found — 116 to `upload.wikimedia.org`, 13 to `i.imgur.com`,
    4 to `derivates.kicker.de`, and single ones to fussballdaten.de,
    dfb.de, bundesliga-reisefuehrer.de and openligadb.de. Many of the
    Wikimedia ones will be the non-free crests the badge item already
    rules out. So for badge work it is a second **list of URLs**, not a
    second **source of usable images**; each would need its own licence
    checked. The run summary prints this breakdown every day.
  - **The ids are OpenLigaDB's own** and share nothing with
    football-data.org's or Wikidata's. Joining a team to a club on the
    map is not done and would need its own matching step.

---

## Planned, not built

1. ~~A ticket-info file~~ **— the files exist now.** `club-tickets.csv`,
   `club-ticket-windows.csv` and `club-ticket-prices.csv` are described
   under Files and Conventions above, and FC Bayern's men's team is the
   first and so far only entry. **Stable facts only — a specific
   match's sale date or deadline still stays hand-written by Alexandru,
   and none of the three files has a column that could hold one.** The
   one date-shaped thing they do carry is a *pattern* estimate of when a
   recurring window tends to open, which is a different claim from a
   deadline and carries its own `dateSource` and `basis` saying how much
   to trust it.
   **The reader is built.** `tools/check_tickets.py` parses all three,
   prints back every accepted row exactly as understood, and names every
   rejected row with its line number, so the read-back convention is
   honoured for them now. It rejects a row whose `dateSource` or `basis`
   is not one of the listed values, which is what this entry asked for.
   It never writes to any of the three files, and it exits 1 on a
   problem so a workflow step shows red rather than a green tick. See
   the Conventions entry on it above.
   **What is still not built is the display.** `index.html` does not
   show any of these files. Item 2 below is where that belongs.
   **Five clubs since 2026-10-07**: VfB Stuttgart was researched for an
   outside buyer (Conventions, "VfB Stuttgart, 2026-10-07").
   **Four clubs since 2026-10-06**: Karlsruher SC was researched for an
   outside buyer (Conventions, "Karlsruher SC and Germany's first
   national rows").
   **Three clubs now, not one.** 1. FC Nürnberg and Inter were added on
   2026-09-23 from the derby PDF, and the four files that took to hold
   them — phases, rules, demand, sources — are described under Files
   and Conventions above.
2. ~~Club detail sheet~~ **— built 2026-09-25**, with the fixture
   join it needed. See `index.html`, `link_fixtures.py` and the
   Conventions entry. **Not linked on purpose:** the hand-written
   `clubs` in `football-rules.json` (VfB, KSC, FCK, Kickers, Poli,
   UTA, Dumbrăvița …) carry ticket procedures but no Q-id, so the sheet
   did not show them *(since 2026-10-03 it does, through
   `data/football-rules-links.csv`, on Alexandru's instruction - see
   Files)* — joining them by name, or adding a Q-id to a
   file whose structure is decided, is Alexandru's call.
3. ~~Search box on the map~~ **— built 2026-10-03**, top right; see the
   Conventions entry "Club search".
4. Badges. 284 crest URLs already sit unused in `data/fixtures/`.
   Wikidata `P154` covers German clubs patchily and Romanian ones barely.
   Licensing is unresolved: only freely licensed images may be used on a
   public site, and Wikipedia's non-free crests may not. Fallback is a
   generated marker — club colours plus initials.
5. ~~Revamped bucket list and ticket info tabs, plus a fourth tab for
   memberships and tickets already held~~ **— built 2026-10-04**: the
   tabs in "Ticket info and the Bucket list" and "The Bucket list: List,
   Calendar, favorites", the fourth tab in "The Me tab" (Conventions).
6. Expansion to more countries, one at a time.
7. ~~The official-roster check~~ **— built 2026-09-20, and everything
   below is the design it was built to.** `tools/check_rosters.py` and
   `data/league-rosters.csv` exist; the first real run against all
   eleven mapped German and Romanian leagues is written up under Known
   open problems above. Every design decision below held up: the
   Wikipedia season article is one shape across all of them, the
   sitelink hop means no club name is ever matched against another, and
   the two guards both earned their place on the first day — the
   sitelink guard by catching a silent total failure, and "do not
   hardcode league sizes" by letting the 3. Liga's real membership come
   back as 20 rather than as whatever a constant said.
   **Three things the design did not anticipate**, all recorded above:
   a season article often links a club through a **redirect**, which has
   no Wikidata item and read as "no Wikidata item" until the tool
   learned to follow them; a **league table** is the only membership
   list on the Regionalliga and Liga III pages, so the parser needed a
   second table shape; and Wikidata keeps a **club item and a men's
   first team item** for many German clubs, which makes one club look
   like two.
   **A fourth thing it did not anticipate, and this one changed another
   tool.** The design lists three kinds of "missing" and gives each a
   remedy. There is a **fourth**: a club whose `P118` names a mapped
   league on a statement `wdt:P118` will not yield, because a
   preferred-rank statement asserts no league on top of it. It is not
   "absent from Wikidata's answer" in the sense the design meant — the
   league tag is right there on the item — and no hand row could reach
   it, because `apply_manual`'s guard rejects a `clubQid` that is not
   in the fetched clubs. The remedy turned out to belong in
   `fetch_clubs.py` rather than here: the **novalue fallback**, which
   uses this tool's own `roster_qids()` to decide whether to read
   through the suppression. So the roster check now answers a question
   for the club builder as well as reporting on it.
   **The original design note follows, unchanged**, because the
   reasoning is why the tool looks the way it does.

   **The official-roster check — designed 2026-09-19.**
   Every accuracy pass this project has runs on what is already on the
   map: `crosscheck_capacity.py` compares figures for clubs it has,
   `country-review.csv` flags clubs that reached the wrong file,
   `coordinate-review.csv` places clubs it knows about. **Nothing
   anywhere asks whether a club that should be there is missing**, and
   a club absent from the club query leaves no trace to find. The
   roster check is the pass that asks the question from the league's
   side: here is the division's actual current membership, does the
   pipeline have all of it.

   **The counts already say something is wrong, and that is the
   motivation.** Germany is 18 at tier 1, 18 at tier 2 and **22 at
   tier 3**, where the 3. Liga fields twenty. Romania is 16 at tier 1,
   **16 at tier 2** where Liga II fields around twenty-two, and **32
   at tier 3** where Liga III fields something near a hundred across
   its series. Those gaps are invisible today because nothing compares
   the club layer against a membership list.

   **Three different things are being called "missing" and they want
   three different remedies**, which is why the check reports a verdict
   per club rather than a count:
   1. **Absent from Wikidata's answer** — no `P118`, or a `P118` naming
      a league not in `league-tiers.csv`. The pipeline cannot see the
      club at all. Remedy: an add row in `clubs-manual.csv`.
   2. **In the answer, dropped at the coordinates gate** — the
      documented case of the 31 Regionalliga clubs with no `P115` and
      no `P625`. The pipeline knows the club and cannot place it.
      Remedy: the route that already exists, `coordinate-review.csv`
      and then europlan.
   3. **Present at the wrong tier** — a stale `P118` from last season.
      Not absent from the file, absent from its division. Remedy: the
      `tier` cell in `clubs-manual.csv`.
   A bare count cannot tell these apart, and worse, **a count can come
   out right while the membership is wrong** — one club promoted in and
   one relegated out, both mistagged, cancel exactly.

   **The source: Wikipedia's current-season article, and the reason is
   measured rather than preferred.** `P1923` was tried first, because
   it would have returned Q-ids and needed no name matching at all, and
   it is empty — see the entry under Known open problems. League
   official sites were rejected as the backbone for the opposite
   reason: they are authoritative and every one of them is a different
   site in a different language with a different layout, several of
   them rendered in the browser, so six countries means six brittle
   parsers and a silent breakage looks exactly like "every club is
   missing". Wikipedia's season articles are one shape in one language
   across all of them. Tested on 2026-09-19 with a single generic
   parser — find the first `wikitable` whose header mentions a stadium
   or venue and a capacity, take the first linked article in each row:

   | article | clubs parsed |
   |---|---|
   | 2026–27 Bundesliga | 18 |
   | 2026–27 2. Bundesliga | 18 |
   | 2026–27 Ligue 2 | 18 |
   | 2026–27 Serie B | 20 |
   | 2026–27 Swiss Challenge League | 10 |
   | 2026–27 Serbian First League | 16 |
   | 2026–27 Super League Greece 2 | 16 |

   **Seven of nine on the first attempt.** The two that failed —
   Austrian 2. Liga and Romanian Liga II — failed on the **article
   title**, not on the table: nothing was found under the titles
   guessed for them. That is the failure mode a hand-written config
   column fixes once and for good, and it is exactly the kind of thing
   this project already hand-writes rather than infers.

   **The en dash is not optional.** The articles are `2026–27`, not
   `2026-27`. The probe tried both and only the en dash resolved.

   **Name matching is avoided by hopping through the sitelink.** A
   Wikipedia row gives an article title; `wbgetentities` with
   `sites=enwiki` turns that title into a **Q-id**, which joins to the
   club layer exactly. So the comparison is id-to-id even though the
   source is an HTML table, and none of the fuzzy matching that put
   Eutin 08 next to FC 08 Homburg is needed. This is the same sitelink
   machinery the SSV Ulm question already used.

   **What it would write.** `data/clubs/roster-review.csv`, in the
   column order of `clubs-manual.csv` followed by underscore-prefixed
   diagnostics, the same shape as `capacity-review.csv` and
   `coordinate-review.csv` so an accepted row pastes straight across.
   `_verdict` carries one of the five outcomes: `ok`, `missing-from-
   wikidata`, `unplaced-no-coordinates`, `wrong-tier`, `extra-not-in-
   roster`. It **reads and never writes** to any club file, and it
   reports rather than corrects, because deciding which of the three
   remedies applies is a judgement — the SSV Ulm case is the standing
   proof that two items on one ground can want opposite answers.

   **Two guards it must have, both from mistakes this project has
   already made.** First, **a source that returns nothing is a failed
   fetch, not an empty league**: if the article is missing or the table
   does not parse, the run keeps the last good review file and says so
   in the summary, the rule `capacity-review.csv` and
   `unmapped-leagues.csv` already follow. A parser that silently
   returns zero clubs would otherwise report an entire division as
   missing, with a green tick. Second, **it must not hardcode league
   sizes.** The expected membership comes from the source; writing "the
   3. Liga has 20 clubs" into the tool would be inventing the very fact
   the check exists to obtain.

   **Where two sources are wanted.** Following the capacity
   cross-check's own rule — where two independent sources agree the
   figure is almost certainly right and the row is left out — a club
   should be reported as genuinely missing when **the roster source and
   a second source agree it is in the division**. football-data.org is
   already wired up and its token is already in Actions secrets, and it
   gives a real team list per competition; its free tier reaches the
   top flights and not the second tiers, so it confirms tier 1 and
   stays silent below. OpenLigaDB would do the same job for Germany's
   2. Bundesliga, 3. Liga and Regionalliga and is still not wired up.
   Where only one source speaks, the row says so rather than being
   suppressed or promoted.

   **The per-league configuration is one small hand-written file**,
   `data/league-rosters.csv`, rather than a change to
   `league-tiers.csv`, so no existing hand-written file's schema moves:
   `leagueQid`, `country`, `tier`, `season`, `article`, `note`. The
   `season` cell is hand-written because deriving "2026–27" from the
   date is an inference that is wrong for weeks every summer, and the
   `article` cell is what fixes Austria's and Romania's titles. One
   line per league, edited once a year.

   **The capacity column comes free.** The table the check reads for
   membership is the "Stadiums and locations" table, which carries a
   capacity per club. Since StadiumDB turned out not to cover the
   second tiers of Switzerland, Austria, Serbia or Greece, this is the
   better answer to the capacity question too: the coverage is the
   league by construction. Whether to use it that way is a separate
   decision and nothing here assumes it.

   **What this does not do.** It says nothing about tier 4 and below,
   where no season article reliably exists and where Romania's Liga III
   would need its series enumerated. It cannot see a club that both
   sources miss. And it is a check on *membership*, not on grounds,
   capacities or coordinates — a club can be correctly listed and still
   be sitting on the wrong pin.

Every change must actually land in the repository. Write files to disk, commit them, and push the branch — do not finish a task with changes left only in the working tree or described in the reply. When the task is done, state which files were committed and what the branch is called, so the diff can be reviewed.
8. ~~Country-level ticket rules~~ **— built 2026-09-24.** The file,
   the checker change and the `country` column on `club-tickets.csv`
   landed together, and Italy's rows were **moved** out of Inter's
   (legal framework, named tickets, and the national half of the
   residency-limits row; its club half — Inter's 2025-26 derby had no
   limit — stayed a derby-home row). Two things the checker now says
   out loud that it could not before: the Inter–Milan **away** leg gets
   **no** national layer, because `Q1543` has no ticket row and no
   Italian club file exists, so nothing records the venue country; and
   `appliesTo` is `unknown` on all four Italian rows, because no source
   names which competitions the rules cover. The design text below is
   kept as written.
   **Country-level ticket rules — designed 2026-09-23.**
   `data/country-ticket-rules.csv`: rules no club decides
   and every club in a country inherits — Italy's named tickets,
   fidelity-card requirement for high-risk matches and reserved sectors,
   and Osservatorio/Questura residency limits are the model case, today
   written as Inter's rows in `club-ticket-rules.csv` lines 28–30. The
   full design, including **where a fact belongs when it could sit in
   either file**, is in `docs/country-ticket-rules-design.md`. The short
   version of the boundary: the requirement is the country's, the
   implementation is the club's; one fixture's facts are neither; a club
   doing something is never evidence the country requires it; and when
   in doubt a fact stays in the club file, because a wrong country row
   silently applies to every club in that country. The file does not
   exist yet on purpose — it lands together with the checker change,
   or a hand-written file would go unread. Four open questions in that
   document are Alexandru's to answer first.
