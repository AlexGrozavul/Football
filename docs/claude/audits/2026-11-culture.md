# Culture rows audit, phase 5 (November 2026)

Fact check of the hand-written culture files: a seeded sample of 60 rows of
`data/club-rivalries.csv`, `data/club-friendships.csv` and
`data/club-parents.csv` read against the page each row's source names
(Part A); the fixture links, offline (Part B); the unused sources of
`data/club-culture-sources.csv` (Part C). This file was written in two
steps: the method and the sample first, **before any page was read** (its
own commit), the results after.

## Part A: method and sample (written before any page was read)

- **Population**: the data rows of the three files as of 2026-11-18
  (rivalries 826, friendships 156, parents 35). A row's id is its **line
  number in the file** (the header is line 1).
- **Country** of a row: the country of the club file in `data/clubs/??.json`
  that holds the row's `clubQ` (every sampled population row has one).
- **Seats**. Rivalries: 40 in proportion to the classes (largest
  remainder): `other` 654 -> 32, `local` 130 -> 6, `main` 42 -> 2.
  Friendships: 15, of them 3 from the 25 rows with status `unclear`; the
  other 12 by largest remainder over `active` (115) and `ended` (16):
  11 and 1. Of the 11 `active` seats, 10 go to German rows and 1 to the 7
  rows outside Germany (149 of the 156 rows are German; without this seat
  the draw would hold no other country). Parents: 5.
- **Spread across countries**: inside each class or status the rows are
  ordered by (country, line) and drawn by systematic sampling: step = rows
  / seats, start = `rng.random()` x step, the rows at floor(start + k x
  step). The non-German friendship seat is `rng.choice` over those rows in
  line order.
- **Draw**: Python `random.Random(20261118)`, one generator, in this
  order: rivalries `main`, `local`, `other`; friendships `active` (German
  systematic, then the one non-German choice), `ended`, `unclear`;
  parents.
- **Seed**: 20261118.
- **Reading**: each row's source page through the temporary probe
  workflow only (MediaWiki API, User-Agent `FootballPlannerBot/1.0
  (https://github.com/AlexGrozavul/Football)`, `maxlag=5`). Every sampled
  source is a Wikipedia page (one source, any language).
- **Verdicts**: correct (the page names the pair and supports the class or
  status; the quote, if any, is on the page); wrong (the page states
  something else: the row is fixed from the page); not on the page (the
  pair or the quote is not there: listed, not deleted); cannot verify
  (host closed, page gone). Pass rule per file: 0 or 1 errors (wrong or
  not on the page) passes; 2 or more means a full check of that file
  later.

| id | file | line | country | class/status | club | other side | source |
|---|---|---|---|---|---|---|---|
| S01 | rivalries | 809 | DE | main | Kickers Emden (`Q319167`) | VfB Oldenburg (`Q826212`) | C531 |
| S02 | rivalries | 746 | RO | main | FC Argeș Pitești (`Q841245`) | Dinamo București (`Q204237`) | C392 |
| S03 | rivalries | 366 | DE | local | VfL Wolfsburg (`Q101859`) | Eintracht Braunschweig (`Q154053`) | C27 |
| S04 | rivalries | 398 | DE | local | Rot-Weiss Essen (`Q155218`) | Wuppertaler SV | C49 |
| S05 | rivalries | 649 | ES | local | Cádiz Club de Fútbol (`Q460448`) | Xerez CD | C214 |
| S06 | rivalries | 685 | FR | local | Stade lavallois (`Q760736`) | Le Mans Football Club (`Q210864`) | C227 |
| S07 | rivalries | 554 | IT | local | Benevento Calcio (`Q652516`) | Campobasso | C196 |
| S08 | rivalries | 767 | RO | local | FCV Farul Constanța (`Q368104`) | CS Năvodari | C399 |
| S09 | rivalries | 52 | AT | other | LASK (`Q392310`) | FC Blau-Weiß Linz (`Q696525`) | C64 |
| S10 | rivalries | 739 | BE | other | K Beerschot VA (`Q2268833`) | Royal Antwerp FC (`Q732002`) | C246 |
| S11 | rivalries | 2 | DE | other | 1. FC Köln (`Q104770`) | Borussia Mönchengladbach (`Q101959`) | R1 |
| S12 | rivalries | 23 | DE | other | Werder Bremen (`Q51976`) | FC Bayern München (`Q15789`) | R2 |
| S13 | rivalries | 105 | DE | other | Hansa Rostock (`Q142005`) | FC St. Pauli (`Q6463`) | R17 |
| S14 | rivalries | 404 | DE | other | SV Waldhof Mannheim (`Q170134`) | VfR Mannheim | C52 |
| S15 | rivalries | 139 | ES | other | Real Madrid Club de Fútbol (`Q8682`) | Atlético Madrid (`Q8701`) | C95 |
| S16 | rivalries | 160 | ES | other | FC Barcelona (`Q7156`) | Atlético Madrid (`Q8701`) | C105 |
| S17 | rivalries | 663 | ES | other | CD Castellón (`Q743557`) | Nàstic de Tarragona | C216 |
| S18 | rivalries | 182 | FR | other | OGC Nice (`Q185163`) | SC Bastia | C118 |
| S19 | rivalries | 687 | FR | other | Angers SCO (`Q845137`) | Football Club de Nantes (`Q192071`) | C228 |
| S20 | rivalries | 234 | GB | other | Aston Villa F.C. (`Q18711`) | West Bromwich Albion F.C. (`Q18744`) | C143 |
| S21 | rivalries | 255 | GB | other | Nottingham Forest F.C. (`Q19490`) | Notts County F.C. | C157 |
| S22 | rivalries | 275 | GB | other | Chelsea F.C. (`Q9616`) | Liverpool F.C. (`Q1130849`) | C169 |
| S23 | rivalries | 296 | GB | other | Queens Park Rangers F.C. (`Q18723`) | Brentford F.C. (`Q19571`) | C175 |
| S24 | rivalries | 703 | GB | other | Bolton Wanderers F.C. (`Q19451`) | Preston North End F.C. (`Q19612`) | C230 |
| S25 | rivalries | 219 | GR | other | OFI Crete F.C. (`Q931704`) | Ergotelis F.C. | C135 |
| S26 | rivalries | 113 | IT | other | SS Lazio (`Q2609`) | AS Roma (`Q2739`) | C81 |
| S27 | rivalries | 133 | IT | other | Cagliari Calcio (`Q1900`) | Palermo FC (`Q2674`) | C91 |
| S28 | rivalries | 442 | IT | other | Ascoli Calcio 1898 FC (`Q6630`) | FC Inter (`Q631`) | C186 |
| S29 | rivalries | 464 | IT | other | Atalanta Bergamasca Calcio (`Q1886`) | ACF Fiorentina (`Q2052`) | C188 |
| S30 | rivalries | 488 | IT | other | Cesena Football Club (`Q16848949`) | Salernitana | C191 |
| S31 | rivalries | 508 | IT | other | Virtus Entella (`Q2276413`) | Lavagnese | C192 |
| S32 | rivalries | 530 | IT | other | US Avellino 1912 (`Q298217`) | SSC Napoli (`Q2641`) | C194 |
| S33 | rivalries | 552 | IT | other | Benevento Calcio (`Q652516`) | Nocerina | C196 |
| S34 | rivalries | 575 | IT | other | Unione Sportiva Sassuolo Calcio (`Q8603`) | Sansovino | C201 |
| S35 | rivalries | 606 | IT | other | Modena Football Club 2018 (`Q8408`) | Triestina | C203 |
| S36 | rivalries | 626 | IT | other | Frosinone Calcio (`Q845043`) | Grosseto | C204 |
| S37 | rivalries | 321 | NL | other | Fortuna Sittard (`Q854167`) | MVV Maastricht (`Q876568`) | C178 |
| S38 | rivalries | 341 | NL | other | FC Volendam (`Q738060`) | Almere City FC (`Q653119`) | C178 |
| S39 | rivalries | 68 | RO | other | FC Botoșani (`Q1262822`) | CSM Politehnica Iași | C71 |
| S40 | rivalries | 74 | RS | other | FK Vojvodina (`Q207501`) | FK Partizan (`Q188656`) | C73 |
| S41 | friendships | 3 | DE | active | Borussia Dortmund (`Q41420`) | Celtic Glasgow | C1 |
| S42 | friendships | 23 | DE | active | Hamburger SV (`Q51974`) | VfB Lübeck (`Q665920`) | C5 |
| S43 | friendships | 51 | DE | active | FC Augsburg (`Q97905916`) | SC Austria Lustenau (`Q696507`) | C18 |
| S44 | friendships | 65 | DE | active | VfB Stuttgart (`Q4512`) | AS Saint-Étienne (`Q19521`) | C25 |
| S45 | friendships | 82 | DE | active | Karlsruher SC (`Q105853`) | Racing Straßburg (`Q126334`) | C30 |
| S46 | friendships | 93 | DE | active | SpVgg Greuther Fürth (`Q153539`) | FSV Frankfurt (`Q157352`) | C34 |
| S47 | friendships | 104 | DE | active | Hannover 96 (`Q33748`) | Hamburger SV (`Q51974`) | C41 |
| S48 | friendships | 120 | DE | active | Rot-Weiss Essen (`Q155218`) | Werder Bremen (`Q51976`) | C49 |
| S49 | friendships | 132 | DE | active | SV Wehen Wiesbaden (`Q310621`) | FC Ingolstadt 04 (`Q170117`) | C55 |
| S50 | friendships | 146 | DE | active | Preußen Münster (`Q316865`) | Pescara Calcio | C181 |
| S51 | friendships | 24 | FR | active | RC Strasbourg Alsace (`Q126334`) | Karlsruher SC (`Q105853`) | C7 |
| S52 | friendships | 34 | DE | ended | 1. FSV Mainz 05 (`Q105254`) | Borussia Mönchengladbach (`Q101959`) | C14 |
| S53 | friendships | 7 | DE | unclear | Borussia Dortmund (`Q41420`) | Karlsruher SC (`Q105853`) | C1 |
| S54 | friendships | 36 | DE | unclear | 1. FSV Mainz 05 (`Q105254`) | FC Carl Zeiss Jena (`Q155186`) | C14 |
| S55 | friendships | 114 | DE | unclear | 1. FC Kaiserslautern (`Q8466`) | Werder Bremen (`Q51976`) | C44 |
| S56 | parents | 11 | BE | - | Jong KAA Gent (`Q117384089`) | KAA Gent (`Q18232`) | URL in row |
| S57 | parents | 5 | DE | - | FC Augsburg II (`Q5424829`) | FC Augsburg (`Q97905916`) | URL in row |
| S58 | parents | 15 | DE | - | TSG 1899 Hoffenheim II (`Q16637410`) | TSG 1899 Hoffenheim (`Q22707`) | URL in row |
| S59 | parents | 26 | ES | - | RC Celta Fortuna (`Q2311865`) | RC Celta de Vigo (`Q8749`) | URL in row |
| S60 | parents | 35 | PT | - | FC Porto B (`Q5423714`) | FC Porto (`Q128446`) | URL in row |

## Part A: results

Read on 2026-11-18 through the probe workflow (PR #226, runs 1 to 3; 63 requests to the Wikipedia API, none to another host). Every sampled source is Wikipedia (one source). No host stopped the reading, no page was gone.

| id | verdict | page read (language, revision) | what the page says | fix |
|---|---|---|---|---|
| S01 | correct | Kickers Emden (de), rev 271680809 | "Hauptrivalen", class `main`; quote on the page | - |
| S02 | correct | FC Argeș Pitești (ro), rev 18046585 | quote "principalul rival tradițional" on the page, class `main` | - |
| S03 | correct | VfL Wolfsburg (de), rev 271264110 | "als Derbys"; quote on the page | - |
| S04 | correct | Rot-Weiss Essen (de), rev 271638901 | "Rivalitäten ... zu anderen Vereinen aus der Region", Wuppertaler SV named; quote on the page | - |
| S05 | correct | Cádiz CF (es), rev 176330661 | "Derbi gaditano"; quote on the page | - |
| S06 | correct | Stade lavallois (fr), rev 241351102 | "derby du Maine"; quote on the page | - |
| S07 | correct | Benevento Calcio (it), rev 153241771 | "derby del Sannio"; quote on the page | - |
| S08 | correct | FCV Farul Constanța (en), rev 1384952732 | "local rivalries against teams from nearby cities"; quote on the page | - |
| S09 | wrong | List of association football club rivalries in Europe (en), rev 1382126581 | line "Linz Derby: FC Blau-Weiß Linz vs. LASK Linz": a city derby, row said `other` | class `local`, quote added (also counterpart line 51) |
| S10 | correct | Beerschot VAC (nl), rev 71668307 | "grote rivaliteit"; quote on the page, class follows the quote | - |
| S11 | wrong | Rhine derby (en), rev 1383281165 | "the term Rhine derby is mostly used for matches between FC Köln and Borussia Mönchengladbach" | class `local`, quote added (also line 9) |
| S12 | correct | German football rivalries (en), rev 1386379485 | table row Werder Bremen / Bayern Munich, "Nord-Süd Klassiker"; no local wording | - |
| S13 | correct (class open) | Politisches derby (en), rev 1366964740 | Hansa Rostock v St. Pauli named; the page calls it a derby, the clubs are about 180 km apart | none; Alexandru's call (see below) |
| S14 | correct | SV Waldhof Mannheim (de), rev 272232200 | quote "Die älteste Rivalität besteht jedoch zum VfR Mannheim" on the page | - |
| S15 | wrong | Madrid derby (en), rev 1376398881 | "matches between Atlético Madrid and Real Madrid, both hailing from the Spanish capital city of Madrid" | class `local`, quote added (also line 140) |
| S16 | correct (class open) | El Otro Clásico (en), rev 1383722851 | Atlético v Barcelona named; "The Other Derby" as a name only | none; Alexandru's call |
| S17 | correct | CD Castellón (es), rev 175651126 | "rivalidades de menor importancia"; quote on the page | - |
| S18 | correct (class open) | Derby de la Mediterranée (en), rev 1366958635 | Bastia v Nice named; "Mediterranean Derby", clubs across the sea | none; Alexandru's call |
| S19 | correct (class open) | Angers SCO (fr), rev 241323473 | quote "Le principal compétiteur du SCO d'Angers est le FC Nantes" on the page; the same paragraph says "cette rivalité prit fin" in the early 1980s and calls it "ce derby de la région" | none; `principal compétiteur` read as `other` by the batch, Alexandru's call |
| S20 | wrong | Aston Villa F.C.–West Bromwich Albion F.C. rivalry (en), rev 1376404707 | "... from the West Midlands who share a local rivalry" | class `local`, quote added (also line 235) |
| S21 | wrong | Nottingham derby (en), rev 1380192513 | "derby is the name given to football matches contested between Nottingham Forest and Notts County" | class `local`, quote added |
| S22 | correct | Chelsea F.C.–Liverpool F.C. rivalry (en), rev 1382548297 | "not traditional rivals", a modern rivalry: `other` | - |
| S23 | wrong | West London derby (en), rev 1386284647 | "a local football rivalry ... between any two of Brentford, Chelsea, Fulham, and Queens Park Rangers"; line "Brentford vs QPR derby" | class `local`, quote "Brentford vs QPR derby" (also line 295) |
| S24 | correct (class open) | Bolton Wanderers F.C. (en), rev 1383709848 | quote on the page; the sentence goes on "separated by less than 20 miles" | none; regional wording in the quote, Alexandru's call |
| S25 | wrong | Cretan derby (en), rev 1366958092 | "an association football rivalry between Ergotelis and OFI, two teams from Heraklion, Crete" | class `local`, quote added |
| S26 | wrong | Derby della Capitale (en), rev 1381422757 | "is the football local derby in Rome, Italy, between Lazio and Roma" | class `local`, quote added (also line 114) |
| S27 | correct (class open) | Derby delle Isole (en), rev 1366958772 | Cagliari v Palermo named; "Derby of the Islands", clubs on two islands | none; Alexandru's call |
| S28 | correct | Ascoli Calcio 1898 FC (en), rev 1380609213 | quote "Other rivalries include ... Inter." on the page | - |
| S29 | correct | Atalanta BC (en), rev 1384110383 | quote on the page | - |
| S30 | correct | Cesena FC (it), rev 153366403 | Salernitana in the quoted list | - |
| S31 | correct | Virtus Entella (it), rev 153161987 | Lavagnese in the quoted sentence | - |
| S32 | correct | US Avellino 1912 (it), rev 153391885 | quote on the page | - |
| S33 | correct (class open) | Benevento Calcio (it), rev 153241771 | quote "Le rivalità più accese riguardano altre tifoserie campane" on the page; Nocerina named in the next words | none; regional wording, Alexandru's call |
| S34 | correct | US Sassuolo (it), rev 153318543 | Sansovino in the quoted list | - |
| S35 | correct | Modena FC 2018 (it), rev 153366458 | "Arezzo e Triestina (rivalità nate negli anni 2000)" | - |
| S36 | correct | Frosinone Calcio (it), rev 153341578 | Grosseto in the quoted list | - |
| S37 | wrong | Football derbies in the Netherlands (en), rev 1386250215 | line "Derby van het Zuiden: MVV Maastricht vs. Fortuna Sittard" | class `local`, quote added (also line 320) |
| S38 | wrong | Football derbies in the Netherlands (en), rev 1386250215 | line "Markermeerderby: Almere City FC vs. FC Volendam" | class `local`, quote added (also line 340) |
| S39 | wrong | List of association football club rivalries in Europe (en), rev 1382126581 | line "North-East derby: FC Botoşani vs Foresta Suceava vs Politehnica Iași" | class `local`, quote added |
| S40 | correct (class open) | Derby of Serbia (en), rev 1381432219 | Vojvodina v Partizan named; a derby between Novi Sad and Belgrade | none; Alexandru's call |
| S41 | correct | Borussia Dortmund (de), rev 272009577 | quote on the page, present tense: `active` | - |
| S42 | correct | Hamburger SV (de), rev 272177354 | quote on the page; "eine Fanfreundschaft mit dem VfB Lübeck ... haben" | - |
| S43 | correct | FC Augsburg (de), rev 272044701 | "gibt es freundschaftliche Beziehungen" | - |
| S44 | correct | VfB Stuttgart (de), rev 272038923 | "Auf Ultraebene gibt es freundschaftliche Kontakte ... zur AS Saint-Étienne" | - |
| S45 | correct | Karlsruher SC (de), rev 270869888 | "Eine sehr starke Fanfreundschaft pflegt man ... Racing Straßburg" | - |
| S46 | not on the page (quote) | SpVgg Greuther Fürth (de), rev 272126362 | the page now reads "der SpVgg Bayreuth, des 1. FC Heidenheim, des FSV Frankfurt" (the quote had "dem 1. FC Heidenheim"); pair and `active` supported | quote set to the page's current words, checkedOn 2026-11-18 |
| S47 | correct | Hannover 96 (de), rev 272116937 | quote on the page | - |
| S48 | correct | Rot-Weiss Essen (de), rev 271638901 | quote on the page | - |
| S49 | correct | SV Wehen Wiesbaden (de), rev 271153619 | quote on the page | - |
| S50 | correct | Preußen Münster (de), rev 272188984 | "pflegen ... freundschaftliche Kontakte ... zu ... Pescara Calcio" | - |
| S51 | correct | Supporters du Racing Club de Strasbourg Alsace (fr), rev 241134075 | "ont une amitié avec ceux du Karlsruher SC" | - |
| S52 | correct | 1. FSV Mainz 05 (de), rev 271857642 | "von 1994 bis 1999", "kündigten die Gladbacher diese Freundschaft kurzerhand auf": `ended` | - |
| S53 | correct | Borussia Dortmund (de), rev 272009577 | "In den 1990er Jahren gab es einige lose Fanfreundschaften ... Karlsruher SC": past, no end stated: stays `unclear` | - |
| S54 | correct | 1. FSV Mainz 05 (de), rev 271857642 | "bestanden ... wobei diese nur wenig aktiv geführt werden": mixed tense, stays `unclear` | - |
| S55 | correct | 1. FC Kaiserslautern (de), rev 272219813 | "bestand ... fast gar nicht mehr gepflegt", and Facebook pages "zur Fanfreundschaft mit Bremen" (Stand 2018): neither ended nor active by wording, stays `unclear` | - |
| S56 | correct | Jong KAA Gent (en, redirect page), rev 1310588907 | redirects to "KAA Gent#Jong KAA Gent" | - |
| S57 | correct | FC Augsburg II (de, redirect page), rev 264000066 | redirects to "FC Augsburg#Zweite Mannschaft" | - |
| S58 | correct | TSG 1899 Hoffenheim II (de, redirect page), rev 264000069 | redirects to "TSG 1899 Hoffenheim#Zweite Mannschaft" | - |
| S59 | correct | RC Celta Fortuna (en), rev 1385697249 | "The reserve team of Celta will be named Celta Fortuna" | - |
| S60 | correct | FC Porto B (en), rev 1374875129 | "serves as the reserve side of FC Porto" | - |

### Counts and pass verdict

| file | sampled | correct | of them class open | wrong | not on the page | cannot verify | verdict |
|---|---|---|---|---|---|---|---|
| `club-rivalries.csv` | 40 | 29 | 9 | 11 | 0 | 0 | **fails: full check** |
| `club-friendships.csv` | 15 | 14 | 0 | 0 | 1 | 0 | passes (1 error) |
| `club-parents.csv` | 5 | 5 | 0 | 0 | 0 | 0 | passes |

- **Every rivalry error is the same one, a class.** The 11 wrong rows all had a blank quote: they are the rows imported on 2026-10-03 and 2026-10-17 (the `derbies.csv` import), which were written `other` by construction after a check that the page names both clubs, never classed from the page's wording. 11 of the 19 unquoted rows in the sample are wrong; 0 of the 21 quoted rows. Each of the 11 now has `local`, a quote of the page's own words (15 words at most, checked as a substring of the posted page text) and `checkedOn` 2026-11-18. **The other side of the same pair** (lines 9, 51, 114, 140, 235, 295, 320, 340), same source, same blank quote, same `other`, was changed the same way with the same quote, so a pair does not show two classes: 19 rivalry rows changed in all. No pair, rival or source was wrong.
- **Full check of `club-rivalries.csv`**, by the pass rule: 826 rows. The error is concentrated in the rows without a quote, **323 rows left after this pass**: those are the ones to read first; the 503 quoted rows showed no error in the sample.
- **Class open (counted correct, left unchanged; Alexandru's call)**: five unquoted rows whose page names a *derby* between clubs that are not near each other (S13 Rostock v St. Pauli, S16 Atlético v Barcelona, S18 Nice v Bastia, S27 Cagliari v Palermo, S40 Vojvodina v Partizan). The documented table reads "derby" as `local`; these are not local in any other sense, so they stay `other` until he says which way the table goes. Four quoted rows whose quote carries regional or "principal" wording that the batch read as `other` (S19, S24, S33; S31 has "province liguri", left too).
- **Friendships**: the one error is a quote that no longer matches the page (one word changed on Wikipedia since 2026-10-16); the quote now matches the page. None of the 3 `unclear` rows is settled by its page (S53 past with no end, S54 mixed tense, S55 "fast gar nicht mehr gepflegt" but Facebook pages still about the friendship), so no status changed.

## Part B: fixture links (offline)

- `data/fixture-links-manual.csv`: 21 rows (14 football-data, 7 OpenLigaDB), all `link`. For each, the team name in `data/fixtures/` is the same club as the map's Q-id: Saarbrücken (417, 3078), Würzburger Kickers (398, 5276), SSV Jeddeloh (4762), Le Mans FC, FC Internazionale Milano, Atalanta BC, US Sassuolo Calcio, Real Madrid CF, Club Atlético de Madrid, CA Osasuna, RC Deportivo La Coruña, Real Racing Club de Santander, AZ, PSV, SBV Excelsior, SC Cambuur-Leeuwarden, Willem II Tilburg, Club Brugge KV, Sporting Clube de Braga. Every club is still on the map; each appears in `data/clubs/fixture-links.json` with basis `manual`.
- The one name with a reserve marker, `SSV Jeddeloh II`, is the village Jeddeloh II, not a reserve side (already in the row's note and in conventions.md); the map's `Q2207914` is that club.
- `data/clubs/fixture-links.json`: 247 links for 227 clubs; no link to a Q-id that is not on the map, no fixture-source team linked to two clubs, no reserve or first-team mismatch between a team name and its club. None of the 123 `skip` rows of `clubs-manual.csv` appears in the link file, in `data/fixtures/` or in the manual link file.
- **Wrong or dead links: 0. Nothing changed.**

## Part C: unused culture sources

- `check_club_culture.py` listed 453 sources used by no row of rivalries, friendships or founding (`club-parents.csv` cites URLs, not ids). Each id was then searched as a word in all of `data/`, `index.html` and `tools/` (outside the sources file): 4 ids (C23, C43, C46, C50) appear in `competition-info.csv`, `competition-sources.csv` and `data/ro/competition-info.json`, but there they are ids of `competition-sources.csv`, a separate list with its own C-numbers, so they are not uses.
- **Removed: 453 rows. Before 798 sources, after 345.** The checker now prints no "used by no row" warning (9 warnings left, none about sources). Git keeps the removed rows.

## Part D: checks

- Romanian: no changed row has a Romanian text (quotes are shown untranslated); `docs/ro-review.md` has no culture data rows, only the `riv.*` labels (`grep -c 'Q[0-9]' docs/ro-review.md` gives 0 rows with a club id), so nothing to update.
- `check_club_culture.py`, `check_derbies.py`, `check_translations.py`: exit 0. `test_sheet_tickets.js` and `test_derbies.js` run locally (results in the PR).
- Probe: 3 runs of 8, none failed before a request. Workflow and script removed in their own commit before the merge.

## Phase 5b: reclassifying the quote-less `other` rows of club-rivalries.csv

Method (written before any page was read): the population is every row of
`data/club-rivalries.csv` with class `other` and an empty quote, ordered by
row id (line number, the header is line 1); 323 such rows on 2026-11-18. Each
session takes the first 100 that have no line in this section yet. Each row's
source page is read only through the temporary probe workflow (MediaWiki
parse API, User-Agent `FootballPlannerBot/1.0
(https://github.com/AlexGrozavul/Football)`, `maxlag=5`), which posts only
the sentences naming both clubs (plus class words) and their section heading.
Classes follow the coordinator's decision of 18 Nov 2026: `local` only where
the page calls the pair a local derby (or the same words in the page's
language: Lokalderby, derby local, derby cittadino, city derby, Stadtderby);
`main` where it calls the other club the main rival (or arch-rival, as the
class table of files.md has it); otherwise `other`. A named derby alone is
not enough for `local`.

### Session 1 (2026-11-18): batch

Batch (100 row ids): 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 45, 46, 47, 48, 49, 50, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111.
Extra rows: 687 (Angers SCO v FC Nantes; it has a quote, so it is not in the
batch: "principal compétiteur" is re-read for the main decision) and 112
(FC Inter v Juventus, partner of 111, outside the batch).

### Session 1 (2026-11-18): results

Per row: id, club v rival, verdict, class before -> after, quote, page (source id). Pages read in three probe runs (run1 1e9f8a3, run2 955ab5a, run3 5602810; 50 requests).

- 3: 1. FC Köln v FC Viktoria Köln: **local**, other -> local, "Cologne derby: 1. FC Köln vs. Fortuna Köln vs. Viktoria Köln", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 4: 1. FC Köln v SC Fortuna Köln: **local**, other -> local, "Cologne derby: 1. FC Köln vs. Fortuna Köln vs. Viktoria Köln", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 5: 1. FC Union Berlin v BFC Dynamo: **local**, other -> local, "East Berlin derby: Union Berlin vs. BFC Dynamo", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 6: 1. FC Union Berlin v Hertha BSC: **other**, other -> other, "has more recently referred to the derby between 1. FC Union Berlin and Hertha BSC", R3 https://en.wikipedia.org/wiki/Berlin_derby
- 7: Borussia Dortmund v FC Bayern München: **other**, other -> other, "the name given to any football match between Bayern Munich and Borussia Dortmund", R4 https://en.wikipedia.org/wiki/Der_Klassiker
- 8: Borussia Dortmund v FC Schalke 04: **other**, other -> other, "It is considered the greatest rivalry in German football.", R5 https://en.wikipedia.org/wiki/Revierderby
- 10: Eintracht Frankfurt v FSV Frankfurt: **local**, other -> local, "Frankfurt derby: Eintracht Frankfurt vs. FSV Frankfurt", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 11: Eintracht Frankfurt v SV Darmstadt 98: **other**, other -> other, "Hesse derby", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 12: FC Augsburg v TSV 1860 München: **other**, other -> other, "an association football rivalry in Bavaria, Germany, between FC Augsburg and TSV 1860 Munich", R6 https://en.wikipedia.org/wiki/FC_Augsburg%E2%80%93TSV_1860_Munich_rivalry
- 13: FC Augsburg v TSV Schwaben Augsburg: **other**, other -> other, "in more recent times, a game between Schwaben Augsburg and FC Augsburg", R7 https://en.wikipedia.org/wiki/Augsburg_derby
- 14: FC Bayern München v Borussia Dortmund: **other**, other -> other, "the name given to any football match between Bayern Munich and Borussia Dortmund", R4 https://en.wikipedia.org/wiki/Der_Klassiker
- 15: FC Bayern München v Real Madrid Club de Fútbol: **other**, other -> other, "a European club rivalry between Bayern Munich and Real Madrid", R9 https://en.wikipedia.org/wiki/Bayern_Munich%E2%80%93Real_Madrid_rivalry
- 16: FC Bayern München v TSV 1860 München: **local**, other -> local, "Münchner Lokalderby", R8 https://en.wikipedia.org/wiki/Munich_derby
- 17: FC Bayern München v Werder Bremen: **other**, other -> other, "Nord-Süd Klassiker ('North-South classic')", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 18: FC Schalke 04 v Borussia Dortmund: **other**, other -> other, "It is considered the greatest rivalry in German football.", R5 https://en.wikipedia.org/wiki/Revierderby
- 19: Hamburger SV v FC St. Pauli: **local**, other -> local, "The Hamburg derby (German: Hamburger Stadtderby) is a football rivalry between two major Hamburg sides", R10 https://en.wikipedia.org/wiki/Hamburg_derby
- 20: Hamburger SV v Werder Bremen: **other**, other -> other, "The Nordderby or Northern derby is a match between Hamburger SV and Werder Bremen", R11 https://en.wikipedia.org/wiki/Nordderby
- 21: VfB Stuttgart v Karlsruher SC: **other**, other -> other, "Als Baden-Württemberg-Derby wird das Fußballspiel zwischen dem Karlsruher SC und dem VfB Stuttgart bezeichnet", R12 https://de.wikipedia.org/wiki/Baden-W%C3%BCrttemberg-Derby
- 22: VfB Stuttgart v Stuttgarter Kickers: **local**, other -> local, "Stuttgarter Lokalderby", R13 https://en.wikipedia.org/wiki/Stuttgart_derby
- 23: Werder Bremen v FC Bayern München: **other**, other -> other, "Nord-Süd Klassiker ('North-South classic')", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 24: Werder Bremen v Hamburger SV: **other**, other -> other, "The Nordderby or Northern derby is a match between Hamburger SV and Werder Bremen", R11 https://en.wikipedia.org/wiki/Nordderby
- 25: 1. FC Heidenheim 1846 v VfR Aalen: **other**, other -> other, "Ostalb-Derby", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 26: 1. FC Kaiserslautern v 1. FC Saarbrücken: **other**, other -> other, "Südwest derby ('south-western derby')", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 27: 1. FC Kaiserslautern v Karlsruher SC: **other**, other -> other, "Abneigung besteht heutzutage gegenüber den Anhängern des VfB Stuttgart (siehe Baden-Württemberg-Derby), des 1. FC Kaiserslautern", R14 https://de.wikipedia.org/wiki/Karlsruher_SC
- 28: 1. FC Nürnberg v SpVgg Greuther Fürth: **local**, other -> local, "Das Frankenderby – auch fränkisches Lokalderby genannt", R15 https://de.wikipedia.org/wiki/Frankenderby
- 29: Arminia Bielefeld v Preußen Münster: **other**, other -> other, "Westphalian derby", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 30: Eintracht Braunschweig v Hannover 96: **other**, other -> other, "a match between the two Lower Saxonian association football clubs Hannover 96 and Eintracht Braunschweig", R16 https://en.wikipedia.org/wiki/Lower_Saxony_derby
- 31: FC St. Pauli v Hamburger SV: **local**, other -> local, "The Hamburg derby (German: Hamburger Stadtderby) is a football rivalry between two major Hamburg sides", R10 https://en.wikipedia.org/wiki/Hamburg_derby
- 32: FC St. Pauli v Hansa Rostock: **other**, other -> other, "is an association football rivalry between German clubs FC Hansa Rostock and FC St. Pauli", R17 https://en.wikipedia.org/wiki/Politisches_derby
- 33: Hannover 96 v Eintracht Braunschweig: **other**, other -> other, "a match between the two Lower Saxonian association football clubs Hannover 96 and Eintracht Braunschweig", R16 https://en.wikipedia.org/wiki/Lower_Saxony_derby
- 34: Hertha BSC v 1. FC Union Berlin: **other**, other -> other, "has more recently referred to the derby between 1. FC Union Berlin and Hertha BSC", R3 https://en.wikipedia.org/wiki/Berlin_derby
- 35: Karlsruher SC v 1. FC Kaiserslautern: **other**, other -> other, "Abneigung besteht heutzutage gegenüber den Anhängern des VfB Stuttgart (siehe Baden-Württemberg-Derby), des 1. FC Kaiserslautern", R14 https://de.wikipedia.org/wiki/Karlsruher_SC
- 36: Karlsruher SC v VfB Stuttgart: **other**, other -> other, "Als Baden-Württemberg-Derby wird das Fußballspiel zwischen dem Karlsruher SC und dem VfB Stuttgart bezeichnet", R12 https://de.wikipedia.org/wiki/Baden-W%C3%BCrttemberg-Derby
- 37: SV Darmstadt 98 v Eintracht Frankfurt: **other**, other -> other, "Hesse derby", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 38: SpVgg Greuther Fürth v 1. FC Nürnberg: **local**, other -> local, "Das Frankenderby – auch fränkisches Lokalderby genannt", R15 https://de.wikipedia.org/wiki/Frankenderby
- 39: VfL Osnabrück v Preußen Münster: **other**, other -> other, "Grenzlandderby ('borderlands derby')", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 45: SK Rapid Wien v FK Austria Wien: **local**, other -> local, "local derby match between city rivals FK Austria Wien and SK Rapid Wien", C63 https://en.wikipedia.org/wiki/Vienna_derby
- 46: FK Austria Wien v SK Rapid Wien: **local**, other -> local, "local derby match between city rivals FK Austria Wien and SK Rapid Wien", C63 https://en.wikipedia.org/wiki/Vienna_derby
- 47: Grazer AK v SK Sturm Graz: **other**, other -> other, "Graz Derby: Grazer AK vs. Sturm Graz", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 48: SK Sturm Graz v Grazer AK: **other**, other -> other, "Graz Derby: Grazer AK vs. Sturm Graz", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 49: LASK v SV Ried: **other**, other -> other, "Upper Austrian Derby : LASK Linz vs. SV Ried", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 50: SV Ried v LASK: **other**, other -> other, "Upper Austrian Derby : LASK Linz vs. SV Ried", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 53: FC Wacker Innsbruck v SV Austria Salzburg: **other**, other -> other, "Western derby: Wacker Innsbruck vs. Austria Salzburg", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 54: SV Austria Salzburg v FC Wacker Innsbruck: **other**, other -> other, "Western derby: Wacker Innsbruck vs. Austria Salzburg", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 55: Wolfsberger AC v SK Austria Klagenfurt: **other**, other -> other, "Carinthian derby : Wolfsberger AC vs. SV Austria Klagenfurt", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 56: FCSB v Dinamo București: **other**, other -> other, "a football match between Bucharest rivals FCSB and Dinamo București", C65 https://en.wikipedia.org/wiki/Eternal_derby_(Romania)
- 57: Dinamo București v FCSB: **other**, other -> other, "a football match between Bucharest rivals FCSB and Dinamo București", C65 https://en.wikipedia.org/wiki/Eternal_derby_(Romania)
- 58: FCSB v FC Rapid București: **local**, other -> local, "the football local derby in Bucharest, Romania, between FCSB and FC Rapid București", C66 https://en.wikipedia.org/wiki/Derbiul_Bucure%C8%99tiului
- 59: FC Rapid București v FCSB: **local**, other -> local, "the football local derby in Bucharest, Romania, between FCSB and FC Rapid București", C66 https://en.wikipedia.org/wiki/Derbiul_Bucure%C8%99tiului
- 60: FC Universitatea Cluj v CFR Cluj: **other**, other -> other, "refers to football matches between CFR Cluj and Universitatea Cluj", C67 https://en.wikipedia.org/wiki/Cluj_derby
- 61: CFR Cluj v FC Universitatea Cluj: **other**, other -> other, "refers to football matches between CFR Cluj and Universitatea Cluj", C67 https://en.wikipedia.org/wiki/Cluj_derby
- 62: UTA Arad v Știința Poli Timișoara: **other**, other -> other, "a match between the fierce rivals SSU Politehnica Timișoara and UTA Arad", C68 https://en.wikipedia.org/wiki/West_derby_(Romania)
- 63: Știința Poli Timișoara v UTA Arad: **other**, other -> other, "a match between the fierce rivals SSU Politehnica Timișoara and UTA Arad", C68 https://en.wikipedia.org/wiki/West_derby_(Romania)
- 64: FC Petrolul Ploiești v FC Astra Giurgiu: **other**, other -> other, "any match between Romanian clubs Petrolul Ploiești and Astra Giurgiu", C69 https://en.wikipedia.org/wiki/Former_Ploie%C8%99ti_derby
- 65: FC Petrolul Ploiești v FC Rapid București: **other**, other -> other, "a Romanian football derby contested between Liga I clubs Rapid București and Petrolul Ploiești", C70 https://en.wikipedia.org/wiki/Primvs_derby
- 66: FC Rapid București v FC Petrolul Ploiești: **other**, other -> other, "a Romanian football derby contested between Liga I clubs Rapid București and Petrolul Ploiești", C70 https://en.wikipedia.org/wiki/Primvs_derby
- 67: FC Botoșani v ACS Foresta Suceava: **other**, other -> other, "North-East derby: FC Botoşani vs Foresta Suceava vs Politehnica Iași", C71 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Romania
- 69: Oțelul Galați v Dacia Unirea Brăila: **other**, other -> other, "Lower Danube derby: Oțelul Galați vs. Dacia Unirea Brăila or Farul Constanța", C71 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Romania
- 70: Bihor Oradea v UTA Arad: **other**, other -> other, "Crișana derby: FC Bihor Oradea vs. UTA Arad", C71 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Romania
- 71: UTA Arad v Bihor Oradea: **other**, other -> other, "Crișana derby: FC Bihor Oradea vs. UTA Arad", C71 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Romania
- 72: FK Crvena zvezda v FK Partizan: **local**, other -> local, "is the local derby in Belgrade", C72 https://en.wikipedia.org/wiki/Eternal_derby_(Serbia)
- 73: FK Partizan v FK Crvena zvezda: **local**, other -> local, "is the local derby in Belgrade", C72 https://en.wikipedia.org/wiki/Eternal_derby_(Serbia)
- 74: FK Vojvodina v FK Partizan: **other**, other -> other, "A Serbian derby match must involve Vojvodina and either one of the Belgrade clubs", C73 https://en.wikipedia.org/wiki/Derby_of_Serbia
- 75: FK Partizan v FK Vojvodina: **other**, other -> other, "A Serbian derby match must involve Vojvodina and either one of the Belgrade clubs", C73 https://en.wikipedia.org/wiki/Derby_of_Serbia
- 76: FK Vojvodina v FK Spartak Subotica: **other**, other -> other, "Derbi nizije (Lowland derby) or Derbi ravnice (Plain derby): Vojvodina Novi Sad vs. Spartak Subotica", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 77: FK Spartak Subotica v FK Vojvodina: **other**, other -> other, "Derbi nizije (Lowland derby) or Derbi ravnice (Plain derby): Vojvodina Novi Sad vs. Spartak Subotica", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 78: FK Novi Pazar v FK Rad: **other**, other -> other, "Political derby: FK Rad vs. FK Novi Pazar", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 79: FK Radnički 1923 v FK Smederevo 1924: **other**, other -> other, "Šumadija derby: Radnički Kragujevac vs. FK Smederevo", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 80: FK Smederevo 1924 v FK Radnički 1923: **other**, other -> other, "Šumadija derby: Radnički Kragujevac vs. FK Smederevo", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 81: GFK Dubočica v FK Radnički Niš: **other**, other -> other, "South Serbian derby: GFK Dubočica vs. Radnički Niš", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 82: FK Radnički Niš v GFK Dubočica: **other**, other -> other, "South Serbian derby: GFK Dubočica vs. Radnički Niš", C74 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Serbia
- 83: FC Basel v BSC Young Boys: **other**, other -> other, "Die Klassikier rivalry: FC Basel vs. Grasshoppers, Young Boys or FC Zürich", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 84: BSC Young Boys v FC Basel: **other**, other -> other, "Die Klassikier rivalry: FC Basel vs. Grasshoppers, Young Boys or FC Zürich", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 85: FC Basel v FC Zürich: **other**, other -> other, "Die Klassikier rivalry: FC Basel vs. Grasshoppers, Young Boys or FC Zürich", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 86: FC Zürich v FC Basel: **other**, other -> other, "Die Klassikier rivalry: FC Basel vs. Grasshoppers, Young Boys or FC Zürich", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 87: Grasshopper Club Zürich v FC Zürich: **other**, other -> other, "a football match between rivals FC Zürich and Grasshopper Club Zurich", C76 https://en.wikipedia.org/wiki/Zurich_derby
- 88: FC Zürich v Grasshopper Club Zürich: **other**, other -> other, "a football match between rivals FC Zürich and Grasshopper Club Zurich", C76 https://en.wikipedia.org/wiki/Zurich_derby
- 89: BSC Young Boys v FC Thun: **other**, other -> other, "Bernese Derby: Young Boys vs. FC Thun", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 90: FC Thun v BSC Young Boys: **other**, other -> other, "Bernese Derby: Young Boys vs. FC Thun", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 91: FC Luzern v SC Kriens: **other**, other -> other, "Luzerner Derby: FC Luzern vs. SC Kriens", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 92: SC Kriens v FC Luzern: **other**, other -> other, "Luzerner Derby: FC Luzern vs. SC Kriens", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 93: FC St. Gallen v FC Wil: **other**, other -> other, "St. Gallen Derby: FC St.Gallen vs. FC Wil", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 94: FC Wil v FC St. Gallen: **other**, other -> other, "St. Gallen Derby: FC St.Gallen vs. FC Wil", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 95: SC Kriens v SC Cham: **other**, other -> other, "Zentralschweizer Derby: SC Cham vs. SC Kriens", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 96: FC Lugano v FC Chiasso: **other**, other -> other, "Derby del Ticino : FC Chiasso vs. AC Bellinzona vs. FC Lugano", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 97: FC Lugano v AC Bellinzona: **other**, other -> other, "Derby del Ticino : FC Chiasso vs. AC Bellinzona vs. FC Lugano", C75 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Switzerland
- 98: Swansea City A.F.C. v Cardiff City F.C.: **local**, other -> local, "a local derby between Welsh association football clubs Cardiff City and Swansea City", C77 https://en.wikipedia.org/wiki/South_Wales_derby
- 99: Cardiff City F.C. v Swansea City A.F.C.: **local**, other -> local, "a local derby between Welsh association football clubs Cardiff City and Swansea City", C77 https://en.wikipedia.org/wiki/South_Wales_derby
- 100: Cardiff City F.C. v Bristol City F.C.: **local**, other -> local, "The Severnside derby is a local derby in football in the United Kingdom", C78 https://en.wikipedia.org/wiki/Severnside_derby
- 101: Bristol City F.C. v Cardiff City F.C.: **local**, other -> local, "The Severnside derby is a local derby in football in the United Kingdom", C78 https://en.wikipedia.org/wiki/Severnside_derby
- 102: TSV 1860 München v FC Bayern München: **local**, other -> local, "Münchner Lokalderby", R8 https://en.wikipedia.org/wiki/Munich_derby
- 103: TSV 1860 München v FC Augsburg: **other**, other -> other, "an association football rivalry in Bavaria, Germany, between FC Augsburg and TSV 1860 Munich", R6 https://en.wikipedia.org/wiki/FC_Augsburg%E2%80%93TSV_1860_Munich_rivalry
- 104: Stuttgarter Kickers v VfB Stuttgart: **local**, other -> local, "Stuttgarter Lokalderby", R13 https://en.wikipedia.org/wiki/Stuttgart_derby
- 105: Hansa Rostock v FC St. Pauli: **other**, other -> other, "is an association football rivalry between German clubs FC Hansa Rostock and FC St. Pauli", R17 https://en.wikipedia.org/wiki/Politisches_derby
- 106: SC Fortuna Köln v 1. FC Köln: **local**, other -> local, "Cologne derby: 1. FC Köln vs. Fortuna Köln vs. Viktoria Köln", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 107: FC Viktoria Köln v 1. FC Köln: **local**, other -> local, "Cologne derby: 1. FC Köln vs. Fortuna Köln vs. Viktoria Köln", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 108: FSV Frankfurt v Eintracht Frankfurt: **local**, other -> local, "Frankfurt derby: Eintracht Frankfurt vs. FSV Frankfurt", R2 https://en.wikipedia.org/wiki/German_football_rivalries
- 109: FC Inter v AC Milan: **local**, other -> local, "It is one of the two major crosstown derbies in association football", C79 https://en.wikipedia.org/wiki/Derby_della_Madonnina
- 110: AC Milan v FC Inter: **local**, other -> local, "It is one of the two major crosstown derbies in association football", C79 https://en.wikipedia.org/wiki/Derby_della_Madonnina
- 111: FC Inter v Juventus FC: **other**, other -> other, "the name of the football derby between Internazionale of Milan and Juventus of Turin", C80 https://en.wikipedia.org/wiki/Derby_d%27Italia
- 112: Juventus FC v FC Inter: **other**, other -> other, "the name of the football derby between Internazionale of Milan and Juventus of Turin", C80 https://en.wikipedia.org/wiki/Derby_d%27Italia
- 687: Angers SCO v Football Club de Nantes: **main**, other -> main, "Le principal compétiteur du SCO d'Angers est le FC Nantes", C228 https://fr.wikipedia.org/wiki/Angers_Sporting_Club_de_l'Ouest

Notes on the readings:

- Rows 3, 4, 5, 10 and their partners (106, 107, 108) are `local` from the
  section heading **Local** of *German football rivalries* ("Domestic club
  football > Local"), under which the page lists these derbies; the quote is
  the list line, the heading is the page's class word. Rows 11, 17, 23, 25,
  26, 29, 37, 39 are table rows under "Regional" or "Inter-regional": the
  quote is the derby's name from the table, class `other`.
- Rows 109/110: "crosstown derbies" taken as the English for derby
  cittadino. Rows 19/31: "Hamburger Stadtderby" and "Hamburg city derby".
- Rows 8/18 (Dortmund v Schalke) stay `other`: the page says "the greatest
  rivalry in German football" (marked citation needed), not that either
  club is the other's main rival, and calls it a local derby only by
  implication ("A local derby between other Ruhr teams ... is often called a
  kleines Revierderby").
- Rows 98/99 (Cardiff v Swansea) are `local` from "a local derby"; the page
  also says Swansea "regarded Cardiff, Bristol City and Bristol Rovers as
  their main rivals" (three clubs, so not `main`).
- Row 13 (FC Augsburg v Schwaben Augsburg): the page's "local derby" is
  said of BC Augsburg (FC Augsburg's predecessor) v Schwaben; for FC
  Augsburg it says only "a game between", so `other`.
- Rows 27/35: the KSC page names Kaiserslautern among three clubs of
  "größte Abneigung"; not a main rival, `other`.
- Rows 29 and 39 stay `other` while their partner rows 408 and 409 are
  `local` from another source (C181); rows with different sources were not
  aligned.
- Row 67 (Botoșani v Foresta) is `other` from the same list line that phase 5
  used to make Iași's row `local`; phase 5 applied the older "derby = local"
  table, this phase the 18 Nov decision. Rows set `local` in phase 5 from a
  named derby alone (Linz, North-East, Derby van het Zuiden, Markermeerderby,
  Brentford v QPR) were not re-read.
- Row 687 (Angers v Nantes, extra): "Le principal compétiteur du SCO d'Angers
  est le FC Nantes" read again; `main` by the 18 Nov decision. Nantes has no
  row of its own for Angers, so no partner row changed.
- Every class change in the batch came with its partner row; all partners
  but 112 were in the batch. Row 112 (Juventus v Inter, extra) got the quote
  of row 111.

Counts, session 1 (100 batch rows): local 27, main 0, other with a quote 73,
not on the page 0, cannot verify 0. Extras: 687 to `main`, 112 `other` with a
quote. Probe runs used: 3 of 8.

Running total, phase 5b (sessions 1): local 27, main 1 (687), other with a
quote 74, not on the page 0, cannot verify 0; quote-less `other` rows left:
222 (of 323).

### Session 2 (2026-11-18, prompt version 2): batch

Class rule from this session on (coordinator's decision of 18 Nov 2026, as
reworded for version 2): `local` where the page calls the pair a local
derby (Lokalderby, Stadtderby, derby local, derby cittadino, derby della
città, stadsderby) or lists it under a section headed "Local", **or** where
the page names it a derby and both clubs play in the same city or
municipality (the grounds' places: the club files have no city, so the
places are taken from Wikidata, club `P115` venue -> `P131`, read by the
probe, or from the page); `main` where the page names the other club the
main rival; `other` for everything else, including a named derby between
clubs of different cities. Session 1 used the older wording (a named derby
alone never `local`); its rows are not re-read here.

Step 0 recount: 222 quote-less `other` rows (826 rows). Row 112 had no quote
before session 1 (323 then), so 323 - 100 - 1 = 222: the running total of
session 1 is right and was not changed.

Batch (100 row ids, lines 115-216; lines 139-140 have quotes): 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216.

Part D (first session of version 2): rows 51, 52 (Linz derby), 68
(North-East derby; Iași is not on the map, no partner row), 295, 296
(Brentford v QPR), 320, 321 (Derby van het Zuiden), 340, 341
(Markermeerderby).

### Session 2 (2026-11-18, prompt version 2): results

Per row: id, club v rival, verdict, class before -> after, quote, page (source id). Pages read in four probe runs (run1 6f52208, run2 5751531, run3 f2ee5ad, run4 48d014f; 60 + 32 + 8 + 4 requests, Wikipedia parse API and Wikidata `wbgetentities`). Batch rows first (115-216), then the Part D rows (51-341).

- 115: Juventus FC v Torino FC: **local**, other -> local, "the local derby played out between Turin's most prominent football clubs, Juventus and Torino", C82 https://en.wikipedia.org/wiki/Derby_della_Mole
- 116: Torino FC v Juventus FC: **local**, other -> local, "the local derby played out between Turin's most prominent football clubs, Juventus and Torino", C82 https://en.wikipedia.org/wiki/Derby_della_Mole
- 117: Genoa CFC v UC Sampdoria: **local**, other -> local, "Genoa's local derby, played by Genoa and Sampdoria", C83 https://en.wikipedia.org/wiki/Derby_della_Lanterna
- 118: UC Sampdoria v Genoa CFC: **local**, other -> local, "Genoa's local derby, played by Genoa and Sampdoria", C83 https://en.wikipedia.org/wiki/Derby_della_Lanterna
- 119: AS Roma v SSC Napoli: **other**, other -> other, "an Italian football derby between Napoli and Roma", C84 https://en.wikipedia.org/wiki/Derby_del_Sole
- 120: SSC Napoli v AS Roma: **other**, other -> other, "an Italian football derby between Napoli and Roma", C84 https://en.wikipedia.org/wiki/Derby_del_Sole
- 121: ACF Fiorentina v Juventus FC: **other**, other -> other, "an inter-city football rivalry contested between Florence-based Fiorentina and Turin-based Juventus", C85 https://en.wikipedia.org/wiki/ACF_Fiorentina%E2%80%93Juventus_FC_rivalry
- 122: Juventus FC v ACF Fiorentina: **other**, other -> other, "an inter-city football rivalry contested between Florence-based Fiorentina and Turin-based Juventus", C85 https://en.wikipedia.org/wiki/ACF_Fiorentina%E2%80%93Juventus_FC_rivalry
- 123: Juventus FC v AC Milan: **other**, other -> other, "the oldest running italian football rivalry", C86 https://en.wikipedia.org/wiki/Juventus_FC%E2%80%93AC_Milan_rivalry
- 124: AC Milan v Juventus FC: **other**, other -> other, "the oldest running italian football rivalry", C86 https://en.wikipedia.org/wiki/Juventus_FC%E2%80%93AC_Milan_rivalry
- 125: Juventus FC v SSC Napoli: **other**, other -> other, "an inter-city football rivalry contested between Turin-based Juventus and Naples-based Napoli", C87 https://en.wikipedia.org/wiki/Juventus_FC%E2%80%93SSC_Napoli_rivalry
- 126: SSC Napoli v Juventus FC: **other**, other -> other, "an inter-city football rivalry contested between Turin-based Juventus and Naples-based Napoli", C87 https://en.wikipedia.org/wiki/Juventus_FC%E2%80%93SSC_Napoli_rivalry
- 127: Bologna FC 1909 v ACF Fiorentina: **other**, other -> other, "a derby between Bologna FC 1909 and ACF Fiorentina, two football clubs in Italy", C88 https://en.wikipedia.org/wiki/Derby_dell%27Appennino
- 128: ACF Fiorentina v Bologna FC 1909: **other**, other -> other, "a derby between Bologna FC 1909 and ACF Fiorentina, two football clubs in Italy", C88 https://en.wikipedia.org/wiki/Derby_dell%27Appennino
- 129: Bologna FC 1909 v Parma Calcio 1913: **other**, other -> other, "the name given in football to any match between Bologna and Parma", C89 https://en.wikipedia.org/wiki/Derby_dell%27Emilia
- 130: Parma Calcio 1913 v Bologna FC 1909: **other**, other -> other, "the name given in football to any match between Bologna and Parma", C89 https://en.wikipedia.org/wiki/Derby_dell%27Emilia
- 131: SSC Napoli v Palermo FC: **other**, other -> other, "an Italian Serie A derby between the Napoli and Palermo football clubs", C90 https://en.wikipedia.org/wiki/Derby_delle_Due_Sicilie
- 132: Palermo FC v SSC Napoli: **other**, other -> other, "an Italian Serie A derby between the Napoli and Palermo football clubs", C90 https://en.wikipedia.org/wiki/Derby_delle_Due_Sicilie
- 133: Cagliari Calcio v Palermo FC: **other**, other -> other, "an Italian association football rivalry between Cagliari Calcio and Palermo", C91 https://en.wikipedia.org/wiki/Derby_delle_Isole
- 134: Palermo FC v Cagliari Calcio: **other**, other -> other, "an Italian association football rivalry between Cagliari Calcio and Palermo", C91 https://en.wikipedia.org/wiki/Derby_delle_Isole
- 135: Parma Calcio 1913 v A.C. Reggiana 1919: **other**, other -> other, "a historical rivalry between the cities of Parma and Reggio Emilia", C92 https://en.wikipedia.org/wiki/Derby_dell%27Enza
- 136: Palermo FC v Catania FC: **local**, other -> local, "a local derby between Italian football clubs Catania FC and Palermo FC", C93 https://en.wikipedia.org/wiki/Derby_di_Sicilia
- 137: FC Barcelona v Real Madrid Club de Fútbol: **other**, other -> other, "the name given to any football match between rival clubs Barcelona and Real Madrid", C94 https://en.wikipedia.org/wiki/El_Cl%C3%A1sico
- 138: Real Madrid Club de Fútbol v FC Barcelona: **other**, other -> other, "the name given to any football match between rival clubs Barcelona and Real Madrid", C94 https://en.wikipedia.org/wiki/El_Cl%C3%A1sico
- 141: FC Barcelona v RCD Espanyol de Barcelona: **other**, other -> other, "the name given to football matches between FC Barcelona and RCD Espanyol", C96 https://en.wikipedia.org/wiki/Derbi_Barcelon%C3%AD
- 142: RCD Espanyol de Barcelona v FC Barcelona: **other**, other -> other, "the name given to football matches between FC Barcelona and RCD Espanyol", C96 https://en.wikipedia.org/wiki/Derbi_Barcelon%C3%AD
- 143: Sevilla FC v Real Betis Balompié: **local**, other -> local, "the name of a local city derby located in Seville, Spain", C97 https://en.wikipedia.org/wiki/Seville_derby
- 144: Real Betis Balompié v Sevilla FC: **local**, other -> local, "the name of a local city derby located in Seville, Spain", C97 https://en.wikipedia.org/wiki/Seville_derby
- 145: Valencia CF v Levante UD: **local**, other -> local, "the two main clubs in the city of Valencia, Spain", C98 https://en.wikipedia.org/wiki/Valencia_derby
- 146: Levante UD v Valencia CF: **local**, other -> local, "the two main clubs in the city of Valencia, Spain", C98 https://en.wikipedia.org/wiki/Valencia_derby
- 147: Athletic Club v Real Sociedad: **local**, other -> local, "the football local derby between Real Sociedad and Athletic Bilbao", C99 https://en.wikipedia.org/wiki/Basque_derby
- 148: Real Sociedad v Athletic Club: **local**, other -> local, "the football local derby between Real Sociedad and Athletic Bilbao", C99 https://en.wikipedia.org/wiki/Basque_derby
- 149: Real Oviedo v Sporting de Gijón: **other**, other -> other, "any association football match contested between Sporting de Gijón and Real Oviedo", C100 https://en.wikipedia.org/wiki/Asturian_derby
- 150: Sporting de Gijón v Real Oviedo: **other**, other -> other, "any association football match contested between Sporting de Gijón and Real Oviedo", C100 https://en.wikipedia.org/wiki/Asturian_derby
- 151: C.D. Tenerife v UD Las Palmas: **other**, other -> other, "any football match contested between Spanish sides UD Las Palmas and CD Tenerife", C101 https://en.wikipedia.org/wiki/Canary_Islands_derby
- 152: UD Las Palmas v C.D. Tenerife: **other**, other -> other, "any football match contested between Spanish sides UD Las Palmas and CD Tenerife", C101 https://en.wikipedia.org/wiki/Canary_Islands_derby
- 153: Valencia CF v Villarreal CF: **other**, other -> other, "regional football rivalry in Spain between La Liga clubs Valencia CF and Villarreal CF", C102 https://en.wikipedia.org/wiki/Derbi_de_la_Comunitat
- 154: Villarreal CF v Valencia CF: **other**, other -> other, "regional football rivalry in Spain between La Liga clubs Valencia CF and Villarreal CF", C102 https://en.wikipedia.org/wiki/Derbi_de_la_Comunitat
- 155: Granada CF v Málaga CF: **other**, other -> other, "a running football club rivalry in the Eastern Andalusia", C103 https://en.wikipedia.org/wiki/Derby_of_eastern_Andalusia
- 156: Málaga CF v Granada CF: **other**, other -> other, "a running football club rivalry in the Eastern Andalusia", C103 https://en.wikipedia.org/wiki/Derby_of_eastern_Andalusia
- 157: Getafe CF v CD Leganés: **other**, other -> other, "any association football match contested between Getafe CF and CD Leganés", C104 https://en.wikipedia.org/wiki/South_Madrid_derby
- 158: CD Leganés v Getafe CF: **other**, other -> other, "any association football match contested between Getafe CF and CD Leganés", C104 https://en.wikipedia.org/wiki/South_Madrid_derby
- 159: Atlético Madrid v FC Barcelona: **other**, other -> other, "the name given to football matches between Atlético de Madrid and Barcelona", C105 https://en.wikipedia.org/wiki/El_Otro_Cl%C3%A1sico
- 160: FC Barcelona v Atlético Madrid: **other**, other -> other, "the name given to football matches between Atlético de Madrid and Barcelona", C105 https://en.wikipedia.org/wiki/El_Otro_Cl%C3%A1sico
- 161: Athletic Club v Real Madrid Club de Fútbol: **other**, other -> other, "the name given to any football match between Athletic Bilbao and Real Madrid", C106 https://en.wikipedia.org/wiki/El_Viejo_Cl%C3%A1sico
- 162: Real Madrid Club de Fútbol v Athletic Club: **other**, other -> other, "the name given to any football match between Athletic Bilbao and Real Madrid", C106 https://en.wikipedia.org/wiki/El_Viejo_Cl%C3%A1sico
- 163: Athletic Club v FC Barcelona: **other**, other -> other, "football matches between Athletic Bilbao and FC Barcelona", C107 https://en.wikipedia.org/wiki/Athletic%E2%80%93Barcelona_cl%C3%A1sico
- 164: FC Barcelona v Athletic Club: **other**, other -> other, "football matches between Athletic Bilbao and FC Barcelona", C107 https://en.wikipedia.org/wiki/Athletic%E2%80%93Barcelona_cl%C3%A1sico
- 165: RCD Mallorca v CD Atlético Baleares: **local**, other -> local, "the derby between the main football clubs in Palma de Mallorca", C108 https://en.wikipedia.org/wiki/Palma_derby
- 166: CE Sabadell FC v Terrassa FC: **other**, other -> other, "the name given to football matches between CE Sabadell and Terrassa FC", C109 https://en.wikipedia.org/wiki/Vall%C3%A8s_derby
- 167: Paris Saint-Germain FC v Olympique de Marseille: **other**, other -> other, "French football rivalry contested between French professional clubs Paris Saint-Germain", C110 https://en.wikipedia.org/wiki/Le_Classique
- 168: Olympique de Marseille v Paris Saint-Germain FC: **other**, other -> other, "French football rivalry contested between French professional clubs Paris Saint-Germain", C110 https://en.wikipedia.org/wiki/Le_Classique
- 169: Olympique lyonnais v Olympique de Marseille: **other**, other -> other, "the football rivalry between two major teams in French football", C111 https://en.wikipedia.org/wiki/Choc_des_Olympiques
- 170: Olympique de Marseille v Olympique lyonnais: **other**, other -> other, "the football rivalry between two major teams in French football", C111 https://en.wikipedia.org/wiki/Choc_des_Olympiques
- 171: RC Lens v Lille OSC: **other**, other -> other, "located in different departments, with Lens being in Pas-de-Calais, and Lille in Nord", C112 https://en.wikipedia.org/wiki/Derby_du_Nord
- 172: Lille OSC v RC Lens: **other**, other -> other, "located in different departments, with Lens being in Pas-de-Calais, and Lille in Nord", C112 https://en.wikipedia.org/wiki/Derby_du_Nord
- 173: Olympique lyonnais v AS Saint-Étienne: **other**, other -> other, "a football rivalry between French clubs Olympique Lyonnais and AS Saint-Étienne", C113 https://en.wikipedia.org/wiki/Olympique_Lyonnais%E2%80%93AS_Saint-%C3%89tienne_rivalry
- 174: AS Saint-Étienne v Olympique lyonnais: **other**, other -> other, "a football rivalry between French clubs Olympique Lyonnais and AS Saint-Étienne", C113 https://en.wikipedia.org/wiki/Olympique_Lyonnais%E2%80%93AS_Saint-%C3%89tienne_rivalry
- 175: AS Monaco FC v OGC Nice: **other**, other -> other, "a football match contested between Ligue 1 clubs AS Monaco and OGC Nice", C114 https://en.wikipedia.org/wiki/Derby_de_la_C%C3%B4te_d%27Azur
- 176: OGC Nice v AS Monaco FC: **other**, other -> other, "a football match contested between Ligue 1 clubs AS Monaco and OGC Nice", C114 https://en.wikipedia.org/wiki/Derby_de_la_C%C3%B4te_d%27Azur
- 177: Paris Saint-Germain FC v Paris FC: **local**, other -> local, "the two largest professional clubs based in Paris, France", C115 https://en.wikipedia.org/wiki/Paris_derby
- 178: Paris FC v Paris Saint-Germain FC: **local**, other -> local, "the two largest professional clubs based in Paris, France", C115 https://en.wikipedia.org/wiki/Paris_derby
- 179: AS Nancy-Lorraine v FC Metz: **other**, other -> other, "a football match contested between French clubs Metz and Nancy", C116 https://en.wikipedia.org/wiki/Derby_Lorrain
- 180: FC Metz v AS Nancy-Lorraine: **other**, other -> other, "a football match contested between French clubs Metz and Nancy", C116 https://en.wikipedia.org/wiki/Derby_Lorrain
- 181: Toulouse FC v FC Girondins de Bordeaux: **other**, other -> other, "a football match contested between French clubs FC Girondins de Bordeaux and Toulouse FC", C117 https://en.wikipedia.org/wiki/Derby_de_la_Garonne
- 182: OGC Nice v SC Bastia: **other**, other -> other, "football match between Bastia and Nice, first contested in 1968", C118 https://en.wikipedia.org/wiki/Derby_de_la_Mediterran%C3%A9e
- 183: En avant Guingamp v FC Lorient: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 184: FC Lorient v En avant Guingamp: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 185: En avant Guingamp v Stade rennais FC: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 186: Stade rennais FC v En avant Guingamp: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 187: FC Lorient v Stade rennais FC: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 188: Stade rennais FC v FC Lorient: **other**, other -> other, "may also refer to matches involving FC Lorient, En Avant Guingamp or Stade Brestois", C119 https://en.wikipedia.org/wiki/Derby_Breton
- 189: AFC Ajax v Feyenoord Rotterdam: **main**, other -> main, "Ajax fans were outraged that Cruyff had jumped to their biggest rival", C120 https://en.wikipedia.org/wiki/De_Klassieker
- 190: Feyenoord Rotterdam v AFC Ajax: **other**, other -> other, "the main football rivalry of the Netherlands", C120 https://en.wikipedia.org/wiki/De_Klassieker
- 191: AFC Ajax v PSV Eindhoven: **other**, other -> other, "one of the main football rivalries of the Netherlands", C121 https://en.wikipedia.org/wiki/AFC_Ajax%E2%80%93PSV_Eindhoven_rivalry
- 192: PSV Eindhoven v AFC Ajax: **other**, other -> other, "one of the main football rivalries of the Netherlands", C121 https://en.wikipedia.org/wiki/AFC_Ajax%E2%80%93PSV_Eindhoven_rivalry
- 193: FC Groningen v SC Heerenveen: **other**, other -> other, "a match between the Dutch football clubs FC Groningen and SC Heerenveen", C122 https://en.wikipedia.org/wiki/Derby_of_the_North
- 194: SC Heerenveen v FC Groningen: **other**, other -> other, "a match between the Dutch football clubs FC Groningen and SC Heerenveen", C122 https://en.wikipedia.org/wiki/Derby_of_the_North
- 195: Go Ahead Eagles v PEC Zwolle: **other**, other -> other, "Go Ahead Eagles from Deventer, and PEC Zwolle from Zwolle", C123 https://en.wikipedia.org/wiki/IJsselderby
- 196: PEC Zwolle v Go Ahead Eagles: **other**, other -> other, "Go Ahead Eagles from Deventer, and PEC Zwolle from Zwolle", C123 https://en.wikipedia.org/wiki/IJsselderby
- 197: FC Twente v Heracles Almelo: **other**, other -> other, "a Dutch football derby between FC Twente and Heracles Almelo", C124 https://en.wikipedia.org/wiki/Twentse_derby
- 198: Heracles Almelo v FC Twente: **other**, other -> other, "a Dutch football derby between FC Twente and Heracles Almelo", C124 https://en.wikipedia.org/wiki/Twentse_derby
- 199: R.S.C. Anderlecht v Club Brugge K.V.: **other**, other -> other, "a football rivalry between two Belgian Pro League clubs Anderlecht and Club Brugge", C125 https://en.wikipedia.org/wiki/RSC_Anderlecht%E2%80%93Club_Brugge_KV_rivalry
- 200: Club Brugge K.V. v R.S.C. Anderlecht: **other**, other -> other, "a football rivalry between two Belgian Pro League clubs Anderlecht and Club Brugge", C125 https://en.wikipedia.org/wiki/RSC_Anderlecht%E2%80%93Club_Brugge_KV_rivalry
- 201: Club Brugge K.V. v Cercle Brugge K.S.V.: **local**, other -> local, "The Bruges derby (Dutch: Brugse stadsderby, French: derby de Bruges)", C126 https://en.wikipedia.org/wiki/Bruges_derby
- 202: Cercle Brugge K.S.V. v Club Brugge K.V.: **local**, other -> local, "The Bruges derby (Dutch: Brugse stadsderby, French: derby de Bruges)", C126 https://en.wikipedia.org/wiki/Bruges_derby
- 203: SK Beveren v KSC Lokeren: **other**, other -> other, "the supporters of both clubs demanded the derby", C127 https://en.wikipedia.org/wiki/Waasland_derby
- 204: KSC Lokeren v SK Beveren: **other**, other -> other, "the supporters of both clubs demanded the derby", C127 https://en.wikipedia.org/wiki/Waasland_derby
- 205: Olympiacos F.C. v Panathinaikos F.C.: **other**, other -> other, "an association football derby contested between the two most successful clubs of Greece", C128 https://en.wikipedia.org/wiki/Derby_of_the_Eternal_Enemies
- 206: Panathinaikos F.C. v Olympiacos F.C.: **other**, other -> other, "an association football derby contested between the two most successful clubs of Greece", C128 https://en.wikipedia.org/wiki/Derby_of_the_Eternal_Enemies
- 207: AEK Athens F.C. v Panathinaikos F.C.: **local**, other -> local, "the football local derby in the Athens urban area", C129 https://en.wikipedia.org/wiki/Athenian_derby
- 208: Panathinaikos F.C. v AEK Athens F.C.: **local**, other -> local, "the football local derby in the Athens urban area", C129 https://en.wikipedia.org/wiki/Athenian_derby
- 209: AEK Athens F.C. v Olympiacos F.C.: **local**, other -> local, "a football local derby played between AEK Athens and Olympiacos", C130 https://en.wikipedia.org/wiki/A.E.K.%E2%80%93Olympiacos_rivalry
- 210: Olympiacos F.C. v AEK Athens F.C.: **local**, other -> local, "a football local derby played between AEK Athens and Olympiacos", C130 https://en.wikipedia.org/wiki/A.E.K.%E2%80%93Olympiacos_rivalry
- 211: PAOK FC v Aris Thessaloniki F.C.: **local**, other -> local, "local rivalry between Aris and PAOK, both of which are based in Thessaloniki", C131 https://en.wikipedia.org/wiki/Derby_of_Thessaloniki
- 212: Aris Thessaloniki F.C. v PAOK FC: **local**, other -> local, "local rivalry between Aris and PAOK, both of which are based in Thessaloniki", C131 https://en.wikipedia.org/wiki/Derby_of_Thessaloniki
- 213: AEK Athens F.C. v PAOK FC: **other**, other -> other, "a football derby between AEK Athens and PAOK", C132 https://en.wikipedia.org/wiki/Double-headed_eagles_derby
- 214: PAOK FC v AEK Athens F.C.: **other**, other -> other, "a football derby between AEK Athens and PAOK", C132 https://en.wikipedia.org/wiki/Double-headed_eagles_derby
- 215: Olympiacos F.C. v PAOK FC: **other**, other -> other, "the most intense intercity rivalry in Greek football", C133 https://en.wikipedia.org/wiki/Olympiacos%E2%80%93PAOK_rivalry
- 216: PAOK FC v Olympiacos F.C.: **other**, other -> other, "the most intense intercity rivalry in Greek football", C133 https://en.wikipedia.org/wiki/Olympiacos%E2%80%93PAOK_rivalry

Part D rows:

- 51: FC Blau-Weiß Linz v LASK: **local**, local -> local, "Linz Derby: FC Blau-Weiß Linz vs. LASK Linz", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 52: LASK v FC Blau-Weiß Linz: **local**, local -> local, "Linz Derby: FC Blau-Weiß Linz vs. LASK Linz", C64 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Austria
- 68: FC Botoșani v CSM Politehnica Iași: **other**, local -> other, "North-East derby: FC Botoşani vs Foresta Suceava vs Politehnica Iași", C71 https://en.wikipedia.org/wiki/List_of_association_football_club_rivalries_in_Europe#Romania
- 295: Brentford F.C. v Queens Park Rangers F.C.: **local**, local -> local, "The West London derby is a local football rivalry", C175 https://en.wikipedia.org/wiki/West_London_derby
- 296: Queens Park Rangers F.C. v Brentford F.C.: **local**, local -> local, "The West London derby is a local football rivalry", C175 https://en.wikipedia.org/wiki/West_London_derby
- 320: MVV Maastricht v Fortuna Sittard: **other**, local -> other, "Derby van het Zuiden: MVV Maastricht vs. Fortuna Sittard", C178 https://en.wikipedia.org/wiki/Football_derbies_in_the_Netherlands
- 321: Fortuna Sittard v MVV Maastricht: **other**, local -> other, "Derby van het Zuiden: MVV Maastricht vs. Fortuna Sittard", C178 https://en.wikipedia.org/wiki/Football_derbies_in_the_Netherlands
- 340: Almere City FC v FC Volendam: **other**, local -> other, "Markermeerderby: Almere City FC vs. FC Volendam", C178 https://en.wikipedia.org/wiki/Football_derbies_in_the_Netherlands
- 341: FC Volendam v Almere City FC: **other**, local -> other, "Markermeerderby: Almere City FC vs. FC Volendam", C178 https://en.wikipedia.org/wiki/Football_derbies_in_the_Netherlands

Notes on the readings:

- **`local` by the second clause (named derby, same city)**: 145/146
  (Valencia derby: "the two main clubs in the city of Valencia"; Wikidata
  `P131` of Mestalla is a disambiguation item, so the city is the page's),
  165 (Palma derby: "the main football clubs in Palma de Mallorca"), 177/178
  (Paris derby: "based in Paris"; grounds in the 16th and 13th
  arrondissements), 211/212 (Derby of Thessaloniki: "both of which are based
  in Thessaloniki"; both grounds in Thessaloniki Municipality). The quote is
  the city phrase; the derby is the article's own subject.
- **`local` by the first clause although the grounds are in different
  cities**: 136 (Catania v Palermo, "a local derby"), 147/148 (Real Sociedad
  v Athletic, San Sebastián v Bilbao, "local derby"), 207/208 (AEK in Nea
  Filadelfeia v Panathinaikos in Athens, "local derby in the Athens urban
  area"), 209/210 (AEK v Olympiacos of Piraeus, "local derby"). The rule
  takes the page's words; see open-problems.md.
- **Named derby, different cities, so `other`**: 205/206 (Olympiacos "from
  Piraeus" v Panathinaikos; grounds in Piraeus and Athens municipalities),
  197/198 (Twente's ground in Enschede, Heracles in Almelo; Wikidata labels
  read in run4), 195/196, 213/214, and every other derby of the batch whose
  page names two cities. **141/142 (Derbi Barceloní) is `other`** because
  Espanyol's ground is in Cornellà de Llobregat (Wikidata), not Barcelona;
  the page calls it the "Barcelonian derby"; no sentence the probe posted
  calls it a local derby.
- **189 (Ajax v Feyenoord) `main`** from "Ajax fans were outraged that Cruyff
  had jumped to their biggest rival". **The partner row 190 was NOT made
  `main`**: the page says Feyenoord is Ajax's biggest rival, not the
  reverse, and a class is the stating club's view; 190 got the page's lead
  phrase and stays `other`. This departs from the partner instruction; it is
  written up for Alexandru.
- **Arch-rival wording left `other`**: 121/122 (the Fiorentina page says
  Fiorentina met "their arch-nemesis Juventus" in the 1990 UEFA Cup final)
  and 167/168 (PSG and Marseille "emerged as arch-rivals" in the early
  1990s). The version 2 rule lists "main rival" and "biggest rival", not
  arch-rival; session 1's method counted arch-rival as `main`.
- 199/200: the page says Dutch speakers call Anderlecht v Club Brugge "the
  main derby"; a main derby of a country is not a club's main rival, `other`.
- 203/204: the page's derby is KSK Beveren v Sporting Lokeren (both gone);
  the quote is from its sentence on the supporters of SK Beveren and KSC
  Lokeren-Temse demanding the derby again, which the page says KSK Beveren
  supporters question.
- 183-188 (Breton derby, Guingamp, Lorient, Rennes): the page's principal
  Breton rivalry is Rennes v Nantes (no row in the batch); the three pairs
  of the batch are "matches involving" the other Breton clubs, `other`.
- Every class change came with its partner row (all partners were in the
  batch), except row 190 above. Rows 135, 136, 165, 166, 181, 182 have no
  rival on the map, so no partner row.

Part D (the five pairs phase 5 made `local` from a named derby):

- Linz derby (51/52): **kept `local`**: "Linz Derby: FC Blau-Weiß Linz vs. LASK
  Linz", both grounds in Linz (Wikidata).
- North-East derby (68): **`local` -> `other`**: FC Botoșani v Politehnica
  Iași, different cities, listed under "Romania", no local wording.
- Brentford v QPR (295/296): **kept `local`**: the page calls the West London
  derby "a local football rivalry"; QPR's ground is in London (Wikidata),
  Brentford's `P115` is still Griffin Park (Brentford, London). The quote was
  changed from the section heading to that lead phrase.
- Derby van het Zuiden (320/321): **`local` -> `other`**: MVV Maastricht v
  Fortuna Sittard, grounds in Maastricht and Sittard-Geleen.
- Markermeerderby (340/341): **`local` -> `other`**: Almere City FC v FC
  Volendam, grounds in Almere and Edam-Volendam.

Counts, session 2 (100 batch rows): local 22, main 1 (189), other with a
quote 77, not on the page 0, cannot verify 0. Part D: 4 rows kept `local`,
5 rows `local` -> `other`. Probe runs used: 4 of 8.

Running total, phase 5b (sessions 1-2): local 49, main 2 (687, 189), other
with a quote 151, not on the page 0, cannot verify 0; quote-less `other`
rows left: 122 (of 323).

### Session 3 (2026-11-18, prompt version 3): batch

Class rule from this session on (coordinator's decision of 18 Nov 2026,
version 3, replacing versions 1 and 2): `local` where the page calls the
pair a local derby (or Lokalderby, Stadtderby, derby local, derby
cittadino, derby della città, stadsderby) or lists it under a section
headed "Local", **or** where the page names it a derby (any named derby)
and the two grounds are at most 20 km apart in a straight line, from the
coordinates in `data/clubs/*.json` (the distance is written per row);
`local` applies to both rows of the pair. `main` where the page names the
other club as this club's main, biggest or arch-rival; one-directional, it
is set only on the row of the club the page says it about, and it beats
`local` for that row. `other` for everything else the page names. Part A
re-applies this rule to every row already classified (phase 5 and phase
5b sessions 1 and 2).

Step 0 recount: 122 quote-less `other` rows (826 rows), as session 2 left.

Batch (100 row ids, lines 217-324; lines 219, 234, 235, 255, 295, 296,
320, 321 have quotes): 217, 218, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 322, 323, 324.
