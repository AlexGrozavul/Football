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
