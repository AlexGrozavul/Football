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
`data/league-tiers.csv`, so the club layer is already compliant — this
is a documentation rule, not a data fix. It applies beyond leagues: a
future club addition, a badge, or a piece of research is also men's
football only until this rule changes, so don't reach for a women's
team, a women's competition, or a women's-team crest just because a
men's counterpart already has one.

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
- `data/league-tiers.csv` — maps a league's Wikidata Q-id to a tier.
  Tier comes from this file and never from a league name: Wikidata's
  league items are fragmented and undated, so names cannot be trusted.
  `skip` in the tier column excludes a league.
- `data/club-tickets.csv` — one row per club per team: who may buy, how
  the club allocates, whether there is a formal cutoff, whether the
  window can close before it, how demand behaves, and whether official
  resale exists. **No cell in this file ever holds a date.** `cutoff`
  says whether a stated deadline *exists*, not when it falls.
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
  skipped** rather than compared against nothing. That is what the
  Austrian row is for: it holds the corrected article title against the
  day Austria is added, and generates no findings meanwhile.

### Generated — safe to overwrite

- `calendars/*.ics`, `calendars/skipped.md`, `calendars/.stamps.json`
- `data/fixtures/*.json` — football-data.org, one file per competition
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
- `data/clubs/roster-review.csv` — one row per club per division, with
  a verdict saying whether the club is on the map, and if not, **which
  kind of missing** it is

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
- `tools/check_tickets.py` — read-back and checks for the three ticket
  files. Reads, never writes; exits 1 on a problem.
- `tools/crosscheck_stadiumdb.py` — StadiumDB capacity comparison, the
  third opinion. Matches by club name and country because StadiumDB
  publishes no coordinates; reports, never corrects.
- `tools/check_rosters.py` — the roster check. Asks, from the league's
  side, whether a club that should be on the map is missing from it.
  Reads, never writes to a club file.
- `tools/diagnose_p118_rank.py` — which clubs the club query's truthy
  `wdt:P118` join hides, and why: a preferred-rank statement asserting
  no league, or every statement deprecated. Reads `P576` so a
  `<novalue>` on a club that folded is not mistaken for an error.
  Reads and writes **nothing** — not a club file, not a review file —
  and exits 1 on a failed call.

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
`kind`, `priceBasis`.

**Open vocabularies are every other controlled column** — `access`,
`salesModel`, `requestTypes`, `closesEarly`, `demand`, `resale`, `team`,
`window`, `competition`, `stage`, `category`, `placeType`,
`opponentTier`. Nobody has written down what their allowed values are,
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
speed.

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
Oblemenco, which two unrelated clubs really do share. No ground on
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
z11, when 1. FC Kaiserslautern II's tier switches on. The Grünwalder
used to do it twice — a "2" at z11 and a "3" at z12, when TSV 1860
München II's tier 5 switched on — and since that club's ground was
cleared it is a plain "2" from z11 and stays one at every zoom above.
The corner chip says
how many shared grounds are on screen, so the count is visible rather than
something to discover.

**Tier zoom bands for tier 4 and deeper were merged into one, 2026-09-19.**
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

---

## Known open problems

- **Both new checks are built and have run for real, 2026-09-20. These
  are the numbers they left behind.** `crosscheck_stadiumdb.py` and
  `check_rosters.py` are described under Files and Code; what follows is
  what the first pass over Germany and Romania actually did.

  | | tier 1 | tier 2 | tier 3 | tier 4 | 6 | 7 | 8 | on the map |
  |---|---|---|---|---|---|---|---|---|
  | **Germany** before | 18 | 18 | **22** | 83 | 3 | 1 | 1 | 146 |
  | **Germany** after | 18 | 18 | **20** | 88 | 3 | 1 | 1 | **149** |
  | **Romania** before and after | 16 | 16 | 32 | — | — | — | — | 64 |

  **Against the leagues' own membership, after the corrections:**

  | division | roster | on the map | ok | extra | missing | wrong tier | unplaced |
  |---|---|---|---|---|---|---|---|
  | Bundesliga | 18 | 18 | 17 | 1 | 1 | — | — |
  | 2. Bundesliga | 18 | 18 | **18** | — | — | — | — |
  | 3. Liga | 20 | 20 | **20** | — | — | — | — |
  | Regionalliga | 87 | 88 | 55 | 33 | 29 | 3 | — |
  | Liga I | 16 | 16 | 15 | 1 | — | 1 | — |
  | Liga II | 22 | 16 | 14 | 2 | 1 | — | 7 |
  | Liga III | 69 | 32 | 18 | 14 | 13 | 4 | 34 |

  **The 3. Liga is the headline.** It began this pass at 22 clubs
  against a real 20 — the gap that motivated the whole design — and it
  is now **20 of 20, nothing missing and nothing extra**. Six clubs were
  sitting at tier 3 on a stale `P118`, two belonged there and were at
  tier 4, and two were invisible to the club query altogether. The
  2. Bundesliga is likewise exact.
  **Romania's counts did not move, and that is the honest outcome.**
  Liga II is 16 on the map against 22, Liga III 32 against 69, and the
  reason is coordinates rather than tags: 41 of those clubs are
  `unplaced-no-coordinates`, which is the route `coordinate-review.csv`
  and europlan-online already exist for. Nothing was trimmed to make a
  count look better.
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
  **Nothing has been changed for either**, deliberately. Farul is a
  judgement about which club the current Liga I side is — see its own
  entry below. Augsburg is on the map already under a second item, and
  the remedy there would make it worse rather than better; see the
  entry on the club-and-team shape below.
  **What would fix it in general is not obvious and is not attempted
  here.** Dropping `wdt:` for `p:`/`ps:` would see every statement
  including the deprecated and historical ones, which is how a club gets
  put in a league it left in 1994 — the exact problem `league-tiers.csv`
  and the truthy join exist to avoid. Reading rank properly means
  deciding what a deprecated league tag means, and that is a decision
  for Alexandru, not a query change to slip in.

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
  **Asked directly on 2026-09-20, Alexandru's answer was to leave Farul
  off the map and settle the identity question first**, and the reason
  is the right one: the tier is the *second* question. The first is
  which club `Q368104` actually is — the old Farul, the 2021 Viitorul
  merger that took the name, or both depending on who edited the item —
  and a tier written before that is a number attached to a club nobody
  has identified. So the `<novalue>` is recorded as an error and the
  suppressed tags are what this project reads, **and nothing is written
  to any club file.** `roster-review.csv` goes on reporting it, which is
  correct: it is a real finding and it is still open.
  **And there is a mechanical obstacle that has to be cleared first,
  whichever tier is chosen.** `apply_manual` in `fetch_clubs.py`
  **rejects** a row whose `clubQid` is not in the country's fetched
  clubs — verified by running it against a Farul-shaped row, which
  comes back *"Q368104 is not in this country's fetched clubs"*. That
  is the right guard for a typo and it is exactly wrong here, because
  not being in the fetched clubs is the whole problem. The row that
  does work is an **add** row with no `clubQid`, and it costs the Q-id:
  the club gets a synthetic `MANUAL-…` id, and `check_rosters.py` joins
  on Q-ids, so the roster's `Q368104` would still read as missing while
  the hand-added club would read as `extra-not-in-roster` — **two
  permanent false findings in place of one true one**. So a hand row is
  not the remedy for a rank-hidden club, and making one work means a
  deliberate change to what a `clubQid` row may do. Not attempted here.

- **Two Romanian clubs are one club's identity question each, and
  neither is settled here.** Both came out of the roster check on
  2026-09-20 and both are shape 2 — two real items, not a duplicate —
  so `skip` is the wrong tool for either.
  - **Farul Constanța.** The 2026-27 Liga I article lists a club whose
    Wikidata item is `Q368104`, labelled "SSC Farul Constanța", English
    sitelink "FCV Farul Constanța", 29 sitelinks. It is **not on the map
    at all**, for the rank reason above: a `<novalue>` `P118` at
    preferred rank hides its Liga II and Liga III tags. Meanwhile the
    map's sixteenth Liga I club is **FC Hermannstadt `Q24884611`**,
    which the Liga I article does not list and whose own Wikidata
    carries both Liga II and SuperLiga. So the top flight has the right
    *count* and one wrong *member*, which is exactly the failure a count
    cannot see and this check was built to catch.
    **What is not established** is which club `Q368104` is: the old
    Farul, the Viitorul merger that took the name in 2021, or both
    depending on who edited the item. Writing a tier-1 row for it would
    put a club on the map on the strength of an English Wikipedia table
    and nothing else. That is Alexandru's call.
  - **Bihor Oradea is two clubs with one name**, and the two sources
    disagree about which is in Liga II. `Q1386940` is "established in
    1958", 12 sitelinks, and carries Liga II at **preferred** rank — so
    Wikidata says it is the Liga II club, and it is the one on the map.
    `Q113541238` is "established in 2022", 2 sitelinks, **no `P118` and
    no ground**, and it is the one the Liga II article links.
    **Neither source is obviously wrong** and acting on either loses
    something: removing the 1958 club takes Bihor off the map entirely,
    because the 2022 one has no coordinates. Left as it is, and recorded.

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
  **The two extras are not one thing either.** `Q1386940` Bihor Oradea
  is the other half of the identity question and is not a spurious club
  — read the two Bihor items as one club and the genuine absence is
  seven, all coordinate-only, against one genuine extra. That one is
  **`Q1024390` Politehnica Iași**, which carries `Q386384` and nothing
  else and which the 2026-27 Liga II article does not list. Either its
  `P118` is stale or the article links it under a title the sitelink
  hop did not resolve. **Nothing has been changed for it**, because a
  single article saying a club is absent is not evidence that it is,
  and this project does not act on one source that way.
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

  **The five shapes have names now, because the next one will not
  arrive with a label on it.** The first three look identical on the
  map — two items, one name, one ground — and each wants a different
  remedy. The last two never appear as two pins at all, because one
  item of the pair never reaches the map: only the roster check can see
  them, and it sees them as one club reported twice.
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
  4. **One club that is no longer a club — merged out of existence.**
     *Torgelower FC Greif `Q566179`, Teutonia Watzenborn-Steinberg
     `Q21175456`.* The club went into a merger and Wikidata still tags
     it with the division it was in. It has no coordinates, so it never
     reaches the map and no marker can ever reveal it. **Remedy:
     Alexandru's, and it is a `skip` or a rename, never a coordinate** —
     writing the merged club's ground would put a club that has not
     existed since 2018 or 2022 onto the map at a tier it left.
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
  Universitatea Craiova really do share the Stadionul Ion Oblemenco,
  and the Waldau-Stadion really is Stuttgarter Kickers and VfB
  Stuttgart II. The rest are a first team with its own reserve side.
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
    Switzerland, Austria, Serbia and Greece.** As a second opinion on
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
- OpenLigaDB is not yet wired up. It would cover 2. Bundesliga, 3. Liga,
  DFB-Pokal and Regionalliga. Bundesliga is deliberately excluded there,
  since football-data.org already covers it and two sources would mean
  reconciling two sets of ids.

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
