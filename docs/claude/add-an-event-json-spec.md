# Add an event: the JSON box (spec)

Written 2026-10-25. Describes what the validator `attCheckEvent()` and the paste check `impEvCheckText()` in `index.html` do today; if they disagree with this file, the code is right and this file is wrong. **Every example below was run through the real validator** (headless Chromium, the page's own functions, English) and gave the answer written next to it.

Note: the repo has no separate "add a match" spec file; for matches the entry "xG, saves, passes and player ratings on a match" in `conventions.md` plus `attCheckMatch()` are the spec. This file follows the same layout.

Where the box is: Me > Events > "Add an event", the JSON box at the end of the form. With the form empty the box is read alone and takes **one object or a list**; with the form filled in it takes **one object** that is merged with the form (a field filled by both is refused). Events are device-only (`football-attended-imported`, key `events`); nothing is committed or sent.

## Fields

| field | required | type | limit |
|---|---|---|---|
| `id` | yes in the box (the form can generate one) | text | 1-80 characters: letters, digits, `.` `_` `-` |
| `date` | yes | text `YYYY-MM-DD`, a real day | `2026-02-30` is refused |
| `title` | yes | text, or `{"ro": …, "en": …}` (only those two keys, at least one not blank) | 300 characters per text |
| `place` | no | text or `{"ro", "en"}` | 300 characters |
| `note` | no | text or `{"ro", "en"}` | 2000 characters |
| `atStadium` | no | `true` or `false` | the form stores `false` when left alone; a JSON paste without it stays without it |

`null` counts as absent for the optional fields. **Unknown keys are refused, and the key is named** (a typo is not silently dropped). Nothing is filled in, guessed or computed (rules 1-2).

## Limits

- 200,000 characters per paste; at most 50 events per paste; at most 100 imported events on a device.
- The id must be free in **all four spaces**: events and matches of `data/attended.json`, imported matches and imported events on the device; and not repeated inside one paste.
- A list is accepted only with the form empty. An empty list is refused.
- Everything is checked whole: if one event fails, **nothing** is stored.

## Most likely refusals

| what was pasted | answer |
|---|---|
| `{` | Not added: this is not valid JSON. |
| `[]` | Not added: the list is empty. |
| only spaces | Nothing pasted. |
| `"id": "ev 1"` | "id" must be 1-80 letters, digits, . _ or - |
| `"date": "2026-02-30"` | "date" must be a real day written YYYY-MM-DD |
| `"title": "  "` or `{"de": "x"}` | "title" must be text (or {"ro": …, "en": …}) and not empty |
| `"atStadium": "yes"` | "atStadium" must be true or false |
| `"venue": "y"` | the event has an unknown field "venue" |
| the same id twice in a list | event 2 ("ev-min"): the id "ev-min" appears twice in what you pasted |
| an id of `data/attended.json` | the id "…" is already used by a match or an event in data/attended.json |
| an id already on the device | the id "…" is already used by an imported match or event on this device |

Every refusal starts with "Not added, nothing was stored:" (except the first three) and names the event by number and id.

## Minimal example (accepted, 1 event)

```json
{"id": "ev-min", "date": "2026-03-14", "title": "Derby day at the pub"}
```

## Full example (accepted)

```json
{
  "id": "ev-full",
  "date": "2026-03-14",
  "title": {"ro": "Meci în parc", "en": "Park kickabout"},
  "place": {"ro": "Leonberg", "en": "Leonberg"},
  "note": "Rain, 2-2.",
  "atStadium": false
}
```

Both together as a list `[minimal, full]` are accepted as 2 events (form empty).

## Not built

An event can be edited in the form and removed from its sheet, but there is **no "Replace with JSON" for events** (only for imported matches, 2026-10-25).
