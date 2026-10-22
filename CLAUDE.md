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

**8. Sale dates are currently shown nowhere in the app.** Since 2026-10-07
the map's club sheet and the Ticket info tab show no sale date (no "Next
window" line, no window's "Typically opens" or past-cycle line), and since
2026-10-08, on Alexandru's instruction, **the Bucket list's Reminders
section is gone too**: no `ticketEvents` entry is drawn on the List, inside
a bucket entry or on the calendar, so no dated sale or deadline from
`football-rules.json` is shown anywhere. **The data is kept**: every
`ticketEvents` entry, every ticket CSV and `calendars/local.ics` (which is
built from those entries, not from the page) are unchanged. The one piece
of sale timing still drawn is the month-level "Typically opens" pattern of
`club-ticket-windows.csv` inside a club block of a Bucket list entry - a
loose-text estimate, not a dated entry - and it stays until he says
otherwise. **A hand-written dated sale or deadline entry** (a `ticketEvents`
entry of `football-rules.json` with a date) **still needs a source URL
(`source`) and a `checkedOn` date**, shown or not, and
**nothing fetches or verifies them automatically**.
`tools/check_sale_dates.py` lists, offline and as warnings only (it always
exits 0), the dated entries missing either field, those whose date passed
more than 14 days ago, and those whose `checkedOn` is over 30 days old
while the date is still ahead; `build-calendars.yml` runs it. Existing
entries have neither field yet: the warnings are the to-do list, and no
value was filled in for them (rules 1 and 2).

**9. Competition info is hand-written, and every row needs a source and a
checked date.** Added 2026-10-08. `data/competitions.csv`,
`data/competition-info.csv` and `data/competition-sources.csv` are never
written by a script and **fetched data never becomes competition info
automatically**: `data/fixtures/`, the OpenLigaDB files and the club layer
may seed a competition's *name* once, never a format, a qualification rule
or a date. Every info row carries `sourceId` and `checkedOn`; a row without
either is a warning, not a pass. **Rules change between seasons**, which is
why every row says when it was checked and `check_competitions.py` warns
past 365 days. **Schedule rows are month level and `inferred` only**
(topic `schedule-announcement`: who announces dates and kick-offs and
roughly when, `basis` `observed-past-cycle`); a day-level date in a text
cell fails the checker, because a plausible-sounding wrong date is worse
than a blank. A page that could not be opened is read from the search
result and the row says `unverified`, never `confirmed`. A competition
with no info row shows "Not researched yet".

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

Index only. The full per-file and per-tool entries (columns, rules, history) are in `docs/claude/files.md`; grep that file for the path before changing or reading any of these.

### Hand-written — never write to these from a script

- `data/football-rules.json` — ticket rules, bucket list, clubs, settings; the irreplaceable file, structure decided
- `data/fixtures-manual.csv` — fixtures Alexandru enters himself, mostly Romanian (required: date, home, away, feed, dateSource)
- `data/clubs-manual.csv` — corrections and additions to the club layer; `skip`, `<clear>`, `allowDissolved`, hand-named fallback
- `data/league-tiers.csv` — maps a league's Wikidata Q-id to a tier; `skip` excludes a league
- `data/club-tickets.csv` — one row per club per team: who may buy, allocation, cutoff, demand, resale; never a date
- `data/club-ticket-windows.csv` — one row per club per sales window; the only place a month-level pattern estimate may live
- `data/club-ticket-prices.csv` — face values and observed resale prices, per season, competition, stage, category, kind
- `data/club-ticket-phases.csv` — one row per phase of a window; only a sourced past date (`pastCycle`) may be day-level
- `data/club-ticket-rules.csv` — one sourced fact per row with confidence, basis, ref; general and derby scopes
- `data/club-ticket-demand.csv` — sell-out track record per club, fixture and season
- `data/ticket-sources.csv` — every citation as its own row (publisher, kind, title, date, URL)
- `data/country-ticket-rules.csv` — rules no club decides, inherited by every club in the country
- `data/fixture-links-manual.csv` — hand corrections to which fixture-source team a map club is; wins over `link_fixtures.py`
- `data/league-rosters.csv` — which Wikipedia season article holds each league's membership (en dash required)
- `data/roster-links-manual.csv` — which Q-id a season-table row is, where the table cannot say
- `data/coordinate-reviews.csv` — what a person already decided about a row of `coordinate-review.csv`
- `data/derbies.csv` — one row per derby, each with a source that names the rivalry
- `data/football-rules-links.csv` — which map club each `clubs` entry of `football-rules.json` is
- `data/event-ticket-rules.csv` — ticket rules for one bucket-list entry (header only so far)
- `data/bucket-links-manual.csv` — which clubs a bucket entry names, and which entry a ticket event belongs to
- `data/holidays-manual.csv` — Baden-Württemberg school holidays for the Bucket list calendar, exactly the rows he gave
- `data/competitions.csv` — one row per competition (id, name, country, level, type)
- `data/competition-info.csv` — hand-written competition info; every row needs `sourceId` and `checkedOn`
- `data/competition-sources.csv` — sources for competition info
- `data/club-rivalries.csv`, `data/club-culture-sources.csv` — hand-written rivalries (class from the source's wording) and their shared sources
- `data/club-friendships.csv` — hand-written fan friendships, each with a source quote
- `data/club-parents.csv` — which map club is the first team of a reserve side on the map
- `data/attended.json` — the matches and events Alexandru attended; never written by the page

### Generated — safe to overwrite

- `calendars/*.ics`, `calendars/skipped.md`, `calendars/.stamps.json`
- `data/fixtures/*.json`, `data/fixtures/openligadb-*.json` — football-data.org and OpenLigaDB fixtures
- `data/clubs/*.json` — Wikidata plus manual corrections
- `data/clubs/unmapped-leagues.csv`, `capacity-review.csv`, `coordinate-review.csv`, `country-review.csv`, `stadiumdb-review.csv`, `fixture-link-review.csv`, `roster-review.csv` — review files for Alexandru to judge
- `data/clubs/fixture-links.json` — which fixture-source team each map club is
- `data/clubs/proposal-<CC>.csv`, `.md` — evidence for adding a country, never a decision

### Code

- `index.html` — the whole app, single file, no framework; tabs, club sheet, route panel, Near me, search, coverage, Me tab
- `manifest.webmanifest`, `sw.js`, `icons/`, `vendor/leaflet-1.9.4/` — the installable app; change `SHELL_VERSION` when `sw.js` changes
- `sheetDrag()` in `index.html` — all sheets and panels share one expand-to-full mechanism; a new `.sheet` must use it
- `tools/fetch_clubs.py` — Wikidata club layer and its fallbacks (novalue, stale-preferred, hand-named)
- `tools/fetch_fixtures.py`, `tools/fetch_openligadb.py` — fixture fetchers (never the Bundesliga from OpenLigaDB)
- `tools/link_fixtures.py` — joins fixture-source teams to map clubs, by name equality, never in the page
- `tools/build_calendars.py` — `.ics` generation, byte-identical when nothing changed
- `tools/crosscheck_capacity.py`, `tools/crosscheck_stadiumdb.py` — capacity opinions from OpenStreetMap and StadiumDB
- `tools/propose_coordinates.py` — OpenStreetMap coordinate proposals for clubs Wikidata cannot place
- `tools/check_rosters.py` — the roster check, from the league's side; exports `roster_qids()`
- `tools/diagnose_p118_rank.py` — which clubs the truthy `wdt:P118` join hides, by rank shape A, B and C
- `tools/propose_country.py`, `tools/propose_grounds.py`, `tools/test_propose_country.py` — read-only evidence for adding a country; measured accuracy is in files.md
- `tools/check_tickets.py` — read-back and checks for the ticket files; exits 1 on a problem
- `tools/check_derbies.py`, `tools/check_holidays.py`, `tools/check_competitions.py`, `tools/check_translations.py`, `tools/check_club_culture.py` — read-backs of the hand-written files they name
- `tools/check_sale_dates.py` — warnings on dated `ticketEvents` entries (rule 8); always exits 0
- `tools/test_*.js` — headless Chromium tests of the page (pwa, derbies, nearme, routes, zoom, search, coverage, sheet_tickets, layout, legend, tickets_bucket, calendar, me, ksc_tickets, vfb_tickets, competitions)
- `.github/workflows/test-pages.yml` — runs the page tests and the checks on a change to the page or its tests

## Where the long entries live

The long entries were moved out of this file on 2026-10-22 so that it stays small (it is read on every request). Nothing in them was changed.

- `docs/claude/files.md` — the full per-file and per-tool entries (Files: hand-written, generated, code).
- `docs/claude/conventions.md` — "Conventions the tools rely on" with all sub-entries, "Adding a country: the places to touch", and the full Secrets text (Stadia key, domain auth, caching terms).
- `docs/claude/open-problems.md` — "Known open problems": every country pass, measurement and open question.
- `docs/claude/planned.md` — "Planned, not built".

Rule for new text: long new entries go into the matching `docs/claude` file; CLAUDE.md keeps only rules and one-line index lines. Every prompt names the file to grep (for example "grep docs/claude/conventions.md for 'Tier zoom bands'"), and nobody reads those files whole.

---

## Secrets

`FOOTBALL_DATA_TOKEN` is in Actions secrets and must never appear in client code, in `data/`, or anywhere under `calendars/`. No other key is needed: Wikidata, Overpass and OpenLigaDB are free and keyless. Since 2026-10-03 the page carries no Stadia Maps key either; map tiles, routing and place search are authenticated by the domain `alexgrozavul.github.io` in the Stadia dashboard. Stadia's caching and storage terms, the measurements and what the service worker may never save are in `docs/claude/conventions.md` under "Secrets"; read them before changing tiles, routes or searches.

---

## Session cost rules

Every request re-reads this file, so a session spends money by reading, polling and printing.

1. Prefer the gh CLI or curl with --jq, grep, head and wc over GitHub MCP tools; list at most 30 items from GitHub; never print a workflow log: download it and grep it.
2. No tool output over about 80 lines enters the context; use head, grep -m, wc -l, awk; write long output to /tmp and read only what is needed.
3. Never poll a running workflow: wait with one blocking background command (gh run watch) or a check-in at least 10 minutes later.
4. After each numbered part, post its results to Alexandru as a message at once, and keep notes in /tmp/notes.txt, so nothing is lost if the context is compacted.
5. Do not re-read a file already read; no whole-file reads of index.html or of any CSV over 200 lines.
6. Stop at about 120 tool calls: report what is done and what is left.
7. End the session when the report is written.

Delivery (copied unchanged from the end of the old file): Every change must actually land in the repository. Write files to disk, commit them, and push the branch — do not finish a task with changes left only in the working tree or described in the reply. When the task is done, state which files were committed and what the branch is called, so the diff can be reviewed.
