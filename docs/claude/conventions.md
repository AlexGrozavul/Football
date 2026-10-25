# Conventions the tools rely on, Adding a country, Secrets (full text)

Moved byte for byte from CLAUDE.md (old lines 1008-3635, 2026-10-22). Long new entries go here; CLAUDE.md keeps only rules and index lines. Grep this file for the name you need.

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

**The dissolution exception of the hand-named fallback, 2026-10-18.**
Alexandru's decision: Calcio Padova (`Q8428`) is on the map at tier 2
although its Wikidata item carries `P576` 2014 (the old club's
bankruptcy; the item now describes the refounded club - its own infobox
says 10th in the 2025-26 Serie B and the 2026-27 Serie B article lists
it). **This supersedes the sentence "must not be loosened for one club"
in the Italy entry.** The dissolution gate itself (CLUB_QUERY, the
novalue fallback) is unchanged; the exception is **per hand row and
roster-gated**: `data/clubs-manual.csv` has an optional column
`allowDissolved` (header-driven; value `yes`, anything else is reported
and ignored, and it needs a `clubQid`). `hand_named_fallback()` accepts a
candidate that carries a `P576` **only if** its hand row says `yes`
**and** a tracked current-season roster names it (condition 3, applied
unchanged - a mistyped Q-id or a club the roster does not name stays off,
with the reason printed). Without the cell the club is left out exactly
as before. The run summary prints, on every run, each club accepted this
way: `ACCEPTED DESPITE P576 (dissolved) <year>: <name> (<Q-id>) -
allowDissolved yes in data/clubs-manual.csv line N, and the roster
article <article> names it`. Padova's row has country IT, tier 2 and no
venue, capacity or coordinates (the fetched ones stand). To undo: empty
the cell or delete the row. Checked offline with the roster and the query
mocked: `yes` plus a roster naming it surfaces the club with its P576
year; the cell blanked leaves it off ("Wikidata marks Q8428 dissolved");
`yes` with a roster that does not name it leaves it off. Padova is the
only club with the cell, and nothing else in this convention changed.
**Proof, on the branch (build-clubs.yml and check-rosters.yml dispatched):**
Calcio Padova is in `data/clubs/IT.json` at tier 2 (stadio Euganeo, 32,420,
45.432222 / 11.858333, fetched), the run summary printed `surfaced by the
hand-named fallback: Calcio Padova (Q8428), named by 2026–27 Serie B; tier 2
from data/clubs-manual.csv line 260; ON THE MAP` and `ACCEPTED DESPITE P576
(dissolved) 2014: ...`, its roster verdict changed from
`missing-from-wikidata` to `ok`, and no other club or country file changed
(`IT.json` gained that one club; `index.json` only its counts).

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
**Primary-source rule, Alexandru's decision of 2026-10-22:** a ticket
row read in full on the club's own page for the season in question is
`confirmed` with basis `published` even when no second source exists; the
two-source requirement applies only to rows that rest on press or other
third parties, and several pages of one club count as one source. The
first lines of the Elversberg research (PR #144) labelled such rows
`unverified` because the prompt then demanded two sources.
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

**Route fuel cost (2026-10-08) is an estimate** from a fetched country-average diesel price (`data/fuel-prices.json`, EU Weekly Oil Bulletin, written only by `tools/fetch_fuel_prices.py`, never hand-edited, never in calendar events) or a manual entry on the device, over Stadia's own route length; tolls and ferries are not priced.

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

**Eintracht Frankfurt, 2026-10-11 - mostly unverified, because no club
page could be opened.** Researched for an outside buyer (a member of no
club, in Germany but not Frankfurt, two tickets together), Bundesliga home
games only: the 2026-27 season article lists no European competition.
`Q38245`, the only Frankfurt item on the map; **no `clubs` entry in
`football-rules.json` and no link line**, so the sheet has no "Your notes".
1 club row, 1 window, 3 phases, 14 rules (5 of them gaps), 2 demand rows,
no price rows, 8 sources (`F1`-`F8`), no country row.
- **Access.** eintracht.de, wochenblatt-reporter.de, hessenschau.de,
  journal-frankfurt.de, diefalsche9.de and goal.com did not resolve from the
  session (DNS failure through the sandbox proxy); web.archive.org was
  refused by the fetch tool. Only Wikipedia opened. So every sale fact rests
  on press the coordinator read and Code did not open (`F1`-`F5`, labelled
  so), and is `unverified`: F1-F3 are one outlet, one source.
- **What it says.** Summer 2026: home games sold in batches, a 24-hour
  members' sale (members from 7, first come first served, mobile only,
  account linked in the app's wallet), then a free sale only if tickets
  remained; up to 4 (Bremen) or 2 (Schalke, Bayern) per member; Bayern
  (matchday 17) sold in August before its kickoff was fixed. Ticketbörse at
  face value (2023 and undated reports). Membership fee, waiting period,
  prices, risk classification and personalisation: **not read**, written as
  gap rows. `not-stated` was added to the demand outcomes (2025-26: no
  source says sold out).
- **Capacity**: 60,100 from 2026-27 (German Wikipedia; the sold-out Freiburg
  game), 53,800 international; the map holds 59,500.

**SV Elversberg, 2026-10-22 - a non-member gets nothing through official
channels.** Researched for an outside buyer (a member of no club, in Germany
but not in Spiesen-Elversberg, two tickets together), Bundesliga 2026-27 home
games, the club's first Bundesliga season; no DFB-Pokal. `Q692691`, the only
Elversberg item on the map (tier 1, capacity 10,000, venue "Waldstadion
Kaiserlinde"); **no `clubs` entry in `football-rules.json` and no link line**
(only the bucket fixture `saarbrucken-v-sv-elversberg`, untouched). 1 club
row, 3 windows, 6 phases, 18 rules, 24 prices, 1 demand row, 12 sources
(`E1`-`E12`), no country row.
- **Access.** The club's site is **sv07elversberg.de** (not sv07.de);
  `robots.txt` disallows only `/wp-admin/`; every club page answered 200 on
  a runner (temporary probe in `build-clubs.yml`, four dispatches, removed;
  the file is byte for byte as before). FAQ answers sit in a hidden
  accordion and were read as page text. **The ticket shop,
  www.ticket-onlineshop.com/ols/sv07elversberg/de, refused twice** (HTTP/2
  protocol error; then a timeout and an unreadable `robots.txt`, so the
  host was not fetched again) and the Internet Archive holds no capture, so
  the shop and its terms are unread. Both Wochenblatt Reporter leads were
  opened (one outlet, one source); they print no prices.
- **What it says.** 2026-27 home day tickets are a small members-only
  contingent (standing block E1): a members' online application, one
  ticket per member, a random draw, no free sale; no new season tickets;
  Club Sale resale is members only, one per member. Membership EUR 66 a
  year + EUR 7, usually active in 7 days, no further wait stated. So two
  people need two memberships (or one family membership) and a win in the
  draw. Day prices EUR 18 standing, EUR 35/41/47 seated (2026/2027 table).
- **Two sources for prices and sale rules** (the brief): only the
  members-only rule, the season-ticket renewal and update tracking have a
  second source; the draw, limits, Club Sale, fees and all 24 prices rest
  on the club alone and are `unverified`, said in each note.
- **Not varied-by-fixture**: no source names a sold-out game or a
  difference between games, so the 2026-27 demand row is `not-stated`.

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
  the Serie A file, while your notes then gave Sun 1 Nov 2026 - both were
  on the card; since 2026-10-11 your notes say 31 Oct too (Known open
  problems). The Frankenderby's is Sun
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
  upcoming day-level date (Derby della Madonnina, 31 Oct 2026 since 2026-10-11, 1 Nov 2026 on the day; Europa
  League final, 26 May 2027), 2 month-level (Frankenderby, January or
  February 2027; KSC v FCK, January 2027), 17 undated, none past. No
  ticket window is day-level (every one is inferred or disputed), so
  none is on a day cell. A month renders in about 17-19 ms in headless
  Chromium with the CPU slowed 4x (this sandbox, not a phone).

**Reminders removed, three entries removed, Pokal and play-offs grouped,
2026-10-08.** Done on Alexandru's instruction; rendering and entries only.
- **Reminders removed from the page.** Gone: the Bucket list's "Reminders"
  section, the "Ticket windows (reminders)" block inside every entry, the
  ticket-window items and diamonds on the calendar, and the sheet that
  opened them (`eventHtml()`, `leadWords()`, the event branch of
  `openBSheet()`); the club sheet's notes no longer list "Dated ticket
  windows for this club" and the Ticket info note says no dated window is
  shown. **Nothing was deleted from data**: every `ticketEvents` entry, every
  CSV and the Me tab's own reminders and `.ics` export are untouched.
  **`calendars/local.ics` is fed by `ticketEvents` entries with `feed`
  `local` through `build_calendars.py`, not by the page**, and today holds
  two `[?]` inferred sale dates (`vfb-presale-active`, `ksc-fck-sale`) -
  so it still contains sale dates. `tools/test_tickets_bucket.js` and
  `tools/test_calendar.js` now assert the Reminders section and every
  ticket-window item are absent (the old "shows its reminders" assertion of
  PR #63 is replaced); `test_layout.js` no longer expects ticket-event
  warnings on a tab.
- **Three entries removed from `bucketList`**: `vfb-regular` ("Become a
  regular at the Cannstatter Kurve"), `away-end-first` ("Any proper away
  end") and `womens-football` ("Any women's match") - the only
  women's-football entry (searched for women, Frauen, Damen, lionesses, UWCL,
  ladies, female, NWSL; rule 6). Their two lines in
  `bucket-links-manual.csv` (both `vfb-regular`; the other two had none) went
  with them; no `ticketEvents`, club entry or ticket file was touched.
  `test_vfb_tickets.js` no longer looks for a VfB card in the Bucket list.
  **Ticket events now linked to no entry: `vfb-presale-active`** (it was
  linked to `vfb-regular`). Unlinked before and still unlinked: `poli-rapid-cup`,
  `fcb-pokal-r2`, `rcsa-resale`. **Now shown nowhere in the app**, all four
  and every other ticket event too, because nothing draws them.
- **"Other entries"** (no `sortKey`) now holds one entry, `liga2-playoff`
  ("Liga 2 promotion play-off, decisive round", Poli's track); it was left
  as it is.
- **The Pokal and the play-offs open the German and Romanian groups.** The
  existing hand-written `pokal-first-round` ("DFB-Pokal first round at an
  amateur host") and `relegation` ("Bundesliga Relegation, second leg") were
  kept with every hand-written field and moved to the start of "Club
  fixtures, Germany" (flagged `listOnly`, so off the calendar); **the Pokal
  entry is undated**: no `date`, `nextFixture` or `fixtures`, only its trigger
  text (draw in June, played August/early September) and a linked
  `pokal-draw-2027` event (inferred, 2027-06-05), which is no longer shown.
  Its home-advantage rule was **not** researched or written. `relegation`
  already covered the Bundesliga relegation, so no duplicate was added; it
  gained the researched note as `whyAssistant`, `whySources`, `whyStatus`
  `unverified`.
- **New undated entries, formats researched on 2026-10-08 and subject to
  rule changes** (the sources are search-result summaries of the pages named
  in `whySources`; the sandbox blocks fetching them, so none was opened):
  `zweite-liga-relegation` (16th of the 2. Bundesliga against the 3rd of the
  3. Liga, two legs, aggregate, no away goals, extra time and penalties;
  played in May in 2026), `regionalliga-aufstiegsspiele` (**not** 3. Liga
  v Regionalliga: two Regionalliga champions play home and away for the last
  3. Liga place; the June 2026 reform vote gave no clear result and a change
  is put at 2028/29 at the earliest, so the current model is expected for
  2026/27 - not confirmed by the DFB), `superliga-relegation-baraj` (two
  Superliga clubs above the directly relegated places against Liga 2's third
  and fourth, two legs; May to early June 2026; the 2026-27 rules were not
  found) and `liga3-promotion-tournament` (runners-up of the Liga 3
  play-off groups, single-match semi-finals and a final for the fifth Liga 2
  place, 2025-26 rules; older editions differed; Liga 2's own relegation
  baraj is between Liga 2 clubs and has no entry). Each: `whyStatus`
  `unverified`, a new `whySources` list of URLs (shown as "Sources for the
  note"), the playing month only, tagged inferred and observed in 2025-26 /
  2026, and no host, club, capacity, ticket rule or sale date. A format the
  sources would not confirm gets no entry.
- **`sortKey` renumbered 10, 20 ... 1660 with no gap**, existing relative
  order unchanged; the Pokal and the three German entries are the first four
  of Germany, the two Romanian ones the first two of Romania. `bucketList`
  now holds 167 entries (166 - 3 + 4).

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

**48 more bucket entries, 2026-10-10: undated, in the same unverified shape.** Added on Alexandru's instruction in the shape of the 160-entry batch: 39 derbies (Bavaria, Baden-Württemberg, Rhineland-Palatinate/Saarland/Hesse, North Rhine-Westphalia, the north, the east; three in Switzerland, one in Austria, one in France), the Finaltag der Amateure and eight regional cup finals. `bucketList` now holds 215 entries.
- **The why texts were written from memory by an assistant and stay unverified** (`whyStatus` `unverified`, shown as "Not yet verified"). Nothing in them was read from a source. They carry no date, capacity, ticket rule or sale window of ours, and the entries have no `date`, `nextFixture`, `fixtures`, `trigger`, `clubs`, `venue` or `whySources`. Statements in them such as "about 20 km apart", "with heavy security" or "Scope unverified" are claims to check, not facts. The 39 derbies carry `leagueCheck: true` (the check itself is not built); the nine cup entries do not.
- **Field names follow the existing schema, not the words of the brief.** `type` stays `fixture` (derbies) or `event` (cup entries) because the page reads it; the brief's "type" is `kind` (`derby`, `final`, and `event` for the Finaltag der Amateure); the brief's "country (ISO-2)" is `countryCode`, while `country` keeps the country's name, as on every other entry. No field was added.
- **Order.** The nine cup entries follow `pokal-first-round` directly, in the listed order, ahead of the three German play-off entries; they are in the group "Club fixtures, Germany". The new derbies were merged into each country's existing order by normalised title (case, accents and a leading "FC" or "1. FC" set aside). **The existing Germany order is not strictly alphabetical** (the named rivalries Der Klassiker, Revierderby, Ostderby, Südwest-Derby and Frankenderby sit where they were put), so for those five the position they already held was kept and a new entry went before the first existing entry that sorts after it. `sortKey` was renumbered 10, 20 ... 2150 with the relative order of the 167 older entries unchanged.
- **Links.** Clubs are linked in `bucket-links-manual.csv` only where the club's name equals a name in the country's `data/clubs/*.json` exactly (case set aside, nothing else), the host is empty, and an entry with no matched club has no line. 37 lines were added. Unlinked: Bayern München, 1. FC Schweinfurt 05, 1. FC Heidenheim, FC Heidenheim, Waldhof Mannheim, Mainz 05, FC Saarbrücken, Darmstadt 98, Schalke 04, Viktoria Köln, Fortuna Köln, RC Strasbourg and FC Mulhouse - most because the map's name differs ("FC Bayern München", "SV Darmstadt 98", "FC Schalke 04"), which is a naming question, not a missing club, and was left alone. Viktoria Köln v Fortuna Köln and RC Strasbourg v FC Mulhouse have no line at all.
- **Duplicates.** No new entry covers a fixture an older one already does: by Wikidata ids (both clubs linked) none matched an existing entry's club pair, and by normalised title the only near match is VfB Stuttgart II v Stuttgarter Kickers against the older VfB Stuttgart v Stuttgarter Kickers, which is a different club (the reserve side `Q107421`, not `Q4512`), so both stay. Because nothing matched, no older entry was touched.

**The Bucket list filter and the Competitions tab, 2026-10-08.** Built on
Alexandru's instruction.
- **Two fields were added to every `bucketList` entry, not the ones the
  brief named, because those were taken.** `type` already exists
  (`fixture`, `experience`, `event`) and the page's "Next meeting" logic
  reads it, so the filter's type is **`kind`** (`tournament`, `final`,
  `national-team`, `derby`, `playoff`, `cup-round`, `event`, `other`).
  `country` already exists on 166 entries as a **name** ("Germany",
  "Scotland", `none` for several) and the "other countries" sub-headings
  read it, and the brief said never to overwrite a non-empty one, so the
  ISO-2 code is **`countryCode`** (empty for a multi-country tournament).
  Both derived from the group and title; `countryCode` agrees with the
  country of every linked club's file (`bucket-links-manual.csv`,
  `football-rules-links.csv`) for every linked entry - no disagreement.
  Scotland, England and Wales are all `GB` (GB.json is England's pyramid
  with Welsh clubs); the filter calls it "United Kingdom". A derby is any
  club fixture between two clubs, linked or not, including pairs that are
  not rivalries.
- **`liga2-playoff` moved to the start of the Romania group** (`group`,
  `country` "Romania" - the name, not "RO" - and `countryCode` "RO"); every
  entry now has group, country and `sortKey`, which was renumbered 10, 20 ...
  1670 in the old relative order. "Other entries" no longer shows, because
  nothing lacks a `sortKey`.
- **One filter, two lists.** The chip ("Filter · n of total") above the
  Bucket list's sub-tabs and the one on the Competitions tab open the same
  panel (the coverage panel's sheet, checkbox rows). Choices in a group are
  "or", groups are "and", only values that exist are offered with their
  counts. It filters the List (all three sorts, empty groups hidden) and the
  calendar; an empty result says "No entries match" with a reset button.
  **Kept on this device only**, `football-planner-bucket-filter` and
  `football-planner-comp-filter` in `localStorage`, not in the Me tab's
  export, not read by any tool.
- **The Competitions tab** is fifth, between Ticket info and Me. Bottom-bar
  labels had to shrink (10 px, no side padding) for "COMPETITIONS" to fit
  five slots at 390 px; it fits, with almost no gap beside TICKET INFO. A
  list grouped Germany, Romania, other countries A-Z, then Europe and
  international; a name search; the same country filter; a tap opens a sheet
  in the club sheet's shape with the seven topics, a status label per row
  ("Confirmed", "Estimated, based on past seasons", "Not yet verified"), its
  source links and "Checked on <date>". A day-level future date in a text is
  shown as its month as a second line of defence.
- `SHELL_VERSION` is `v11`.

**The Me tab's attended matches and events, 2026-10-09.** The Me tab now has
four sub-tabs, in this order: **Stats**, **Matches**, **Events**, **Tickets**
(the labels are short so the four fit 390 px; the page's own long names are
"My stats", "My attended matches", "My attended events", "My tickets/memberships").
**All the content the Me tab had before is the fourth sub-tab, unchanged**
(its element is still `#meBody`).
- **Data.** The first three read `data/attended.json` with `getJSON()`, so it
  is network first like every other data file, and **only when one of them is
  opened** (Stats is the one the Me tab opens on, so the file is requested the
  first time the Me tab is opened, never at start-up; a failed load says so and
  is tried again on the next open).
- **Stats are calculated in the page from the file**: matches, goals seen and
  per match, penalties scored, stadiums, yellow cards and **red cards** (counted only for
  matches whose `cardsComplete` is true, with the "complete data for a of b
  matches" notice; since 2026-10-13 one "red cards" card whose number is straight reds plus second yellows, with the split under it and a per-match figure; the yellow total counts only cards typed `yellow`, so a dismissed player's first yellow is in it only where the file lists it as its own card), most-seen team, most-seen player (from line-ups, with its
  notice), biggest and smallest crowd, and the lists of stadiums, cities,
  countries and competitions. Nothing is hardcoded.
  **Exhibition matches (2026-10-15)**: a match carrying `"exhibition": true` is
  left out of **goals seen, goals per match (divided by the number of
  non-exhibition matches) and penalties scored**; the matches card, the card
  stats, stadiums, the record and the most-seen stats still count it, and
  friendlies count as normal matches. A goal is counted by the existing rule:
  the two numbers of the score (the goals list only feeds the penalty count
  and the scorer lists). Notes under the goals cards, in this order: "Includes
  n goals from m matches without a full goals list" (non-exhibition matches
  only, shown only when it applies), then, only when at least one goal is
  excluded, "Doesn't include goals from exhibition matches (n goals excluded)"
  (`aGoalsExcl`; n by the same rule over the exhibition matches). The flag is
  hand-written in `data/attended.json` (one match so far, the 2019 charity
  match, 13 goals); no other match was marked.
- **Order.** Matches by `date`, oldest first, the same date in the file's order,
  numbered 1..n, as the old app listed them; events in the file's order.
  A card shows teams and score, competition and stage, stadium and city, date.
  Tapping one opens the sheet (`#asheet`, the club sheet's shape): until
  2026-10-09 with the basic header fields only, since then the full detail
  sheet (next entry).
- **Detail sheet, 2026-10-09 (step 2).** Tapping a match or event opens the full
  detail sheet (`#asheet`, the club sheet's shape), from `data/attended.json`
  only. The old app's match detail had five sub-tabs: **Line-ups** (a pitch of
  the starting eleven laid out from the formation, goal, card and substitution
  badges beside names, a home/away switch, coach, substitutions with minutes,
  unused bench), **Timeline** (goals, cards and substitutions sorted by minute,
  stoppage time after its minute, a card with no minute first and shown as "—",
  the away side mirrored), **Stats** (six paired bars and the source),
  **Photos/videos** and **Notes** (the factual note, "My note", ticket, seat,
  block, who I went with); an event's detail had What it was, Why it mattered,
  My note, ticket/seat/block (only `atStadium`), who I went with, and media.
  **Reproduced, stacked in the sheet in that order, each only if the data has
  something for it** (an absent pane is not drawn empty): header (the old
  header's attendance, referee and after-90 score added when the file has
  them), line-ups with the pitch as inline SVG, timeline, stats, factual note,
  personal fields; for an event, the `atStadium` flag, one "Factual note" (its `note`, line breaks kept; before 2026-10-13 two sections, What it was and Why it mattered) and the
  personal fields. **Not reproduced: photos and videos (step 3).** The pitch is
  drawn only where the formation's rows add up to the ten outfield players of an
  eleven-man list; otherwise the starting eleven is listed with no pitch. **A
  formation is never inferred.** On 2026-10-09 the file holds 21 matches with
  line-ups (40 teams, every one with a formation that draws), 15 with stats.
  The assistant-written factual notes (`note` on a match or an event)
  are labelled "Written by an assistant from memory, not yet verified".
- **Personal fields are device-only and never committed.** My notes, Ticket,
  Block, Row, Seat and Who I went with (in that order on the sheet) are kept in this browser's `localStorage`
  under `football-attended-personal`, one object keyed by entry id with the old
  app's `mf_personal` shape plus `row` (`{id: {note, ticket, block, row, seat, withWho, supported}}`), saved as
  typed. **`row` was added on 2026-10-18** (label "Row", ro "Rând", unchecked): a new free-text field beside
  seat and block, same limit as seat, card-number check as for seat, on a match sheet and on an event sheet
  (where the ticket, block, row and seat fields still show only when "I was at the stadium" is Yes). **No stored value was moved or
  parsed**: a seat reading "Row 8 Seat 8" stays as typed. The Me export's `personal` records carry `row`
  when set; import accepts it. `ME_FILE_VERSION` stays 3 (versions 1 to 3 import as before; a file without `row` is unchanged): an older build
  refuses a file that has a `row` with its usual "unknown field" message and changes nothing, which was judged enough. **Never in the repo, never read by any tool, never in the Me tab's
  export (nothing was added to it), never in a request.** The page does **not**
  read the old app's `mf_personal`, `mf_imported`, `mf_lang`, `mf_theme` or the
  IndexedDB `mf_media`; moving that data is step 3 and needs an export file. A
  value on Ticket, Seat, Block or Who I went with holding a payment card number
  (the Me tab's own check, 13-19 digits passing Luhn) is refused and not saved,
  with the reason shown; My notes is not checked. Storage blocked: the fields
  work for the visit and the sheet says so. `tools/test_me.js` checks the new key
  is the only one used and no read or write is an `mf_` key (131 checks).
- **Not reproduced from the old app**: the theme switch. *(The supporter
  buttons, the record, "Add a match" and the photos and videos were added
  later the same day - see "Imported matches, supporter choices and media"
  below. The old "Save a copy" export is replaced by the Me tab's own export;
  the old export format is not read.)*
- **Language.** Every new string goes through `t(key)` and the `I18N`
  dictionary, with the same keys in `en` and `ro` (checked by
  `tools/test_me.js`). The `ro` block is marked **"RO unchecked by the user"**:
  the assistant wrote it. English is the default; the choice (`setLang()`) is
  kept on the device under `football-planner-lang`. *(Since later the same
  day the toggle is in Settings and every string of the interface is in the
  dictionary, the Tickets sub-tab's included: see "The interface is
  translated".)*
- **Step 2 and the device.** *(Since the additions below the sub-tabs also
  read `football-attended-imported` and the supporter choices; the sentence
  that follows described the state before them.)* The new sub-tabs read
  **nothing** from browser storage except the language key and, once a detail
  sheet is opened, `football-attended-personal` (the test records every
  `localStorage` read and write; none is an `mf_` key). The old `supported`
  choice was not kept then.
  The old app's keys are `mf_personal` (per match or event id: `note`, `ticket`,
  `seat`, `block`, `withWho`, `supported`), `mf_imported`, `mf_lang`, `mf_theme`,
  and IndexedDB `mf_media` (store `items`); ids in `data/attended.json` are the
  same ids those keys use. This site is a different origin from Meciuri's, so
  nothing in the old phone's storage is visible here; moving it means an export
  file, never the repo.

**Imported matches, supporter choices and media, 2026-10-09.** The rest of
the old app's features, rebuilt on Alexandru's instruction. **Everything here
is device-only: nothing is committed, nothing is migrated from the old app, and
`data/attended.json` is never written by the page** (it is fetched with GET and
the test asserts no other request reaches the server). The old app's
`mf_personal`, `mf_imported`, `mf_media` and the rest are **never read or
opened**; every `localStorage` read and write and every IndexedDB open is
recorded in `tools/test_me.js` and none is an `mf_` name. Everything starts
empty on a device.
- **How the old app did it** (read in `Meciuri/index.html`, left unchanged).
  *Supporter*: three buttons on each match card (home, Neutral, away),
  pressing the chosen one clears it, stored as `supported` in `mf_personal[id]`;
  nothing chosen by default. *Record*: counted only where `supported` is home
  or away (a draw is a D, otherwise W or L by the side supported, from the
  match `score`), shown only when at least one counted, else a hint; it did not
  say how many matches were counted. *Add a match*: a text box taking one
  match object or a list, `JSON.parse`d, **only `id` was required**, a repeated
  id replaced the stored one, stored in `mf_imported`, merged into the list by
  date. *Save a copy*: dumped `{personal, imported}` as text into the same box
  to copy by hand, no file. *Photos and videos*: file input
  `accept="image/*,video/*" multiple` from the gallery, **no size or count
  limit** (only the browser's quota; a `QuotaExceededError` said "no room"),
  the file stored as a blob in IndexedDB `mf_media` (store `items`, index on
  match id), a 3-column square thumbnail grid (`<img>`, or `<video>` with a
  VIDEO tag), tap for a full-screen viewer with Close and Delete (asks first),
  object URLs revoked on redraw, a "used of quota" line and a storage
  persistence request and line.
- **Reproduced** with the same behaviour, in the new keys' own names:
  *Supporter buttons* on every match sheet (imported ones too), same field
  name and shape, `football-attended-personal` = `{entry key: {supported:
  "home"|"neutral"|"away"|""}}` beside note/ticket/seat/block/withWho; a
  press on the chosen button writes `""`. *Record* on My stats from the
  matches with a supporter chosen, **with "n of total matches counted"** so
  it does not look complete when it is not; Neutral, no choice and a score
  that is not `N-N` are not counted (as the old app), and the stats say so.
  *Add a match* on My attended matches (a collapsed box above the list; since 2026-10-13 a form with the JSON box at its end - see the entry below).
  *Photos and videos* on match, imported-match and event sheets: same
  inputs, grid, viewer and delete (from the viewer, asking first), quota and
  persistence lines, and the **same absence of limits of our own**.
- **Where it differs from the old app, on purpose.** (1) The import is
  **validated whole** and refused with a reason if anything fails: the old
  format's fields are checked by type (unknown fields are refused, so a typo is
  not silently dropped); required are `id` (1-80 of letters, digits, `.`, `_`,
  `-`), `date` (a real day), `home.name`, `away.name` and `score` ("2-1");
  at most 50 matches and 200,000 characters per paste and 300 imported matches
  in all. (2) **A clashing id is refused**, never replaced: a match whose id
  the file already uses, that is already imported, or that appears twice in
  one paste. (3) A file that is not an image or video type is refused by name
  (the old app stored it as an "image"). (4) Persistence is requested on the
  first add, not on every opening. (5) A device-only **"Remove this imported
  match"** control (asks first; deletes its notes, supporter choice and
  media) - not requested, added because an import could otherwise not be
  undone.
- **The Add a match form, 2026-10-13.** The collapsed box on My attended matches is now a form (labelled fields, errors next to the field, Save and Cancel, in the Me forms' style) with the JSON box kept at its end, labelled optional. Fields and the validator's own names they are stored under: Date `date` (required), Kick-off `kickoff` (HH:MM, no source), Home team `home.name` and Away team `away.name` (required), Score `score` (two number boxes stored as "H-A", required), Competition `competition`, Stage or round `stage`, Stadium `stadium`, City `city`, Attendance `attendance.value` (whole number), Referee `referee`, Note `note` (plain text, up to 2000 characters), and a repeating "Add goal" row stored in the validator's goal shape `{team: "home" or "away", player, minute}` (a list that does not add up to the score is allowed). The user never types an id: it is generated as date and team names, ASCII, at most 80 characters, with `-2`, `-3` on a clash with the file's ids or the imported ones. The record goes through **the same validator, `attCheckMatch()`, as every import**, so nothing is accepted that a paste would refuse; ticket, seat, block, who I went with, My notes and the supporter buttons stay on the match sheet. **Merge rule: with the form completely empty the JSON box behaves exactly as before (one object or a list, `id` required, up to 50). With the form partly or fully filled the JSON must be one object, merged into the form's match at leaf level: a leaf both fill (goals count as filled when the form has goal rows) is refused with the key named and nothing is stored, a key the form left empty may come from the JSON, objects merge, required fields may come from either, and the merged result is validated whole.** An imported match's sheet has **Edit this match**: the same form pre-filled from the stored record, same id (so its notes, supporter choice and photos stay attached), replacing only the fields the form covers - line-ups, timeline, stats, `kickoffSource`, a goal's `pen`/`added`/`assist` and a stored `{ro, en}` text the user did not change stay untouched; the JSON box is hidden while editing. A note typed on an imported match is the user's own, so the sheet does not label it "Written by an assistant". Changing the language redraws the tab and clears an unsaved form. Tested in `tools/test_me.js`.
- **The Add an event form and imported events, 2026-10-13.** The Events sub-tab has a collapsed "Add an event" above the list, built on the match form's helpers and styles, same device-only rules as imported matches. **Storage:** the same record `football-attended-imported`, as an optional `events` array beside `matches` (`{version: 1, matches, events}`; `events` is left out while there are none; a stored record without it reads as no events and is not rewritten by reading; a stored event that no longer validates is left out and counted on the tab). **Own id space:** an imported event is addressed as **`impev:` + its id** (an imported match is `imp:` + id, a file entry its plain id), and its personal fields and media are kept under that address; the prefixes cannot meet, since ids hold no colon. **Fields are exactly the ones the three file events hold** (`id`, `date`, `title`, `place`, `note`, `atStadium`; unknown fields are refused by `attCheckEvent()`, the event validator): Name `title` and Date `date` required, Place `place`, a Yes/No "I was at the stadium" `atStadium` (default No, stored false; ticket, seat and block appear on the sheet only when true, as for file events), one "Factual note" `note` (plain text; a stored `{ro, en}` pair is kept when untouched). Limits: 300 characters for title and place, 2000 for note. **The id is never typed**: date and name, ASCII, at most 80, unique across **all four id spaces** (the file's events and matches, imported matches, imported events), `-2`, `-3` on a clash; the match form's generator now also avoids event ids. An explicit JSON id is refused if it is used in any of the four spaces. **JSON box (optional, at the end), same merge rule as the match form**: form empty = one object or a list as a plain import; form filled = ONE object merged leaf by leaf, a leaf both fill refused with its key named and nothing stored, a key the form left empty may come from the JSON, the merged result validated whole (all reasons shown). **The Yes/No counts as filled only when Yes**: a default No leaves `atStadium` to the JSON, and says false if the JSON has none. Limits, counted apart from the matches: 50 per paste, 200,000 characters, **100 imported events in all**. An imported event's sheet is marked "Imported on this device", has **Edit this event** (same form pre-filled, same id; notes and media stay attached; the JSON box is hidden) and **Remove this imported event** (asks first; deletes its personal fields and media), and its note is the user's own, so it carries no "written by an assistant" label. **Nothing in an imported event is checked for card numbers** (as for imported matches; only the personal fields ticket, seat, block and who I went with are). Tested in `tools/test_me.js`.
- **xG, saves, passes and player ratings on a match, 2026-10-25.** Checked by `attCheckMatch()` (the same validator for a paste, the form's JSON box, an imported file and the stored list); no separate add-a-match spec file exists in the repo, so this entry and the validator are the spec. `stats` keeps its six keys (`possession`, `shots`, `onTarget`, `fouls`, `corners`, `offsides`: two numbers 0-1000, unchanged) and gains `xg` (`[home, away]`, numbers 0-100, decimals ok), `saves` (`[home, away]`, whole numbers 0-1000) and `passes` (`[[madeHome, totalHome], [madeAway, totalAway]]`, whole numbers 0-5000, made not above total, a total of 0 is allowed). `lineups.<side>.xi[]` items gain an optional `rating` and `lineups.<side>.subs[]` items an optional `onRating` (the player who came on): numbers 0-10, decimals ok. `null` counts as absent. `bench[]` items are unchanged, so a `rating` there, or a `rating` on a sub, is refused as an unknown field, and any other unknown key is still refused. Drawing: the new stat rows come after the six, only when present, in the same bar style; passes read like "88% (532/606)" (percentage rounded by the app, bar sized by passes made), a total of 0 shows a dash, xG shows at most two decimals. A rating is drawn with one decimal: left of the shirt disc on the pitch picture, as a small grey pill after the name in the list view and after the player who came on in the subs list; with no rating nothing is drawn and a match without the new fields has the same markup as before. Nothing here is fetched or inferred: a value missing from the source stays missing (rules 1-2). Tests: `tools/test_me.js`, block "xG, saves, passes and player ratings".
- **Exhibition and suggestions in the Add a match form, 2026-10-15.** An imported match accepts an optional boolean `exhibition` (any other type is refused; unknown fields still are). The form has a Yes/No "Exhibition match", default No: `"exhibition": true` is stored only on Yes and omitted otherwise; in the JSON merge rule it counts as filled **only when Yes** (a default No leaves it to the JSON, as for an event's `atStadium`); Edit shows the stored state and sets or removes it; a small "Exhibition" tag is on the match card and the sheet header. The **Competition** and **Stadium** fields show suggestions as you type (`wireSuggestions()`), in the club search's style: a list directly under the field **in the page flow** (never over a button), matching with the search's `fold()`, names that start with what was typed first, then a word that does, then the rest, up to 8 rows plus "+ n more", its height capped by `visualViewport` so it ends above the keyboard. A row fills the field with the name as written and closes the list; free text still works; Enter closes the list and keeps what is typed (it does **not** save the form from these two fields); leaving the field keeps it. **Stadium** rows: the venue of every club in the club files (`CLUBS`) plus the stadiums of the file's and the imported matches, one row per folded name, second line the club(s) playing there and the country; filling it does not fill the city. **Competition** rows: "Friendly" and "Exhibition" (shown through `t()`, stored as the English word; tapping "Exhibition" also sets the toggle to Yes, no other row does), every name of `data/competitions.csv` (loaded lazily through the page's `csvFile()` when the form opens; if it cannot load the other sources still work), the leagues the coverage panel lists, and the competition texts of the file's and imported matches. **Home team and Away team (2026-10-16)** have the same kind of list (`sugTeams()`, `data-sug="team"`, the same code path: `sugSearch()`, `sugShow()`, `sugPick()`, keyboard and placement), two independent fields. Rows: every club of `CLUBS` in every country (the name exactly as the club file has it; one row per folded name **and** country, so the same name in two countries is two rows), plus every team name used in the file's and the imported matches that no club of `CLUBS` carries by folded name (the English text, `nameEn` when there is one, otherwise `name`, or `en` of a `{ro, en}` pair; typing the stored `name` also finds it; a national team is one). A match team whose name is a club's is that club's row, not a second one: a team only in his matches has no country, so the country test cannot separate it. **Second line**: country and competition as the club search shows them (`competitionLabel()`, "league not recorded (tier N)" where that applies) for a club, "Used in your matches" (`sug.usedInMatches`) for a team only in his matches. **Order**: names starting with what was typed, then a name with a word that starts with it, then the rest; within each, the more senior tier first (a team only in his matches last), then name (`sugSearch()` sorts by tier now; the other two lists carry no tier and sort as before). A row fills only that field (and tells the goal rows' team menu, which shows the typed names); it fills nothing else, free text is saved as typed, and Edit opens the stored names unchanged. No new storage key, no request. Names are data, never translated; nothing is stored and no request is made beyond that one GET. Tested in `tools/test_me.js` (expected values worked out from the files; the team lists are checked against the club files and the match file by the test itself).
- **Imported matches** live only under `football-attended-imported`
  (`{version: 1, matches: [...]}`), are marked **"Imported on this device"**
  in the list and the sheet, are in the list (sorted by date, the file's
  matches first on a tie) and the stats, and have **their own id space**:
  an entry is addressed as `imp:` + its id for its supporter choice, notes and
  media, so it can never meet an id of the file even if the file later gains
  one. A stored imported match that no longer validates is left out and
  counted on the tab. **A line is Alexandru's own data**: nothing checks the
  facts in it.
- **Media** live only in the IndexedDB `football-attended-media` (store
  `items`, one record per file: `entryId`, `name`, `mime`, `size`, `kind`,
  `added`, `blob`), keyed by entry id. Nothing is committed, exported or sent.
  If the browser refuses the database the sheet says so ("refuses to store
  photos and videos here"); a quota error names the file ("no room left").
- **The Me export is version 3** (since 2026-10-13; version 2 before). It holds, besides the memberships, tickets,
  favorites and renewal window, `personal` (the personal fields **and the
  supporter choices**, keyed by entry), `importedMatches` and, **from version 3, `importedEvents`** (validated whole by `attCheckEvent()`, at most 100, ids free in all four spaces and not repeated; a version 3 file without the list is refused; the card-number rule applies to the personal fields of an `impev:` address like any other), and says
  `notIncluded: photos and videos`; **the media are never in the file**, and
  the Back up section and the export message say so. An import is checked
  whole: the existing card-number rejection also applies to the personal
  fields that the sheet checks (ticket, seat, block, who I went with; not
  "my notes", as on the sheet), `supported` must be home, neutral, away or
  empty, unknown fields are refused, and an imported match whose id the file
  already uses is refused (which loads `data/attended.json` to check). **A
  version 1 file (the Me tab's own, written before) still imports and leaves
  the attended records and imported matches alone, and says so.** **The old
  app's `{personal, imported}` dump is not a Me-tab export and is refused.**
  Replace semantics as before: a version 3 file replaces the device's
  personal records, imported matches and imported events; **a version 1 or 2 file leaves the imported events alone and the message says so**; a version newer than 3 is still refused (media of an imported match that the
  file drops stay in the database, unseen, until that id is imported again).
  The backup banner is raised by a supporter choice, a typed personal field,
  an import and a removal. `ME_VERSION` (the stored record's) stays 1; the
  file's is `ME_FILE_VERSION` 2.
- **Language.** New strings are in `I18N` in both languages; the `ro` ones
  are the assistant's, **"RO unchecked by the user"**. *(The toggle, in Settings at the top
  of the Me tab, was added later the same day: see "The interface is translated".)*
- **Tested** in `tools/test_me.js` (no new file), all read from the data: the
  supporter choice and the record with "n of total"; every invalid paste
  refused with nothing stored and a valid one stored under the new key and
  counted in the stats; all 23 file matches re-pasted with new ids accepted;
  the export round trip and its refusals; media added, thumbnailed, viewed,
  deleted, kept over a reload, refused storage and quota said clearly; no
  `mf_` key or database touched; nothing overflows at 390 px in English and
  Romanian. `SHELL_VERSION` is `v17`.

**The interface is translated, 2026-10-09.** Done on Alexandru's instruction.
The interface speaks English or Romanian; **text that comes from a data file
stays English** and **the Romanian is unchecked until he says otherwise**.
- **What is translated: every word the interface itself writes** - map
  (search, chips, legend, coverage, route and cost sheet, Near me, club sheet
  labels), Bucket list (filter, sort, group headings, labels, calendar),
  Ticket info, Competitions, Me (all four sub-tabs and sheets), empty states,
  error messages, the offline banner. All of it is in `I18N` (`en` and `ro`,
  identical key sets, checked by `tools/test_me.js`) and used through `t(key,
  vars)`, `tn(key, n)` (key.one / key.other) and `vocab(prefix, word)` (a data
  word the interface can say, otherwise shown as the file wrote it). Dates use
  `toLocaleDateString(LOC())` and numbers `nf()` / `nfg()`, so Romanian shows
  month and weekday names and a decimal comma; `<html lang>` follows.
  **Not translated, on purpose:** everything a data file holds (rule texts,
  notes, `why` texts, titles, names, derby names, source titles, league names,
  the values of closed vocabularies a tag shows that the interface has no word
  for), the English month names the code READS in data texts (`MONTH_NAMES`),
  the `.ics` property names, and the export file's `notIncluded` sentence.
  Areas written from data carry `data-content` (the test skips them).
  `NOTE_LABEL` translates the field names of `football-rules.json` entries
  the files use today; a new field name shows as its English fallback.
- **The toggle is in Settings**, a small button at the top of the Me tab (no
  new tab) that opens a sheet with English and Română. The choice is kept on
  the device only under `football-planner-lang`, default English, and no
  `mf_*` key is read. **It applies at once to what is open**: map chips and
  legend, the open club sheet, route, Near me, coverage and filter panels, the
  Bucket list and calendar and their sheet, Ticket info, Competitions and its
  sheet, the Me sub-tabs and an open match sheet, the offline banner.
  **Not redrawn at once:** a Me form being filled in (typed text is never
  thrown away; its labels change when it is closed and opened again), a
  message already shown (a Me import or export message, the Near me location
  message, the attended paste box message) which stays in the language it was
  written in until the next one, and names stored when made (a saved route's
  default name). Ticket info closes the cards that were open.
- **Romanian: unchecked.** Written by the assistant, kept under the comment
  "RO unchecked by the user" in the dictionary. `docs/ro-review.md` is the
  whole dictionary as a table of key, English and Romanian, in dictionary
  order, for reading on a phone; regenerate it after any dictionary change.
  Plurals have two forms (one / other); since 2026-10-11 a key may have a third,
  `key.many`, used only in Romanian for a count of 20 or more whose last two
  digits are 00 or 20-99 ("20 de meciuri", "101 meciuri"), and a key without it
  keeps using `.other`. Only the stats footnote (`st.nGoals`, `st.nMatches`) has it
  so far, so other Romanian counts of 20 or more still lack the "de" ("20 de
  cluburi"); nobody has checked the wording of any row.
  The sub-tab "Tickets" became **"Tickets/Memberships"** (Romanian
  "Bilete/Abonamente"); the four sub-tabs fit at 390 px in both languages
  by sizing each tab to its label (`flex: 1 1 auto`, 13 px): all four sit on
  one line at 390 and 360 px, in English and Romanian, and on a narrower
  screen a label wraps at the slash instead of overflowing. The bottom bar's
  Romanian "Lista de dorințe" would have run into its neighbour, so its
  label there is "Dorințe" (a test checks all five fit their slot). The tab has no heading of its own
  beyond its two section headings ("Tickets held - N", "Memberships - N",
  in that order since 2026-10-15), which were left as they were.
- **Tested** in `tools/test_me.js`: identical key sets, no `ro` value equal to
  its `en` value except a short whitelist of names and units, every
  `{placeholder}` kept, the choice kept over a reload, and in Romanian every
  main tab, the four Me sub-tabs, the panels and the sheets free of English
  interface text and without sideways scroll at 390 px. A scratch scan for
  English function words found only data-file text. `SHELL_VERSION` is `v18`.

**Romanian translations of data texts, 2026-10-11: derived data, the English file is the original.** Built on Alexandru's instruction. **Translations are derived data** in `data/ro/<source>.json` (one file per translated source: `football-rules`, `derbies`, `club-ticket-windows`, `club-ticket-phases`, `club-ticket-rules`, `club-ticket-demand`, `country-ticket-rules`, `event-ticket-rules`, `competition-info`): an entry is keyed `<rowKey>#<field>` and holds `en` (an 8-digit fingerprint of the English it was made from), `ro` and `status` (`machine-unchecked`: **the Romanian is unchecked** - written by an assistant, not read by Alexandru, and listed in `docs/ro-review.md` under "Texts from data files"). **The English data file is the original and is never changed by a translation.** **Editing the English makes its entry stale**: the fingerprint no longer matches, the page shows the English again, and `tools/check_translations.py` warns "STALE" until somebody retranslates it - nothing is ever shown as a translation of text it was not made from. Rules 1 and 2 hold: a translation adds no date, rule or number the English does not have, and the checker fails a Romanian that lacks a number group, an ISO date or a URL/domain of its English.
- **Fingerprint**: 32-bit FNV-1a over the UTF-8 bytes of the text trimmed of space, tab, newline, carriage return, form feed, vertical tab and NBSP, as 8 lower-case hex digits; `fnv1a()` in `index.html` and `fingerprint()` in `tools/check_translations.py`, tested against `tools/translation-fingerprints.json` (accented, padded and astral strings) by the checker and by `tools/test_me.js`.
- **Row keys**: `football-rules` rows are `bucketList:<id>` and `clubs:<id>` with the path of the leaf as the field (`why`, `trigger.action`, `unblockCondition[1]`); the CSVs join their key columns with `|` (derbies `clubA|clubB`; windows `clubQid|team|window`; phases the same plus `|phase`; rules `clubQid|team|scope|opponentQid|topic|season`; demand `clubQid|team|scope|opponentQid|season`; country rules `country|topic|appliesTo|condition`; event rules `bucketId|scope|opponentQid|topic|season`; competition info `competitionId|topic|sourceId`).
- **What is translated** is the registry in `tools/check_translations.py` (the page's `TX_*_PATHS` and its `tx()` call sites mirror it; `test_me.js` compares the two leaf by leaf): the visible prose of the data files. **Kept, not translated**: names (clubs, derbies, competitions, holidays), source titles and publishers, URLs, ids and codes, original-language quotes (friendship quotes, the German quotes inside `pastCycle`), dates, and `data/attended.json` (it already holds `{en, ro}` objects). **Not drawn, so not translated**: every `note` column of the ticket files (club-ticket-prices alone holds 143,858 characters of them), `ticketEvents`, `offMap`, `bucket-links-manual.csv`, and `competition-sources.csv`'s `note` (a hover title only).
- **The page**: `tx(source, rowKey, field, enText)` returns the Romanian only when the language is Romanian, the "Show original English for data texts" switch is off, an entry exists and its fingerprint matches; otherwise the English. Text it translated carries `lang="ro" data-tx="ro"`; English left in a Romanian page carries `lang="en"`; **the English view carries no new attribute at all**. `data/ro/*.json` is fetched only when the language is Romanian, network first through `getJSON()` like every data file, so the existing offline copy covers it; a file that cannot be loaded leaves its texts in English and is retried at the next language change. A sheet, panel or tab that holds translated text ends with "Automatic translation, English is the original." (`tx.note`; a MutationObserver adds and removes it). A competition text the page shortens to its month (`monthOnly()`) is shown in English. **The switch** (Settings, `football-planner-tx-original`, default off, device only, never in the Me export) shows the English originals everywhere while the interface stays Romanian.
- **Codes in words**: a code from a ticket file that reached the screen raw now goes through `vocab()` with a prefix of the dictionary: topics (`tp.`), scope (`scp.`), competition (`cmp.`), stage (`stg.`), opponent tier (`ot.`), price class (`pcl.`), price kind (`pk.`), price basis (`pb.`), demand outcome (`oc.`), who may buy (`ac.`), how it sells (`sm.`), request types (`rq.`), closes early (`ce.`), demand (`dm.`), resale (`rs.`), update tracking (`ut.`), minors (`mn.`), authority kind (`ak.`), cut-short link (`uc.`), window basis (`wb.`), window code (`wn.`). **The English label is the code itself**, so the English view is unchanged (a prettier English word is a separate decision); a code with no key is shown as the file wrote it. Seat categories (`kat-1-mitte-1`, `terzo-rosso`) are the clubs' own labels and stay as written. `data/ro-glossary.csv` (`english, romanian, note`) holds the terms from the interface dictionary that translations must use; the checker warns when an English term is there and its Romanian is not.
- **Pilot, 2026-10-11**: the `why` of the first 25 Bucket list entries that have one, in the List's own (Group) order: 25 of 361 translatable strings of `football-rules.json` (2,729 of 32,317 characters). Everything else is untranslated until a later pass.

**Colours live in CSS variables, and the light map falls back to dark,
2026-10-09.** Done on Alexandru's instruction.
- **Theme.** Settings (the button at the top of the Me tab) has a **Theme**
  group, **Dark** (the default, the look the app always had) and **Light**,
  kept on this device only under `football-planner-theme` (`light` or `dark`;
  anything else is dark; no `mf_*` key is read). A tiny inline script in
  `<head>`, before the stylesheet, sets `<html data-theme>` and the
  `theme-color` meta before first paint, so there is no flash of the wrong
  theme. Labels go through `t(key)` (`set.theme`, `set.theme.dark`,
  `set.theme.light`, `set.themeNote`, `map.lightUnavail`), `en` and `ro`, the
  Romanian **unchecked by the user**; `docs/ro-review.md` has the five new rows.
- **Every colour in `index.html` is a variable**: a dark set in `:root` and a
  light set in `:root[data-theme="light"]`. Nothing else in the file holds a
  hex, `rgb()` or `hsl()` literal (`tools/test_me.js` fails if one appears)
  **except**: the two copies of the dark and light `theme-color` in the
  pre-paint script and the meta tag (a script that must run before the CSS
  cannot read it). Not themed on purpose, defined once in `:root`: the photo
  viewer (always black: `--media-*`, `--scrim`) and the line-up pitch (always
  grass: `--pitch-*`). Map markers need real colour values, so
  `syncPalette()` reads `--t1`...`--t8`, `--route`, `--pin-ink` and the two ink
  colours from the CSS at start-up and on every theme change; HTML uses
  `var(--tN)` through `tv()` and `tierStyle()`. **A new colour goes in as a
  variable in both sets, never as a literal.**
- **The pre-paint script also sets the root `color-scheme`** (inline), so the canvas before the stylesheet loads, scrollbars and the browser's own controls follow the theme; in dark that is the one visible difference from before (they were left light).
- **Dark was kept except two values, both for contrast (4.5:1)**: `--faint`
  `#6b7681` to `#808b97` (3.7:1 on the panel before) and `--accent`
  `#d9483b` to `#ea6a5a` (the calendar's today number, 4.3:1 on its cell), and
  placeholders now use `--faint` (the browser default was 4.1:1).
- **The light map is Stadia's Alidade Smooth**
  (`tiles.stadiamaps.com/tiles/alidade_smooth/{z}/{x}/{y}{r}.png`, the light
  sibling of the dark style already used), the same domain authentication, no
  key, nothing cached, one credit per tile as before. The style name and URL
  shape were confirmed only from search results: the Stadia docs page was not
  opened (the sandbox cannot reach Stadia). **If four light tiles fail in a row
  while the phone is online, the page uses the dark tiles for the rest of the
  session and shows a short note ("The light map is unavailable...");** the
  stored choice stays Light, a reload tries the light tiles again, and a late
  failure of a tile asked for under the old style is ignored. Offline, or
  when the dark tiles fail too, the existing "needs a connection" card is the
  only message.
- **Light palette.** Tier colours are deeper in light so they stand out from
  pale tiles and keep 4.5:1 as tag text (`--t1` `#c9301d`, `--t2` `#9c5c00`,
  `--t3` `#1769c2`, `--t4` `#0f7f69`, `--t5` `#237a2e`, `--t6` `#7440c0`,
  `--t7` `#cc3a78`, `--t8` `#6a4726`; route `#0a3fbf`); the marker outline and
  the shared-ground ring switch to dark ink on light tiles. Checked in
  `test_me.js` on both themes: the eight tiers and the route pairwise at least
  10 apart in CIE76 colour difference (the dark route `#58a6ff` against tier 3
  `#3fa0e8` is the closest pair, 11), and every colour or its outline 3:1 against
  the map background. **There are no Near me markers on the map** (the list
  has none); the route's A and B pins use `--route`.
- **Not seen on a real phone or against Stadia**: the tiles are stubbed, so
  what the light map looks like under the markers was not looked at.
  `SHELL_VERSION` is `v19`.

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
- **Order on the Tickets/Memberships sub-tab (since 2026-10-15)**: the backup
  banner and the "kept on this device" note, then **Tickets held** (its Add
  ticket button, the list, the collapsed Past section, and the note about
  linking a ticket to a bucket entry), then **Memberships** (its Add
  membership button, the renewal-window setting and the list), then the
  alerts note and the Back up section last. Memberships came first until
  then; only the order changed, no field, text, count, sort or stored data.
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
  (`v1` → ... → `v11` → `v12` → `v13` → `v14` → `v15` → `v16` → `v17` → `v18` → `v19`; it has been `v40` since 2026-10-20, when Portugal's country file joined `COUNTRY_FILES` and the page learned its name and fixture coverage; it was `v39` from 2026-10-19, when `drawClubs()` began to draw only grounds inside the visible bounds plus 50% padding; it was `v38` the same day, when a reserve side's sheet began to point to its first team's sheet; it was `v37` from 2026-10-18, when rivalries began to show on the rival's sheet too; it was `v36` the same day, when the Row personal field shipped; it was `v35` from 2026-10-17, when rivalry rows began to show a source quote; it was `v34` from 2026-10-16, when the Home team and Away team fields of the match form got their suggestion lists; it was `v33` from 2026-10-15, when a friendship stated on one club's page only began to show on the friend's sheet; it was `v32` the same day, when exhibition matches left the goal stats and the match form got its suggestions; it was `v31` the same day, when the Me tab's Tickets/Memberships sub-tab began showing tickets first; it was `v30` from 2026-10-13, when the Add an event form and the version 3 backup file shipped; it was `v29` the same day, when the red-cards card and the event `note` shipped; it was `v28` the same day, when the Add a match form shipped; it was `v27` from 2026-10-12, when the researched kick-off times shipped (the five `user-supplied` kick-off times of 2026-10-13 arrived with no version change: a change to `data/attended.json` alone needs none); it was `v26` from 2026-10-11, when the Romanian translations of data texts shipped (`v25` before that, when sheets and panels learned to expand to full size); it was `v23` from 2026-10-10, when the source quote on fan friendships shipped; it was `v22` the same day, when the atmosphere section was removed; it was `v21` the same day, when the atmosphere section was reduced to recurring occasions with a recurrence; it was `v20` from 2026-10-09, when Fan friendships shipped; it was `v19` the same day, when the Light theme shipped; it was `v18` the same day, when the whole interface was translated (it was `v17` from the same day, when the imported matches, supporter buttons and media shipped); it was `v16` from the same day, when the attended detail sheet shipped; it was `v15` from the same day, when the Me tab's attended matches and events shipped; it was `v14` from the same day, when the atmosphere section shipped (`v12` and `v13` were bumped without being recorded here); it was `v11` from 2026-10-08, when the Competitions tab and the Bucket list filter shipped, `v10` before that, when the Reminders came out, and `v9` before that, since
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
something to discover. **Since 2026-10-19 only grounds inside the visible
bounds plus 50% padding get a marker, and the chip's club and shared-ground
counts are still taken over every club the zoom shows, drawn or not, so a
shared ground just off screen is counted and has no marker until the map
moves toward it.**

**Tier zoom bands: tier 3 and everything deeper switch on together at
z9, and that is a GUARANTEED PROPERTY, since 2026-10-03.** At z9 - the
zoom tier 3 used on its own before - **every club inside the visible
bounds plus 50% padding is drawn, whatever its tier**, and at every zoom
above it (changed 2026-10-19 from "every club on the map": `drawClubs()`
now gives a marker only to a ground inside `MAP.getBounds().pad(0.5)`,
and the redraw on `moveend` and `zoomend` draws the grounds a move
brings in; a club farther out is on the map in every other sense - the
corner chip, search, Near me, the coverage panel and the sheets count and
reach it - and is drawn as soon as the map is there). Tiers 1 and 2 keep
their thresholds (z0 and z7), so the country view is unchanged.
`TIER_FROM_ZOOM` lists tiers 1 and 2 only and `zoomForTier()` gives
every tier from 3 down `DEEP_TIER_ZOOM`, 9, so a tier 9 or 10 club found
later needs no change. The map's `minZoom` is 3 (it was unset), and
`zoomDelta` and `zoomSnap` are 1 - Leaflet's defaults, **checked in the
vendored copy and on the live map rather than assumed**, and now also
set explicitly - so the map always rests on a whole zoom and is either
below 9 or at it. **`tools/test_zoom.js` holds the property**: it fails,
naming each club, if any club inside the padded bounds is not drawn at z9,
and it runs on every change to the page. First run: 556 of 556 clubs drawn
at z9 (when every club was drawn).
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

**Visible-only drawing, measured and built 2026-10-19.** Measured the same day on a SYNTHETIC benchmark of 1,865 clubs (the 565 real clubs plus 600 generated tier 1 and 700 generated tier 2 clubs, Alexandru's figure for the load test; it is not a count of anything real - the club files on `main` hold 565 on the map, and 565 is the real count): redrawing every marker with SVG cost 123-147 ms for `drawClubs()` and 215-266 ms for a zoom step at z7-z9 at 4x CPU; drawing only the clubs inside the padded visible bounds cut z7 to 21 / 43 ms and z9 to 5 / 12 ms (draw / zoom step); at z3-z5 everything is in view and nothing changes. **Those four figures (123-147, 215-266, 21 / 43, 5 / 12 ms) are the synthetic benchmark's, not the real map's; the new-against-old timings of the visible-only drawing ("Measured on this branch with the repo's 565 clubs", below) were measured on the real 565 clubs, by `tools/test_zoom.js`.** **Built** in `drawClubs()`: the tier rule and the grouping by exact coordinate still run over every club, so the chip counts every club and shared ground the zoom shows; only a ground inside `MAP.getBounds().pad(0.5)` gets a marker. It redraws on `zoomend` and `moveend` (through `redrawOnMove()`, which skips a move that stays inside the last redraw's padded bounds at the same zoom, so a zoom - `zoomend` then `moveend` - draws once and a pan of up to half a screen costs nothing, and an open ground popup is not closed by its own auto-pan), and, as before, after the club files load, a language change and a theme change (those call `drawClubs()` itself, which always redraws). A map measured at zero size draws everything, as before. **Measured on this branch with the repo's 565 clubs** (`tools/test_zoom.js`, 4x CPU, median of 15, `drawClubs()` / zoom step to painted frame, new then old): z7 Ruhr 15.1 / 38.5 ms against 45.9 / 77.3; z8 Ruhr 4.7 / 18.4 against 57.0 / 92.0; z9 Ruhr 6.8 / 11.1 against 64.1 / 105.7; z9 Bucharest 4.0 / 11.0 against 51.2 / 81.4 (18 pairs are printed by every run). **Places that could have expected a marker for an off-screen club, checked:** `goToClub()` (flies first; its sheet opens on `moveend`, which draws the club first), the search, the Near me and coverage rows (all call `goToClub()`), the route panel and the derbies panel (their rows call `openSheet()` on a club from `CLUBS` directly, with no marker and no flight; a route's `fitBounds` ends in a `moveend`, which draws what the route passes), the sheet's ground-mates (built from `CLUBS`; a mate or a rival tapped in the sheet goes through `goToClub()`), the legend's shared-ground row and the corner chip (computed over all grouped clubs). Nothing reads a marker except the tests, which fly first.

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

- **A merge is not live until Pages says so (2026-10-25).** The site is
  published from the repo root by GitHub's "pages build and deployment"
  workflow, and `.nojekyll` next to `index.html` keeps Jekyll out of it
  (`test_pwa.js` fails without it). After a merge, the latest run named
  "pages build and deployment" for the merge commit must have conclusion
  `success`; until then the merge is not live. Check with
  `curl -s "https://api.github.com/repos/AlexGrozavul/Football/actions/runs?per_page=5" | jq -r '.workflow_runs[] | [.name, .head_sha, .conclusion] | @tsv'`
  (curl has no `--jq` option; that is `gh`, which is not authenticated here).

---

## Adding a country: the places to touch

Read off the Belgium and Greece wiring on 2026-10-20 (Portugal pass); keep it in step when a file below changes.

**Start with `propose-country.yml` (2026-10-21).** Dispatch it on `main` with the country code, the country's Wikidata item, the tier 1 and tier 2 season articles (en dash), the third- and fourth-tier articles as `below_articles` (separated by `;`, they are the independent statement a `skip` needs) and the extra label languages. In about a minute (Portugal: 34 s of job time) it commits `data/clubs/proposal-<CC>.csv` and `.md`: the leagues and their P3983/P17, the trap items, every candidate with its evidence, the printed `league-tiers.csv` and `league-rosters.csv` rows, the `COUNTRY_BOX` proposals, football-data.org candidates, the StadiumDB slug found by probe, the proposed grounds, positions and capacities, and **this list below with the line numbers of the most recently added country**. Read the `.md`, then wire with its patch. **What stays manual** (the tool never does these): every `clubs-manual.csv` row (each `skip` needs two complete division articles agreeing on the absence and an independent statement, the Hermannstadt standard; each tier, ground, capacity, `<clear>` and hand-named row is a decision), the `roster-links-manual.csv`, `fixture-links-manual.csv` and `coordinate-reviews.csv` rows, every position the tool could not find (OpenStreetMap is asked by the tool since 2026-10-21, but only **around a position some other source already gave**: a club with no ground position anywhere gets no OpenStreetMap search, see Known open problems, "Overpass and robots.txt: resolved"), the `index.html` edits, the CLAUDE.md entry, the dispatches of the checks below on the branch, and the merge.
- **Hand-written data**: `data/league-tiers.csv` (one row per league: Q-id from the league article's enwiki sitelink, read by probe, never remembered); `data/league-rosters.csv` (the 2026–27 article, en dash, a complete table); `data/clubs-manual.csv` (skip, tier, ground, hand-named rows); `data/roster-links-manual.csv` (reserve rows the reader refuses); `data/coordinate-reviews.csv` (`open` or `rejected` rows for clubs left unplaced); `data/fixture-links-manual.csv` (abbreviations).
- **`tools/fetch_clubs.py`**: `COUNTRIES` (code, P17 Q-id, name), `COUNTRY_BOX` and its comment, `COUNTRY_NAMES` (Q-id to name), and the label languages in the build loop.
- **Other tools**: `diagnose_p118_rank.py` `COUNTRIES` (P17 Q-id to code); `crosscheck_stadiumdb.py` `COUNTRY_PAGES` (the slug by probe: the `/stadiums/<slug>` that answers 200 with a table) and `EXTRA_PAGES` if the pyramid crosses a border; `link_fixtures.py` `CLUB_FILES`, and `FD_COUNTRY` if football-data carries a league of that country; `fetch_fixtures.py` only if football-data carries it; `build_calendars.py` time zone (usually there already).
- **Nothing to edit** (they read the folder or the lists above): `crosscheck_capacity.py` (every `data/clubs/XX.json`; the file code is the Overpass ISO code), `propose_coordinates.py` (`COUNTRIES`), `check_rosters.py` (`league-rosters.csv`; `RESERVE_MARKERS` only for a reserve naming it has not seen), `check_tickets.py`, `test_zoom.js` and `test_coverage.js` (they read `COUNTRY_FILES`), every workflow file.
- **`index.html`**: `COUNTRY_FILES`; `cn.XX` in `en` and `ro` and the `COUNTRY_NAME` list; `adj.XX` and `COUNTRY_ADJ` for a country with no fixtures; the `top` map of `noFixturesReason()` for a country whose first division has fixtures and its second has not; `fx.coverage` (`en` and `ro`) and `LEAGUE_CODES` if a football-data league is added; `iso.XX` exists for most codes. Then `docs/ro-review.md` (rows for new keys), `sw.js` `SHELL_VERSION` with its history line here, and the printed count in `tools/test_nearme.js` ("of N country files"). **`tools/test_pwa.js` counted twelve country files by hand** and turned the Portugal pull request's CI red on its first run (a bare number, so a grep for the country codes did not find it); it reads `COUNTRY_FILES` from the page since 2026-10-20 and needs no edit. Before the first push, run `grep -nE "=== [0-9]+|of [0-9]+ country" tools/test_*.js` and run the page tests locally (`NODE_PATH=<playwright> node tools/test_pwa.js /tmp/site /tmp` on a copy, the others with `.`).
- **Order that worked**: probe the league items and season tables, wire, build, classify every difference by the six shapes, hand rows, rebuild, then dispatch `check-rosters.yml`, `diagnose-rank.yml`, `crosscheck-stadiumdb.yml` and `crosscheck-capacity.yml` on the branch (`link-fixtures.yml` runs after the build).

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

