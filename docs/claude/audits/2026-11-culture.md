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
