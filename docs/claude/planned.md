# Planned, not built

Moved byte for byte from CLAUDE.md (old lines 8491-8745, 2026-10-22). Long new entries go here; CLAUDE.md keeps only rules and index lines. Grep this file for the name you need.

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
