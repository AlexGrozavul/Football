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
  row without one adds a club. Same column set as `capacity-review.csv`.
- `data/league-tiers.csv` — maps a league's Wikidata Q-id to a tier.
  Tier comes from this file and never from a league name: Wikidata's
  league items are fragmented and undated, so names cannot be trusted.
  `skip` in the tier column excludes a league.

### Generated — safe to overwrite

- `calendars/*.ics`, `calendars/skipped.md`, `calendars/.stamps.json`
- `data/fixtures/*.json` — football-data.org, one file per competition
- `data/clubs/*.json` — Wikidata plus manual corrections
- `data/clubs/unmapped-leagues.csv` — seed list for `league-tiers.csv`
- `data/clubs/capacity-review.csv` — disagreements for Alexandru to judge

### Code

- `index.html` — the whole app. Single file, no framework, Leaflet from
  CDN, three tabs: map, bucket list, ticket info.
- `tools/build_calendars.py` — `.ics` generation
- `tools/fetch_fixtures.py` — football-data.org
- `tools/fetch_clubs.py` — Wikidata club layer
- `tools/crosscheck_capacity.py` — OpenStreetMap capacity comparison

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

**Past dates drop out of calendars but stay in the JSON.** The file is
the history and the anchor for next year's estimate; the calendar is only
what lies ahead.

**Six feeds plus admin**: `bayern`, `germany-nt`, `local`, `italy`,
`romania`, `uefa-finals`, `admin`. `local` means within day-trip range of
Leonberg, not a fixed list of clubs. `bayern` is a loyalty feed and stays
separate even though Munich is also day-trip range. Hand-entered fixtures
go to `fixtures-<feed>.ics`, never into the ticket-window feeds.

**Distance** is straight-line times `settings.estimateMultiplier` (1.25).
No routing API. It is a road-distance estimate and is deliberately not
converted into a travel time, because that would need an invented average
speed.

---

## Secrets

`FOOTBALL_DATA_TOKEN` is in Actions secrets. It must never appear in
client code, in `data/`, or anywhere under `calendars/`. No other key is
needed: Wikidata, Overpass and OpenLigaDB are all free and keyless.

---

## Known open problems

- Hamburger SV appears twice in the club layer (`Q51974` at tier 1 and
  `Q97905930` at tier 2). `clubs-manual.csv` can override a club but not
  remove one; it needs a `skip` value in the tier column.
- Three clubs are missing from the German layer entirely: SV Meppen,
  Erzgebirge Aue, 1. FC Schweinfurt.
- FC Unirea Dej has plainly wrong coordinates in Wikidata — placed near
  Bucharest, roughly 300km from Dej.
- Several capacities are wrong in Wikidata (Preußen Münster, Fortuna
  Düsseldorf, 1. FC Saarbrücken among them). The cross-check tool exists
  to surface these; it has not been run for real yet.
- About 37 Regionalliga clubs are missing, probably reserve teams typed
  oddly in Wikidata. Dropping the type filter from the club query may
  have fixed this — unverified.
- Wikidata's `P3983` (league level) is not set on Bundesliga, so it
  cannot be the sole source of tier data. It can generate a draft of
  `league-tiers.csv` for review, which is the plan for expanding beyond
  Germany and Romania.
- OpenLigaDB is not yet wired up. It would cover 2. Bundesliga, 3. Liga,
  DFB-Pokal and Regionalliga. Bundesliga is deliberately excluded there,
  since football-data.org already covers it and two sources would mean
  reconciling two sets of ids.

---

## Planned, not built

1. `skip` support in `clubs-manual.csv`
2. A ticket-info file: official ticket page, whether a club sells to
   non-members, typical price range with the season noted, how demand
   behaves, whether matches sell out. **Stable facts only — sale dates
   and deadlines stay hand-written by Alexandru.**
3. Club detail sheet: a pull-up panel replacing the map popup, showing
   name, ground, capacity, competition name with tier in brackets,
   distance, fixtures and ticket info, each saying "unavailable" rather
   than being hidden when there is nothing.
4. Search box on the map, top right, live matches, enter flies to the club.
5. Badges. 284 crest URLs already sit unused in `data/fixtures/`.
   Wikidata `P154` covers German clubs patchily and Romanian ones barely.
   Licensing is unresolved: only freely licensed images may be used on a
   public site, and Wikipedia's non-free crests may not. Fallback is a
   generated marker — club colours plus initials.
6. Revamped bucket list and ticket info tabs, plus a fourth tab for
   memberships and tickets already held: cost, renewal date, benefits.
7. Expansion to more countries, one at a time.

Every change must actually land in the repository. Write files to disk, commit them, and push the branch — do not finish a task with changes left only in the working tree or described in the reply. When the task is done, state which files were committed and what the branch is called, so the diff can be reviewed.
