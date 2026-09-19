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
  row without one adds a club; `skip` in the tier column removes one,
  which is how a duplicate Wikidata item is dropped, and also how a club
  that only reaches the map through a wrong league tag is removed — SC
  Veltheim is the second kind. A `skip` row needs a `clubQid`, because
  there has to be something already there to remove, and every other
  cell on it is ignored. Same column set as `capacity-review.csv`.
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
- `data/clubs/coordinate-review.csv` — proposed coordinates for clubs
  Wikidata cannot place, for Alexandru to judge

### Code

- `index.html` — the whole app. Single file, no framework, Leaflet from
  CDN, three tabs: map, bucket list, ticket info.
- `tools/build_calendars.py` — `.ics` generation
- `tools/fetch_fixtures.py` — football-data.org
- `tools/fetch_clubs.py` — Wikidata club layer
- `tools/crosscheck_capacity.py` — OpenStreetMap capacity comparison
- `tools/propose_coordinates.py` — OpenStreetMap coordinates for the
  clubs Wikidata cannot place. Matches on names, proposes only, and
  flags anything ambiguous rather than settling it with a rule.

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

`unmapped-leagues.csv` now follows the same rule. It is read from and
pasted out of exactly like a review file, and it used to be rewritten
unconditionally — so a run where one country's league discovery failed
replaced the whole seed list with the other country's half, with a green
tick. It now keeps the last good file and says which country was
missing.

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

**Clubs on the same coordinate share one marker.** `drawClubs()` used to
make one circle per club with no idea that another club was already
standing on that pixel, and the circle drawn second covered the first
completely: the club underneath was in the data, on the map, and had no
marker anyone could see or click. It was silent — nothing counted it,
nothing reported it, and the club count in the corner said it was there.
Measured on 2026-09-19 across both country files: **10 grounds carry more
than one club, 21 clubs sit on them, and 11 of those 21 had no reachable
marker.** That is one club in eighteen on the map.

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
z11, when 1. FC Kaiserslautern II's tier switches on. The corner chip says
how many shared grounds are on screen, so the count is visible rather than
something to discover.

---

## Secrets

`FOOTBALL_DATA_TOKEN` is in Actions secrets. It must never appear in
client code, in `data/`, or anywhere under `calendars/`. No other key is
needed: Wikidata, Overpass and OpenLigaDB are all free and keyless.

---

## Known open problems

- **One duplicate Wikidata item and one wrongly-copied ground, found by
  grouping clubs on their coordinates.** Of the 10 shared grounds, two
  looked like one club entered twice. On 2026-09-19 one of the two
  turned out not to be a duplicate at all:
  - **Dinamo București is two real clubs, not one item twice.**
    `Q204237` is the Liga 1 club at Stadionul Dinamo. `Q113577526` is
    **CS Dinamo București**, a separate club currently in Liga 2, whose
    ground is CNF Buftea (also called Stadionul CNAF), capacity 1,600 —
    established by Alexandru from its Wikipedia article and the club's
    own csdinamofotbal accounts. What is wrong is Wikidata's data, not
    the item: `Q113577526` carries the senior club's venue, capacity and
    coordinates, copied or inherited by mistake. `clubs-manual.csv` now
    corrects the name, venue and capacity.
    **The coordinates are still not fixed and the two clubs still share
    one pin.** They have to come from `Q7596368`, the ground's own
    Wikidata item, which could not be read on 2026-09-19: that session's
    network policy blocked `wikidata.org`, `query.wikidata.org` and
    Overpass, so nothing could be fetched. Until `lat`/`lon` are filled
    in on that row, CS Dinamo București sits on Stadionul Dinamo with a
    popup naming a ground it does not play at. That mismatch is
    deliberate and visible — it is not a second bug to hunt. How far
    apart the two grounds actually are is not written down here because
    it has not been measured; Buftea is outside Bucharest, and that is
    as much as can be said without the coordinate.
  - **SSV Ulm 1846** is still unresolved, and is a genuine duplicate:
    `Q14551982` and `Q701290`, same name, ground, capacity, coordinates
    and tier, differing only in the league tag (`Q154069` 3. Liga
    against `Q322128` Regionalliga Südwest). The check to run is the
    sitelink count used for Lok Leipzig — keep the item with more
    Wikipedia sitelinks — and it could not be run on 2026-09-19 for the
    same network reason. Both outcomes are already worked out, so
    whoever can reach Wikidata has one step, not a decision:
    - if **`Q701290`** wins, it already carries the Regionalliga tag on
      its own and resolves to tier 4 unaided, so the `Q14551982` row in
      `clubs-manual.csv` becomes a `skip` row and the hand-written
      `tier 4` relegation correction is deleted with it — it would be
      correcting an item that is no longer on the map.
    - if **`Q14551982`** wins, its `tier 4` correction has to stay,
      because its own tag is the 3. Liga one, and `Q701290` gets the
      `skip` row instead.
    Nothing was changed either way, because guessing which item survives
    is exactly the assumption this entry exists to prevent.

  So the 10 shared grounds break down as eight genuinely shared, one
  duplicate item (SSV Ulm) and one wrong coordinate (Dinamo) — and the
  Dinamo pair is not a shared ground at all, it only looks like one.
  The eight real ones: FCU Craiova and Universitatea Craiova genuinely
  share the Stadionul Ion Oblemenco, and the Waldau-Stadion really is
  Stuttgarter Kickers and VfB Stuttgart II. The remaining six are a
  first team with its own reserve side, the Grünwalder being three at
  once: TSV 1860 München, TSV 1860 München II and FC Bayern München II.

  SSV Ulm is the third case of the duplicate-item problem already
  recorded above for Hamburger SV and Lok Leipzig, and the first two
  were found by eye. Dinamo is not a fourth — it is the opposite case,
  and worth keeping in mind next time two pins land on one ground: a
  shared coordinate can mean a copied coordinate rather than a copied
  club. Until now a duplicate of this kind was
  *invisible* — the second pin sat exactly under the first. A "2" over
  two identical club names is how the next one gets spotted.

- **The Franz-Kremer-Stadion is not in the data at all**, so it was not
  one of the grounds this fixed. The bug report that prompted the change
  named 1. FC Köln II, the women's team and the U19s as three clubs
  sharing it; none of the three is in `data/clubs/DE.json`. Only three
  clubs in the German file have "Köln" in the name — 1. FC Köln at the
  RheinEnergieStadion, SC Fortuna Köln at the Südstadion and FC Viktoria
  Köln at the Sportpark Höhenberg — and no club anywhere in either file
  has a Franz-Kremer venue. 1. FC Köln II is one of the 31 Regionalliga
  clubs listed below that Wikidata cannot place, so it never reaches the
  map to collide with anything. It is a candidate for `clubs-manual.csv`
  by way of `coordinate-review.csv`, not a marker problem.

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
  20 agree and 7 disagree; the rest could not be compared because only
  one source has a figure. Fortuna Düsseldorf (Wikidata 9,917 against
  OpenStreetMap 54,600) and 1. FC Saarbrücken (35,303 against 16,003)
  are the two worst. Preußen Münster was not among them — OpenStreetMap
  has no capacity for its ground, so nothing could be checked.
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
    came back, and the club layer is unchanged at 129 German and 64
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
- **OpenStreetMap has now been asked where the unplaced clubs are**, by
  `propose_coordinates.py`, first real run 2026-09-16. Of the 31
  Regionalliga clubs with no coordinates: 9 got a confident proposal,
  19 are ambiguous, 3 got nothing. Five of the nine are certain enough
  to be worth reading first — the OpenStreetMap ground names the club in
  its `operator` tag (DJK Vilzing, SSV Jeddeloh, SV Rödinghausen,
  TSV 1896 Rain, VfB Auerbach). The other four rest on a town match and
  deserve a harder look. Six of the seven reserve teams are ambiguous on
  purpose: their town is the first team's town and says nothing about
  which of the club's grounds they play on. Nothing has been applied to
  any club file — `data/clubs/coordinate-review.csv` is a list to judge.
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
- **FC Triesenberg is not German either, and it is on the map right
  now.** `Q1387764`, in `data/clubs/DE.json` at tier 3, venue
  Sportanlage Leitawis, capacity 800, coordinates 47.1145 / 9.5401 —
  which is in **Liechtenstein**, not Germany. It reaches the German map
  the same way SC Veltheim did: its Wikidata item carries `Q154069`, the
  German 3. Liga, and the club query is bounded by league rather than by
  country. Liechtenstein has no league of its own; its clubs play in the
  Swiss pyramid, so the tag is most likely the same Swiss-for-German
  confusion as Veltheim's. That last part is inference and is **not**
  confirmed: on 2026-09-19 the network policy blocked every source that
  could check it. What is not inference is the coordinate, which comes
  from Wikidata itself and is in Liechtenstein.
  No `skip` row has been added — that is Alexandru's call, and it was
  not what this session was asked to do. It is listed here so it is not
  lost.
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
- **Editing `clubs-manual.csv` does not rebuild the club layer.**
  `.github/workflows/build-clubs.yml` reruns on a push that touches
  `league-tiers.csv`, `fetch_clubs.py` or the workflow itself — but not
  `clubs-manual.csv`, even though a hand correction decides what is on
  the map just as directly. So a correction sits inert until the Sunday
  04:23 UTC cron, or until "Run workflow" is pressed by hand. This bit
  the Dinamo correction above: the row is committed and correct and the
  map will not show it until one of those two happens. Adding the path
  to the workflow is a one-line change and was not made here, because it
  was not what this session was asked to do.
- **A bounding-box check would catch this class automatically, and
  does not exist.** Both Veltheim and Triesenberg would have been caught
  by comparing each fetched club's own coordinates against a bounding
  box for the country file it is being written into. Unlike the `P17`
  country filter that was considered and rejected above, this costs
  nothing in lost clubs: a club with no coordinates never reaches the
  map anyway, so there is no field to be missing. It would report, not
  drop — the same shape as `capacity-review.csv`. Proposed on
  2026-09-19, not built, because it was outside what was asked.
- The missing Regionalliga clubs are not a query problem, and the type
  filter was never what stood in the way. The club query returns 95 clubs
  tagged with one of the five mapped Regionalliga items. 31 of them have
  no ground (`P115`) and no coordinates (`P625`) anywhere on the item, so
  they are dropped at the coordinates gate; 64 survive, and 61 reach the
  map once two are moved to tier 3 by hand and one duplicate is skipped.
  The 31 are seven reserve teams (1. FC Köln II, FC Schalke 04 II,
  Hertha BSC II, Borussia Mönchengladbach II, FC Augsburg II,
  1. FC Nürnberg II, SpVgg Greuther Fürth II) and 24 first teams,
  including SV Rödinghausen, TSV Steinbach Haiger, FC Viktoria 1889
  Berlin, SV Heimstetten and FC Erzgebirge Aue. The gap is missing data
  in Wikidata, not a filter, so no change to the query will close it.
  What can close it is a second source, which is what
  `coordinate-review.csv` above now offers for 28 of the 31.
- **europlan-online as a second stadium source: still a question, and
  the go/no-go part of it was not answerable on 2026-09-18.** The site
  could not be reached at all from the machine doing the work — its
  network policy blocks europlan-online.de, and Wikidata and Overpass
  with it. So none of the three things that decide it were checked:
  what `robots.txt` says, what the terms of use say about automated
  reading, and whether the coordinates and capacities on the page are
  as precise and as consistently laid out as the two hand-checked pages
  suggested. Nobody should treat the question as settled until those
  three have been read from the site itself.
  What could be established, from a search engine's index of the site's
  own pages rather than from the pages — so worth a second look, not a
  decision:
  - There is a systematic way round it. A ground is
    `/<name>/stadion-<id>.html`, a league is `index.php?s=liga&id=<n>`
    and lists that league's grounds and clubs, a country is
    `index.php?s=land&id=1`, and leagues go down to Kreisliga level.
  - The thing OpenStreetMap cannot do, this site appears to do: a club
    is a page *under a ground* — `/<ground>/verein/<clubId>` — so the
    club-to-ground link is the site's own structure rather than
    something to infer from a name.
  - Eight of ten ambiguous clubs came back with a named ground:
    1. FC Köln II at the Franz-Kremer-Stadion, Borussia Mönchengladbach
    II at the Grenzlandstadion in Rheydt, FC Augsburg II at the
    Rosenaustadion, FC Ismaning at the Prof.-Erich-Greipl-Stadion,
    FC Kray at the KrayArena, FC Viktoria 1889 Berlin at Stadion
    Lichterfelde, FC Erzgebirge Aue at the Erzgebirgsstadion, Eutin 08
    at the Eutina-Platz. Two did not: FC Schalke 04 II, and
    1. FC Nürnberg II, where the Sportpark Valznerweiher is four
    separate pitches on the site and nothing said which one.
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
- Wikidata's Regionalliga season items carry no participant list
  (`P1923`) for any of the five divisions, so there is no way inside
  Wikidata to enumerate who should be in a division and compare it
  against what came back.
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

1. A ticket-info file: official ticket page, whether a club sells to
   non-members, typical price range with the season noted, how demand
   behaves, whether matches sell out. **Stable facts only — sale dates
   and deadlines stay hand-written by Alexandru.**
2. Club detail sheet: a pull-up panel replacing the map popup, showing
   name, ground, capacity, competition name with tier in brackets,
   distance, fixtures and ticket info, each saying "unavailable" rather
   than being hidden when there is nothing.
3. Search box on the map, top right, live matches, enter flies to the club.
4. Badges. 284 crest URLs already sit unused in `data/fixtures/`.
   Wikidata `P154` covers German clubs patchily and Romanian ones barely.
   Licensing is unresolved: only freely licensed images may be used on a
   public site, and Wikipedia's non-free crests may not. Fallback is a
   generated marker — club colours plus initials.
5. Revamped bucket list and ticket info tabs, plus a fourth tab for
   memberships and tickets already held: cost, renewal date, benefits.
6. Expansion to more countries, one at a time.

Every change must actually land in the repository. Write files to disk, commit them, and push the branch — do not finish a task with changes left only in the working tree or described in the reply. When the task is done, state which files were committed and what the branch is called, so the diff can be reviewed.
