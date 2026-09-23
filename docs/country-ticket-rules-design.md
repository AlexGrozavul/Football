# country-ticket-rules.csv — design, 2026-09-23

**Status: proposed, not built, not populated.** The file does not exist
yet, deliberately: a hand-written file that `tools/check_tickets.py`
does not read would break the read-back convention from its first
row. The file and the checker change land together or not at all.

---

## What it is for

Some ticket-buying rules are not decided by any club. Italy is the
model case: named tickets, the fidelity-card requirement for high-risk
matches and reserved sectors, and residency limits set by the
Osservatorio Nazionale and the local Questura/Prefettura. Every Italian
club inherits them. Today they are written as **Inter's** rules, in
`club-ticket-rules.csv` lines 28–30, because there was nowhere else to
put them. The day a second Italian club is added they would have to be
copied, and two copies of one fact drift.

The country file holds the rule **once**, and every club in that
country picks it up in the layered read-back.

**Only the rules file gets a country counterpart.** Windows, phases,
prices and demand are each one club's own sale; no national body sells
tickets. A national rule that *shapes* a sale (away sectors only to
card holders) is a rule and goes here; the sale phase it produces stays
in `club-ticket-phases.csv`.

---

## The file

`data/country-ticket-rules.csv`. Header-driven, one sourced fact per
row, the same shape as `club-ticket-rules.csv` so a row can move
between them with the least possible rewriting.

| column | req. | meaning |
|---|---|---|
| `country` | yes | ISO 3166-1 alpha-2, upper case: `IT`, `DE`, `RO`. The same codes as `data/clubs/*.json` and `league-rosters.csv`. The country **whose authority issues the rule**, which is normally where the ground is — see *Which country applies* below |
| `authority` | yes | who issued it, as text: `Ministero dell'Interno`, `Osservatorio Nazionale sulle Manifestazioni Sportive`, `DFL`. Not a vocabulary — names are too varied |
| `authorityKind` | yes | open vocabulary, seeded `law`, `government`, `national-observatory`, `police`, `federation`, `league`. Says *what kind* of body, because that decides the boundary (below) |
| `appliesTo` | yes | which matches: `all`, or a `;`-list of league Q-ids from `league-tiers.csv`, or `unknown`. **Never blank** — a blank read as "all" would be exactly the default-fill rule 2 forbids |
| `condition` | yes | when the rule bites: open vocabulary, seeded `always`, `high-risk-match`, `away-sector`, `reserved-sector`. **Never blank**, for the same reason: Italy's card rule is *conditional*, and a row that loses its condition reads as "you always need a card", which is false and expensive |
| `topic` | yes | **the same vocabulary as `club-ticket-rules.csv`** — one `KNOWN` list in the checker for both files. Layering matches on topic, so a second list would silently stop the layers meeting |
| `rule` | yes | the fact, in words |
| `clubLatitude` | yes | closed vocabulary, below |
| `season` | no | a cycle like `2025-26`, when the source is about one season. Blank means the rule is standing |
| `confidence` | yes | closed, as in the rules file: `confirmed`, `inferred`, `unverified` |
| `basis` | yes | closed, as in the rules file |
| `ref` | no | the source document's item number (`I-6`), exactly as in the rules file |
| `sourceRefs` | no | ids into `ticket-sources.csv` |
| `source` | no | URL list, split the same way as everywhere else |
| `checked` | no | ISO date |
| `note` | no | free text. Quote it if it has a comma |

**Key:** `country`, `topic`, `condition`, `appliesTo`, `season`, `ref`.
`condition` is in the key because one topic can have an unconditional
rule and a high-risk one (`personalisation` always; `fidelity-card`
only on high-risk). `appliesTo` is in it because a league's rule and
the law can speak on the same topic. `ref` for the reason it is in the
rules key: one source item can split into two topics.

### `clubLatitude` — the one genuinely new idea

It says how to read a **club** row on the same topic, which is the
thing the layered view has to decide. Closed, because the checker's
behaviour depends on it:

| value | meaning | Italian example | what the read-back does with a club row on the same topic |
|---|---|---|---|
| `none` | clubs comply, full stop | named tickets and assigned seats | prints both side by side and **reports** "check these agree". It never picks one — both are hand-written, and if they disagree one of them is wrong, which is Alexandru's call |
| `may-add` | a floor; a club may be stricter | **none in the repo yet.** Residency limits looked like one and are not: it is the authorities, not the club, who add them, per match. The value is here because a floor is a real shape of national rule, not because a row needs it today | prints both; the club row is an addition, not a contradiction |
| `implements` | the rule requires a scheme and each club runs its own | the fidelity card: the law requires one, Inter's is Siamo Noi at EUR 15 | prints the country row as the frame and the club row as the implementation, together |

**A club row never replaces a country row.** That is the difference
from derby layering, where a derby row does replace the club's general
row on the same topic. A club cannot override a law; at most it adds
to it or implements it.

### Sources

`ticket-sources.csv` gains one optional column, `country`, beside the
existing optional `club`. A source cited by a country row fills
`country` and may leave `club` blank. A source cited by both files —
I7 and I8 will be — keeps one row and one id; there is no reason to
copy a citation.

### `club-tickets.csv` gains `country`

The layered view has to know which country's rows apply to a club.
Nothing in the ticket files says so today, and it cannot be read from
`data/clubs/*.json` for Inter, because there is no Italian club file.
So: an optional, **hand-written** `country` column on
`club-tickets.csv`, meaning the country of the club's ground.

- Blank is allowed and is **said out loud**: the layered view prints
  "country not given — no national rules applied" for that club,
  rather than quietly showing a club view with the national layer
  missing.
- Where the club *is* in a `data/clubs/*.json`, the checker compares
  and **reports** a mismatch. It does not fill a blank from that file:
  two sources for one fact is a conflict waiting to happen, and the
  hand-written one wins (rule 3).

---

## Which country applies

**The venue's, for law and policing; the competition's, for league
rules.** Stated because it will be tested:

- Bayern away at Inter in the Champions League: Italian law applies
  (named ticket, and the away-sector conditions). German rules do not
  follow Bayern fans abroad.
- A `derby-away` row today does not fall through to the club's general
  rows, because those describe home sales. **Country rows do fall
  through for an away leg — the venue country's.** For both current
  derbies that is the same country as the club's.
- A club that plays in another country's pyramid (Liechtenstein's
  clubs in Swiss leagues — FC Triesenberg was the case on the map) is
  under the law where its ground is and the rules of the league it
  plays in. **This design does not handle that case**, and says so
  rather than pretending: the layered view joins on the club's
  `country`, so a Swiss league row would not reach a Liechtenstein
  ground. Fixing it would need the ticket files to record a club's
  league, which they do not. No such club has ticket rows today.
- **UEFA is not a country.** Its competition ticketing rules (away
  allocations, finals portals) do not belong here, and forcing them in
  under a fake country code would be wrong. If they are wanted they
  want their own file. Not proposed now.

---

## Where a fact belongs — the boundary

This is the part that will be tested on the first real row. The tests,
in order. The first one that answers decides.

1. **Is it about one fixture?** "The 2025-26 derby was classified
   high-risk", "there was a residency limit for this match" — that is a
   **fixture** fact, never a country fact and never a club's general
   fact. For a derby it goes in `club-ticket-rules.csv` with the derby
   `scope` and a `season`, as I-7 already does. For any other fixture
   there is **no home in the ticket files yet** (see open questions).
   *The country row says the category exists and who assigns it; which
   match is in it is not a country fact.*

2. **Who could change it tomorrow?** If the club could, by deciding
   differently, it is a **club** fact — even if every club in the
   country happens to do the same. If only a law, a ministry, a police
   authority, the federation or the league could, it is a **country**
   fact.

3. **Would it be true of a club in that country you have never read
   about?** Only if a source **that speaks for the country** says so:
   a government, the federation or league, a law, or press explaining
   the law. **A club doing something is never evidence the country
   requires it**, and neither are two clubs doing the same thing — that
   is a coincidence until a national source says otherwise. A club's
   page *can* support a country row, but only where the page itself
   attributes the rule to the national authority ("required by law"),
   and then it is evidence about the law, like a press article.

4. **The requirement is the country's; the implementation is the
   club's.** "You need a fidelity card for high-risk matches" →
   country. "Inter's card is Siamo Noi, EUR 15, six years, sold at
   tdt.inter.it, cutoff before each derby" → club. Name, price,
   validity, channel, which sectors, the cap per holder — all club.

5. **When in doubt, it stays in the club file.** The costs are not
   symmetric. A national fact left in a club file is merely repeated.
   A club fact wrongly promoted to country is silently applied to
   **every** club in that country, and nothing would ever flag it.

6. **An absence is a fact only when a source states it.** "Germany has
   no national personalisation requirement" may be written as a
   country row only if a source says so. No country row on a topic
   means *nobody has written one*, not *there is no national rule* —
   and the layered view has to say "no national rows for DE" out loud
   rather than print nothing.

7. **Rule 1 does not loosen.** A country row never holds a sale date,
   window or deadline, and never a "typical" lead time ("high-risk
   designations come out about ten days before"). The checker's
   day-level date guard runs on `rule` and `condition` here, not just
   `topic` as in the rules file: a national rule has no reason to carry
   a day, and a law's own date belongs in `ticket-sources.csv`'s
   `published`.

### Worked on the rows already in the repo

What each would become **when the file is populated** — nothing has
been moved.

| today | verdict | why |
|---|---|---|
| rules l.28, `legal-framework`, I-6: Tessera del Tifoso became fidelity cards in 2017, open sale restored except high-risk and reserved sectors | **country** `IT`, `condition` `always` for the open-sale part; the card requirement becomes its own row with `high-risk-match` / `reserved-sector`, `clubLatitude` `implements` | a ministry decision (I7 is the Ministero dell'Interno). Test 2 |
| rules l.29, `personalisation`, I-6: named tickets and assigned seats mandatory | **country** `IT`, `always`, `none` | its own note already says "the general rule in Italy". Test 2 |
| rules l.30, `residency-limits`, I-7 — **splits** | first sentence (limits are set by the Osservatorio and Questura/Prefettura) → **country**, `high-risk-match`, `none` (the limits are the authorities' per-match decision, not something a club adds to). Second sentence (Inter's 2025-26 derby announcement had no limit) → **stays club**, derby-home, 2025-26 | one row, two facts at two levels. Tests 1 and 2 |
| rules l.26, `fidelity-card`, I-4: Siamo Noi, EUR 15, 6 years | **club** | the implementation. Test 4 |
| rules l.31, `fidelity-card-foreign`, I-8: can a non-Italian get a Siamo Noi card without a codice fiscale | **club**, and the hard one | the question as written is about Inter's signup. Its evidence, I9, is SSC Napoli's FAQ about the national Tessera — another club speaking about national law. If a national source ever says the scheme itself requires a codice fiscale, that is a *separate* country row; this one does not move. Tests 3 and 4 |
| rules l.33, `purchase-limit`, I-11: up to 2 tickets in the Siamo Noi phase | **club** | Inter chose the cap. Test 2 |
| rules l.8, `sector-separation`, N-9: the Frankenderby's DFB classification triggers full sector separation | **club/fixture**, stays | the classification *scheme* may be national, but no source here describes it; this row is one fixture's consequence at one ground. A German country row on match classification needs a DFB/police source, which nothing in the PDF is. Tests 1 and 3 |
| rules l.9, `personalisation`, N-10: none found for Nürnberg home derbies | **club/fixture**, stays | an absence observed at one club is not a national absence. Test 6 |
| rules l.19, `resale-price-cap`, N-21: face value +10% | **club** | it is in the club's terms. Test 2 |
| CLAUDE.md, `priceBasis`: German consumer prices include VAT by law (PAngV) | **country** `DE`, `law`, `none` — *if* written as a row, with the law as a source | the one German national fact already known. It is not in any data file today, and adding it is not part of this design |

**When the file is populated, rows move; they are not copied.** A
country row and a club row saying the same thing is the drift this
file exists to prevent. That means the move and the checker change
must land in the same commit — otherwise Inter's layered derby view
loses its personalisation rule in between.

---

## What the checker would do

Designed, not built. In `tools/check_tickets.py`:

- a `SCHEMA` entry with the columns and key above;
- `country` must match `^[A-Z]{2}$`; `appliesTo` must be `all`,
  `unknown`, or Q-ids — and a Q-id not in `league-tiers.csv` is
  **reported**, the same way `league-rosters.csv` handles one;
- `clubLatitude`, `confidence`, `basis` closed; `authorityKind`,
  `condition`, `topic` open, with `topic` sharing the rules file's
  `KNOWN` list;
- the date guard on `topic`, `condition` and `rule`;
- read-back of every row, as for the other files;
- in the **layered** view, after each club's own rows, the national
  rows of that club's `country`, marked `[national]`, each printed
  with its `appliesTo` and `condition` — **not filtered by them**. The
  ticket files do not record which league a club plays in or whether a
  match is high-risk, so the view shows "applies to Serie A, only on
  high-risk matches" and leaves the reading to a person rather than
  guessing which rows bite; with the
  `clubLatitude` reading above; for a `derby-away` leg, the venue
  country's; and a "country not given" or "no national rows for XX"
  line where there is nothing, never silence;
- every `clubLatitude` `none` row that has a club row on the same
  topic, listed in one place as "check these agree";
- `unverified` country rows join the existing low-confidence list.

---

## Open questions — Alexandru's to decide

1. **Fixture facts for non-derby matches have no home.** "This Serie A
   match is high-risk" or "residency limit for Inter v Napoli" can only
   be written today for a derby (`scope` `derby-home` / `derby-away`).
   Options: extend `scope` with a `fixture` value plus a fixture key, or
   keep such facts in `football-rules.json` beside the fixture. The
   recommendation is `football-rules.json`, because that is where
   match-specific hand-written facts already live — but it is your file
   and nothing writes to it.
2. **League rules here, or separately?** The design puts domestic
   league rules (DFL, Lega Serie A) in this file with `appliesTo`
   naming the leagues. The alternative is a league file. Recommended
   here: they are national in reach and the same person reads them.
3. **Move, not copy**, when populating — the four Italian rows above
   leave `club-ticket-rules.csv`. Recommended; say if you would rather
   keep them duplicated until more Italian clubs exist.
4. **The `country` column on `club-tickets.csv`** is a schema change to
   an existing file. It is optional and blank is reported, so nothing
   breaks — but it is a change.
