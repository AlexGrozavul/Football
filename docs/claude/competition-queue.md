# German competitions queue

Created 2026-11-19 (first session of the German competitions job). One batch
per session: up to 4 national competitions, or up to 6 regional cups, or up to
8 "follow only" rows. Men's football only. Every row is researched under the
"Competition research procedure" of `docs/claude/conventions.md`.

- **status**: `researched` = the competition has info rows from the
  competition procedure (a pass of its own, PR #158 DFB-Pokal, PR #159
  Bundesliga); `pending` = it has none. The three play-offs have rows from the
  phase 4a fact check (PR #224) only, not from a research pass, so they are
  `pending`; their rows are kept and corrected under the procedure when their
  turn comes.
- **follow**: `done` = the competition has a "where to follow it" row (topic
  `tracking`); `missing` = it has none.
- Order: pending national competitions (as in `data/competitions.csv`), then
  the regional cups (the three Baden-Württemberg associations first, then the
  rest alphabetically by association), then researched competitions whose
  "follow" is missing.

## Queue

| # | id | kind | status | follow | batch / PR / date |
|---|---|---|---|---|---|
| 1 | de-2-bundesliga | national | pending | missing | batch 1 |
| 2 | de-3-liga | national | pending | missing | batch 1 |
| 3 | de-regionalliga-bayern | national | pending | missing | batch 1 |
| 4 | de-regionalliga-nord | national | pending | missing | batch 1 |
| 5 | de-regionalliga-nordost | national | pending | missing | |
| 6 | de-regionalliga-suedwest | national | pending | missing | |
| 7 | de-regionalliga-west | national | pending | missing | |
| 8 | de-dfl-supercup | national | pending | missing | |
| 9 | de-2-bundesliga-relegation-play-off | national | pending | missing | |
| 10 | de-aufstiegsspiele-zur-3-liga | national | pending | missing | |
| 11 | de-bundesliga-relegation-play-off | national | pending | missing | |

Regional cups: to be added in batch 1 from a DFB page read in this session
(the list of the regional associations) and each association's own site (the
cup's name), before they are queued.

Researched: `de-dfb-pokal` (follow `done`), `de-bundesliga` (follow `done`).
No researched German competition has "follow" missing.

## Batch 1 (2026-11-19)

Rows 1 to 4: 2. Bundesliga, 3. Liga, Regionalliga Bayern, Regionalliga Nord.
Written before any page was read.
